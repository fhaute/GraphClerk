from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SemanticSearchEmbeddingAdapter = Literal["not_configured", "deterministic_fake"]
LanguageDetectionAdapterName = Literal["not_configured", "lingua"]


class Settings(BaseSettings):
    """Typed application settings loaded from environment.

    Phase 1 settings are infrastructure-only. They must fail clearly when required
    values are missing.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()

