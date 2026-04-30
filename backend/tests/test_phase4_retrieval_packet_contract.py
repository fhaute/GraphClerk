from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.retrieval_packet import (
    AlternativeInterpretation,
    ContextBudgetSummary,
    EvidenceUnitPacket,
    GraphPathPacket,
    InterpretedIntent,
    RetrievalPacket,
    SelectedSemanticIndex,
)


def test_retrieval_packet_required_fields_round_trip() -> None:
    """All phase-required fields must serialize and validate."""

    packet = RetrievalPacket(
        question="How do I reduce hallucination in RAG?",
        interpreted_intent=InterpretedIntent(intent_type="explain", confidence=0.78, notes=[]),
        selected_indexes=[
            SelectedSemanticIndex(
                semantic_index_id="idx-1",
                meaning="Hallucination reduction",
                score=0.91,
                selection_reason="Best semantic match.",
            )
        ],
        graph_paths=[
            GraphPathPacket(
                start_node_id="node-1",
                nodes=["node-1", "node-2"],
                edges=["edge-1"],
                depth=1,
            )
        ],
        evidence_units=[
            EvidenceUnitPacket(
                evidence_unit_id="ev-1",
                artifact_id="art-1",
                modality="text",
                content_type="paragraph",
                source_fidelity="verbatim",
                text="Example evidence.",
                location={"section_path": ["A"], "line_start": 1, "line_end": 2},
                selection_reason="Supports graph edge edge-1.",
                confidence=0.86,
            )
        ],
        alternative_interpretations=[
            AlternativeInterpretation(
                if_user_meant="token cost",
                suggested_semantic_indexes=["idx-cost"],
                reason="Ambiguous wording.",
            )
        ],
        context_budget=ContextBudgetSummary(
            max_evidence_units=8,
            selected_evidence_units=1,
            pruned_evidence_units=0,
            pruning_reasons=[],
            max_graph_paths=3,
            max_selected_indexes=3,
        ),
        warnings=["low_confidence"],
        confidence=0.79,
        answer_mode="answer_with_evidence",
    )
    dumped = packet.model_dump(mode="json")
    restored = RetrievalPacket.model_validate(dumped)
    assert restored.packet_type == "retrieval_packet"
    assert restored.question == packet.question


def test_retrieval_packet_rejects_invalid_answer_mode() -> None:
    with pytest.raises(ValidationError):
        RetrievalPacket(
            question="q",
            interpreted_intent=InterpretedIntent(intent_type="unknown", confidence=0.1, notes=[]),
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
            warnings=["no_semantic_index_match"],
            confidence=0.0,
            answer_mode="not_a_mode",  # type: ignore[arg-type]
        )
