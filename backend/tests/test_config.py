from __future__ import annotations

import os

import pytest

from app.core.config import Settings


def test_config_loads_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings should parse from environment variables."""

    monkeypatch.setenv("APP_NAME", "GraphClerk")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/db")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "optional")

    settings = Settings()  # do not use cached get_settings in tests

    assert settings.app_name == "GraphClerk"
    assert settings.app_env == "test"
    assert settings.log_level == "INFO"
    assert settings.database_url
    assert settings.qdrant_url == "http://localhost:6333"
    assert settings.qdrant_api_key == "optional"


def test_missing_required_config_fails_clearly(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing required env vars should raise a validation error."""

    for key in ["APP_NAME", "APP_ENV", "LOG_LEVEL", "DATABASE_URL", "QDRANT_URL", "QDRANT_API_KEY"]:
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(Exception) as excinfo:
        Settings()

    # Ensure we didn't silently fallback.
    msg = str(excinfo.value).lower()
    assert "app_name" in msg or "app env" in msg or "database" in msg or "qdrant" in msg

