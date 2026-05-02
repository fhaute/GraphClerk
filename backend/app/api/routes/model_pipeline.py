"""Track D D7b — read-only model pipeline configuration (no writes, no inference)."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.model_pipeline_config import (
    ModelPipelineConfigResponse,
    build_model_pipeline_config_response,
)

router = APIRouter(tags=["model-pipeline"])


@router.get(
    "/model-pipeline/config",
    response_model=ModelPipelineConfigResponse,
    summary="Read-only model pipeline configuration",
)
def get_model_pipeline_config() -> ModelPipelineConfigResponse:
    """Return effective env-derived pipeline settings and purpose registry state.

    Does not call external models, does not expose API keys or raw base URLs.
    """

    return build_model_pipeline_config_response(get_settings())
