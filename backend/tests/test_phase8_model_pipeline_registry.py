"""Track D Slice D2 — static model pipeline adapter registry (no HTTP, no ingestion wiring)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core import config as config_module
from app.core.config import Settings
from app.services.model_pipeline_contracts import (
    DeterministicTestModelPipelineAdapter,
    ModelOutputKind,
    ModelPipelineResult,
    ModelPipelineRole,
    ModelPipelineStatus,
    NotConfiguredModelPipelineAdapter,
)
from app.services.model_pipeline_ollama_adapter import OllamaModelPipelineAdapter
from app.services.model_pipeline_registry import (
    MODEL_PIPELINE_ADAPTER_KEYS,
    MODEL_PIPELINE_IMPLEMENTED_ADAPTER_KEYS,
    MODEL_PIPELINE_RESERVED_ADAPTER_KEYS,
    ModelPipelineAdapterNotImplementedError,
    build_model_pipeline_adapter,
)


def _minimal_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "GraphClerk")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/db")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "optional")
    for key in (
        "GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER",
        "GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER",
        "GRAPHCLERK_MODEL_PIPELINE_ADAPTER",
        "GRAPHCLERK_MODEL_PIPELINE_BASE_URL",
        "GRAPHCLERK_MODEL_PIPELINE_MODEL",
        "GRAPHCLERK_MODEL_PIPELINE_TIMEOUT_SECONDS",
        "GRAPHCLERK_MODEL_PIPELINE_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    config_module.get_settings.cache_clear()


def test_default_settings_build_not_configured_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    settings = Settings()
    adapter = build_model_pipeline_adapter(settings)
    assert isinstance(adapter, NotConfiguredModelPipelineAdapter)


def test_unknown_adapter_fails_settings_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "quantum_llm")
    with pytest.raises(ValidationError):
        Settings()


def test_timeout_zero_fails_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_TIMEOUT_SECONDS", "0")
    with pytest.raises(ValidationError):
        Settings()


def test_timeout_above_bound_fails_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_TIMEOUT_SECONDS", "301")
    with pytest.raises(ValidationError):
        Settings()


def test_ollama_builds_when_base_url_and_model_set(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "ollama")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_MODEL", "llama3.1:8b")
    settings = Settings()
    adapter = build_model_pipeline_adapter(settings)
    assert isinstance(adapter, OllamaModelPipelineAdapter)


def test_ollama_missing_base_url_fails_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "ollama")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_MODEL", "m")
    settings = Settings()
    with pytest.raises(ModelPipelineAdapterNotImplementedError) as ei:
        build_model_pipeline_adapter(settings)
    assert ei.value.code == "model_pipeline_ollama_misconfigured"


def test_ollama_missing_model_fails_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "ollama")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://localhost:11434")
    settings = Settings()
    with pytest.raises(ModelPipelineAdapterNotImplementedError) as ei:
        build_model_pipeline_adapter(settings)
    assert ei.value.code == "model_pipeline_ollama_misconfigured"


def test_ollama_whitespace_only_base_url_fails_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "ollama")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "   ")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_MODEL", "m")
    settings = Settings()
    with pytest.raises(ModelPipelineAdapterNotImplementedError) as ei:
        build_model_pipeline_adapter(settings)
    assert ei.value.code == "model_pipeline_ollama_misconfigured"


def test_openai_compatible_fails_at_registry_build(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "openai_compatible")
    settings = Settings()
    with pytest.raises(ModelPipelineAdapterNotImplementedError) as ei:
        build_model_pipeline_adapter(settings)
    assert ei.value.code == "model_pipeline_adapter_not_implemented"


def test_deterministic_test_without_factory_fails_loudly(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("RUN_INTEGRATION_TESTS", "1")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "deterministic_test")
    settings = Settings()
    with pytest.raises(ModelPipelineAdapterNotImplementedError) as ei:
        build_model_pipeline_adapter(settings)
    assert ei.value.code == "model_pipeline_deterministic_test_requires_factory"


def test_deterministic_test_requires_integration_gate_in_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.delenv("RUN_INTEGRATION_TESTS", raising=False)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "deterministic_test")
    with pytest.raises(ValidationError) as ei:
        Settings()
    assert "run_integration_tests" in str(ei.value).lower()


def test_deterministic_test_in_prod_fails_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("RUN_INTEGRATION_TESTS", "1")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "deterministic_test")
    with pytest.raises(ValidationError) as ei:
        Settings()
    assert "prod" in str(ei.value).lower()


def test_deterministic_test_with_factory_builds_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("RUN_INTEGRATION_TESTS", "1")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "deterministic_test")
    settings = Settings()
    result = ModelPipelineResult(
        role=ModelPipelineRole.extraction_helper,
        output_kind=ModelOutputKind.candidate_metadata,
        status=ModelPipelineStatus.success,
        payload={},
        warnings=[],
        provenance={"source": "deterministic_test"},
    )
    adapter = build_model_pipeline_adapter(
        settings,
        deterministic_test_factory=lambda: DeterministicTestModelPipelineAdapter(result=result),
    )
    assert isinstance(adapter, DeterministicTestModelPipelineAdapter)


def test_reserved_keys_do_not_silently_fallback_to_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "openai_compatible")
    settings = Settings()
    with pytest.raises(ModelPipelineAdapterNotImplementedError):
        build_model_pipeline_adapter(settings)

    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "ollama")
    monkeypatch.delenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", raising=False)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_MODEL", "m")
    settings = Settings()
    with pytest.raises(ModelPipelineAdapterNotImplementedError):
        build_model_pipeline_adapter(settings)


def test_registry_module_imports_avoid_ingestion_and_file_clerk() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "app" / "services" / "model_pipeline_registry.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = {
        "app.services.file_clerk_service",
        "app.services.text_ingestion_service",
        "app.services.multimodal_ingestion_service",
        "app.services.evidence_enrichment_service",
        "app.services.retrieval_packet_builder",
        "app.services.evidence_selection_service",
    }
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
    assert not (imported & forbidden)


def test_adapter_key_constants_align_with_settings_literals() -> None:
    assert MODEL_PIPELINE_IMPLEMENTED_ADAPTER_KEYS == ("not_configured", "ollama")
    assert MODEL_PIPELINE_ADAPTER_KEYS == (
        "not_configured",
        "deterministic_test",
        "ollama",
        "openai_compatible",
    )
    assert set(MODEL_PIPELINE_RESERVED_ADAPTER_KEYS) == {
        "deterministic_test",
        "openai_compatible",
    }


def test_build_performs_no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Registry has no HTTP clients; smoke-check default path."""
    _minimal_env(monkeypatch)
    settings = Settings()
    adapter = build_model_pipeline_adapter(settings)
    assert adapter is not None
