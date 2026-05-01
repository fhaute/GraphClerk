"""Track B Slice B1 — manual vector indexing path and explicit vector_status transitions."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import httpx
import pytest
from httpx import ASGITransport

from app.core import config as config_module
from app.db.session import get_sessionmaker
from app.main import create_app
from app.models.enums import GraphNodeType, SemanticIndexVectorStatus
from app.models.semantic_index import SemanticIndex
from app.services.embedding_adapter import DeterministicFakeEmbeddingAdapter
from app.services.embedding_service import EmbeddingService
from app.services.errors import EmbeddingAdapterNotConfiguredError, VectorIndexOperationError
from app.services.semantic_index_search_service import SemanticIndexSearchService
from app.services.semantic_index_service import SemanticIndexVectorIndexingService
from app.services.vector_index_service import SearchHit, VectorIndexService


class _RecordingVectorIndexService(VectorIndexService):
    """VectorIndexService that records upserts (collection name unchanged for unit tests)."""

    def __init__(self, *, fail_upsert: bool = False) -> None:
        self._fail_upsert = fail_upsert
        self.ensure_calls = 0
        self.upserts: list[tuple[uuid.UUID, list[float], dict | None]] = []

        class _Client:
            def get_collection(self, _name: str) -> object:
                return object()

            def create_collection(self, *_a, **_k) -> None:
                return None

            def upsert(self, *_a, **_k) -> None:
                return None

            def query_points(self, *_a, **_k) -> object:
                return type("_R", (), {"points": []})()

        super().__init__(qdrant_client=_Client(), expected_dimension=8)

    def ensure_semantic_indexes_collection(self) -> None:
        self.ensure_calls += 1

    def upsert_semantic_index_vector(
        self,
        *,
        semantic_index_id: uuid.UUID,
        vector: list[float],
        payload: dict | None = None,
    ) -> None:
        if self._fail_upsert:
            raise VectorIndexOperationError("upsert_failed_stub")
        self.upserts.append((semantic_index_id, vector, payload))


def _indexing_service(
    session, vector: _RecordingVectorIndexService
) -> SemanticIndexVectorIndexingService:
    emb = EmbeddingService(
        adapter=DeterministicFakeEmbeddingAdapter(dimension=8),
        expected_dimension=8,
    )
    return SemanticIndexVectorIndexingService(
        session=session,
        embedding_service=emb,
        vector_index_service=vector,
    )


def test_indexing_fails_when_embedding_text_empty(db_ready: None) -> None:
    SessionMaker = get_sessionmaker()
    vector = _RecordingVectorIndexService()
    with SessionMaker() as session:
        from app.models.graph_node import GraphNode

        node = GraphNode(node_type=GraphNodeType.concept, label="n")
        session.add(node)
        session.flush()
        idx = SemanticIndex(
            meaning="m",
            summary=None,
            embedding_text=None,
            entry_node_ids=None,
            vector_status=SemanticIndexVectorStatus.pending,
            metadata_json=None,
        )
        session.add(idx)
        session.flush()
        from app.models.semantic_index_entry_node import SemanticIndexEntryNode

        session.add(SemanticIndexEntryNode(semantic_index_id=idx.id, graph_node_id=node.id))

        svc = _indexing_service(session, vector)
        out = svc.index_semantic_index(semantic_index_id=idx.id, force=False)
        session.commit()

        assert out.status == "failed"
        assert out.detail == "embedding_text_empty"
        refreshed = session.get(SemanticIndex, idx.id)
        assert refreshed is not None
        assert refreshed.vector_status == SemanticIndexVectorStatus.failed
        meta = refreshed.metadata_json or {}
        assert (
            meta.get("graphclerk_vector_indexing", {}).get("last_error_code")
            == "embedding_text_empty"
        )
        assert vector.upserts == []


def test_indexing_marks_indexed_on_success(db_ready: None) -> None:
    SessionMaker = get_sessionmaker()
    vector = _RecordingVectorIndexService()
    with SessionMaker() as session:
        from app.models.graph_node import GraphNode

        node = GraphNode(node_type=GraphNodeType.concept, label="n2")
        session.add(node)
        session.flush()
        idx = SemanticIndex(
            meaning="meaning x",
            summary=None,
            embedding_text="non-empty embedding source",
            entry_node_ids=None,
            vector_status=SemanticIndexVectorStatus.pending,
            metadata_json=None,
        )
        session.add(idx)
        session.flush()
        from app.models.semantic_index_entry_node import SemanticIndexEntryNode

        session.add(SemanticIndexEntryNode(semantic_index_id=idx.id, graph_node_id=node.id))

        svc = _indexing_service(session, vector)
        out = svc.index_semantic_index(semantic_index_id=idx.id, force=False)
        session.commit()

        assert out.status == "indexed"
        assert vector.ensure_calls == 1
        assert len(vector.upserts) == 1
        assert vector.upserts[0][0] == idx.id
        refreshed = session.get(SemanticIndex, idx.id)
        assert refreshed is not None
        assert refreshed.vector_status == SemanticIndexVectorStatus.indexed


def test_indexing_marks_failed_on_vector_error(db_ready: None) -> None:
    SessionMaker = get_sessionmaker()
    vector = _RecordingVectorIndexService(fail_upsert=True)
    with SessionMaker() as session:
        from app.models.graph_node import GraphNode

        node = GraphNode(node_type=GraphNodeType.concept, label="n3")
        session.add(node)
        session.flush()
        idx = SemanticIndex(
            meaning="m",
            summary=None,
            embedding_text="hello",
            entry_node_ids=None,
            vector_status=SemanticIndexVectorStatus.pending,
            metadata_json=None,
        )
        session.add(idx)
        session.flush()
        from app.models.semantic_index_entry_node import SemanticIndexEntryNode

        session.add(SemanticIndexEntryNode(semantic_index_id=idx.id, graph_node_id=node.id))

        svc = _indexing_service(session, vector)
        out = svc.index_semantic_index(semantic_index_id=idx.id, force=False)
        session.commit()

        assert out.status == "failed"
        assert out.detail == "VectorIndexOperationError"
        refreshed = session.get(SemanticIndex, idx.id)
        assert refreshed is not None
        assert refreshed.vector_status == SemanticIndexVectorStatus.failed


def test_indexing_skips_already_indexed_without_force(db_ready: None) -> None:
    SessionMaker = get_sessionmaker()
    vector = _RecordingVectorIndexService()
    with SessionMaker() as session:
        from app.models.graph_node import GraphNode

        node = GraphNode(node_type=GraphNodeType.concept, label="n4")
        session.add(node)
        session.flush()
        idx = SemanticIndex(
            meaning="m",
            summary=None,
            embedding_text="x",
            entry_node_ids=None,
            vector_status=SemanticIndexVectorStatus.indexed,
            metadata_json=None,
        )
        session.add(idx)
        session.flush()
        from app.models.semantic_index_entry_node import SemanticIndexEntryNode

        session.add(SemanticIndexEntryNode(semantic_index_id=idx.id, graph_node_id=node.id))

        svc = _indexing_service(session, vector)
        out = svc.index_semantic_index(semantic_index_id=idx.id, force=False)
        session.commit()

        assert out.status == "skipped"
        assert vector.upserts == []


class _StubVectorIndexServiceSearchOnly:
    def __init__(self, hits: list[SearchHit]) -> None:
        self._hits = hits

    def search_semantic_indexes(
        self, *, query_vector: list[float], limit: int = 5
    ) -> list[SearchHit]:
        _ = query_vector
        _ = limit
        return self._hits


@pytest.mark.asyncio
async def test_retrieve_returns_non_empty_evidence_after_indexing_service(
    db_ready: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Uses real DB + indexing service + stubbed semantic search (no Qdrant in retrieve path)."""

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        ing = await client.post(
            "/artifacts",
            json={
                "filename": "b1.txt",
                "artifact_type": "text",
                "text": "Track B slice B1 evidence line.\n\nSecond paragraph.\n",
            },
        )
        assert ing.status_code == 200
        artifact_id = ing.json()["artifact_id"]
        evs = await client.get(f"/artifacts/{artifact_id}/evidence")
        evidence_unit_id = evs.json()["items"][0]["id"]

        node_resp = await client.post(
            "/graph/nodes", json={"node_type": "concept", "label": "B1Node"}
        )
        node_id = node_resp.json()["id"]
        link = await client.post(
            f"/graph/nodes/{node_id}/evidence",
            json={
                "evidence_unit_id": evidence_unit_id,
                "support_type": "supports",
                "confidence": 0.9,
            },
        )
        assert link.status_code == 200

        si_body = {
            "meaning": "track_b_b1",
            "embedding_text": "track b slice b1 semantic index embedding text",
            "entry_node_ids": [node_id],
        }
        si_res = await client.post("/semantic-indexes", json=si_body)
        assert si_res.status_code == 200
        sid = si_res.json()["id"]
        assert si_res.json()["vector_status"] == "pending"

    SessionMaker = get_sessionmaker()
    vector = _RecordingVectorIndexService()
    with SessionMaker() as session:
        svc = _indexing_service(session, vector)
        out = svc.index_semantic_index(semantic_index_id=uuid.UUID(sid), force=False)
        session.commit()
        assert out.status == "indexed"

    hits = [
        SearchHit(
            semantic_index_id=uuid.UUID(sid),
            score=0.95,
            payload={"semantic_index_id": sid},
        ),
    ]

    def factory(*, session):
        embedding = EmbeddingService(
            adapter=DeterministicFakeEmbeddingAdapter(dimension=8),
            expected_dimension=8,
        )
        search_vec = _StubVectorIndexServiceSearchOnly(hits=hits)
        return SemanticIndexSearchService(
            session=session,
            embedding_service=embedding,
            vector_index_service=search_vec,
        )

    import app.services.semantic_index_search_factory as factory_module

    monkeypatch.setattr(factory_module, "build_semantic_index_search_service", factory)

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/retrieve", json={"question": "track b slice b1 semantic probe"})
        assert res.status_code == 200
        body = res.json()
        units = body["evidence_units"]
        match = next((u for u in units if u["evidence_unit_id"] == evidence_unit_id), None)
        assert match is not None, f"expected evidence in packet, got {units!r}"
        assert match["artifact_id"] == artifact_id
        lc = body.get("language_context")
        assert lc is not None
        assert lc.get("source") == "selected_evidence_metadata"


