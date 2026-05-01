"""Phase 7 Slice 7D — EvidenceEnrichmentService wired into ingestion (default no-op)."""

from __future__ import annotations

import os
import uuid
from collections.abc import Sequence
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import config as config_module
from app.models.artifact import Artifact
from app.models.enums import Modality, SourceFidelity
from app.models.evidence_unit import EvidenceUnit
from app.schemas.evidence_unit_candidate import (
    LANGUAGE_METADATA_KEY_LANGUAGE,
    LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE,
    LANGUAGE_METADATA_KEY_LANGUAGE_DETECTION_METHOD,
    EvidenceUnitCandidate,
)
from app.services.evidence_enrichment_service import (
    EvidenceEnrichmentEmptiedCandidatesError,
    EvidenceEnrichmentService,
)
from app.services.extraction.extractor_registry import ExtractorRegistry
from app.services.language_detection_service import (
    DeterministicTestLanguageDetectionAdapter,
    LanguageDetectionService,
)
from app.services.multimodal_ingestion_service import MultimodalIngestionService
from app.services.text_ingestion_service import TextIngestionService


def _session() -> Session:
    from sqlalchemy import create_engine

    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    return Session(engine, expire_on_commit=False)


class SpyEnrichmentService(EvidenceEnrichmentService):
    """Records ``enrich`` inputs; default behavior is identity."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[list[EvidenceUnitCandidate]] = []

    def enrich(self, candidates: Sequence[EvidenceUnitCandidate]) -> list[EvidenceUnitCandidate]:
        self.calls.append(list(candidates))
        return super().enrich(candidates)


class EmptyReturnEnrichmentService(EvidenceEnrichmentService):
    def __init__(self) -> None:
        super().__init__()

    def enrich(self, candidates: Sequence[EvidenceUnitCandidate]) -> list[EvidenceUnitCandidate]:  # type: ignore[override]
        _ = candidates
        return []


class KeepFirstOnlyEnrichmentService(EvidenceEnrichmentService):
    def __init__(self) -> None:
        super().__init__()

    def enrich(self, candidates: Sequence[EvidenceUnitCandidate]) -> list[EvidenceUnitCandidate]:  # type: ignore[override]
        c = list(candidates)
        return [c[0]] if c else []


class StubPdfExtractor:
    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        _ = artifact
        return [
            EvidenceUnitCandidate(
                modality=Modality.pdf,
                content_type="pdf_page_text",
                text="alpha page",
                location={"page": 1},
                source_fidelity=SourceFidelity.extracted,
                confidence=1.0,
            ),
            EvidenceUnitCandidate(
                modality=Modality.pdf,
                content_type="pdf_page_text",
                text="beta page",
                location={"page": 2},
                source_fidelity=SourceFidelity.extracted,
                confidence=0.9,
            ),
        ]


def test_text_ingestion_calls_enrichment_before_persistence(db_ready: None) -> None:
    config_module.get_settings.cache_clear()
    settings = config_module.get_settings()
    spy = SpyEnrichmentService()
    svc = TextIngestionService(settings=settings, enrichment=spy)

    with _session() as session:
        result = svc.ingest(
            session=session,
            filename="spy.txt",
            artifact_type="text",
            mime_type="text/plain",
            content_bytes=b"One\n\nTwo\n",
        )

    assert len(spy.calls) == 1
    assert len(spy.calls[0]) == 2
    assert result.evidence_unit_count == 2


def test_text_ingestion_preserves_text_and_source_fidelity(db_ready: None) -> None:
    settings = config_module.get_settings()
    spy = SpyEnrichmentService()
    svc = TextIngestionService(settings=settings, enrichment=spy)

    with _session() as session:
        result = svc.ingest(
            session=session,
            filename="fid.txt",
            artifact_type="text",
            mime_type="text/plain",
            content_bytes=b"Hello\n\nWorld\n",
        )

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
    assert evs[0].text == spy.calls[0][0].text
    assert evs[1].text == spy.calls[0][1].text
    assert evs[0].source_fidelity == spy.calls[0][0].source_fidelity
    assert evs[1].source_fidelity == spy.calls[0][1].source_fidelity


def test_multimodal_ingestion_calls_enrichment_before_persistence(db_ready: None) -> None:
    settings = config_module.get_settings()
    registry = ExtractorRegistry()
    registry.register(Modality.pdf, StubPdfExtractor())
    spy = SpyEnrichmentService()
    svc = MultimodalIngestionService(settings=settings, registry=registry, enrichment=spy)

    with _session() as session:
        result = svc.ingest(
            session=session,
            filename="stub.pdf",
            artifact_type="pdf",
            mime_type="application/pdf",
            content_bytes=b"%PDF-1.4 stub",
        )

    assert len(spy.calls) == 1
    assert len(spy.calls[0]) == 2
    assert result.evidence_unit_count == 2


def test_multimodal_ingestion_preserves_text_and_source_fidelity(db_ready: None) -> None:
    settings = config_module.get_settings()
    registry = ExtractorRegistry()
    registry.register(Modality.pdf, StubPdfExtractor())
    spy = SpyEnrichmentService()
    svc = MultimodalIngestionService(settings=settings, registry=registry, enrichment=spy)

    with _session() as session:
        result = svc.ingest(
            session=session,
            filename="stub2.pdf",
            artifact_type="pdf",
            mime_type="application/pdf",
            content_bytes=b"%PDF-1.4 stub",
        )

        evs = (
            session.execute(
                select(EvidenceUnit)
                .where(EvidenceUnit.artifact_id == result.artifact.id)
                .order_by(EvidenceUnit.created_at)
            )
            .scalars()
            .all()
        )

    assert evs[0].text == spy.calls[0][0].text
    assert evs[1].text == spy.calls[0][1].text
    assert evs[0].source_fidelity == spy.calls[0][0].source_fidelity
    assert evs[1].source_fidelity == spy.calls[0][1].source_fidelity


def test_text_ingestion_uses_returned_list_when_enrichment_truncates(db_ready: None) -> None:
    settings = config_module.get_settings()
    svc = TextIngestionService(settings=settings, enrichment=KeepFirstOnlyEnrichmentService())

    with _session() as session:
        result = svc.ingest(
            session=session,
            filename="trunc.txt",
            artifact_type="text",
            mime_type="text/plain",
            content_bytes=b"A\n\nB\n",
        )

        evs = (
            session.execute(
                select(EvidenceUnit).where(EvidenceUnit.artifact_id == result.artifact.id)
            )
            .scalars()
            .all()
        )

    assert result.evidence_unit_count == 1
    assert len(evs) == 1
    assert evs[0].text == "A"


def test_text_ingestion_raises_when_enrichment_drops_all_candidates(db_ready: None) -> None:
    settings = config_module.get_settings()
    svc = TextIngestionService(settings=settings, enrichment=EmptyReturnEnrichmentService())

    with _session() as session:
        with pytest.raises(EvidenceEnrichmentEmptiedCandidatesError):
            svc.ingest(
                session=session,
                filename="empty-meta.txt",
                artifact_type="text",
                mime_type="text/plain",
                content_bytes=b"X\n\nY\n",
            )


def test_multimodal_raises_when_enrichment_drops_all_candidates(db_ready: None) -> None:
    settings = config_module.get_settings()
    registry = ExtractorRegistry()
    registry.register(Modality.pdf, StubPdfExtractor())
    svc = MultimodalIngestionService(
        settings=settings, registry=registry, enrichment=EmptyReturnEnrichmentService()
    )

    with _session() as session:
        with pytest.raises(EvidenceEnrichmentEmptiedCandidatesError):
            svc.ingest(
                session=session,
                filename="drop.pdf",
                artifact_type="pdf",
                mime_type="application/pdf",
                content_bytes=b"%PDF-1.4 stub",
            )


def _configure_test_settings_env(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "GraphClerk")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    config_module.get_settings.cache_clear()


def test_text_ingestion_calls_enrichment_before_persistence_mock(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DB-free wiring check: enrichment runs before ``create_from_candidates``."""

    _configure_test_settings_env(tmp_path, monkeypatch)
    settings = config_module.get_settings()
    spy = SpyEnrichmentService()
    svc = TextIngestionService(settings=settings, enrichment=spy)

    art = MagicMock()
    art.id = uuid.uuid4()

    mock_session = MagicMock()
    begin_cm = MagicMock()
    begin_cm.__enter__.return_value = mock_session
    begin_cm.__exit__.return_value = None
    mock_session.begin.return_value = begin_cm

    captured: list[list[EvidenceUnitCandidate]] = []

    with patch("app.services.text_ingestion_service.ArtifactService") as AS_cls:
        AS_cls.return_value.create_from_bytes.return_value = (art, None)
        with patch("app.services.text_ingestion_service.EvidenceUnitService") as ES_cls:
            ES_cls.return_value.create_from_candidates.side_effect = lambda **kw: captured.append(
                list(kw["candidates"])
            )

            svc.ingest(
                session=mock_session,
                filename="mock.txt",
                artifact_type="text",
                mime_type="text/plain",
                content_bytes=b"Hello\n\nWorld\n",
            )

    assert len(spy.calls) == 1
    assert len(spy.calls[0]) == 2
    assert len(captured) == 1
    assert captured[0][0] is spy.calls[0][0]
    assert captured[0][1] is spy.calls[0][1]
    assert captured[0][0].text == "Hello"


