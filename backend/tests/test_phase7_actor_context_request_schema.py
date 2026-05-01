"""Phase 7 Slice 7G — optional ActorContext on POST /retrieve (request-only; no retrieval effect)."""

from __future__ import annotations

import uuid

import httpx
import pytest
from httpx import ASGITransport
from pydantic import ValidationError

from app.main import create_app
from app.models.enums import SemanticIndexVectorStatus
from app.schemas.retrieval import MAX_ACTOR_STRING_FIELD_LEN, ActorContext
from app.schemas.retrieval_packet import RetrievalPacket, RetrieveRequest
from app.services.embedding_adapter import DeterministicFakeEmbeddingAdapter
from app.services.embedding_service import EmbeddingService
from app.services.semantic_index_search_service import SemanticIndexSearchService
from app.services.vector_index_service import SearchHit


class _StubVectorIndexService:
    def __init__(self, hits: list[SearchHit]) -> None:
        self._hits = hits

    def search_semantic_indexes(self, *, query_vector: list[float], limit: int = 5) -> list[SearchHit]:
        _ = query_vector
        _ = limit
        return self._hits


def test_retrieve_request_without_actor_context() -> None:
    r = RetrieveRequest.model_validate({"question": "hello"})
    assert r.actor_context is None
    assert r.question == "hello"


def test_retrieve_request_minimal_actor_context() -> None:
    r = RetrieveRequest.model_validate({"question": "q", "actor_context": {}})
    assert r.actor_context is not None
    assert r.actor_context.actor_id is None


def test_retrieve_request_full_actor_context() -> None:
    payload = {
        "question": "q",
        "actor_context": {
            "actor_id": "opaque-1",
            "actor_type": "human",
            "role": "developer",
            "expertise_level": "senior",
            "preferred_language": "en",
            "purpose": "debugging",
            "metadata": {"tenant": "acme"},
        },
    }
    r = RetrieveRequest.model_validate(payload)
    assert r.actor_context is not None
    assert r.actor_context.actor_id == "opaque-1"
    assert r.actor_context.metadata == {"tenant": "acme"}


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "   ",
        "\t\n",
    ],
)
def test_actor_context_rejects_empty_or_whitespace_strings(bad: str) -> None:
    with pytest.raises(ValidationError):
        ActorContext.model_validate({"actor_id": bad})


def test_actor_context_rejects_overlong_strings() -> None:
    too_long = "x" * (MAX_ACTOR_STRING_FIELD_LEN + 1)
    with pytest.raises(ValidationError):
        ActorContext.model_validate({"actor_id": too_long})


def test_actor_context_metadata_must_be_object() -> None:
    with pytest.raises(ValidationError):
        ActorContext.model_validate({"metadata": []})


def test_actor_context_rejects_unknown_nested_fields() -> None:
    with pytest.raises(ValidationError):
        ActorContext.model_validate({"extra_field": "nope"})


def test_retrieval_packet_has_no_actor_context_field() -> None:
    assert "actor_context" not in RetrievalPacket.model_fields


@pytest.mark.asyncio
async def test_retrieve_api_with_and_without_actor_context(db_ready: None, monkeypatch) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        n1 = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "N1"})).json()["id"]
        n2 = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "N2"})).json()["id"]
        s1 = (await client.post("/semantic-indexes", json={"meaning": "m1", "entry_node_ids": [n1]})).json()["id"]
        s2 = (await client.post("/semantic-indexes", json={"meaning": "m2", "entry_node_ids": [n2]})).json()["id"]

    from app.db.session import get_sessionmaker
    from app.models.semantic_index import SemanticIndex

    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
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

    question = "same question for language_context parity"
    base_body = {"question": question}
    with_body = {
        "question": question,
        "actor_context": {
            "actor_id": "actor-99",
            "metadata": {"scope": "test"},
        },
    }

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res_base = await client.post("/retrieve", json=base_body)
        res_actor = await client.post("/retrieve", json=with_body)
    assert res_base.status_code == 200
    assert res_actor.status_code == 200

    body_base = res_base.json()
    body_actor = res_actor.json()

    assert "actor_context" not in body_base
    assert "actor_context" not in body_actor

    assert body_base["language_context"] == body_actor["language_context"]
    assert body_base["selected_indexes"] == body_actor["selected_indexes"]
    assert body_base["warnings"] == body_actor["warnings"]
