"""Track C Slice C8 — ``POST /artifacts`` wires configured language detection into enrichment."""

from __future__ import annotations

import os
import uuid
from unittest.mock import MagicMock

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api.routes import artifacts as artifacts_routes
from app.core import config as config_module
from app.main import create_app
from app.models.artifact import Artifact
from app.models.enums import Modality, SourceFidelity
from app.models.evidence_unit import EvidenceUnit
from app.schemas.evidence_unit_candidate import (
    LANGUAGE_METADATA_KEY_LANGUAGE,
    EvidenceUnitCandidate,
)
from app.schemas.retrieval_packet import InterpretedIntent, SelectedSemanticIndex
from app.services.artifact_language_aggregation_service import GRAPHCLERK_LANGUAGE_AGGREGATION_KEY
from app.services.errors import LanguageDetectionUnavailableError
from app.services.evidence_selection_service import EvidenceCandidate
from app.services.extraction.extractor_registry import ExtractorRegistry
from app.services.language_detection_service import (
    DeterministicTestLanguageDetectionAdapter,
    LanguageDetectionService,
)
from app.services.retrieval_packet_builder import (
    RetrievalPacketAssemblyInput,
    RetrievalPacketBuilder,
)
from app.services.route_selection_service import RouteSelection
from app.services.semantic_index_search_service import SemanticIndexSearchResult


def _session() -> Session:
    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    return Session(engine, expire_on_commit=False)


def _minimal_route_with_primary() -> tuple[RouteSelection, MagicMock]:
    idx = MagicMock()
    idx.id = uuid.uuid4()
    idx.meaning = "meaning"
    primary = SemanticIndexSearchResult(
        semantic_index=idx, entry_node_ids=[uuid.uuid4()], score=0.9
    )
    route = RouteSelection(
        primary=primary,
        alternatives=[],
        selection_reasons={str(idx.id): "best"},
        search_warnings=[],
    )
    return route, idx


def _minimal_neighborhood() -> MagicMock:
    nh = MagicMock()
    nh.start_node_id = uuid.uuid4()
    nh.depth = 1
    nh.nodes = []
    nh.edges = []
    nh.truncated = False
    nh.node_evidence = []
    nh.edge_evidence = []
    return nh


class _PdfStubExtractor:
    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        _ = artifact
        return [
            EvidenceUnitCandidate(
                modality=Modality.pdf,
                content_type="stub_unit",
                text="stub extracted body long enough for lingua rules",
                location={"page": 1},
                source_fidelity=SourceFidelity.extracted,
                confidence=1.0,
            )
        ]


