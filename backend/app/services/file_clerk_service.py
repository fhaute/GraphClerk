"""File Clerk orchestration for Phase 4 retrieval packets."""

from __future__ import annotations

import time
from typing import Callable

from sqlalchemy.orm import Session

from app.schemas.retrieval import ActorContext
from app.schemas.retrieval_packet import RetrieveOptions, RetrievalPacket, SelectedSemanticIndex
from app.services.context_budget_service import ContextBudgetService
from app.services.errors import GraphNodeNotFoundError
from app.services.evidence_selection_service import EvidenceSelectionService
from app.services.graph_traversal_service import GraphNeighborhood, GraphTraversalService
from app.services.query_intent_service import QueryIntentService
from app.services.retrieval_packet_builder import RetrievalPacketAssemblyInput, RetrievalPacketBuilder
from app.services.route_selection_service import RouteSelection, RouteSelectionService
from app.services.semantic_index_search_service import SemanticIndexSearchResult, SemanticIndexSearchService


class FileClerkService:
    """Coordinate retrieval services and persist an honest `RetrievalLog` snapshot."""

    def __init__(
        self,
        *,
        session: Session,
        search_service_factory: Callable[[Session], SemanticIndexSearchService] | None = None,
    ) -> None:
        self._session = session
        self._intent = QueryIntentService()
        self._routes = RouteSelectionService(session=session, search_service_factory=search_service_factory)
        self._traversal = GraphTraversalService(session=session)
        self._evidence = EvidenceSelectionService(session=session)
        self._budget = ContextBudgetService()
        self._builder = RetrievalPacketBuilder()

    def retrieve(
        self,
        question: str,
        options: RetrieveOptions | None = None,
        *,
        actor_context: ActorContext | None = None,
    ) -> RetrievalPacket:
        """Run the documented retrieval pipeline and return a validated `RetrievalPacket`."""

        opts = options or RetrieveOptions()
        started = time.perf_counter()

        intent_res = self._intent.classify(question)
        route = self._routes.select_routes(
            question=question,
            max_selected_indexes=opts.max_selected_indexes,
            search_limit=max(12, opts.max_selected_indexes * 4),
        )

        warnings: list[str] = list(route.search_warnings)
        if route.primary is None and "vector_index_unavailable" not in warnings:
            warnings.append("no_semantic_index_match")

        ordered_results = self._ordered_search_results(route)
        selected_index_models = self._selected_indexes_from_results(route, ordered_results)

        neighborhoods: list[GraphNeighborhood] = []
        remaining_paths = opts.max_graph_paths
        for res in ordered_results:
            if remaining_paths <= 0:
                break
            for entry_id in sorted(res.entry_node_ids, key=lambda x: str(x)):
                if remaining_paths <= 0:
                    break
                try:
                    nh = self._traversal.neighborhood(
                        start_node_id=entry_id,
                        depth=opts.max_graph_depth,
                        max_nodes=25,
                        max_edges=50,
                        relation_types=None,
                    )
                except GraphNodeNotFoundError:
                    warnings.append("no_graph_path_found")
                    continue
                neighborhoods.append(nh)
                remaining_paths -= 1

        ranked = self._evidence.collect_from_neighborhoods(neighborhoods)
        budgeted = self._budget.apply(
            ranked_evidence=ranked,
            max_evidence_units=opts.max_evidence_units,
            max_tokens_estimate=opts.max_tokens_estimate,
        )

        if not ranked and neighborhoods:
            warnings.append("no_evidence_support_found")

        latency_ms = int((time.perf_counter() - started) * 1000)
        token_estimate = sum(len((e.text or "")) for e in budgeted.selected) // 4 or None

        assembly = RetrievalPacketAssemblyInput(
            question=question.strip(),
            interpreted_intent=intent_res.intent,
            route_selection=route,
            selected_indexes=selected_index_models,
            graph_neighborhoods=neighborhoods,
            evidence_selected=budgeted.selected,
            evidence_pruned=budgeted.pruned_count,
            pruning_reasons=budgeted.pruning_reasons,
            warnings=warnings,
            options_max_evidence_units=opts.max_evidence_units,
            options_max_graph_paths=opts.max_graph_paths,
            options_max_selected_indexes=opts.max_selected_indexes,
            include_alternatives=opts.include_alternatives,
            request_actor_context=actor_context,
        )
        packet = self._builder.build(assembly)

        # Persistence is explicit and best-effort: failures should not replace a valid packet.
        try:
            from app.repositories.retrieval_log_repository import RetrievalLogRepository

            RetrievalLogRepository(self._session).create_from_packet(
                packet=packet,
                latency_ms=latency_ms,
                token_estimate=token_estimate,
                metadata=None,
            )
            self._session.commit()
        except Exception:
            self._session.rollback()
            # Observability loss is acceptable vs returning invalid structured output.
            # Callers still receive the packet.

        return packet

    @staticmethod
    def _ordered_search_results(route: RouteSelection) -> list[SemanticIndexSearchResult]:
        out: list[SemanticIndexSearchResult] = []
        if route.primary is not None:
            out.append(route.primary)
        out.extend(route.alternatives)
        return out

    @staticmethod
    def _selected_indexes_from_results(
        route: RouteSelection,
        ordered_results: list[SemanticIndexSearchResult],
    ) -> list[SelectedSemanticIndex]:
        items: list[SelectedSemanticIndex] = []
        for r in ordered_results:
            sid = str(r.semantic_index.id)
            reason = route.selection_reasons.get(sid, "Semantic index selected for traversal.")
            items.append(
                SelectedSemanticIndex(
                    semantic_index_id=sid,
                    meaning=r.semantic_index.meaning,
                    score=float(r.score),
                    selection_reason=reason,
                )
            )
        return items
