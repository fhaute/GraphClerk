from __future__ import annotations

import uuid

import httpx
import pytest
from httpx import ASGITransport

from app.db.session import get_sessionmaker
from app.main import create_app
from app.models.enums import SemanticIndexVectorStatus
from app.services.embedding_adapter import DeterministicFakeEmbeddingAdapter
from app.services.embedding_service import EmbeddingService
from app.services.errors import VectorIndexUnavailableError
from app.services.semantic_index_search_service import SemanticIndexSearchService
from app.services.vector_index_service import SearchHit


class _StubVectorIndexService:
    def __init__(self, hits: list[SearchHit] | None = None, exc: Exception | None = None) -> None:
        self._hits = hits or []
        self._exc = exc

    def search_semantic_indexes(self, *, query_vector: list[float], limit: int = 5) -> list[SearchHit]:
        _ = query_vector
        _ = limit
        if self._exc:
            raise self._exc
        return self._hits


@pytest.mark.asyncio
async def test_semantic_index_search_filters_pending_and_failed_preserves_order(db_ready: None, monkeypatch) -> None:
    app = create_app()

    # Create 2 nodes and 3 semantic indexes (all start pending).
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        n1 = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "N1"})).json()["id"]
        n2 = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "N2"})).json()["id"]

        s1 = (await client.post("/semantic-indexes", json={"meaning": "m1", "entry_node_ids": [n1]})).json()["id"]
        s2 = (await client.post("/semantic-indexes", json={"meaning": "m2", "entry_node_ids": [n2]})).json()["id"]
        s3 = (await client.post("/semantic-indexes", json={"meaning": "m3", "entry_node_ids": [n1]})).json()["id"]

    # Update vector_status in DB to represent pre-existing indexing state (Slice H does not persist transitions).
    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        from app.models.semantic_index import SemanticIndex

        idx1 = session.get(SemanticIndex, uuid.UUID(s1))
        idx2 = session.get(SemanticIndex, uuid.UUID(s2))
        idx3 = session.get(SemanticIndex, uuid.UUID(s3))
        assert idx1 and idx2 and idx3
        idx1.vector_status = SemanticIndexVectorStatus.indexed
        idx2.vector_status = SemanticIndexVectorStatus.pending
        idx3.vector_status = SemanticIndexVectorStatus.failed
        session.commit()

    # Stub vector search ordering: pending first, then indexed, then failed.
    hits = [
        SearchHit(semantic_index_id=uuid.UUID(s2), score=0.99, payload={"semantic_index_id": s2}),
        SearchHit(semantic_index_id=uuid.UUID(s1), score=0.50, payload={"semantic_index_id": s1}),
        SearchHit(semantic_index_id=uuid.UUID(s3), score=0.10, payload={"semantic_index_id": s3}),
    ]

    def _build_search_service(*, session):
        embedding = EmbeddingService(adapter=DeterministicFakeEmbeddingAdapter(dimension=8), expected_dimension=8)
        vector = _StubVectorIndexService(hits=hits)
        return SemanticIndexSearchService(session=session, embedding_service=embedding, vector_index_service=vector)

    import app.api.routes.semantic_indexes as route_module

    monkeypatch.setattr(route_module, "_build_search_service", _build_search_service)

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/semantic-indexes/search", params={"q": "hello", "limit": 5})
        assert res.status_code == 200
        body = res.json()
        # Only indexed included (s1), with score preserved.
        assert len(body["results"]) == 1
        assert body["results"][0]["id"] == s1
        assert body["results"][0]["vector_status"] == "indexed"
        assert body["results"][0]["score"] == 0.50
        assert body["results"][0]["entry_node_ids"] == [n1]


@pytest.mark.asyncio
async def test_semantic_index_search_empty_q_returns_422(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/semantic-indexes/search", params={"q": "   "})
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_semantic_index_search_vector_unavailable_maps_503(db_ready: None, monkeypatch) -> None:
    app = create_app()

    def _build_search_service(*, session):
        embedding = EmbeddingService(adapter=DeterministicFakeEmbeddingAdapter(dimension=8), expected_dimension=8)
        vector = _StubVectorIndexService(exc=VectorIndexUnavailableError("down"))
        return SemanticIndexSearchService(session=session, embedding_service=embedding, vector_index_service=vector)

    import app.api.routes.semantic_indexes as route_module

    monkeypatch.setattr(route_module, "_build_search_service", _build_search_service)

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/semantic-indexes/search", params={"q": "hello"})
        assert res.status_code == 503

