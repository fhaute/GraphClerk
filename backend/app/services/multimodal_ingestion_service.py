from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.services.artifact_language_aggregation_service import (
    apply_language_aggregation_to_artifact,
)
from app.services.artifact_service import ArtifactService
from app.services.errors import ExtractionReturnedNoEvidenceError, UnsupportedArtifactTypeError
from app.services.evidence_enrichment_service import (
    EvidenceEnrichmentEmptiedCandidatesError,
    EvidenceEnrichmentService,
)
from app.services.evidence_unit_service import EvidenceUnitService
from app.services.extraction import ExtractorRegistry
from app.services.ingestion.artifact_type_resolver import (
    modality_for_artifact_type,
    supported_artifact_types,
)
from app.services.raw_source_store import RawSourceStore
from app.services.text_ingestion_service import IngestResult

_MULTIMODAL_ARTIFACT_TYPES = frozenset(supported_artifact_types()) - {"text", "markdown"}


class MultimodalIngestionService:
    """Orchestrate multimodal ingestion using ``ExtractorRegistry`` (Phase 5 shell).

    Text and Markdown remain on ``TextIngestionService``; this service handles
    only registered multimodal extractors. Does not implement extraction itself.

    Phase 7: optional ``enrichment`` (defaults to no-op ``EvidenceEnrichmentService``)
    runs on extractor output immediately before ``EvidenceUnitService.create_from_candidates``.
    """

    def __init__(
        self,
        *,
        settings: Settings,
        registry: ExtractorRegistry,
        enrichment: EvidenceEnrichmentService | None = None,
    ) -> None:
        self._settings = settings
        self._registry = registry
        self._enrichment = enrichment if enrichment is not None else EvidenceEnrichmentService()

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
            msg = f"Unsupported multimodal artifact_type: {artifact_type!r}"
            raise UnsupportedArtifactTypeError(msg)

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

                enriched = self._enrichment.enrich(candidates)
                if candidates and not enriched:
                    raise EvidenceEnrichmentEmptiedCandidatesError(
                        "enrichment_removed_all_candidates"
                    )

                created_eus = evidence_service.create_from_candidates(
                    artifact_id=artifact.id,
                    candidates=enriched,
                )
                apply_language_aggregation_to_artifact(
                    artifact=artifact, evidence_units=created_eus
                )

            return IngestResult(artifact=artifact, evidence_unit_count=len(enriched))
        except Exception:
            if disk_path_str:
                from pathlib import Path

                raw_store.best_effort_cleanup(Path(disk_path_str))
            raise
