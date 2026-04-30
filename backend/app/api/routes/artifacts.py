from __future__ import annotations

"""Artifact ingestion and inspection APIs (Phase 2).

This module defines endpoints for creating and inspecting ingested artifacts.

Scope and invariants:
- Phase 2 supports **text** and **Markdown** artifacts only.
- Artifact creation delegates ingestion orchestration to `TextIngestionService`,
  which is responsible for creating the Artifact + Evidence Units.
- Pagination uses `limit`/`offset` (offset-based, deterministic ordering owned by
  the repository).
- Identifiers are UUIDs provided as strings at the HTTP boundary.

Error semantics:
- Unsupported file types and ingestion validation errors return HTTP 400.
- Unknown artifact IDs return HTTP 404.
- Invalid UUID strings raise a 422 validation error via FastAPI/Starlette.
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
from app.services.errors import GraphClerkError
from app.services.text_ingestion_service import TextIngestionService

router = APIRouter(prefix="", tags=["artifacts"])


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
    """Create an artifact and ingest it into Evidence Units (Phase 2).

    Input modes:
    - Multipart upload via `file` (preferred for real uploads).
    - Inline JSON payload (required because mixing `File` and JSON `Body` is
      awkward in FastAPI signatures).

    Returns HTTP 400 for unsupported file types or ingestion validation errors.
    """

    settings = get_settings()
    SessionMaker = get_sessionmaker()

    if file is not None:
        content_bytes = await file.read()
        filename = file.filename or "upload.txt"
        mime_type = file.content_type

        lower = filename.lower()
        if lower.endswith((".md", ".markdown")):
            artifact_type = "markdown"
        elif lower.endswith(".txt") or (mime_type or "").startswith("text/"):
            artifact_type = "text"
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type for Phase 2 (text/markdown only).")
        title = None
    else:
        # JSON inline mode (can't rely on Body model when File is in signature)
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

    svc = TextIngestionService(settings=settings)
    with SessionMaker() as session:
        try:
            result = svc.ingest(
                session=session,
                filename=filename,
                artifact_type=artifact_type,
                mime_type=mime_type,
                content_bytes=content_bytes,
                title=title,
                metadata={"ingestion_phase": "phase_2_text_first_ingestion"},
            )
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

