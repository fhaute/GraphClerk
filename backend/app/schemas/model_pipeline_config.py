"""Read-only model pipeline configuration projection for operators (Track D D7b).

No secrets, no outbound HTTP, no adapter instances — derives shape from
:class:`~app.core.config.Settings` and :func:`build_default_model_pipeline_purpose_registry`.
"""

from __future__ import annotations

from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import Settings
from app.services.model_pipeline_contracts import ModelPipelineRole
from app.services.model_pipeline_purpose_registry import (
    ModelPipelinePurposeResolutionError,
    build_default_model_pipeline_purpose_registry,
    resolve_model_pipeline_purpose,
)

ModelPipelineGlobalAdapterName = Literal[
    "not_configured",
    "deterministic_test",
    "ollama",
    "openai_compatible",
]

PurposeAdapterName = Literal["not_configured", "ollama", "openai_compatible"]

PurposeStatusName = Literal["disabled", "configured", "misconfigured", "policy_blocked"]


class ModelPipelinePurposeStatusPayload(BaseModel):
    """One purpose row for GET /model-pipeline/config."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool
    allowed: bool = Field(
        description="Phase 1–8 policy: only evidence_candidate_enricher may be enabled.",
    )
    adapter: PurposeAdapterName | None = Field(
        default=None,
        description="Purpose-level adapter from registry or resolution (never deterministic_test).",
    )
    model: str | None = None
    timeout_seconds: float | None = None
    output_kind: str
    status: PurposeStatusName


class ModelPipelinePurposeRegistryPayload(BaseModel):
    """Nested purposes (stable OpenAPI field names)."""

    model_config = ConfigDict(extra="forbid")

    evidence_candidate_enricher: ModelPipelinePurposeStatusPayload
    artifact_classifier: ModelPipelinePurposeStatusPayload
    extraction_helper: ModelPipelinePurposeStatusPayload
    routing_hint_generator: ModelPipelinePurposeStatusPayload


class ModelPipelineConfigResponse(BaseModel):
    """Wire shape for GET /model-pipeline/config."""

    model_config = ConfigDict(extra="forbid")

    adapter: ModelPipelineGlobalAdapterName
    base_url_configured: bool
    model_configured: bool
    timeout_seconds: float
    purpose_registry: ModelPipelinePurposeRegistryPayload
    warnings: list[str] = Field(default_factory=list)


def _non_enricher_payload(
    cfg_adapter: PurposeAdapterName,
    output_kind: str,
) -> ModelPipelinePurposeStatusPayload:
    return ModelPipelinePurposeStatusPayload(
        enabled=False,
        allowed=False,
        adapter=cfg_adapter,
        model=None,
        timeout_seconds=None,
        output_kind=output_kind,
        status="policy_blocked",
    )


def build_model_pipeline_config_response(settings: Settings) -> ModelPipelineConfigResponse:
    """Build read-only config view. Never performs HTTP or loads API keys into extra fields."""

    warnings: list[str] = []
    registry = build_default_model_pipeline_purpose_registry(settings)

    base_url_configured = bool(
        settings.model_pipeline_base_url and str(settings.model_pipeline_base_url).strip(),
    )
    model_configured = bool(
        settings.model_pipeline_model and str(settings.model_pipeline_model).strip(),
    )

    ec = ModelPipelineRole.evidence_candidate_enricher
    ec_cfg = registry.configs[ec]

    if not ec_cfg.enabled:
        ec_payload = ModelPipelinePurposeStatusPayload(
            enabled=False,
            allowed=True,
            adapter=ec_cfg.adapter,
            model=None,
            timeout_seconds=None,
            output_kind=ec_cfg.output_kind.value,
            status="disabled",
        )
    else:
        try:
            res = resolve_model_pipeline_purpose(registry, ec, settings)
        except ModelPipelinePurposeResolutionError as e:
            warnings.append(str(e))
            ec_payload = ModelPipelinePurposeStatusPayload(
                enabled=True,
                allowed=True,
                adapter=ec_cfg.adapter,
                model=ec_cfg.model,
                timeout_seconds=ec_cfg.timeout_seconds,
                output_kind=ec_cfg.output_kind.value,
                status="misconfigured",
            )
        else:
            ec_payload = ModelPipelinePurposeStatusPayload(
                enabled=True,
                allowed=True,
                adapter=res.adapter,
                model=res.model,
                timeout_seconds=res.timeout_seconds,
                output_kind=res.output_kind.value if res.output_kind else ec_cfg.output_kind.value,
                status="configured",
            )

    ac = ModelPipelineRole.artifact_classifier
    eh = ModelPipelineRole.extraction_helper
    rh = ModelPipelineRole.routing_hint_generator

    purpose_registry = ModelPipelinePurposeRegistryPayload(
        evidence_candidate_enricher=ec_payload,
        artifact_classifier=_non_enricher_payload(
            cast(PurposeAdapterName, registry.configs[ac].adapter),
            registry.configs[ac].output_kind.value,
        ),
        extraction_helper=_non_enricher_payload(
            cast(PurposeAdapterName, registry.configs[eh].adapter),
            registry.configs[eh].output_kind.value,
        ),
        routing_hint_generator=_non_enricher_payload(
            cast(PurposeAdapterName, registry.configs[rh].adapter),
            registry.configs[rh].output_kind.value,
        ),
    )

    return ModelPipelineConfigResponse(
        adapter=settings.model_pipeline_adapter,
        base_url_configured=base_url_configured,
        model_configured=model_configured,
        timeout_seconds=float(settings.model_pipeline_timeout_seconds),
        purpose_registry=purpose_registry,
        warnings=warnings,
    )


__all__ = [
    "ModelPipelineConfigResponse",
    "ModelPipelineGlobalAdapterName",
    "ModelPipelinePurposeRegistryPayload",
    "ModelPipelinePurposeStatusPayload",
    "PurposeStatusName",
    "build_model_pipeline_config_response",
]
