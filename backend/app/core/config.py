from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()

