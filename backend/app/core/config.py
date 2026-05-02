from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SemanticSearchEmbeddingAdapter = Literal["not_configured", "deterministic_fake"]
LanguageDetectionAdapterName = Literal["not_configured", "lingua"]
ModelPipelineAdapterName = Literal[
    "not_configured",
    "deterministic_test",
    "ollama",
    "openai_compatible",
]


class Settings(BaseSettings):
    """Typed application settings loaded from environment.

    Phase 1 settings are infrastructure-only. They must fail clearly when required
    values are missing.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    app_name: str = Field(alias="APP_NAME")
    app_env: Literal["local", "dev", "test", "prod"] = Field(alias="APP_ENV")
    log_level: str = Field(alias="LOG_LEVEL")

    database_url: str = Field(alias="DATABASE_URL")

    qdrant_url: str = Field(alias="QDRANT_URL")
    qdrant_api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")

    artifacts_dir: str = Field(default="./data/artifacts", alias="ARTIFACTS_DIR")

    semantic_search_embedding_adapter: SemanticSearchEmbeddingAdapter = Field(
        default="not_configured",
        alias="GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER",
    )

    language_detection_adapter: LanguageDetectionAdapterName = Field(
        default="not_configured",
        alias="GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER",
    )

    model_pipeline_adapter: ModelPipelineAdapterName = Field(
        default="not_configured",
        alias="GRAPHCLERK_MODEL_PIPELINE_ADAPTER",
    )
    model_pipeline_base_url: str | None = Field(
        default=None,
        alias="GRAPHCLERK_MODEL_PIPELINE_BASE_URL",
    )
    model_pipeline_model: str | None = Field(default=None, alias="GRAPHCLERK_MODEL_PIPELINE_MODEL")
    model_pipeline_timeout_seconds: float = Field(
        default=30.0,
        alias="GRAPHCLERK_MODEL_PIPELINE_TIMEOUT_SECONDS",
        gt=0.0,
        le=300.0,
    )
    model_pipeline_api_key: str | None = Field(
        default=None,
        alias="GRAPHCLERK_MODEL_PIPELINE_API_KEY",
    )

    model_pipeline_evidence_enricher_enabled: bool = Field(
        default=False,
        alias="GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED",
    )
    model_pipeline_evidence_enricher_model: str | None = Field(
        default=None,
        alias="GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL",
    )
    model_pipeline_evidence_enricher_timeout_seconds: float | None = Field(
        default=None,
        alias="GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_TIMEOUT_SECONDS",
    )

    @model_validator(mode="after")
    def _validate_semantic_search_embedding_adapter(self) -> Settings:
        """``deterministic_fake`` is integration-test-only and must never load in production."""

        if self.semantic_search_embedding_adapter != "deterministic_fake":
            return self
        if self.app_env == "prod":
            msg = (
                "GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER=deterministic_fake is not allowed "
                "when APP_ENV=prod"
            )
            raise ValueError(msg)
        if os.environ.get("RUN_INTEGRATION_TESTS") != "1":
            msg = (
                "GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER=deterministic_fake requires "
                "RUN_INTEGRATION_TESTS=1 (integration-test-only; not production semantics)"
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _validate_model_pipeline_adapter(self) -> Settings:
        """``deterministic_test`` is registry-test-only; never valid in production."""

        if self.model_pipeline_adapter != "deterministic_test":
            return self
        if self.app_env == "prod":
            msg = (
                "GRAPHCLERK_MODEL_PIPELINE_ADAPTER=deterministic_test is not allowed "
                "when APP_ENV=prod"
            )
            raise ValueError(msg)
        if os.environ.get("RUN_INTEGRATION_TESTS") != "1":
            msg = (
                "GRAPHCLERK_MODEL_PIPELINE_ADAPTER=deterministic_test requires "
                "RUN_INTEGRATION_TESTS=1 "
                "(test-only; inject DeterministicTest adapter via "
                "build_model_pipeline_adapter factory)"
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _validate_model_pipeline_evidence_enricher(self) -> Settings:
        """D6: optional per-purpose enricher; fail loud when enabled and misconfigured."""

        ts = self.model_pipeline_evidence_enricher_timeout_seconds
        if ts is not None and not (0.0 < ts <= 300.0):
            msg = (
                "GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_TIMEOUT_SECONDS must be "
                "in (0, 300] when set"
            )
            raise ValueError(msg)

        if not self.model_pipeline_evidence_enricher_enabled:
            return self

        if self.model_pipeline_adapter != "ollama":
            msg = (
                "GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED requires "
                "GRAPHCLERK_MODEL_PIPELINE_ADAPTER=ollama"
            )
            raise ValueError(msg)

        base = self.model_pipeline_base_url
        if base is None or not str(base).strip():
            msg = (
                "GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED requires non-empty "
                "GRAPHCLERK_MODEL_PIPELINE_BASE_URL"
            )
            raise ValueError(msg)

        purpose_model = self.model_pipeline_evidence_enricher_model
        if purpose_model is None or not str(purpose_model).strip():
            msg = (
                "GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED requires non-empty "
                "GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL"
            )
            raise ValueError(msg)

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()

