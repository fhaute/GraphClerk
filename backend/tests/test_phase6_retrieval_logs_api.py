"""Phase 6 Slice A — RetrievalLog read API tests."""

from __future__ import annotations

import uuid

import httpx
import pytest
from httpx import ASGITransport

from app.db.session import get_sessionmaker
from app.main import create_app
from app.models.enums import SemanticIndexVectorStatus
from app.models.semantic_index import SemanticIndex
from app.services.embedding_adapter import DeterministicFakeEmbeddingAdapter
from app.services.embedding_service import EmbeddingService
from app.services.semantic_index_search_service import SemanticIndexSearchService
from app.services.vector_index_service import SearchHit


class _StubVectorIndexService:
    def __init__(self, hits: list[SearchHit]) -> None:
        self._hits = hits

    def search_semantic_indexes(
        self,
        *,
        query_vector: list[float],
        limit: int = 5,
    ) -> list[SearchHit]:
        _ = query_vector
        _ = limit
        return self._hits


@pytest.mark.asyncio
async def test_list_retrieval_logs_empty_returns_items_array(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/retrieval-logs")
    assert res.status_code == 200
    body = res.json()
    assert body == {"items": []}


@pytest.mark.asyncio
async def test_retrieval_logs_list_and_detail_after_retrieve(
    db_ready: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        n1 = (
            await client.post("/graph/nodes", json={"node_type": "concept", "label": "RLN1"})
        ).json()["id"]
        idx_res = await client.post(
            "/semantic-indexes",
            json={"meaning": "rl_meaning", "entry_node_ids": [n1]},
        )
        sid = idx_res.json()["id"]

    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        row = session.get(SemanticIndex, uuid.UUID(sid))
        assert row is not None
        row.vector_status = SemanticIndexVectorStatus.indexed
        session.commit()

    hits = [
        SearchHit(
            semantic_index_id=uuid.UUID(sid),
            score=0.88,
            payload={"semantic_index_id": sid},
        )
    ]

    def factory(*, session):
        embedding = EmbeddingService(
            adapter=DeterministicFakeEmbeddingAdapter(dimension=8),
            expected_dimension=8,
        )
        vector = _StubVectorIndexService(hits=hits)
        return SemanticIndexSearchService(
            session=session,
            embedding_service=embedding,
            vector_index_service=vector,
        )

    import app.services.semantic_index_search_factory as factory_module

    monkeypatch.setattr(factory_module, "build_semantic_index_search_service", factory)

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r_ret = await client.post("/retrieve", json={"question": "phase six retrieval log probe"})
        assert r_ret.status_code == 200

        r_list = await client.get("/retrieval-logs", params={"limit": 10})
        assert r_list.status_code == 200
        items = r_list.json()["items"]
        assert len(items) >= 1
        top = items[0]
        assert top["question"] == "phase six retrieval log probe"
        assert top["has_retrieval_packet"] is True
        assert top["id"]

        r_detail = await client.get(f"/retrieval-logs/{top['id']}")
        assert r_detail.status_code == 200
        detail = r_detail.json()
        assert detail["question"] == "phase six retrieval log probe"
        assert detail["retrieval_packet"] is not None
        assert detail["retrieval_packet"]["packet_type"] == "retrieval_packet"


@pytest.mark.asyncio
async def test_get_retrieval_log_unknown_returns_404(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(f"/retrieval-logs/{uuid.uuid4()}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_get_retrieval_log_invalid_uuid_returns_422(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/retrieval-logs/not-a-uuid")
    assert res.status_code == 422