@pytest.fixture(autouse=True)
def _clear_language_detection_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid leaking ``GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER`` across tests."""
    monkeypatch.delenv("GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER", raising=False)
    config_module.get_settings.cache_clear()
    yield
    monkeypatch.delenv("GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER", raising=False)
    config_module.get_settings.cache_clear()


@pytest.mark.asyncio
async def test_default_post_artifacts_succeeds_without_detector_language_metadata(
    db_ready: None,
) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            json={
                "filename": "c8-default.txt",
                "artifact_type": "text",
                "text": "First paragraph here.\n\nSecond paragraph here.\n",
            },
        )
    assert res.status_code == 200
    aid = res.json()["artifact_id"]
    with _session() as session:
        evs = (
            session.execute(select(EvidenceUnit).where(EvidenceUnit.artifact_id == uuid.UUID(aid)))
            .scalars()
            .all()
        )
        art = session.get(Artifact, uuid.UUID(aid))
    assert len(evs) >= 1
    for eu in evs:
        meta = eu.metadata_json or {}
        lang = meta.get(LANGUAGE_METADATA_KEY_LANGUAGE)
        assert lang is None or (isinstance(lang, str) and lang.strip() == "")
    agg = (art.metadata_json or {})[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]
    assert agg.get("primary_language") is None


@pytest.mark.asyncio
async def test_lingua_configured_monkeypatch_enriches_metadata_aggregation_and_packet_context(
    db_ready: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER", "lingua")
    config_module.get_settings.cache_clear()

    fake = LanguageDetectionService(
        adapter=DeterministicTestLanguageDetectionAdapter(
            default_language="eo",
            default_confidence=0.93,
            short_text_max_chars=0,
        )
    )
    monkeypatch.setattr(artifacts_routes, "build_language_detection_service", lambda _s: fake)

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            json={
                "filename": "c8-lang.txt",
                "artifact_type": "text",
                "text": "Alpha paragraph text.\n\nBeta paragraph text.\n",
            },
        )
    assert res.status_code == 200
    aid = uuid.UUID(res.json()["artifact_id"])
    with _session() as session:
        evs = (
            session.execute(
                select(EvidenceUnit)
                .where(EvidenceUnit.artifact_id == aid)
                .order_by(EvidenceUnit.created_at)
            )
            .scalars()
            .all()
        )
        art = session.get(Artifact, aid)
    assert len(evs) == 2
    for eu in evs:
        assert "paragraph" in (eu.text or "")
        assert eu.source_fidelity == SourceFidelity.verbatim
        meta = eu.metadata_json or {}
        assert meta.get(LANGUAGE_METADATA_KEY_LANGUAGE) == "eo"
    agg = (art.metadata_json or {})[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]
    assert agg["primary_language"] == "eo"

    route, idx = _minimal_route_with_primary()
    nh = _minimal_neighborhood()
    ev_candidates = [
        EvidenceCandidate(
            evidence_unit_id=eu.id,
            artifact_id=eu.artifact_id,
            modality=str(eu.modality),
            content_type=eu.content_type,
            source_fidelity=str(eu.source_fidelity),
            text=eu.text,
            location=eu.location,
            unit_confidence=eu.confidence,
            support_confidence=0.9,
            selection_reason="product_wiring_test",
            metadata_json=eu.metadata_json,
        )
        for eu in evs
    ]
    assembly = RetrievalPacketAssemblyInput(
        question="q",
        interpreted_intent=InterpretedIntent(intent_type="explain", confidence=0.9, notes=[]),
        route_selection=route,
        selected_indexes=[
            SelectedSemanticIndex(
                semantic_index_id=str(idx.id),
                meaning="meaning",
                score=0.9,
                selection_reason="best",
            )
        ],
        graph_neighborhoods=[nh],
        evidence_selected=ev_candidates,
        evidence_pruned=0,
        pruning_reasons=[],
        warnings=[],
        options_max_evidence_units=8,
        options_max_graph_paths=3,
        options_max_selected_indexes=3,
        include_alternatives=False,
    )
    packet = RetrievalPacketBuilder().build(assembly)
    lc = packet.language_context
    assert lc is not None
    assert lc.primary_evidence_language == "eo"


@pytest.mark.asyncio
async def test_lingua_configured_build_failure_returns_503_no_not_configured_fallback(
    db_ready: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER", "lingua")
    config_module.get_settings.cache_clear()

    def boom(_settings):
        raise LanguageDetectionUnavailableError("language_detection_lingua_extra_not_installed")

    monkeypatch.setattr(artifacts_routes, "build_language_detection_service", boom)

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            json={"filename": "fail.txt", "artifact_type": "text", "text": "Hello\n\nWorld\n"},
        )
    assert res.status_code == 503
    assert "language_detection_lingua_extra_not_installed" in res.json()["detail"]


@pytest.mark.asyncio
async def test_multimodal_pdf_ingest_enriches_when_lingua_configured(
    db_ready: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER", "lingua")
    config_module.get_settings.cache_clear()

    fake = LanguageDetectionService(
        adapter=DeterministicTestLanguageDetectionAdapter(
            default_language="qu",
            default_confidence=0.88,
            short_text_max_chars=0,
        )
    )
    monkeypatch.setattr(artifacts_routes, "build_language_detection_service", lambda _s: fake)

    reg = ExtractorRegistry()
    reg.register(Modality.pdf, _PdfStubExtractor())
    monkeypatch.setattr(artifacts_routes, "get_multimodal_extractor_registry", lambda: reg)

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts", files={"file": ("doc.pdf", b"%PDF-1.4 stub", "application/pdf")}
        )
    assert res.status_code == 200
    aid = uuid.UUID(res.json()["artifact_id"])
    with _session() as session:
        evs = (
            session.execute(select(EvidenceUnit).where(EvidenceUnit.artifact_id == aid))
            .scalars()
            .all()
        )
    assert len(evs) == 1
    eu = evs[0]
    assert eu.text == "stub extracted body long enough for lingua rules"
    assert eu.source_fidelity == SourceFidelity.extracted
    assert (eu.metadata_json or {}).get(LANGUAGE_METADATA_KEY_LANGUAGE) == "qu"
