"""Track D Slice D4 — purpose registry contracts (no adapters, no HTTP)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core import config as config_module
from app.core.config import Settings
from app.services.model_pipeline_contracts import (
    ModelOutputKind,
    ModelPipelineRole,
)
from app.services.model_pipeline_purpose_registry import (
    CODE_PURPOSE_POLICY_BLOCKED,
    ModelPipelinePurposeConfig,
    ModelPipelinePurposePolicyError,
    ModelPipelinePurposeRegistry,
    ModelPipelinePurposeResolutionError,
    build_default_model_pipeline_purpose_registry,
    resolve_model_pipeline_purpose,
)


def _minimal_env(monkeypatch: pytest.MonkeyPatch) -> Settings:
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
        "GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED",
        "GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL",
        "GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(key, raising=False)
    config_module.get_settings.cache_clear()
    return Settings()


def _with_enricher(
    registry: ModelPipelinePurposeRegistry,
    *,
    model: str = "llama3.1:8b",
    timeout_seconds: float | None = 45.0,
) -> ModelPipelinePurposeRegistry:
    ec = ModelPipelineRole.evidence_candidate_enricher
    cfg = registry.configs[ec].model_copy(
        update={
            "enabled": True,
            "adapter": "ollama",
            "model": model,
            "timeout_seconds": timeout_seconds,
        },
    )
    merged = dict(registry.configs)
    merged[ec] = cfg
    return ModelPipelinePurposeRegistry(configs=merged)


def test_default_registry_all_purposes_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _minimal_env(monkeypatch)
    reg = build_default_model_pipeline_purpose_registry(settings)
    for role, cfg in reg.configs.items():
        assert cfg.enabled is False, role
        assert cfg.adapter == "not_configured"


def test_resolve_disabled_enricher_returns_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _minimal_env(monkeypatch)
    reg = build_default_model_pipeline_purpose_registry(settings)
    ec = ModelPipelineRole.evidence_candidate_enricher
    res = resolve_model_pipeline_purpose(reg, ec, settings)
    assert res.disabled is True
    assert res.adapter is None
    assert res.model is None
    assert res.base_url is None


def test_resolve_enabled_enricher_success(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://localhost:11434")
    settings = Settings()
    reg = build_default_model_pipeline_purpose_registry(settings)
    reg = _with_enricher(reg)
    ec = ModelPipelineRole.evidence_candidate_enricher
    res = resolve_model_pipeline_purpose(reg, ec, settings)
    assert res.disabled is False
    assert res.role == ModelPipelineRole.evidence_candidate_enricher
    assert res.output_kind == ModelOutputKind.derived_metadata
    assert res.adapter == "ollama"
    assert res.model == "llama3.1:8b"
    assert res.timeout_seconds == 45.0
    assert res.base_url == "http://localhost:11434"


def test_resolve_uses_settings_timeout_when_purpose_timeout_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_TIMEOUT_SECONDS", "60")
    settings = Settings()
    base = build_default_model_pipeline_purpose_registry(settings)
    reg = _with_enricher(base, timeout_seconds=None)
    ec = ModelPipelineRole.evidence_candidate_enricher
    res = resolve_model_pipeline_purpose(reg, ec, settings)
    assert res.timeout_seconds == 60.0


def test_enabled_missing_model_fails_at_config_validation() -> None:
    with pytest.raises(ValidationError):
        ModelPipelinePurposeConfig(
            enabled=True,
            adapter="ollama",
            model=None,
            timeout_seconds=30.0,
            output_kind=ModelOutputKind.derived_metadata,
        )
    with pytest.raises(ValidationError):
        ModelPipelinePurposeConfig(
            enabled=True,
            adapter="ollama",
            model="   ",
            timeout_seconds=10.0,
            output_kind=ModelOutputKind.derived_metadata,
        )


def test_invalid_timeout_on_enabled_config() -> None:
    with pytest.raises(ValidationError):
        ModelPipelinePurposeConfig(
            enabled=True,
            adapter="ollama",
            model="m",
            timeout_seconds=400.0,
            output_kind=ModelOutputKind.derived_metadata,
        )


def test_enabling_routing_hint_fails_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _minimal_env(monkeypatch)
    reg = build_default_model_pipeline_purpose_registry(settings)
    merged = dict(reg.configs)
    rh = ModelPipelineRole.routing_hint_generator
    merged[rh] = merged[rh].model_copy(
        update={"enabled": True, "adapter": "ollama", "model": "m", "timeout_seconds": 30.0},
    )
    with pytest.raises(ModelPipelinePurposePolicyError) as ei:
        ModelPipelinePurposeRegistry(configs=merged)
    assert ei.value.code == CODE_PURPOSE_POLICY_BLOCKED


def test_enabling_artifact_classifier_fails_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _minimal_env(monkeypatch)
    reg = build_default_model_pipeline_purpose_registry(settings)
    ac = ModelPipelineRole.artifact_classifier
    merged = dict(reg.configs)
    merged[ac] = reg.configs[ac].model_copy(
        update={"enabled": True, "adapter": "ollama", "model": "m", "timeout_seconds": 20.0},
    )
    with pytest.raises(ModelPipelinePurposePolicyError):
        ModelPipelinePurposeRegistry(configs=merged)


def test_enricher_openai_adapter_blocked_by_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _minimal_env(monkeypatch)
    reg = build_default_model_pipeline_purpose_registry(settings)
    ec = ModelPipelineRole.evidence_candidate_enricher
    merged = dict(reg.configs)
    merged[ec] = reg.configs[ec].model_copy(
        update={
            "enabled": True,
            "adapter": "openai_compatible",
            "model": "gpt-4",
            "timeout_seconds": 30.0,
        },
    )
    with pytest.raises(ModelPipelinePurposePolicyError):
        ModelPipelinePurposeRegistry(configs=merged)


def test_enabling_extraction_helper_fails_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _minimal_env(monkeypatch)
    reg = build_default_model_pipeline_purpose_registry(settings)
    ex = ModelPipelineRole.extraction_helper
    merged = dict(reg.configs)
    merged[ex] = reg.configs[ex].model_copy(
        update={"enabled": True, "adapter": "ollama", "model": "m", "timeout_seconds": 20.0},
    )
    with pytest.raises(ModelPipelinePurposePolicyError):
        ModelPipelinePurposeRegistry(configs=merged)


def test_resolve_enabled_enricher_without_base_url_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _minimal_env(monkeypatch)
    reg = _with_enricher(build_default_model_pipeline_purpose_registry(settings))
    ec = ModelPipelineRole.evidence_candidate_enricher
    with pytest.raises(ModelPipelinePurposeResolutionError):
        resolve_model_pipeline_purpose(reg, ec, settings)


def test_purpose_registry_module_imports_clean() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "app" / "services" / "model_pipeline_purpose_registry.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = {
        "app.services.file_clerk_service",
        "app.services.text_ingestion_service",
        "app.services.multimodal_ingestion_service",
        "app.services.evidence_enrichment_service",
        "app.services.retrieval_packet_builder",
        "app.services.evidence_selection_service",
        "app.services.model_pipeline_registry",
        "app.services.model_pipeline_ollama_adapter",
    }
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
    assert not (imported & forbidden)


def test_resolution_json_has_no_answer_path(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _minimal_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://localhost:11434")
    settings = Settings()
    reg = _with_enricher(build_default_model_pipeline_purpose_registry(settings))
    ec = ModelPipelineRole.evidence_candidate_enricher
    res = resolve_model_pipeline_purpose(reg, ec, settings)
    blob = json.dumps(res.model_dump(mode="json"))
    assert "/answer" not in blob.lower()


def test_registry_does_not_import_adapter_registry() -> None:
    import app.services.model_pipeline_purpose_registry as m

    assert not hasattr(m, "build_model_pipeline_adapter")
