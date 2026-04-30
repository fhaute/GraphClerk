from __future__ import annotations

import os

import pytest

from app.services.qdrant_service import QdrantService


def test_qdrant_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify we can reach Qdrant with a real call when configured.

    This is an integration test. It is skipped unless QDRANT_URL is set in the
    environment for the test run.
    """

    if os.getenv("RUN_INTEGRATION_TESTS") != "1":
        pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable.")

    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        pytest.skip("QDRANT_URL not set; skipping Qdrant connectivity test.")

    try:
        import qdrant_client  # noqa: F401
    except ModuleNotFoundError:
        pytest.skip("qdrant-client not installed in this environment.")

    # Provide minimal required settings for Settings() to load.
    monkeypatch.setenv("APP_NAME", "GraphClerk")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/db")
    monkeypatch.setenv("QDRANT_URL", qdrant_url)

    svc = QdrantService()
    availability = svc.check_available()

    assert availability.ok, availability.detail