def _factory_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "GraphClerk")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/db")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "optional")


def test_semantic_index_search_factory_not_configured_embedding_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default app wiring keeps semantic search on NotConfigured (Track B Slice B2)."""

    from app.services.semantic_index_search_factory import build_semantic_index_search_service

    _factory_test_env(monkeypatch)
    monkeypatch.delenv("RUN_INTEGRATION_TESTS", raising=False)
    monkeypatch.delenv("GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER", raising=False)
    config_module.get_settings.cache_clear()

    svc = build_semantic_index_search_service(session=MagicMock())
    with pytest.raises(EmbeddingAdapterNotConfiguredError):
        svc._embedding.embed_text("probe")  # type: ignore[attr-defined]


def test_semantic_index_search_factory_uses_deterministic_when_guards_allow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services.semantic_index_search_factory import build_semantic_index_search_service

    _factory_test_env(monkeypatch)
    monkeypatch.setenv("RUN_INTEGRATION_TESTS", "1")
    monkeypatch.setenv("GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER", "deterministic_fake")
    config_module.get_settings.cache_clear()

    svc = build_semantic_index_search_service(session=MagicMock())
    vec = svc._embedding.embed_text("hello world")  # type: ignore[attr-defined]
    assert isinstance(vec, list)
    assert len(vec) == 8
