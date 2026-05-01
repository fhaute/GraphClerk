"""Assemble and validate `RetrievalPacket` instances (Phase 4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.schemas.retrieval import ActorContext
from app.schemas.retrieval_packet import (
    AlternativeInterpretation,
    ContextBudgetSummary,
    EvidenceLanguageAggregateRow,
    EvidenceUnitPacket,
    GraphPathPacket,
    InterpretedIntent,
    PacketActorContextRecording,
    RetrievalLanguageContext,
    RetrievalPacket,
    SelectedSemanticIndex,
)
from app.services.artifact_language_aggregation_service import (
    GRAPHCLERK_LANGUAGE_AGGREGATION_KEY,
    ArtifactLanguageAggregationService,
)
from app.services.evidence_selection_service import EvidenceCandidate
from app.services.graph_traversal_service import GraphNeighborhood
from app.services.route_selection_service import RouteSelection


@dataclass(frozen=True)
class RetrievalPacketAssemblyInput:
    """Inputs required to assemble a retrieval packet."""

    question: str
    interpreted_intent: InterpretedIntent
    route_selection: RouteSelection
    selected_indexes: list[SelectedSemanticIndex]
    graph_neighborhoods: list[GraphNeighborhood]
    evidence_selected: list[EvidenceCandidate]
    evidence_pruned: int
    pruning_reasons: list[str]
    warnings: list[str]
    options_max_evidence_units: int
    options_max_graph_paths: int
    options_max_selected_indexes: int
    include_alternatives: bool = True
    request_actor_context: ActorContext | None = None


class RetrievalPacketBuilder:
    """Build a validated `RetrievalPacket` from orchestrated retrieval artifacts."""

    def build(self, data: RetrievalPacketAssemblyInput) -> RetrievalPacket:
        """Construct a packet with explicit warnings and suggested answer mode."""

        warnings = sorted(set(data.warnings))

        graph_paths: list[GraphPathPacket] = []
        for nh in data.graph_neighborhoods:
            graph_paths.append(
                GraphPathPacket(
                    start_node_id=str(nh.start_node_id),
                    nodes=sorted([str(n.id) for n in nh.nodes], key=lambda x: x),
                    edges=sorted([str(e.id) for e in nh.edges], key=lambda x: x),
                    depth=nh.depth,
                )
            )

        evidence_units = [
            EvidenceUnitPacket(
                evidence_unit_id=str(c.evidence_unit_id),
                artifact_id=str(c.artifact_id),
                modality=c.modality,
                content_type=c.content_type,
                source_fidelity=c.source_fidelity,
                text=c.text,
                location=c.location,
                selection_reason=c.selection_reason,
                confidence=c.unit_confidence,
            )
            for c in data.evidence_selected
        ]

        alternatives: list[AlternativeInterpretation] = []
        if (
            data.include_alternatives
            and data.route_selection.primary is not None
            and len(data.route_selection.alternatives) > 0
        ):
            alt_ids = [str(x.semantic_index.id) for x in data.route_selection.alternatives]
            alternatives.append(
                AlternativeInterpretation(
                    if_user_meant="Alternate semantic meaning suggested by next-best semantic index matches.",
                    suggested_semantic_indexes=alt_ids,
                    reason="Multiple semantic indexes scored closely; see warnings for ambiguity signal.",
                )
            )

        context_budget = ContextBudgetSummary(
            max_evidence_units=data.options_max_evidence_units,
            selected_evidence_units=len(evidence_units),
            pruned_evidence_units=data.evidence_pruned,
            pruning_reasons=sorted(set(data.pruning_reasons)),
            max_graph_paths=data.options_max_graph_paths,
            max_selected_indexes=data.options_max_selected_indexes,
        )

        if context_budget.pruned_evidence_units >= 3 and "context_budget_pruned_many_items" not in warnings:
            warnings = sorted(set([*warnings, "context_budget_pruned_many_items"]))

        confidence = self._compute_confidence(
            interpreted_intent=data.interpreted_intent,
            route_selection=data.route_selection,
            evidence=data.evidence_selected,
            warnings=warnings,
        )

        answer_mode = self._suggest_answer_mode(
            has_primary=data.route_selection.primary is not None,
            evidence_count=len(evidence_units),
            graph_path_count=len(graph_paths),
            warnings=warnings,
            confidence=confidence,
        )

        if confidence < 0.35 and "low_confidence" not in warnings:
            warnings = sorted(set([*warnings, "low_confidence"]))

        language_context = self._build_language_context(data.evidence_selected)

        actor_packet = self._build_actor_context_recording(data.request_actor_context)

        packet = RetrievalPacket(
            question=data.question,
            interpreted_intent=data.interpreted_intent,
            selected_indexes=data.selected_indexes,
            graph_paths=graph_paths,
            evidence_units=evidence_units,
            alternative_interpretations=alternatives,
            context_budget=context_budget,
            warnings=warnings,
            confidence=confidence,
            answer_mode=answer_mode,
            language_context=language_context,
            actor_context=actor_packet,
        )
        # Final validation pass (explicit, even though models enforce shape).
        return RetrievalPacket.model_validate(packet.model_dump(mode="json"))

    def _build_language_context(self, evidence_selected: list[EvidenceCandidate]) -> RetrievalLanguageContext:
        """Aggregate language fields from selected evidence ``metadata_json`` only (Slice 7F)."""

        projections: list[dict[str, Any]] = []
        for c in evidence_selected:
            projections.append(dict(c.metadata_json) if c.metadata_json is not None else {})

        merged = ArtifactLanguageAggregationService().aggregate(
            artifact_metadata=None,
            evidence_metadata_projections=projections,
        )
        inner = merged[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]

        lc_warnings = list(inner["warnings"])
        if evidence_selected and all(c.metadata_json is None for c in evidence_selected):
            lc_warnings.append("language_metadata_unavailable_in_packet_builder")
        lc_warnings = sorted(set(lc_warnings))

        rows = [
            EvidenceLanguageAggregateRow(
                language=r["language"],
                evidence_unit_count=r["evidence_unit_count"],
                average_confidence=r["average_confidence"],
                min_confidence=r["min_confidence"],
                max_confidence=r["max_confidence"],
            )
            for r in inner["languages"]
        ]

        return RetrievalLanguageContext(
            evidence_languages=rows,
            primary_evidence_language=inner["primary_language"],
            distinct_evidence_language_count=inner["distinct_language_count"],
            evidence_units_without_language_metadata_count=inner[
                "evidence_units_without_language_metadata_count"
            ],
            warnings=lc_warnings,
        )

    @staticmethod
    def _build_actor_context_recording(request_actor_context: ActorContext | None) -> PacketActorContextRecording:
        """Attach explicit actor-context recording without retrieval influence (Slice 7H)."""

        if request_actor_context is None:
            return PacketActorContextRecording(
                used=False,
                recorded_context=None,
                influence="none",
                warnings=[],
            )
        return PacketActorContextRecording(
            used=True,
            recorded_context=request_actor_context,
            influence="recorded_only_no_route_boost_applied",
            warnings=[],
        )

    @staticmethod
    def _compute_confidence(
        *,
        interpreted_intent: InterpretedIntent,
        route_selection: RouteSelection,
        evidence: list[EvidenceCandidate],
        warnings: list[str],
    ) -> float:
        if route_selection.primary is None:
            base = 0.25
        else:
            scores = [route_selection.primary.score, interpreted_intent.confidence]
            if evidence:
                confs = [c.unit_confidence or c.support_confidence or 0.0 for c in evidence]
                scores.append(sum(confs) / max(1, len(confs)))
            else:
                scores.append(0.35)
            base = float(sum(scores) / len(scores))

        penalty = 0.0
        if "ambiguous_query" in warnings:
            penalty += 0.07
        if "vector_index_unavailable" in warnings:
            penalty += 0.10
        if "no_semantic_index_match" in warnings:
            penalty += 0.15
        if "semantic_index_has_no_entry_nodes" in warnings:
            penalty += 0.05

        return max(0.0, min(1.0, base - penalty))

    @staticmethod
    def _suggest_answer_mode(
        *,
        has_primary: bool,
        evidence_count: int,
        graph_path_count: int,
        warnings: list[str],
        confidence: float,
    ) -> str:
        if not has_primary or "no_semantic_index_match" in warnings:
            return "not_enough_evidence"
        if "vector_index_unavailable" in warnings:
            return "not_enough_evidence"
        if evidence_count == 0 and graph_path_count > 0:
            return "not_enough_evidence"
        if evidence_count == 0:
            return "not_enough_evidence"
        if "ambiguous_query" in warnings:
            return "answer_with_caveats"
        if confidence < 0.45:
            return "answer_with_caveats"
        return "answer_with_evidence"
