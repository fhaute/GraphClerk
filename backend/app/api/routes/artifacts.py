from __future__ import annotations

"""Artifact ingestion and inspection APIs (Phase 2 + Phase 5 shell).

Multipart uploads:
- **text** and **markdown** delegate to ``TextIngestionService`` (unchanged Phase 2).
- Known **multimodal** types (pdf, pptx, image, audio) delegate to
  ``MultimodalIngestionService`` with ``ExtractorRegistry``. **PDF:** ``PdfExtractor``
  is registered when the optional ``pdf`` extra (pypdf) is installed; otherwise
  PDF uploads return **503** with an install hint.

Inline JSON remains **text** / **markdown** only.

Error semantics at ``POST /artifacts``:
- ``UnsupportedArtifactTypeError``, ``ExtractorNotRegisteredError``,
  ``ExtractionReturnedNoEvidenceError``, and most ``GraphClerkError`` → **400**.
- ``ExtractorUnavailableError`` → **503**.
"""

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.core.config import get_settings
from app.db.session import get_sessionmaker
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.artifact import (
    ArtifactCreateInlineRequest,
    ArtifactCreateResponse,
    ArtifactListResponse,
    ArtifactResponse,
)
from app.models.artifact import Artifact
from app.models.enums import Modality
from app.schemas.evidence_unit_candidate import EvidenceUnitCandidate
from app.services.errors import ExtractorUnavailableError, GraphClerkError, UnsupportedArtifactTypeError
from app.services.extraction import ExtractorRegistry
from app.services.multimodal_ingestion_service import MultimodalIngestionService
from app.services.text_ingestion_service import TextIngestionService

router = APIRouter(prefix="", tags=["artifacts"])


class _PdfDependencyPlaceholder:
    """Registers for ``Modality.pdf`` when pypdf is not installed so uploads fail with 503, not fake success."""

    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        raise ExtractorUnavailableError(
            "PDF extraction requires the optional `pdf` dependency (e.g. pip install -e '.[pdf]').",
        )


def get_multimodal_extractor_registry() -> ExtractorRegistry:
    """Return the multimodal ``ExtractorRegistry`` (tests may monkeypatch this).

    Registers ``PdfExtractor`` when pypdf is available; otherwise a placeholder
    that raises ``ExtractorUnavailableError``. Does not register video.
    """

    from app.services.extraction import pdf_extractor as pdf_extraction_module

    reg = ExtractorRegistry()
    if pdf_extraction_module.PdfReader is None:
        reg.register(Modality.pdf, _PdfDependencyPlaceholder())
    else:
        from app.services.extraction.pdf_extractor import PdfExtractor

        reg.register(Modality.pdf, PdfExtractor(settings=get_settings()))
    return reg


def _resolve_multipart_artifact_type(filename: str, mime_type: str | None) -> str:
    """Classify multipart upload as text, markdown, or multimodal ``artifact_type``.

    Raises:
        UnsupportedArtifactTypeError: unknown types or deferred video.
    """

    lower = filename.lower()
    mt = (mime_type or "").lower()

    if lower.endswith((".md", ".markdown")):
        return "markdown"
    if lower.endswith(".txt") or mt.startswith("text/"):
        return "text"

    if lower.endswith((".mp4", ".webm", ".mov", ".mkv", ".avi")) or mt.startswith("video/"):
        raise UnsupportedArtifactTypeError("Video ingestion is not supported.")

    if lower.endswith(".pdf") or mt == "application/pdf":
        return "pdf"
    if lower.endswith(".pptx") or mt == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        return "pptx"
    image_ext = (".png", ".jpg", ".jpeg", ".webp")
    if lower.endswith(image_ext) or mt.startswith("image/"):
        return "image"
    audio_ext = (".mp3", ".wav", ".m4a", ".ogg", ".flac")
    if lower.endswith(audio_ext) or mt.startswith("audio/"):
        return "audio"

    raise UnsupportedArtifactTypeError(f"Unsupported file type for ingestion: {filename!r}.")


def _artifact_to_response(a) -> ArtifactResponse:
    """Convert an Artifact ORM model into its API response schema."""
    return ArtifactResponse(
        id=str(a.id),
        filename=a.filename,
        title=a.title,
        artifact_type=a.artifact_type,
        mime_type=a.mime_type,
        storage_uri=a.storage_uri,
        checksum=a.checksum,
        size_bytes=a.size_bytes,
        created_at=a.created_at,
        updated_at=a.updated_at,
        metadata=a.metadata_json,
    )


@router.post("/artifacts", response_model=ArtifactCreateResponse)
async def create_artifact(
    request: Request,
    file: UploadFile | None = File(default=None),
) -> ArtifactCreateResponse:
    """Create an artifact and ingest it into Evidence Units."""

    settings = get_settings()
    SessionMaker = get_sessionmaker()

    if file is not None:
        content_bytes = await file.read()
        filename = file.filename or "upload.txt"
        mime_type = file.content_type
        try:
            artifact_type = _resolve_multipart_artifact_type(filename, mime_type)
        except UnsupportedArtifactTypeError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        title = None
    else:
        try:
            payload = await request.json()
        except Exception as e:
            raise HTTPException(status_code=400, detail="Provide either multipart file upload or JSON inline payload.") from e

        inline = ArtifactCreateInlineRequest.model_validate(payload)
        content_bytes = inline.text.encode("utf-8")
        filename = inline.filename
        mime_type = inline.mime_type
        artifact_type = inline.artifact_type
        title = inline.title

    with SessionMaker() as session:
        try:
            if artifact_type in {"text", "markdown"}:
                svc = TextIngestionService(settings=settings)
                result = svc.ingest(
                    session=session,
                    filename=filename,
                    artifact_type=artifact_type,
                    mime_type=mime_type,
                    content_bytes=content_bytes,
                    title=title,
                    metadata={"ingestion_phase": "phase_2_text_first_ingestion"},
                )
            else:
                mm = MultimodalIngestionService(settings=settings, registry=get_multimodal_extractor_registry())
                result = mm.ingest(
                    session=session,
                    filename=filename,
                    artifact_type=artifact_type,
                    mime_type=mime_type,
                    content_bytes=content_bytes,
                    title=title,
                    metadata={"ingestion_phase": "phase_5_multimodal_ingestion"},
                )
        except ExtractorUnavailableError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e
        except GraphClerkError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    return ArtifactCreateResponse(
        artifact_id=str(result.artifact.id),
        status="ingested",
        artifact_type=result.artifact.artifact_type,
        evidence_unit_count=result.evidence_unit_count,
    )


@router.get("/artifacts", response_model=ArtifactListResponse)
def list_artifacts(limit: int = 100, offset: int = 0) -> ArtifactListResponse:
    """List artifacts (newest-first ordering is defined by the repository)."""
    settings = get_settings()
    SessionMaker = get_sessionmaker()
    _ = settings

    with SessionMaker() as session:
        repo = ArtifactRepository(session)
        items = repo.list(limit=limit, offset=offset)
        return ArtifactListResponse(items=[_artifact_to_response(a) for a in items])


@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
def get_artifact(artifact_id: str) -> ArtifactResponse:
    """Fetch a single artifact by id.

    Returns 404 if the artifact does not exist.
    """
    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        repo = ArtifactRepository(session)
        a = repo.get(_uuid(artifact_id))
        if a is None:
            raise HTTPException(status_code=404, detail="Artifact not found.")
        return _artifact_to_response(a)


def _uuid(value: str):
    """Parse a UUID string into a `uuid.UUID` for repository/service calls."""
    import uuid

    return uuid.UUID(value)
