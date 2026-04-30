from __future__ import annotations

import uuid

import pytest

from app.services.errors import (
    VectorIndexDimensionMismatchError,
    VectorIndexOperationError,
    VectorIndexUnavailableError,
)
from app.services.vector_index_service import SearchHit, VectorIndexService


class _FakeScoredPoint:
    def __init__(self, payload, score) -> None:
        self.payload = payload
        self.score = score


class _StubQdrantClient:
    def __init__(self) -> None:
        self.collections: set[str] = set()
        self.created: list[tuple[str, int, str]] = []
        self.upserts: list[tuple[str, str, list[float], dict]] = []
        self.search_results = []
        self.fail_get = False
        self.fail_create = False
        self.fail_upsert = False
        self.fail_search = False

    def get_collection(self, collection_name: str):
        if self.fail_get or collection_name not in self.collections:
            raise RuntimeError("not found")
        return {"name": collection_name}

    def create_collection(self, collection_name: str, vectors_config):
        if self.fail_create:
            raise RuntimeError("create failed")
        self.collections.add(collection_name)
        self.created.append((collection_name, vectors_config.size, str(vectors_config.distance)))
        return True

    def upsert(self, collection_name: str, points, wait: bool | None = None):
        _ = wait
        if self.fail_upsert:
            raise RuntimeError("upsert failed")
        p = points[0]
        self.upserts.append((collection_name, p.id, p.vector, p.payload))
        return True

    def query_points(self, collection_name: str, query, limit: int, with_payload=None):
        if self.fail_search:
            raise RuntimeError("search failed")
        class _Resp:
            def __init__(self, points):
                self.points = points

        return _Resp(self.search_results[:limit])


def test_ensure_collection_creates_when_missing() -> None:
    client = _StubQdrantClient()
    svc = VectorIndexService(qdrant_client=client, expected_dimension=8)
    svc.ensure_semantic_indexes_collection()
    assert VectorIndexService.collection_name in client.collections
    assert client.created[0][0] == VectorIndexService.collection_name
    assert client.created[0][1] == 8


def test_ensure_collection_already_exists_no_create() -> None:
    client = _StubQdrantClient()
    client.collections.add(VectorIndexService.collection_name)
    svc = VectorIndexService(qdrant_client=client, expected_dimension=8)
    svc.ensure_semantic_indexes_collection()
    assert client.created == []


def test_upsert_semantic_index_vector_calls_client() -> None:
    client = _StubQdrantClient()
    client.collections.add(VectorIndexService.collection_name)
    svc = VectorIndexService(qdrant_client=client, expected_dimension=3)
    sid = uuid.uuid4()
    svc.upsert_semantic_index_vector(semantic_index_id=sid, vector=[0.1, 0.2, 0.3], payload={"meaning": "m"})
    assert len(client.upserts) == 1
    collection, pid, vec, payload = client.upserts[0]
    assert collection == VectorIndexService.collection_name
    assert pid == str(sid)  # point id strategy: UUID string
    assert vec == [0.1, 0.2, 0.3]
    assert payload["semantic_index_id"] == str(sid)
    assert payload["meaning"] == "m"


def test_search_semantic_indexes_returns_hits() -> None:
    client = _StubQdrantClient()
    client.collections.add(VectorIndexService.collection_name)
    sid = uuid.uuid4()
    client.search_results = [_FakeScoredPoint(payload={"semantic_index_id": str(sid)}, score=0.9)]
    svc = VectorIndexService(qdrant_client=client, expected_dimension=2)
    hits = svc.search_semantic_indexes(query_vector=[0.0, 1.0], limit=5)
    assert hits == [SearchHit(semantic_index_id=sid, score=0.9, payload={"semantic_index_id": str(sid)})]


def test_qdrant_unavailable_fails_explicitly() -> None:
    client = _StubQdrantClient()
    client.fail_search = True
    svc = VectorIndexService(qdrant_client=client, expected_dimension=2)
    with pytest.raises(VectorIndexUnavailableError):
        svc.search_semantic_indexes(query_vector=[0.0, 1.0], limit=5)


def test_dimension_mismatch_fails_before_client_call() -> None:
    client = _StubQdrantClient()
    client.fail_search = True
    svc = VectorIndexService(qdrant_client=client, expected_dimension=3)
    with pytest.raises(VectorIndexDimensionMismatchError):
        svc.search_semantic_indexes(query_vector=[0.0, 1.0], limit=5)


def test_malformed_search_payload_fails_clearly() -> None:
    client = _StubQdrantClient()
    client.collections.add(VectorIndexService.collection_name)
    client.search_results = [_FakeScoredPoint(payload={"wrong": "x"}, score=0.1)]
    svc = VectorIndexService(qdrant_client=client, expected_dimension=2)
    with pytest.raises(VectorIndexOperationError):
        svc.search_semantic_indexes(query_vector=[0.0, 1.0], limit=5)

