from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.core.config import Settings, get_settings
from app.db.session import get_sessionmaker
from app.models.artifact import Artifact
from app.models.enums import Modality
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.artifact import (
    ArtifactCreateInlineRequest,
    ArtifactCreateResponse,
    ArtifactListResponse,
    ArtifactResponse,
)
from app.schemas.evidence_unit_candidate import EvidenceUnitCandidate
from app.services.errors import (
    ExtractorUnavailableError,
    GraphClerkError,
    LanguageDetectionUnavailableError,
    UnsupportedArtifactTypeError,
)
from app.services.evidence_enrichment_service import EvidenceEnrichmentService
from app.services.extraction import ExtractorRegistry
from app.services.ingestion.artifact_type_resolver import resolve_from_filename_and_mime
from app.services.language_detection_service import build_language_detection_service
from app.services.model_pipeline_candidate_projection_service import (
    ModelPipelineCandidateMetadataProjectionService,
)
from app.services.model_pipeline_contracts import ModelPipelineAdapter, ModelPipelineRole
from app.services.model_pipeline_metadata_enrichment_service import (
    ModelPipelineMetadataEnrichmentService,
)
from app.services.model_pipeline_ollama_adapter import OllamaModelPipelineAdapter
from app.services.model_pipeline_output_validation_service import (
    ModelPipelineOutputValidationService,
)
from app.services.model_pipeline_purpose_registry import (
    ModelPipelinePurposeResolution,
    build_default_model_pipeline_purpose_registry,
    resolve_model_pipeline_purpose,
)
from app.services.multimodal_ingestion_service import MultimodalIngestionService
from app.services.text_ingestion_service import TextIngestionService

__doc__ = """Artifact ingestion and inspection APIs (Phase 2 + Phase 5 shell).

Multipart uploads:
- **text** and **markdown** delegate to ``TextIngestionService``.
- Known **multimodal** types (pdf, pptx, image, audio) delegate to
  ``MultimodalIngestionService`` with ``ExtractorRegistry``. **PDF:** ``PdfExtractor``
  when optional ``pdf`` extra is installed; else **503** with install hint.
  **PPTX:** ``PptxExtractor`` when optional ``pptx`` extra is installed; else **503**.
  **Image:** ``ImageExtractor`` when optional ``image`` extra (Pillow) is installed;
  validates bytes then **503** until OCR/caption is approved in a later slice; if Pillow
  is missing, **503** with install hint.
  **Audio:** ``AudioExtractor`` when optional ``audio`` extra (mutagen) is installed;
  validates bytes then **503** until transcription is approved in a later slice; if
  mutagen is missing, **503** with install hint.

Inline JSON remains **text** / **markdown** only.

Error semantics at ``POST /artifacts``:
- ``UnsupportedArtifactTypeError``, ``ExtractorNotRegisteredError``,
  ``ExtractionReturnedNoEvidenceError``, and most ``GraphClerkError`` → **400**.
- ``ExtractorUnavailableError`` → **503**.
- ``LanguageDetectionUnavailableError`` when ``GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER=lingua``
  but Lingua cannot be constructed (e.g. optional extra missing) → **503** (fail loud).
- Track **D6:** ``GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED`` (default **false**) gates
  optional **metadata-only** model enrichment after language enrichment; requires
  ``GRAPHCLERK_MODEL_PIPELINE_ADAPTER=ollama``, non-empty ``GRAPHCLERK_MODEL_PIPELINE_BASE_URL``,
  and non-empty ``GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL``. Misconfiguration fails at
  ``Settings`` parse time. Runtime adapter failures do **not** block ingestion.
"""

router = APIRouter(prefix="", tags=["artifacts"])


def build_evidence_enricher_model_pipeline_adapter(
    settings: Settings,
    resolution: ModelPipelinePurposeResolution,
) -> ModelPipelineAdapter:
    """Build Ollama adapter for ``evidence_candidate_enricher`` (purpose model + timeout).

    Monkeypatch this in tests to inject deterministic adapters (no live HTTP).
    """

    timeout = float(resolution.timeout_seconds or settings.model_pipeline_timeout_seconds)
    base = settings.model_pipeline_base_url
    model = resolution.model
    if base is None or not str(base).strip():
        msg = "GRAPHCLERK_MODEL_PIPELINE_BASE_URL required for evidence enricher adapter"
        raise ValueError(msg)
    if model is None or not str(model).strip():
        msg = "resolved purpose model required for evidence enricher adapter"
        raise ValueError(msg)
    return OllamaModelPipelineAdapter(
        base_url=str(base).strip(),
        model=str(model).strip(),
        timeout_seconds=timeout,
    )


