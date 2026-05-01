from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from app.schemas.retrieval_packet import InterpretedIntent, SelectedSemanticIndex
from app.services.evidence_selection_service import EvidenceCandidate
from app.services.graph_traversal_service import GraphNeighborhood
from app.services.retrieval_packet_builder import RetrievalPacketAssemblyInput, RetrievalPacketBuilder
from app.services.route_selection_service import RouteSelection
from app.services.semantic_index_search_service import SemanticIndexSearchResult


def test_packet_builder_no_semantic_match_packet() -> None:
    route = RouteSelection(primary=None, alternatives=[], selection_reasons={}, search_warnings=["no_semantic_index_match"])

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
    assert packet.answer_mode == "not_enough_evidence"
    assert "no_semantic_index_match" in packet.warnings
    assert packet.language_context is not None
    assert packet.language_context.query_language is None
    assert packet.language_context.source == "selected_evidence_metadata"
    assert "no_language_metadata" in packet.language_context.warnings
    assert packet.actor_context is not None
    assert packet.actor_context.used is False
    assert packet.actor_context.influence == "none"


def test_packet_builder_with_primary_and_evidence() -> None:
    idx = MagicMock()
    idx.id = uuid.uuid4()
    idx.meaning = "meaning"

    primary = SemanticIndexSearchResult(semantic_index=idx, entry_node_ids=[uuid.uuid4()], score=0.9)
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
        text="hello world",
        location=None,
        unit_confidence=0.8,
        support_confidence=0.8,
        selection_reason="linked",
    )

    assembly = RetrievalPacketAssemblyInput(
        question="what is x?",
        interpreted_intent=InterpretedIntent(intent_type="explain", confidence=0.8, notes=[]),
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
    )
    packet = RetrievalPacketBuilder().build(assembly)
    assert packet.answer_mode in {"answer_with_evidence", "answer_with_caveats"}
    assert len(packet.evidence_units) == 1
    assert packet.language_context is not None
    assert packet.language_context.query_language is None
    assert packet.actor_context is not None
    assert packet.actor_context.used is False
    assert packet.actor_context.influence == "none"
