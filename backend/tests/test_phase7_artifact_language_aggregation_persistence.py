"""Track C Slice C5 — ``graphclerk_language_aggregation`` on Artifact after EU create."""

from __future__ import annotations

import os
from unittest.mock import MagicMock

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core import config as config_module
from app.models.artifact import Artifact
from app.models.enums import Modality, SourceFidelity
from app.models.evidence_unit import EvidenceUnit
from app.schemas.evidence_unit_candidate import (
    LANGUAGE_METADATA_KEY_LANGUAGE,
    EvidenceUnitCandidate,
)
from app.services.artifact_language_aggregation_service import (
    GRAPHCLERK_LANGUAGE_AGGREGATION_KEY,
    WARNING_NO_LANGUAGE_METADATA,
    apply_language_aggregation_to_artifact,
)
from app.services.evidence_enrichment_service import EvidenceEnrichmentService
from app.services.extraction.extractor_registry import ExtractorRegistry
from app.services.language_detection_service import (
    DeterministicTestLanguageDetectionAdapter,
    LanguageDetectionService,
)
from app.services.multimodal_ingestion_service import MultimodalIngestionService
from app.services.text_ingestion_service import TextIngestionService


def _session() -> Session:
    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    return Session(engine, expire_on_commit=False)


class _StubPdfTwoPages:
    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        _ = artifact
        return [
            EvidenceUnitCandidate(
                modality=Modality.pdf,
                content_type="pdf_page_text",
                text="alpha page long enough",
                location={"page": 1},
                source_fidelity=SourceFidelity.extracted,
                confidence=1.0,
                metadata={LANGUAGE_METADATA_KEY_LANGUAGE: "en"},
            ),
            EvidenceUnitCandidate(
                modality=Modality.pdf,
                content_type="pdf_page_text",
                text="beta page long enough",
                location={"page": 2},
                source_fidelity=SourceFidelity.extracted,
                confidence=0.9,
                metadata={LANGUAGE_METADATA_KEY_LANGUAGE: "en"},
            ),
        ]


def test_apply_language_aggregation_reads_each_evidence_unit_metadata_json() -> None:
    """Aggregation input is ``EvidenceUnit.metadata_json``, not candidate text."""

    art = MagicMock()
    art.metadata_json = {}
    eu1 = MagicMock()
    eu1.metadata_json = {LANGUAGE_METADATA_KEY_LANGUAGE: "pl"}
    eu2 = MagicMock()
    eu2.metadata_json = {LANGUAGE_METADATA_KEY_LANGUAGE: "sv"}
    apply_language_aggregation_to_artifact(artifact=art, evidence_units=[eu1, eu2])
    sub = art.metadata_json[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]
    assert sub["distinct_language_count"] == 2
    assert sub["primary_language"] in {"pl", "sv"}


def test_text_ingestion_persists_honest_absence_when_no_eu_language_metadata(
    db_ready: None,
) -> None:
    settings = config_module.get_settings()
    svc = TextIngestionService(settings=settings)

    with _session() as session:
        result = svc.ingest(
            session=session,
            filename="no-lang.txt",
            artifact_type="text",
            mime_type="text/plain",
            content_bytes=b"Line one here\n\nLine two here\n",
        )
        art = session.get(Artifact, result.artifact.id)
        evs = (
            session.execute(
                select(EvidenceUnit)
                .where(EvidenceUnit.artifact_id == result.artifact.id)
                .order_by(EvidenceUnit.created_at)
            )
            .scalars()
            .all()
        )

    assert len(evs) == 2
    agg = (art.metadata_json or {})[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]
    assert agg["primary_language"] is None
    assert WARNING_NO_LANGUAGE_METADATA in agg["warnings"]
    assert agg["evidence_units_without_language_metadata_count"] == 2


def test_text_ingestion_persists_aggregation_with_language_when_enrichment_injected(
    db_ready: None,
) -> None:
    settings = config_module.get_settings()
    adapter = DeterministicTestLanguageDetectionAdapter(
        default_language="fr",
        default_confidence=0.91,
        short_text_max_chars=0,
    )
    enrichment = EvidenceEnrichmentService(
        language_detection=LanguageDetectionService(adapter=adapter),
    )
    svc = TextIngestionService(settings=settings, enrichment=enrichment)

    with _session() as session:
        result = svc.ingest(
            session=session,
            filename="agg-lang.txt",
            artifact_type="text",
            mime_type="text/plain",
            content_bytes=b"First block text\n\nSecond block text\n",
        )
        art = session.get(Artifact, result.artifact.id)
        evs = (
            session.execute(
                select(EvidenceUnit)
                .where(EvidenceUnit.artifact_id == result.artifact.id)
                .order_by(EvidenceUnit.created_at)
            )
            .scalars()
            .all()
        )

    assert len(evs) == 2
    for ev in evs:
        assert "block" in ev.text
        assert ev.source_fidelity == SourceFidelity.verbatim
    agg = (art.metadata_json or {})[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]
    assert agg["primary_language"] == "fr"
    assert agg["distinct_language_count"] == 1


def test_text_ingestion_preserves_unrelated_artifact_metadata_and_replaces_aggregation_subtree(
    db_ready: None,
) -> None:
    settings = config_module.get_settings()
    svc = TextIngestionService(settings=settings)
    prior_agg = {"version": 0, "stale": True}

    with _session() as session:
        result = svc.ingest(
            session=session,
            filename="meta.txt",
            artifact_type="text",
            mime_type="text/plain",
            content_bytes=b"A\n\nB\n",
            metadata={"operator_note": "keep-me", GRAPHCLERK_LANGUAGE_AGGREGATION_KEY: prior_agg},
        )
        art = session.get(Artifact, result.artifact.id)

    meta = art.metadata_json or {}
    assert meta.get("operator_note") == "keep-me"
    new_sub = meta[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]
    assert new_sub.get("version") == 1
    assert "stale" not in new_sub


def test_multimodal_ingestion_persists_aggregation_after_extraction(db_ready: None) -> None:
    settings = config_module.get_settings()
    registry = ExtractorRegistry()
    registry.register(Modality.pdf, _StubPdfTwoPages())
    svc = MultimodalIngestionService(settings=settings, registry=registry)

    with _session() as session:
        result = svc.ingest(
            session=session,
            filename="agg.pdf",
            artifact_type="pdf",
            mime_type="application/pdf",
            content_bytes=b"%PDF-1.4 stub",
        )
        art = session.get(Artifact, result.artifact.id)
        evs = (
            session.execute(
                select(EvidenceUnit)
                .where(EvidenceUnit.artifact_id == result.artifact.id)
                .order_by(EvidenceUnit.created_at)
            )
            .scalars()
            .all()
        )

    assert len(evs) == 2
    for ev in evs:
        assert ev.text.startswith("alpha") or ev.text.startswith("beta")
        assert ev.source_fidelity == SourceFidelity.extracted
    agg = (art.metadata_json or {})[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]
    assert agg["primary_language"] == "en"
    assert agg["distinct_language_count"] == 1
