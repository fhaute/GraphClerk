from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from app.core import config as config_module
from app.db.base import Base


@pytest.fixture(scope="session")
def integration_enabled() -> None:
    if os.getenv("RUN_INTEGRATION_TESTS") != "1":
        pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable.")


@pytest.fixture()
def integration_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set required env vars and clear cached settings for tests."""

    monkeypatch.setenv("APP_NAME", "GraphClerk")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")

    artifacts_dir = tmp_path / "artifacts"
    monkeypatch.setenv("ARTIFACTS_DIR", str(artifacts_dir))

    # Clear cached settings/engine between tests when env changes.
    config_module.get_settings.cache_clear()


@pytest.fixture()
def db_ready(integration_enabled: None, integration_env: None) -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not set; skipping DB-backed Phase 2 tests.")

    engine = create_engine(database_url, pool_pre_ping=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

