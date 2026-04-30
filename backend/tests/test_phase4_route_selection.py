from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models.enums import SemanticIndexVectorStatus
from app.models.semantic_index import SemanticIndex
from app.services.errors import VectorIndexUnavailableError
from app.services.route_selection_service import RouteSelectionService
from app.services.semantic_index_search_service import SemanticIndexSearchResult, SemanticIndexSearchService


def _idx(i: int) -> SemanticIndex:
    return SemanticIndex(
        id=uuid.uuid4(),
        meaning=f"m{i}",
        summary=None,
        embedding_text=f"t{i}",
        vector_status=SemanticIndexVectorStatus.indexed,
        metadata_json=None,
    )


def test_route_selection_primary_and_alternates() -> None:
    session = MagicMock(spec=Session)
    a, b, c = _idx(1), _idx(2), _idx(3)

    def factory(_s: Session) -> SemanticIndexSearchService:
        svc = MagicMock(spec=SemanticIndexSearchService)

        def search(*, q: str, limit: int = 5):
            _ = q
            _ = limit
            return [
                SemanticIndexSearchResult(semantic_index=a, entry_node_ids=[uuid.uuid4()], score=0.9),
                SemanticIndexSearchResult(semantic_index=b, entry_node_ids=[uuid.uuid4()], score=0.4),
                SemanticIndexSearchResult(semantic_index=c, entry_node_ids=[uuid.uuid4()], score=0.39),
            ]

        svc.search.side_effect = search
        return svc

    sel = RouteSelectionService(session=session, search_service_factory=factory)
    out = sel.select_routes(question="hello", max_selected_indexes=2, search_limit=5)
    assert out.primary is not None and out.primary.semantic_index.id == a.id
    assert len(out.alternatives) == 1
    assert str(a.id) in out.selection_reasons


def test_route_selection_skips_empty_entry_nodes() -> None:
    session = MagicMock(spec=Session)
    a = _idx(1)

    def factory(_s: Session) -> SemanticIndexSearchService:
        svc = MagicMock(spec=SemanticIndexSearchService)

        def search(*, q: str, limit: int = 5):
            _ = q
            _ = limit
            return [
                SemanticIndexSearchResult(semantic_index=a, entry_node_ids=[], score=0.99),
            ]

        svc.search.side_effect = search
        return svc

    sel = RouteSelectionService(session=session, search_service_factory=factory)
    out = sel.select_routes(question="hello", max_selected_indexes=3, search_limit=5)
    assert out.primary is None
    assert "semantic_index_has_no_entry_nodes" in out.search_warnings


def test_route_selection_vector_unavailable() -> None:
    session = MagicMock(spec=Session)

    def factory(_s: Session) -> SemanticIndexSearchService:
        svc = MagicMock(spec=SemanticIndexSearchService)
        svc.search.side_effect = VectorIndexUnavailableError("down")
        return svc

    sel = RouteSelectionService(session=session, search_service_factory=factory)
    out = sel.select_routes(question="hello")
    assert out.primary is None
    assert "vector_index_unavailable" in out.search_warnings
