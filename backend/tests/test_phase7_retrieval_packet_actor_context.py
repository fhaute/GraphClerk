"""Phase 7 Slice 7H — PacketActorContextRecording on RetrievalPacket (recording-only)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import httpx
import pytest
from httpx import ASGITransport
from pydantic import ValidationError

from app.main import create_app
from app.models.enums import SemanticIndexVectorStatus
from app.schemas.retrieval import ActorContext
from app.schemas.retrieval_packet import (
    ContextBudgetSummary,
    InterpretedIntent,
    RetrievalPacket,
    SelectedSemanticIndex,
)
from app.services.embedding_adapter import DeterministicFakeEmbeddingAdapter
from app.services.embedding_service import EmbeddingService
from app.services.evidence_selection_service import EvidenceCandidate
from app.services.graph_traversal_service import GraphNeighborhood
from app.services.retrieval_packet_builder import (
    RetrievalPacketAssemblyInput,
    RetrievalPacketBuilder,
)
from app.services.route_selection_service import RouteSelection
from app.services.semantic_index_search_service import (
    SemanticIndexSearchResult,
    SemanticIndexSearchService,
)
from app.services.vector_index_service import SearchHit


class _StubVectorIndexService:
    def __init__(self, hits: list[SearchHit]) -> None:
        self._hits = hits

    def search_semantic_indexes(
        self, *, query_vector: list[float], limit: int = 5
    ) -> list[SearchHit]:
        _ = query_vector
        _ = limit
        return self._hits


def test_retrieval_packet_backward_compatible_without_actor_context() -> None:
    packet = RetrievalPacket(
        question="q",
        interpreted_intent=InterpretedIntent(intent_type="unknown", confidence=0.2, notes=[]),
        selected_indexes=[],
        graph_paths=[],
        evidence_units=[],
        alternative_interpretations=[],
        context_budget=ContextBudgetSummary(
            max_evidence_units=8,
            selected_evidence_units=0,
            pruned_evidence_units=0,
            pruning_reasons=[],
        ),
        warnings=[],
        confidence=0.5,
        answer_mode="not_enough_evidence",
    )
    assert packet.actor_context is None


def test_builder_records_used_false_when_no_request_actor_context() -> None:
    route = RouteSelection(
        primary=None,
        alternatives=[],
        selection_reasons={},
        search_warnings=["no_semantic_index_match"],
    )
    assembly = RetrievalPacketAssemblyInput(
        question="hello",
        interpreted_intent=InterpretedIntent(intent_type="unknown", confidence=0.2, notes=[]),
        route_selection=route,
        selected_indexes=[],
        graph_neighborhoods=[],
        evidence_selected=[],
        evidence_pruned=0,
        pruning_reasons=[],
        warnings=["no_semantic_index_match"],
        options_max_evidence_units=8,
        options_max_graph_paths=3,
        options_max_selected_indexes=3,
        include_alternatives=False,
    )
    packet = RetrievalPacketBuilder().build(assembly)
    assert packet.actor_context is not None
    assert packet.actor_context.used is False
    assert packet.actor_context.recorded_context is None
    assert packet.actor_context.source == "request_actor_context"
    assert packet.actor_context.influence == "none"
    assert packet.actor_context.warnings == []


def test_builder_records_used_true_and_context_when_provided() -> None:
    route = RouteSelection(
        primary=None,
        alternatives=[],
        selection_reasons={},
        search_warnings=["no_semantic_index_match"],
    )
    ac = ActorContext(actor_id=" a ", role="dev")
    assembly = RetrievalPacketAssemblyInput(
        question="hello",
        interpreted_intent=InterpretedIntent(intent_type="unknown", confidence=0.2, notes=[]),
        route_selection=route,
        selected_indexes=[],
        graph_neighborhoods=[],
        evidence_selected=[],
        evidence_pruned=0,
        pruning_reasons=[],
        warnings=["no_semantic_index_match"],
        options_max_evidence_units=8,
        options_max_graph_paths=3,
        options_max_selected_indexes=3,
        include_alternatives=False,
        request_actor_context=ac,
    )
    packet = RetrievalPacketBuilder().build(assembly)
    assert packet.actor_context is not None
    assert packet.actor_context.used is True
    assert packet.actor_context.recorded_context is not None
    assert packet.actor_context.recorded_context.actor_id == "a"
    assert packet.actor_context.recorded_context.role == "dev"
    assert packet.actor_context.influence == "recorded_only_no_route_boost_applied"


def test_evidence_units_do_not_contain_actor_context_key() -> None:
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
    nh = MagicMock(spec=GraphNeighborhood)
    nh.start_node_id = uuid.uuid4()
    nh.depth = 1
    nh.nodes = []
    nh.edges = []
    nh.truncated = False
    ev = EvidenceCandidate(
        evidence_unit_id=uuid.uuid4(),
        artifact_id=uuid.uuid4(),
        modality="text",
        content_type="paragraph",
        source_fidelity="verbatim",
        text="x",
        location=None,
        unit_confidence=0.9,
        support_confidence=0.9,
        selection_reason="linked",
    )
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
        evidence_selected=[ev],
        evidence_pruned=0,
        pruning_reasons=[],
        warnings=[],
        options_max_evidence_units=8,
        options_max_graph_paths=3,
        options_max_selected_indexes=3,
        include_alternatives=False,
        request_actor_context=ActorContext(actor_id="u1"),
    )
    packet = RetrievalPacketBuilder().build(assembly)
    for eu in packet.evidence_units:
        dumped = eu.model_dump(mode="json")
        assert "actor_context" not in dumped


@pytest.mark.asyncio
async def test_retrieve_api_actor_context_recording_and_retrieval_parity(
    db_ready: None, monkeypatch
) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        n1 = (
            await client.post("/graph/nodes", json={"node_type": "concept", "label": "N1"})
        ).json()["id"]
        n2 = (
            await client.post("/graph/nodes", json={"node_type": "concept", "label": "N2"})
        ).json()["id"]
        s1 = (
            await client.post("/semantic-indexes", json={"meaning": "m1", "entry_node_ids": [n1]})
        ).json()["id"]
        s2 = (
            await client.post("/semantic-indexes", json={"meaning": "m2", "entry_node_ids": [n2]})
        ).json()["id"]

    from app.db.session import get_sessionmaker
    from app.models.semantic_index import SemanticIndex

    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        for sid in (s1, s2):
            row = session.get(SemanticIndex, uuid.UUID(sid))
            assert row is not None
            row.vector_status = SemanticIndexVectorStatus.indexed
        session.commit()

    hits = [
        SearchHit(semantic_index_id=uuid.UUID(s1), score=0.91, payload={"semantic_index_id": s1}),
        SearchHit(semantic_index_id=uuid.UUID(s2), score=0.90, payload={"semantic_index_id": s2}),
    ]

    def factory(*, session):
        embedding = EmbeddingService(
            adapter=DeterministicFakeEmbeddingAdapter(dimension=8), expected_dimension=8
        )
        vector = _StubVectorIndexService(hits=hits)
        return SemanticIndexSearchService(
            session=session, embedding_service=embedding, vector_index_service=vector
        )

    import app.services.semantic_index_search_factory as factory_module

    monkeypatch.setattr(factory_module, "build_semantic_index_search_service", factory)

    question = "parity check actor recording"
    base_body = {"question": question}
    with_body = {
        "question": question,
        "actor_context": {"actor_id": "actor-api", "metadata": {"k": "v"}},
    }

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res_base = await client.post("/retrieve", json=base_body)
        res_actor = await client.post("/retrieve", json=with_body)
        res_bad = await client.post(
            "/retrieve", json={"question": "ok", "actor_context": {"actor_id": ""}}
        )
    assert res_base.status_code == 200
    assert res_actor.status_code == 200
    assert res_bad.status_code == 422

    body_base = res_base.json()
    body_actor = res_actor.json()

    assert body_base["actor_context"]["used"] is False
    assert body_base["actor_context"]["influence"] == "none"
    assert body_base["actor_context"]["recorded_context"] is None

    assert body_actor["actor_context"]["used"] is True
    assert body_actor["actor_context"]["influence"] == "recorded_only_no_route_boost_applied"
    rc = body_actor["actor_context"]["recorded_context"]
    assert rc["actor_id"] == "actor-api"
    assert rc["metadata"] == {"k": "v"}

    keys_compare = (
        "question",
        "interpreted_intent",
        "selected_indexes",
        "graph_paths",
        "evidence_units",
        "alternative_interpretations",
        "context_budget",
        "warnings",
        "confidence",
        "answer_mode",
        "language_context",
    )
    for k in keys_compare:
        assert body_base[k] == body_actor[k], k


def test_builder_with_actor_context_language_context_still_from_evidence_only() -> None:
    """C6 regression: actor recording must not replace or blank ``language_context``."""

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
    nh = MagicMock(spec=GraphNeighborhood)
    nh.start_node_id = uuid.uuid4()
    nh.depth = 1
    nh.nodes = []
    nh.edges = []
    nh.truncated = False
    ev = EvidenceCandidate(
        evidence_unit_id=uuid.uuid4(),
        artifact_id=uuid.uuid4(),
        modality="text",
        content_type="paragraph",
        source_fidelity="verbatim",
        text="hello",
        location=None,
        unit_confidence=0.9,
        support_confidence=0.9,
        selection_reason="linked",
        metadata_json={"language": "de", "language_confidence": 0.95},
    )
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
        evidence_selected=[ev],
        evidence_pruned=0,
        pruning_reasons=[],
        warnings=[],
        options_max_evidence_units=8,
        options_max_graph_paths=3,
        options_max_selected_indexes=3,
        include_alternatives=False,
        request_actor_context=ActorContext(actor_id="actor-1"),
    )
    packet = RetrievalPacketBuilder().build(assembly)
    assert packet.actor_context is not None
    assert packet.actor_context.used is True
    assert packet.language_context is not None
    assert packet.language_context.primary_evidence_language == "de"
    assert len(packet.evidence_units) == 1


def test_packet_actor_context_recording_rejects_unknown_fields() -> None:
    from app.schemas.retrieval_packet import PacketActorContextRecording

    with pytest.raises(ValidationError):
        PacketActorContextRecording.model_validate(
            {
                "used": True,
                "recorded_context": None,
                "influence": "recorded_only_no_route_boost_applied",
                "extra": "no",
            }
        )
