from __future__ import annotations

import os
import uuid

import pytest

from app.core import config as config_module
from app.services.vector_index_service import VectorIndexService


def test_qdrant_vector_index_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    if os.getenv("RUN_INTEGRATION_TESTS") != "1":
        pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable.")

    try:
        from qdrant_client import QdrantClient  # noqa: F401
    except ModuleNotFoundError:
        pytest.skip("qdrant-client not installed; skipping Qdrant integration test.")

    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        pytest.skip("QDRANT_URL not set; skipping Qdrant integration test.")

    # Provide minimal required settings for Settings() to load.
    monkeypatch.setenv("APP_NAME", "GraphClerk")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/db")
    monkeypatch.setenv("QDRANT_URL", qdrant_url)

    config_module.get_settings.cache_clear()
    settings = config_module.get_settings()

    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    svc = VectorIndexService(qdrant_client=client, expected_dimension=3)

    svc.ensure_semantic_indexes_collection()

    sid = uuid.uuid4()
    svc.upsert_semantic_index_vector(semantic_index_id=sid, vector=[0.0, 0.0, 1.0], payload={"meaning": "m"})
    hits = svc.search_semantic_indexes(query_vector=[0.0, 0.0, 1.0], limit=5)
    assert any(h.semantic_index_id == sid for h in hits)

