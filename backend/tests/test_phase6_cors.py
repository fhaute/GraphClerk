"""Phase 6 Slice J: CORS allowlist vs loopback defaults (no wildcard)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(autouse=True)
def _clear_cors_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GRAPHCLERK_CORS_ORIGINS", raising=False)
    monkeypatch.delenv("GRAPHCLE_CORS_ORIGINS", raising=False)


def test_default_allows_localhost_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GRAPHCLERK_CORS_ORIGINS", raising=False)
    monkeypatch.delenv("GRAPHCLE_CORS_ORIGINS", raising=False)
    client = TestClient(create_app())
    origin = "http://localhost:5173"
    r = client.get("/health", headers={"Origin": origin})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == origin


def test_default_allows_loopback_ip_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GRAPHCLERK_CORS_ORIGINS", raising=False)
    monkeypatch.delenv("GRAPHCLE_CORS_ORIGINS", raising=False)
    client = TestClient(create_app())
    origin = "http://127.0.0.1:3000"
    r = client.get("/health", headers={"Origin": origin})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == origin


def test_explicit_allowlist_sets_allow_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GRAPHCLERK_CORS_ORIGINS", "https://app.example")
    client = TestClient(create_app())
    origin = "https://app.example"
    r = client.get("/health", headers={"Origin": origin})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == origin


def test_explicit_allowlist_omits_acao_for_other_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GRAPHCLERK_CORS_ORIGINS", "https://app.example")
    client = TestClient(create_app())
    r = client.get("/health", headers={"Origin": "https://evil.example"})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") is None


def test_legacy_grapcle_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GRAPHCLERK_CORS_ORIGINS", raising=False)
    monkeypatch.setenv("GRAPHCLE_CORS_ORIGINS", "https://legacy.example")
    client = TestClient(create_app())
    origin = "https://legacy.example"
    r = client.get("/health", headers={"Origin": origin})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == origin


def test_graphclerk_env_precedence_over_legacy_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GRAPHCLERK_CORS_ORIGINS", "https://preferred.example")
    monkeypatch.setenv("GRAPHCLE_CORS_ORIGINS", "https://ignored.example")
    client = TestClient(create_app())
    assert (
        client.get("/health", headers={"Origin": "https://preferred.example"}).headers.get(
            "access-control-allow-origin"
        )
        == "https://preferred.example"
    )
    assert (
        client.get("/health", headers={"Origin": "https://ignored.example"}).headers.get(
            "access-control-allow-origin"
        )
        is None
    )