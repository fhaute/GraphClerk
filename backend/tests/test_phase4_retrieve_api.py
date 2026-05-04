from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import httpx
import pytest
from httpx import ASGITransport

from sqlalchemy import select

from app.db.session import get_sessionmaker
from app.main import create_app
from app.models.enums import SemanticIndexVectorStatus
from app.models.retrieval_log import RetrievalLog
from app.services.embedding_adapter import DeterministicFakeEmbeddingAdapter
from app.services.embedding_service import EmbeddingService
from app.services.errors import EmbeddingAdapterNotConfiguredError
from app.services.semantic_index_search_service import SemanticIndexSearchService
from app.services.vector_index_service import SearchHit


class _StubVectorIndexService:
    def __init__(self, hits: list[SearchHit]) -> None:
        self._hits = hits

    def search_semantic_indexes(self, *, query_vector: list[float], limit: int = 5) -> list[SearchHit]:
        _ = query_vector
        _ = limit
        return self._hits


@pytest.mark.asyncio
async def test_retrieve_endpoint_returns_retrieval_packet(db_ready: None, monkeypatch) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        n1 = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "N1"})).json()["id"]
        n2 = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "N2"})).json()["id"]

        s1 = (await client.post("/semantic-indexes", json={"meaning": "m1", "entry_node_ids": [n1]})).json()["id"]
        s2 = (await client.post("/semantic-indexes", json={"meaning": "m2", "entry_node_ids": [n2]})).json()["id"]

    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        from app.models.semantic_index import SemanticIndex

        for sid in (s1, s2):
            row = session.get(SemanticIndex, uuid.UUID(sid))
            assert row is not None
            row.vector_status = SemanticIndexVectorStatus.indexed
        session.commit()

    hits = [
        SearchHit(semantic_index_id=uuid.UUID(s1), score=0.91, payload={"semantic_index_id": s1}),
        SearchHit(semantic_index_id=uuid.UUID(s2), score=0.90, payload={"semantic_index_id": s2}),
    ]

    def factory(*, session):
        embedding = EmbeddingService(adapter=DeterministicFakeEmbeddingAdapter(dimension=8), expected_dimension=8)
        vector = _StubVectorIndexService(hits=hits)
        return SemanticIndexSearchService(session=session, embedding_service=embedding, vector_index_service=vector)

    import app.services.semantic_index_search_factory as factory_module

    monkeypatch.setattr(factory_module, "build_semantic_index_search_service", factory)

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/retrieve", json={"question": "hello world"})
        assert res.status_code == 200
        body = res.json()
        assert body["packet_type"] == "retrieval_packet"
        assert body["question"] == "hello world"
        assert len(body["selected_indexes"]) >= 1
        assert isinstance(body["warnings"], list)
        assert isinstance(body["graph_paths"], list)
        assert isinstance(body["evidence_units"], list)
        assert isinstance(body["alternative_interpretations"], list)
        assert "context_budget" in body

    with SessionMaker() as session:
        log = session.execute(select(RetrievalLog).order_by(RetrievalLog.created_at.desc()).limit(1)).scalar_one()
        assert log.retrieval_packet is not None
        assert log.retrieval_packet.get("packet_type") == "retrieval_packet"


@pytest.mark.asyncio
async def test_retrieve_no_semantic_match_returns_packet(db_ready: None, monkeypatch) -> None:
    app = create_app()

    def factory(*, session):
        embedding = EmbeddingService(adapter=DeterministicFakeEmbeddingAdapter(dimension=8), expected_dimension=8)
        vector = _StubVectorIndexService(hits=[])
        return SemanticIndexSearchService(session=session, embedding_service=embedding, vector_index_service=vector)

    import app.services.semantic_index_search_factory as factory_module

    monkeypatch.setattr(factory_module, "build_semantic_index_search_service", factory)

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/retrieve", json={"question": "anything"})
        assert res.status_code == 200
        body = res.json()
        assert body["answer_mode"] == "not_enough_evidence"
        assert "no_semantic_index_match" in body["warnings"]
        assert body["selected_indexes"] == []


@pytest.mark.asyncio
async def test_retrieve_empty_question_422(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/retrieve", json={"question": "   "})
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_retrieve_embedding_adapter_not_configured_returns_packet(db_ready: None, monkeypatch) -> None:
    app = create_app()

    def factory(*, session):
        svc = MagicMock(spec=SemanticIndexSearchService)
        svc.search.side_effect = EmbeddingAdapterNotConfiguredError("embedding_adapter_not_configured")
        return svc

    import app.services.semantic_index_search_factory as factory_module

    monkeypatch.setattr(factory_module, "build_semantic_index_search_service", factory)

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/retrieve", json={"question": "hello"})
        assert res.status_code == 200
        body = res.json()
        assert "embedding_adapter_not_configured" in body["warnings"]
        assert "no_semantic_index_match" not in body["warnings"]
