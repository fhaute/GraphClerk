"""Track B Slice B5 — gated full-stack indexed retrieval (no FileClerk / factory monkeypatch).

Requires real Postgres + Qdrant and explicit env (see ``docs/governance/TESTING_RULES.md``).
"""

from __future__ import annotations

import os
import uuid

import httpx
import pytest
from httpx import ASGITransport

from app.core import config as config_module
from app.db import session as session_module
from app.db.session import get_sessionmaker
from app.main import create_app
from app.models.enums import SemanticIndexVectorStatus
from app.models.semantic_index import SemanticIndex
from app.services.embedding_adapter import DeterministicFakeEmbeddingAdapter
from app.services.embedding_service import EmbeddingService
from app.services.semantic_index_service import SemanticIndexVectorIndexingService
from app.services.vector_index_service import VectorIndexService

# Same string for ``SemanticIndex.embedding_text`` and ``POST /retrieve`` ``question`` so
# DeterministicFakeEmbeddingAdapter yields identical query/index vectors (Qdrant hit).
B5_SEMANTIC_ANCHOR = "track_b_b5_full_stack_semantic_anchor_exact_match_string"
B5_ARTIFACT_TEXT = (
    "Track B slice B5 artifact body. Evidence trace sentence for graph link retrieval.\n\n"
    "Second line.\n"
)


def _b5_skip_unless_env() -> None:
    if os.getenv("RUN_INTEGRATION_TESTS") != "1":
        pytest.skip("RUN_INTEGRATION_TESTS=1 required for Track B B5 full-stack test")
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for Track B B5 full-stack test")
    if not os.getenv("QDRANT_URL"):
        pytest.skip("QDRANT_URL required for Track B B5 full-stack test")
    if os.getenv("GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER") != "deterministic_fake":
        pytest.skip(
            "GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER=deterministic_fake required "
            "for Track B B5 full-stack test"
        )
    if os.getenv("APP_ENV", "").lower() == "prod":
        pytest.skip("APP_ENV=prod is not allowed for Track B B5 full-stack test")


@pytest.fixture()
def track_b_b5_env_gate(integration_enabled: None, integration_env: None) -> None:
    """Fail fast on missing env **before** ``db_ready`` runs (avoids useless DB resets)."""

    _b5_skip_unless_env()


@pytest.fixture()
def track_b_b5_db(track_b_b5_env_gate: None, db_ready: None) -> None:
    """Fresh DB; clears settings/engine cache for ``create_app``."""

    config_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    yield
    config_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()


@pytest.mark.asyncio
async def test_retrieve_non_empty_evidence_full_stack_no_monkeypatch(
    track_b_b5_db: None,
) -> None:
    """HTTP ingest → vector index → ``POST /retrieve`` via real FileClerk + factory (B5)."""

    try:
        from qdrant_client import QdrantClient
    except ModuleNotFoundError:
        pytest.skip("qdrant-client not installed")

    settings = config_module.get_settings()
    try:
        QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key).get_collections()
    except Exception as exc:
        pytest.skip(f"Qdrant unreachable at {settings.qdrant_url!r}: {exc}")

    app = create_app()
    transport = ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        ing = await client.post(
            "/artifacts",
            json={
                "filename": "b5.txt",
                "artifact_type": "text",
                "text": B5_ARTIFACT_TEXT,
            },
        )
        assert ing.status_code == 200, ing.text
        artifact_id = ing.json()["artifact_id"]

        ev_res = await client.get(f"/artifacts/{artifact_id}/evidence")
        assert ev_res.status_code == 200
        items = ev_res.json()["items"]
        assert len(items) >= 1
        evidence_unit_id = items[0]["id"]

        node_resp = await client.post(
            "/graph/nodes", json={"node_type": "concept", "label": "B5FullStackNode"}
        )
        assert node_resp.status_code == 200
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

        si_res = await client.post(
            "/semantic-indexes",
            json={
                "meaning": "b5_full_stack",
                "embedding_text": B5_SEMANTIC_ANCHOR,
                "entry_node_ids": [node_id],
            },
        )
        assert si_res.status_code == 200, si_res.text
        sid = si_res.json()["id"]
        assert si_res.json()["vector_status"] == "pending"

    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        settings = config_module.get_settings()
        qclient = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        vector = VectorIndexService(qdrant_client=qclient, expected_dimension=8)
        embedding = EmbeddingService(
            adapter=DeterministicFakeEmbeddingAdapter(dimension=8),
            expected_dimension=8,
        )
        indexer = SemanticIndexVectorIndexingService(
            session=session,
            embedding_service=embedding,
            vector_index_service=vector,
        )
        outcome = indexer.index_semantic_index(semantic_index_id=uuid.UUID(sid), force=False)
        session.commit()
        assert outcome.status == "indexed", f"indexing failed: {outcome}"

        row = session.get(SemanticIndex, uuid.UUID(sid))
        assert row is not None
        assert row.vector_status == SemanticIndexVectorStatus.indexed

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/retrieve", json={"question": B5_SEMANTIC_ANCHOR})
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["packet_type"] == "retrieval_packet"
        units = body["evidence_units"]
        assert len(units) >= 1, f"expected non-empty evidence_units, got {body!r}"
        match = next((u for u in units if u.get("evidence_unit_id") == evidence_unit_id), None)
        assert match is not None, f"missing evidence unit {evidence_unit_id} in {units!r}"
        assert match.get("artifact_id") == artifact_id
        assert isinstance(body.get("warnings"), list)
        lc = body.get("language_context")
        assert lc is not None
        assert lc.get("source") == "selected_evidence_metadata"
        # Default JSON artifact route does not inject language enrichment on EUs.
        assert lc.get("primary_evidence_language") is None