def build_evidence_enrichment_service(settings: Settings) -> EvidenceEnrichmentService:
    """Build enrichment for ``POST /artifacts`` from settings.

    Language:

    - ``not_configured``: no language detector calls.
    - ``lingua``: ``LanguageDetectionService`` from ``build_language_detection_service``.
      Raises ``LanguageDetectionUnavailableError`` if the optional ``language-detector``
      extra is missing — **no** silent fallback to ``not_configured``.

    Model metadata (Track D6):

    - ``GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED``: when **true**, compose
      ``ModelPipelineMetadataEnrichmentService`` after language enrichment (same ordering
      for text and multimodal). Adapter build uses
      ``build_evidence_enricher_model_pipeline_adapter``.

    The same instance should be passed to both text and multimodal ingestion services
    within a single request.
    """

    language_detection = None
    if settings.language_detection_adapter == "lingua":
        language_detection = build_language_detection_service(settings)
    elif settings.language_detection_adapter != "not_configured":
        raise AssertionError("unexpected language_detection_adapter")

    model_pipeline_enrichment = None
    model_pipeline_resolution = None
    if settings.model_pipeline_evidence_enricher_enabled:
        registry = build_default_model_pipeline_purpose_registry(settings)
        model_pipeline_resolution = resolve_model_pipeline_purpose(
            registry,
            ModelPipelineRole.evidence_candidate_enricher,
            settings,
        )
        adapter = build_evidence_enricher_model_pipeline_adapter(
            settings,
            model_pipeline_resolution,
        )
        model_pipeline_enrichment = ModelPipelineMetadataEnrichmentService(
            adapter=adapter,
            output_validator=ModelPipelineOutputValidationService(),
            projection_service=ModelPipelineCandidateMetadataProjectionService(),
        )

    return EvidenceEnrichmentService(
        language_detection=language_detection,
        model_pipeline_enrichment=model_pipeline_enrichment,
        model_pipeline_enrichment_resolution=model_pipeline_resolution,
    )


class _PdfDependencyPlaceholder:
    """Registers ``Modality.pdf`` when pypdf is missing — uploads fail with 503."""

    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        raise ExtractorUnavailableError(
            "PDF extraction requires the optional `pdf` dependency (e.g. pip install -e '.[pdf]').",
        )


class _PptxDependencyPlaceholder:
    """Registers for ``Modality.slide`` when python-pptx is not installed."""

    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        raise ExtractorUnavailableError(
            "PPTX extraction requires the optional `pptx` dependency "
            "(e.g. pip install -e '.[pptx]').",
        )


class _ImageDependencyPlaceholder:
    """Registers for ``Modality.image`` when Pillow is not installed."""

    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        raise ExtractorUnavailableError(
            "Image handling requires the optional `image` dependency "
            "(e.g. pip install -e '.[image]').",
        )


class _AudioDependencyPlaceholder:
    """Registers for ``Modality.audio`` when mutagen is not installed."""

    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        raise ExtractorUnavailableError(
            "Audio handling requires the optional `audio` dependency "
            "(e.g. pip install -e '.[audio]').",
        )


def get_multimodal_extractor_registry() -> ExtractorRegistry:
    """Return the multimodal ``ExtractorRegistry`` (tests may monkeypatch this).

    Registers PDF, PPTX, image, and audio extractors when optional deps are available;
    otherwise placeholders that raise ``ExtractorUnavailableError``. Does not register video.
    """

    from app.services.extraction import audio_extractor as audio_extraction_module
    from app.services.extraction import image_extractor as image_extraction_module
    from app.services.extraction import pdf_extractor as pdf_extraction_module
    from app.services.extraction import pptx_extractor as pptx_extraction_module

    reg = ExtractorRegistry()
    if pdf_extraction_module.PdfReader is None:
        reg.register(Modality.pdf, _PdfDependencyPlaceholder())
    else:
        from app.services.extraction.pdf_extractor import PdfExtractor

        reg.register(Modality.pdf, PdfExtractor(settings=get_settings()))

    if pptx_extraction_module.Presentation is None:
        reg.register(Modality.slide, _PptxDependencyPlaceholder())
    else:
        from app.services.extraction.pptx_extractor import PptxExtractor

        reg.register(Modality.slide, PptxExtractor(settings=get_settings()))

    if image_extraction_module.Image is None:
        reg.register(Modality.image, _ImageDependencyPlaceholder())
    else:
        from app.services.extraction.image_extractor import ImageExtractor

        reg.register(Modality.image, ImageExtractor(settings=get_settings()))

    if audio_extraction_module.MutagenFile is None:
        reg.register(Modality.audio, _AudioDependencyPlaceholder())
    else:
        from app.services.extraction.audio_extractor import AudioExtractor

        reg.register(Modality.audio, AudioExtractor(settings=get_settings()))
    return reg


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
    file: UploadFile | None = File(default=None),  # noqa: B008
) -> ArtifactCreateResponse:
    """Create an artifact and ingest it into Evidence Units."""

    settings = get_settings()
    SessionMaker = get_sessionmaker()

    try:
        enrichment = build_evidence_enrichment_service(settings)
    except LanguageDetectionUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    if file is not None:
        content_bytes = await file.read()
        filename = file.filename or "upload.txt"
        mime_type = file.content_type
        try:
            artifact_type = resolve_from_filename_and_mime(
                filename=filename,
                mime_type=mime_type,
            ).artifact_type
        except UnsupportedArtifactTypeError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        title = None
    else:
        try:
            payload = await request.json()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail="Provide either multipart file upload or JSON inline payload.",
            ) from e

        inline = ArtifactCreateInlineRequest.model_validate(payload)
        content_bytes = inline.text.encode("utf-8")
        filename = inline.filename
        mime_type = inline.mime_type
        artifact_type = inline.artifact_type
        title = inline.title

    with SessionMaker() as session:
        try:
            if artifact_type in {"text", "markdown"}:
                svc = TextIngestionService(settings=settings, enrichment=enrichment)
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
                mm = MultimodalIngestionService(
                    settings=settings,
                    registry=get_multimodal_extractor_registry(),
                    enrichment=enrichment,
                )
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
