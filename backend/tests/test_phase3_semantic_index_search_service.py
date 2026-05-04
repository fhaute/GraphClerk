from __future__ import annotations

import uuid
from dataclasses import dataclass

import pytest

from app.models.enums import SemanticIndexVectorStatus
from app.models.semantic_index import SemanticIndex
from app.services.errors import (
    EmbeddingAdapterNotConfiguredError,
    EmbeddingTextEmptyError,
    VectorIndexUnavailableError,
)
from app.services.semantic_index_search_service import SemanticIndexSearchService
from app.services.vector_index_service import SearchHit


@dataclass(frozen=True)
class _Link:
    graph_node_id: uuid.UUID


class _StubEmbeddingService:
    def __init__(self, *, vec: list[float] | None = None, exc: Exception | None = None) -> None:
        self._vec = vec or [0.0] * 8
        self._exc = exc

    def embed_text(self, text: str) -> list[float]:
        if self._exc:
            raise self._exc
        return self._vec


class _StubVectorIndexService:
    def __init__(self, *, hits: list[SearchHit] | None = None, exc: Exception | None = None) -> None:
        self._hits = hits or []
        self._exc = exc

    def search_semantic_indexes(self, *, query_vector: list[float], limit: int = 5) -> list[SearchHit]:
        _ = query_vector
        _ = limit
        if self._exc:
            raise self._exc
        return self._hits


class _StubSemanticIndexRepo:
    def __init__(self, rows: list[SemanticIndex]) -> None:
        self._rows = rows

    def list_by_ids(self, semantic_index_ids: list[uuid.UUID]) -> list[SemanticIndex]:
        s = set(semantic_index_ids)
        return [r for r in self._rows if r.id in s]


class _StubEntryRepo:
    def __init__(self, mapping: dict[uuid.UUID, list[uuid.UUID]]) -> None:
        self._mapping = mapping

    def list_by_semantic_index(self, semantic_index_id: uuid.UUID, limit: int = 1000, offset: int = 0):
        _ = limit
        _ = offset
        return [_Link(graph_node_id=nid) for nid in self._mapping.get(semantic_index_id, [])]


def _mk_index(*, sid: uuid.UUID, status: SemanticIndexVectorStatus) -> SemanticIndex:
    return SemanticIndex(
        id=sid,
        meaning="m",
        summary=None,
        embedding_text="t",
        entry_node_ids=None,
        vector_status=status,
        metadata_json={"k": "v"},
    )


def test_happy_path_returns_ordered_postgres_backed_results_with_scores() -> None:
    sid1, sid2 = uuid.uuid4(), uuid.uuid4()
    idx1 = _mk_index(sid=sid1, status=SemanticIndexVectorStatus.indexed)
    idx2 = _mk_index(sid=sid2, status=SemanticIndexVectorStatus.indexed)

    hits = [
        SearchHit(semantic_index_id=sid2, score=0.9, payload={"semantic_index_id": str(sid2)}),
        SearchHit(semantic_index_id=sid1, score=0.8, payload={"semantic_index_id": str(sid1)}),
    ]
    svc = SemanticIndexSearchService(
        session=None,  # not used because repos are stubbed
        embedding_service=_StubEmbeddingService(),
        vector_index_service=_StubVectorIndexService(hits=hits),
        semantic_index_repo=_StubSemanticIndexRepo([idx1, idx2]),
        entry_node_repo=_StubEntryRepo({sid1: [uuid.uuid4()], sid2: [uuid.uuid4()]}),
    )

    results = svc.search(q="hello", limit=5)
    assert [r.semantic_index.id for r in results] == [sid2, sid1]
    assert [r.score for r in results] == [0.9, 0.8]


def test_failed_and_pending_excluded_only_indexed_returned() -> None:
    sid_i, sid_p, sid_f = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    idx_i = _mk_index(sid=sid_i, status=SemanticIndexVectorStatus.indexed)
    idx_p = _mk_index(sid=sid_p, status=SemanticIndexVectorStatus.pending)
    idx_f = _mk_index(sid=sid_f, status=SemanticIndexVectorStatus.failed)

    hits = [
        SearchHit(semantic_index_id=sid_p, score=0.99, payload={"semantic_index_id": str(sid_p)}),
        SearchHit(semantic_index_id=sid_i, score=0.50, payload={"semantic_index_id": str(sid_i)}),
        SearchHit(semantic_index_id=sid_f, score=0.10, payload={"semantic_index_id": str(sid_f)}),
    ]
    svc = SemanticIndexSearchService(
        session=None,
        embedding_service=_StubEmbeddingService(),
        vector_index_service=_StubVectorIndexService(hits=hits),
        semantic_index_repo=_StubSemanticIndexRepo([idx_i, idx_p, idx_f]),
        entry_node_repo=_StubEntryRepo({sid_i: [uuid.uuid4()]}),
    )

    results = svc.search(q="hello", limit=5)
    assert [r.semantic_index.id for r in results] == [sid_i]


def test_embedding_errors_propagate_explicitly() -> None:
    svc = SemanticIndexSearchService(
        session=None,
        embedding_service=_StubEmbeddingService(exc=EmbeddingAdapterNotConfiguredError("embedding_adapter_not_configured")),
        vector_index_service=_StubVectorIndexService(),
        semantic_index_repo=_StubSemanticIndexRepo([]),
        entry_node_repo=_StubEntryRepo({}),
    )
    with pytest.raises(EmbeddingAdapterNotConfiguredError):
        svc.search(q="hello", limit=5)


def test_vector_errors_propagate_explicitly() -> None:
    svc = SemanticIndexSearchService(
        session=None,
        embedding_service=_StubEmbeddingService(),
        vector_index_service=_StubVectorIndexService(exc=VectorIndexUnavailableError("down")),
        semantic_index_repo=_StubSemanticIndexRepo([]),
        entry_node_repo=_StubEntryRepo({}),
    )
    with pytest.raises(VectorIndexUnavailableError):
        svc.search(q="hello", limit=5)


def test_empty_query_rejected_by_embedding_service() -> None:
    svc = SemanticIndexSearchService(
        session=None,
        embedding_service=_StubEmbeddingService(exc=EmbeddingTextEmptyError("embedding_text_empty")),
        vector_index_service=_StubVectorIndexService(),
        semantic_index_repo=_StubSemanticIndexRepo([]),
        entry_node_repo=_StubEntryRepo({}),
    )
    with pytest.raises(EmbeddingTextEmptyError):
        svc.search(q="   ", limit=5)


def test_qdrant_hit_missing_in_postgres_is_skipped() -> None:
    sid = uuid.uuid4()
    hits = [SearchHit(semantic_index_id=sid, score=0.9, payload={"semantic_index_id": str(sid)})]
    svc = SemanticIndexSearchService(
        session=None,
        embedding_service=_StubEmbeddingService(),
        vector_index_service=_StubVectorIndexService(hits=hits),
        semantic_index_repo=_StubSemanticIndexRepo([]),
        entry_node_repo=_StubEntryRepo({}),
    )
    assert svc.search(q="hello", limit=5) == []

