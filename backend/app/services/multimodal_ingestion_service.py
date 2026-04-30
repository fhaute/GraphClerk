from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.enums import Modality
from app.services.artifact_service import ArtifactService
from app.services.errors import ExtractionReturnedNoEvidenceError, UnsupportedArtifactTypeError
from app.services.evidence_unit_service import EvidenceUnitService
from app.services.extraction import ExtractorRegistry
from app.services.raw_source_store import RawSourceStore
from app.services.text_ingestion_service import IngestResult


_MULTIMODAL_ARTIFACT_TYPES = frozenset({"pdf", "pptx", "image", "audio"})


def modality_for_artifact_type(artifact_type: str) -> Modality:
    """Map persisted ``artifact_type`` string to registry ``Modality``."""

    mapping: dict[str, Modality] = {
        "pdf": Modality.pdf,
        "pptx": Modality.slide,
        "image": Modality.image,
        "audio": Modality.audio,
    }
    try:
        return mapping[artifact_type]
    except KeyError as e:
        raise UnsupportedArtifactTypeError(f"Unsupported multimodal artifact_type: {artifact_type!r}") from e


class MultimodalIngestionService:
    """Orchestrate multimodal ingestion using ``ExtractorRegistry`` (Phase 5 shell).

    Text and Markdown remain on ``TextIngestionService``; this service handles
    only registered multimodal extractors. Does not implement extraction itself.
    """

    def __init__(self, *, settings: Settings, registry: ExtractorRegistry) -> None:
        self._settings = settings
        self._registry = registry

    def ingest(
        self,
        *,
        session: Session,
        filename: str,
        artifact_type: str,
        mime_type: str | None,
        content_bytes: bytes,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> IngestResult:
        if artifact_type not in _MULTIMODAL_ARTIFACT_TYPES:
            raise UnsupportedArtifactTypeError(f"Unsupported multimodal artifact_type: {artifact_type!r}")

        modality = modality_for_artifact_type(artifact_type)
        extractor = self._registry.get(modality)

        raw_store = RawSourceStore(self._settings)
        artifact_service = ArtifactService(session=session, raw_source_store=raw_store)
        evidence_service = EvidenceUnitService(session=session)

        disk_path_str: str | None = None
        try:
            with session.begin():
                artifact, disk_path_str = artifact_service.create_from_bytes(
                    filename=filename,
                    artifact_type=artifact_type,
                    mime_type=mime_type,
                    content_bytes=content_bytes,
                    title=title,
                    metadata=metadata,
                )
                session.flush()

                candidates = extractor.extract(artifact)
                if not candidates:
                    raise ExtractionReturnedNoEvidenceError()

                evidence_service.create_from_candidates(artifact_id=artifact.id, candidates=candidates)

            return IngestResult(artifact=artifact, evidence_unit_count=len(candidates))
        except Exception:
            if disk_path_str:
                from pathlib import Path

                raw_store.best_effort_cleanup(Path(disk_path_str))
            raise
