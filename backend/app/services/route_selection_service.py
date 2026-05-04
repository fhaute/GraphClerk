"""Semantic index route selection (Phase 4).

Owns invocation of `SemanticIndexSearchService` so orchestration layers do not call
vector search directly.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Callable

from sqlalchemy.orm import Session

from app.services.errors import EmbeddingAdapterNotConfiguredError, VectorIndexUnavailableError
from app.services.semantic_index_search_service import SemanticIndexSearchResult, SemanticIndexSearchService


@dataclass(frozen=True)
class RouteSelection:
    """Primary semantic route plus ranked alternatives and diagnostics."""

    primary: SemanticIndexSearchResult | None
    alternatives: list[SemanticIndexSearchResult]
    selection_reasons: dict[str, str]
    search_warnings: list[str]


class RouteSelectionService:
    """Select primary and alternative semantic indexes from vector search results."""

    def __init__(
        self,
        *,
        session: Session,
        search_service_factory: Callable[[Session], SemanticIndexSearchService] | None = None,
    ) -> None:
        self._session = session
        self._search_service_factory = search_service_factory

    def _make_search_service(self) -> SemanticIndexSearchService:
        if self._search_service_factory is not None:
            return self._search_service_factory(self._session)
        from app.services.semantic_index_search_factory import build_semantic_index_search_service

        return build_semantic_index_search_service(session=self._session)

    def select_routes(
        self,
        *,
        question: str,
        max_selected_indexes: int = 3,
        search_limit: int = 12,
    ) -> RouteSelection:
        """Run semantic search and pick a primary route plus alternatives."""

        warnings: list[str] = []
        reasons: dict[str, str] = {}

        try:
            search = self._make_search_service()
            raw_results = search.search(q=question, limit=search_limit)
        except VectorIndexUnavailableError:
            return RouteSelection(
                primary=None,
                alternatives=[],
                selection_reasons={},
                search_warnings=["vector_index_unavailable"],
            )
        except EmbeddingAdapterNotConfiguredError:
            return RouteSelection(
                primary=None,
                alternatives=[],
                selection_reasons={},
                search_warnings=["embedding_adapter_not_configured"],
            )

        usable: list[SemanticIndexSearchResult] = []
        skipped_missing_entry_nodes = False
        for r in raw_results:
            if not r.entry_node_ids:
                skipped_missing_entry_nodes = True
                continue
            usable.append(r)

        if skipped_missing_entry_nodes:
            warnings.append("semantic_index_has_no_entry_nodes")

        if not usable:
            return RouteSelection(primary=None, alternatives=[], selection_reasons={}, search_warnings=warnings)

        primary = usable[0]
        reasons[str(primary.semantic_index.id)] = "Highest semantic similarity among indexed routes with entry nodes."

        alts = usable[1:max_selected_indexes]
        for i, alt in enumerate(alts, start=2):
            reasons[str(alt.semantic_index.id)] = f"Alternative semantic route ranked #{i} by similarity score."

        if len(usable) >= 2 and abs(usable[0].score - usable[1].score) < 0.05:
            warnings.append("ambiguous_query")

        return RouteSelection(
            primary=primary,
            alternatives=alts,
            selection_reasons=reasons,
            search_warnings=warnings,
        )

    @staticmethod
    def selected_index_ids(selection: RouteSelection, *, max_selected_indexes: int) -> list[uuid.UUID]:
        """Deterministic ordered list of semantic index ids used for traversal."""

        out: list[uuid.UUID] = []
        if selection.primary is not None:
            out.append(selection.primary.semantic_index.id)
        for alt in selection.alternatives:
            if len(out) >= max_selected_indexes:
                break
            out.append(alt.semantic_index.id)
        return out[:max_selected_indexes]
