"""Static registry for Phase 8 model pipeline adapters (Track D Slice D2 / D3).

``not_configured`` and ``ollama`` (when fully configured) build real adapters.
Reserved adapters fail loudly at ``build_model_pipeline_adapter`` time — no silent
fallback.
"""

from __future__ import annotations

from collections.abc import Callable

from app.core.config import Settings
from app.services.errors import GraphClerkError
from app.services.model_pipeline_contracts import (
    ModelPipelineAdapter,
    NotConfiguredModelPipelineAdapter,
)
from app.services.model_pipeline_ollama_adapter import OllamaModelPipelineAdapter

MODEL_PIPELINE_ADAPTER_NOT_CONFIGURED = "not_configured"
MODEL_PIPELINE_ADAPTER_DETERMINISTIC_TEST = "deterministic_test"
MODEL_PIPELINE_ADAPTER_OLLAMA = "ollama"
MODEL_PIPELINE_ADAPTER_OPENAI_COMPATIBLE = "openai_compatible"

MODEL_PIPELINE_ADAPTER_KEYS: tuple[str, ...] = (
    MODEL_PIPELINE_ADAPTER_NOT_CONFIGURED,
    MODEL_PIPELINE_ADAPTER_DETERMINISTIC_TEST,
    MODEL_PIPELINE_ADAPTER_OLLAMA,
    MODEL_PIPELINE_ADAPTER_OPENAI_COMPATIBLE,
)

MODEL_PIPELINE_IMPLEMENTED_ADAPTER_KEYS: tuple[str, ...] = (
    MODEL_PIPELINE_ADAPTER_NOT_CONFIGURED,
    MODEL_PIPELINE_ADAPTER_OLLAMA,
)

MODEL_PIPELINE_RESERVED_ADAPTER_KEYS: tuple[str, ...] = (
    MODEL_PIPELINE_ADAPTER_DETERMINISTIC_TEST,
    MODEL_PIPELINE_ADAPTER_OPENAI_COMPATIBLE,
)


class ModelPipelineAdapterNotImplementedError(GraphClerkError):
    """Raised when settings select an adapter that cannot be built yet."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def build_model_pipeline_adapter(
    settings: Settings,
    *,
    deterministic_test_factory: Callable[[], ModelPipelineAdapter] | None = None,
) -> ModelPipelineAdapter:
    """Construct the configured model pipeline adapter.

    ``deterministic_test`` requires ``deterministic_test_factory`` — settings alone
    never imply a silently usable test adapter in production registry builds.

    ``ollama`` requires non-empty ``GRAPHCLERK_MODEL_PIPELINE_BASE_URL`` and
    ``GRAPHCLERK_MODEL_PIPELINE_MODEL`` (validated here; not the final D4 purpose
    registry shape per Track D2.5).
    """

    adapter = settings.model_pipeline_adapter
    if adapter == MODEL_PIPELINE_ADAPTER_NOT_CONFIGURED:
        return NotConfiguredModelPipelineAdapter()
    if adapter == MODEL_PIPELINE_ADAPTER_DETERMINISTIC_TEST:
        if deterministic_test_factory is None:
            raise ModelPipelineAdapterNotImplementedError(
                "model_pipeline_deterministic_test_requires_factory",
                (
                    "model pipeline adapter 'deterministic_test' requires an injected "
                    "deterministic_test_factory (registry-test-only)"
                ),
            )
        return deterministic_test_factory()
    if adapter == MODEL_PIPELINE_ADAPTER_OLLAMA:
        base = settings.model_pipeline_base_url
        model = settings.model_pipeline_model
        if base is None or not str(base).strip():
            raise ModelPipelineAdapterNotImplementedError(
                "model_pipeline_ollama_misconfigured",
                (
                    "GRAPHCLERK_MODEL_PIPELINE_BASE_URL is required and must be non-empty "
                    "when GRAPHCLERK_MODEL_PIPELINE_ADAPTER=ollama"
                ),
            )
        if model is None or not str(model).strip():
            raise ModelPipelineAdapterNotImplementedError(
                "model_pipeline_ollama_misconfigured",
                (
                    "GRAPHCLERK_MODEL_PIPELINE_MODEL is required and must be non-empty "
                    "when GRAPHCLERK_MODEL_PIPELINE_ADAPTER=ollama"
                ),
            )
        return OllamaModelPipelineAdapter(
            base_url=str(base).strip(),
            model=str(model).strip(),
            timeout_seconds=float(settings.model_pipeline_timeout_seconds),
        )
    if adapter == MODEL_PIPELINE_ADAPTER_OPENAI_COMPATIBLE:
        raise ModelPipelineAdapterNotImplementedError(
            "model_pipeline_adapter_not_implemented",
            "model pipeline adapter 'openai_compatible' is not implemented yet.",
        )
    msg = f"unknown model pipeline adapter: {adapter!r}"
    raise ModelPipelineAdapterNotImplementedError(
        "model_pipeline_adapter_unknown",
        msg,
    )