def test_multimodal_ingestion_calls_enrichment_before_persistence_mock(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_test_settings_env(tmp_path, monkeypatch)
    settings = config_module.get_settings()
    registry = ExtractorRegistry()
    registry.register(Modality.pdf, StubPdfExtractor())
    spy = SpyEnrichmentService()
    svc = MultimodalIngestionService(settings=settings, registry=registry, enrichment=spy)

    art = MagicMock()
    art.id = uuid.uuid4()

    mock_session = MagicMock()
    begin_cm = MagicMock()
    begin_cm.__enter__.return_value = mock_session
    begin_cm.__exit__.return_value = None
    mock_session.begin.return_value = begin_cm

    captured: list[list[EvidenceUnitCandidate]] = []

    with patch("app.services.multimodal_ingestion_service.ArtifactService") as AS_cls:
        AS_cls.return_value.create_from_bytes.return_value = (art, None)
        with patch("app.services.multimodal_ingestion_service.EvidenceUnitService") as ES_cls:
            ES_cls.return_value.create_from_candidates.side_effect = lambda **kw: captured.append(
                list(kw["candidates"])
            )

            svc.ingest(
                session=mock_session,
                filename="mock.pdf",
                artifact_type="pdf",
                mime_type="application/pdf",
                content_bytes=b"%PDF-1.4",
            )

    assert len(spy.calls) == 1
    assert len(spy.calls[0]) == 2
    assert len(captured) == 1
    assert captured[0] == spy.calls[0]


def test_multimodal_uses_enrichment_returned_list_mock(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_test_settings_env(tmp_path, monkeypatch)
    settings = config_module.get_settings()
    registry = ExtractorRegistry()
    registry.register(Modality.pdf, StubPdfExtractor())
    svc = MultimodalIngestionService(
        settings=settings, registry=registry, enrichment=KeepFirstOnlyEnrichmentService()
    )

    art = MagicMock()
    art.id = uuid.uuid4()

    mock_session = MagicMock()
    begin_cm = MagicMock()
    begin_cm.__enter__.return_value = mock_session
    begin_cm.__exit__.return_value = None
    mock_session.begin.return_value = begin_cm

    captured: list[list[EvidenceUnitCandidate]] = []

    with patch("app.services.multimodal_ingestion_service.ArtifactService") as AS_cls:
        AS_cls.return_value.create_from_bytes.return_value = (art, None)
        with patch("app.services.multimodal_ingestion_service.EvidenceUnitService") as ES_cls:
            ES_cls.return_value.create_from_candidates.side_effect = lambda **kw: captured.append(
                list(kw["candidates"])
            )

            svc.ingest(
                session=mock_session,
                filename="trunc.pdf",
                artifact_type="pdf",
                mime_type="application/pdf",
                content_bytes=b"%PDF-1.4",
            )

    assert len(captured) == 1
    assert len(captured[0]) == 1
    assert captured[0][0].text == "alpha page"


def test_text_enrichment_drops_all_raises_mock(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_test_settings_env(tmp_path, monkeypatch)
    settings = config_module.get_settings()
    svc = TextIngestionService(settings=settings, enrichment=EmptyReturnEnrichmentService())

    art = MagicMock()
    art.id = uuid.uuid4()

    mock_session = MagicMock()
    begin_cm = MagicMock()
    begin_cm.__enter__.return_value = mock_session
    begin_cm.__exit__.return_value = None
    mock_session.begin.return_value = begin_cm

    with patch("app.services.text_ingestion_service.ArtifactService") as AS_cls:
        AS_cls.return_value.create_from_bytes.return_value = (art, None)
        with patch("app.services.text_ingestion_service.EvidenceUnitService"):
            with pytest.raises(EvidenceEnrichmentEmptiedCandidatesError):
                svc.ingest(
                    session=mock_session,
                    filename="bad.txt",
                    artifact_type="text",
                    mime_type="text/plain",
                    content_bytes=b"Z\n\nW\n",
                )


def test_default_text_enrichment_is_no_op_matches_explicit_default(db_ready: None) -> None:
    settings = config_module.get_settings()
    explicit = TextIngestionService(settings=settings, enrichment=EvidenceEnrichmentService())
    implicit = TextIngestionService(settings=settings)

    body = b"P\n\nQ\n"
    with _session() as session:
        r1 = explicit.ingest(
            session=session,
            filename="e.txt",
            artifact_type="text",
            mime_type="text/plain",
            content_bytes=body,
        )
    with _session() as session:
        r2 = implicit.ingest(
            session=session,
            filename="i.txt",
            artifact_type="text",
            mime_type="text/plain",
            content_bytes=body,
        )

    assert r1.evidence_unit_count == r2.evidence_unit_count == 2


def test_text_ingestion_persists_language_metadata_when_detection_injected(db_ready: None) -> None:
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
            filename="lang-meta.txt",
            artifact_type="text",
            mime_type="text/plain",
            content_bytes=b"Alpha line here\n\nAnother paragraph line\n",
        )
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
        meta = ev.metadata_json or {}
        assert meta.get(LANGUAGE_METADATA_KEY_LANGUAGE) == "fr"
        assert meta.get(LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE) == 0.91
        assert meta.get(LANGUAGE_METADATA_KEY_LANGUAGE_DETECTION_METHOD) == "deterministic_test"


def test_text_ingestion_passes_enriched_language_metadata_to_create_from_candidates_mock(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DB-free: injected language detection metadata reaches ``EvidenceUnitService``."""

    _configure_test_settings_env(tmp_path, monkeypatch)
    settings = config_module.get_settings()
    adapter = DeterministicTestLanguageDetectionAdapter(
        default_language="es", short_text_max_chars=0
    )
    enrichment = EvidenceEnrichmentService(
        language_detection=LanguageDetectionService(adapter=adapter)
    )
    svc = TextIngestionService(settings=settings, enrichment=enrichment)

    art = MagicMock()
    art.id = uuid.uuid4()

    mock_session = MagicMock()
    begin_cm = MagicMock()
    begin_cm.__enter__.return_value = mock_session
    begin_cm.__exit__.return_value = None
    mock_session.begin.return_value = begin_cm

    captured: list[list[EvidenceUnitCandidate]] = []

    with patch("app.services.text_ingestion_service.ArtifactService") as AS_cls:
        AS_cls.return_value.create_from_bytes.return_value = (art, None)
        with patch("app.services.text_ingestion_service.EvidenceUnitService") as ES_cls:
            ES_cls.return_value.create_from_candidates.side_effect = lambda **kw: captured.append(
                list(kw["candidates"])
            )

            svc.ingest(
                session=mock_session,
                filename="mock-lang.txt",
                artifact_type="text",
                mime_type="text/plain",
                content_bytes=b"Hello\n\nWorld\n",
            )

    assert len(captured) == 1
    assert len(captured[0]) == 2
    for c in captured[0]:
        assert c.metadata is not None
        assert c.metadata.get(LANGUAGE_METADATA_KEY_LANGUAGE) == "es"
        assert c.metadata.get(LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE) == 0.95
        assert (
            c.metadata.get(LANGUAGE_METADATA_KEY_LANGUAGE_DETECTION_METHOD) == "deterministic_test"
        )
