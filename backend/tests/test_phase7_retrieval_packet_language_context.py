"""Phase 7 Slice 7F — RetrievalPacket.language_context from selected evidence metadata only."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.schemas.retrieval_packet import (
    ContextBudgetSummary,
    EvidenceUnitPacket,
    InterpretedIntent,
    RetrievalLanguageContext,
    RetrievalPacket,
    SelectedSemanticIndex,
)
from app.services.evidence_selection_service import EvidenceCandidate
from app.services.graph_traversal_service import GraphNeighborhood
from app.services.retrieval_packet_builder import RetrievalPacketAssemblyInput, RetrievalPacketBuilder
from app.services.route_selection_service import RouteSelection
from app.services.semantic_index_search_service import SemanticIndexSearchResult


def _minimal_route_with_primary() -> tuple[RouteSelection, MagicMock]:
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
    return route, idx


def _minimal_neighborhood() -> MagicMock:
    nh = MagicMock(spec=GraphNeighborhood)
    nh.start_node_id = uuid.uuid4()
    nh.depth = 1
    nh.nodes = []
    nh.edges = []
    nh.truncated = False
    return nh


def test_retrieval_packet_backward_compatible_without_language_context() -> None:
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
    assert packet.language_context is None
    dumped = packet.model_dump(mode="json")
    assert "language_context" not in dumped or dumped.get("language_context") is None


def test_retrieval_packet_accepts_explicit_language_context() -> None:
    lc = RetrievalLanguageContext(warnings=["no_language_metadata"])
    packet = RetrievalPacket(
        question="q",
        interpreted_intent=InterpretedIntent(intent_type="explain", confidence=0.8, notes=[]),
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
        confidence=0.7,
        answer_mode="answer_with_evidence",
        language_context=lc,
    )
    assert packet.language_context is not None
    assert packet.language_context.version == 1
    assert packet.language_context.source == "selected_evidence_metadata"


def test_retrieval_packet_has_no_translation_answer_language_fields() -> None:
    names = set(RetrievalPacket.model_fields.keys())
    assert "actor_context" in names
    for forbidden in ("query_translation_used", "translated_evidence", "answer_language"):
        assert forbidden not in names


def test_builder_sets_language_context_without_mutating_evidence_packets() -> None:
    route, idx = _minimal_route_with_primary()
    nh = _minimal_neighborhood()
    ev_id = uuid.uuid4()
    art_id = uuid.uuid4()
    ev = EvidenceCandidate(
        evidence_unit_id=ev_id,
        artifact_id=art_id,
        modality="text",
        content_type="paragraph",
        source_fidelity="verbatim",
        text="alpha beta",
        location=None,
        unit_confidence=0.9,
        support_confidence=0.9,
        selection_reason="linked",
        metadata_json={"language": "en", "language_confidence": 0.88},
    )

    assembly = RetrievalPacketAssemblyInput(
        question="what?",
        interpreted_intent=InterpretedIntent(intent_type="explain", confidence=0.85, notes=[]),
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

    assert packet.language_context is not None
    assert packet.language_context.query_language is None
    assert packet.language_context.source == "selected_evidence_metadata"

    assert len(packet.evidence_units) == 1
    eu = packet.evidence_units[0]
    assert eu.text == "alpha beta"
    assert eu.source_fidelity == "verbatim"
    assert eu.evidence_unit_id == str(ev_id)


def test_builder_aggregates_language_from_selected_evidence_metadata() -> None:
    route, idx = _minimal_route_with_primary()
    nh = _minimal_neighborhood()
    evs = [
        EvidenceCandidate(
            evidence_unit_id=uuid.uuid4(),
            artifact_id=uuid.uuid4(),
            modality="text",
            content_type="paragraph",
            source_fidelity="verbatim",
            text="a",
            location=None,
            unit_confidence=0.9,
            support_confidence=0.9,
            selection_reason="linked",
            metadata_json={"language": "en", "language_confidence": 0.9},
        ),
        EvidenceCandidate(
            evidence_unit_id=uuid.uuid4(),
            artifact_id=uuid.uuid4(),
            modality="text",
            content_type="paragraph",
            source_fidelity="verbatim",
            text="b",
            location=None,
            unit_confidence=0.85,
            support_confidence=0.85,
            selection_reason="linked",
            metadata_json={"language": "en", "language_confidence": 0.8},
        ),
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
        evidence_selected=evs,
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
    assert lc.query_language is None
    assert lc.distinct_evidence_language_count == 1
    assert lc.primary_evidence_language == "en"
    assert lc.evidence_units_without_language_metadata_count == 0
    assert len(lc.evidence_languages) == 1
    row = lc.evidence_languages[0]
    assert row.language == "en"
    assert row.evidence_unit_count == 2
    assert row.average_confidence == pytest.approx(0.85)
    assert row.min_confidence == pytest.approx(0.8)
    assert row.max_confidence == pytest.approx(0.9)


def test_builder_explicit_when_evidence_lacks_language_metadata() -> None:
    route, idx = _minimal_route_with_primary()
    nh = _minimal_neighborhood()
    ev = EvidenceCandidate(
        evidence_unit_id=uuid.uuid4(),
        artifact_id=uuid.uuid4(),
        modality="text",
        content_type="paragraph",
        source_fidelity="verbatim",
        text="no lang key",
        location=None,
        unit_confidence=0.9,
        support_confidence=0.9,
        selection_reason="linked",
        metadata_json=None,
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
    )
    packet = RetrievalPacketBuilder().build(assembly)

    lc = packet.language_context
    assert lc is not None
    assert lc.evidence_languages == []
    assert lc.primary_evidence_language is None
    assert lc.distinct_evidence_language_count == 0
    assert "language_missing_or_null" in lc.warnings
    assert "language_metadata_unavailable_in_packet_builder" in lc.warnings


def test_language_context_literal_source_enforced() -> None:
    with pytest.raises(ValidationError):
        RetrievalLanguageContext.model_validate(
            {
                "version": 1,
                "source": "wrong",
                "query_language": None,
                "evidence_languages": [],
                "primary_evidence_language": None,
                "distinct_evidence_language_count": 0,
                "evidence_units_without_language_metadata_count": 0,
                "warnings": [],
            }
        )


def test_evidence_unit_packet_schema_unchanged_shape() -> None:
    """Ensure we did not add translation or language keys to evidence rows."""
    names = set(EvidenceUnitPacket.model_fields.keys())
    assert "language" not in names
    assert "translated_text" not in names
