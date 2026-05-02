"""Track D D7b — read-only GET /model-pipeline/config."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core import config as config_module
from app.core.config import Settings
from app.main import create_app
from app.schemas.model_pipeline_config import build_model_pipeline_config_response
from app.services.model_pipeline_purpose_registry import (
    CODE_PURPOSE_RESOLUTION_FAILED,
    ModelPipelinePurposeResolutionError,
)


def _minimal_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "GraphClerk")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/db")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    for key in (
        "GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER",
        "GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER",
        "GRAPHCLERK_MODEL_PIPELINE_ADAPTER",
        "GRAPHCLERK_MODEL_PIPELINE_BASE_URL",
        "GRAPHCLERK_MODEL_PIPELINE_MODEL",
        "GRAPHCLERK_MODEL_PIPELINE_TIMEOUT_SECONDS",
        "GRAPHCLERK_MODEL_PIPELINE_API_KEY",
        "GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED",
        "GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL",
        "GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(key, raising=False)
    config_module.get_settings.cache_clear()


def _client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    _minimal_env(monkeypatch)
    return TestClient(create_app())


def test_default_config_not_configured_enricher_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch)
    r = client.get("/model-pipeline/config")
    assert r.status_code == 200
    data = r.json()
    assert data["adapter"] == "not_configured"
    ec = data["purpose_registry"]["evidence_candidate_enricher"]
    assert ec["enabled"] is False
    assert ec["status"] == "disabled"
    assert ec["allowed"] is True
    rh = data["purpose_registry"]["routing_hint_generator"]
    assert rh["enabled"] is False
    assert rh["status"] == "policy_blocked"
    assert rh["allowed"] is False


def test_response_has_no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_API_KEY", "unit-test-secret-key-do-not-leak")
    config_module.get_settings.cache_clear()
    client = TestClient(create_app())
    r = client.get("/model-pipeline/config")
    assert r.status_code == 200
    blob = json.dumps(r.json())
    assert "unit-test-secret-key-do-not-leak" not in blob
    assert "api_key" not in blob.lower()


def test_response_hides_raw_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://hidden-host.example:11434")
    config_module.get_settings.cache_clear()
    client = TestClient(create_app())
    r = client.get("/model-pipeline/config")
    assert r.status_code == 200
    data = r.json()
    assert data["base_url_configured"] is True
    blob = json.dumps(data)
    assert "hidden-host.example" not in blob


def test_enricher_configured_with_model_and_output_kind(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED", "true")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "ollama")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL", "llama3.1:8b")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_TIMEOUT_SECONDS", "42")
    config_module.get_settings.cache_clear()
    client = TestClient(create_app())
    r = client.get("/model-pipeline/config")
    assert r.status_code == 200
    data = r.json()
    assert data["adapter"] == "ollama"
    assert data["timeout_seconds"] == 42.0
    ec = data["purpose_registry"]["evidence_candidate_enricher"]
    assert ec["enabled"] is True
    assert ec["status"] == "configured"
    assert ec["model"] == "llama3.1:8b"
    assert ec["output_kind"] == "derived_metadata"
    assert ec["adapter"] == "ollama"


def test_routing_hint_never_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED", "true")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "ollama")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL", "llama3.1:8b")
    config_module.get_settings.cache_clear()
    client = TestClient(create_app())
    r = client.get("/model-pipeline/config")
    rh = r.json()["purpose_registry"]["routing_hint_generator"]
    assert rh["enabled"] is False
    assert rh["status"] == "policy_blocked"


def test_post_returns_405(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch)
    r = client.post("/model-pipeline/config")
    assert r.status_code == 405


def test_put_returns_405(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch)
    r = client.put("/model-pipeline/config")
    assert r.status_code == 405


def test_config_endpoint_does_not_call_resolve_when_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sanity: endpoint uses builder only — patch proves no accidental Ollama import path."""

    _minimal_env(monkeypatch)

    def boom(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("resolve_model_pipeline_purpose should not run when enricher disabled")

    with patch(
        "app.schemas.model_pipeline_config.resolve_model_pipeline_purpose",
        side_effect=boom,
    ):
        client = TestClient(create_app())
        r = client.get("/model-pipeline/config")
    assert r.status_code == 200


def test_misconfigured_when_resolution_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED", "true")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "ollama")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL", "llama3.1:8b")
    config_module.get_settings.cache_clear()
    settings = Settings()

    with patch(
        "app.schemas.model_pipeline_config.resolve_model_pipeline_purpose",
        side_effect=ModelPipelinePurposeResolutionError(
            CODE_PURPOSE_RESOLUTION_FAILED,
            "simulated resolution failure",
        ),
    ):
        body = build_model_pipeline_config_response(settings)

    ec = body.purpose_registry.evidence_candidate_enricher
    assert ec.enabled is True
    assert ec.status == "misconfigured"
    assert body.warnings and "simulated resolution failure" in body.warnings[0]


def test_schema_imports_clean() -> None:
    root = Path(__file__).resolve().parents[1]
    forbidden = {
        "app.services.file_clerk_service",
        "app.services.text_ingestion_service",
        "app.services.multimodal_ingestion_service",
        "app.services.evidence_enrichment_service",
        "app.services.retrieval_packet_builder",
        "app.services.evidence_selection_service",
    }
    for rel in ("app/api/routes/model_pipeline.py", "app/schemas/model_pipeline_config.py"):
        path = root / rel
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
        assert not (imported & forbidden), rel


def test_openapi_includes_model_pipeline_config_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch)
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert "/model-pipeline/config" in spec.get("paths", {})
