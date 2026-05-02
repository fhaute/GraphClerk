"""Phase 8 Track D4 — per-purpose model pipeline configuration contracts (no HTTP, no adapters).

Maps each :class:`ModelPipelineRole` purpose to typed enablement, adapter key, model id,
timeout, and output kind. Validates Phase 1–8 policy: only ``evidence_candidate_enricher``
may be enabled; ``routing_hint_generator`` and other roles are policy-blocked when enabled.

Default output kind for ``evidence_candidate_enricher`` is :attr:`ModelOutputKind.derived_metadata`
(model-derived helper metadata). Global ``GRAPHCLERK_MODEL_PIPELINE_BASE_URL`` from
:class:`~app.core.config.Settings` is combined at **resolution** time (D5/D6), not stored
per-purpose in D4.

This module does **not** import or call ``build_model_pipeline_adapter`` (adapter registry).
"""

from __future__ import annotations

from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, model_validator

from app.core.config import Settings
from app.services.errors import GraphClerkError
from app.services.model_pipeline_contracts import (
    ModelOutputKind,
    ModelPipelineInputKind,
    ModelPipelineRole,
    ModelPipelineTask,
)

ModelPipelinePurposeAdapterName = Literal["not_configured", "ollama", "openai_compatible"]

CODE_PURPOSE_POLICY_BLOCKED = "model_pipeline_purpose_policy_blocked"
CODE_PURPOSE_RESOLUTION_FAILED = "model_pipeline_purpose_resolution_failed"


class ModelPipelinePurposePolicyError(GraphClerkError):
    """Registry configuration violates Track D purpose enablement policy."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class ModelPipelinePurposeResolutionError(GraphClerkError):
    """Resolved enabled purpose failed validation against settings or adapter readiness."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class ModelPipelinePurposeDisabledError(GraphClerkError):
    """Reserved for callers that require an enabled purpose (D5+); D4 resolve returns a flag."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


def _default_output_kind(role: ModelPipelineRole) -> ModelOutputKind:
    """Default ``output_kind`` per purpose for registry templates."""

    return {
        ModelPipelineRole.evidence_candidate_enricher: ModelOutputKind.derived_metadata,
        ModelPipelineRole.artifact_classifier: ModelOutputKind.candidate_metadata,
        ModelPipelineRole.extraction_helper: ModelOutputKind.derived_metadata,
        ModelPipelineRole.routing_hint_generator: ModelOutputKind.routing_hint,
    }[role]


def _default_input_kind(role: ModelPipelineRole) -> ModelPipelineInputKind:
    """``input_kind`` used when building :class:`ModelPipelineTask` in later slices."""

    return {
        ModelPipelineRole.evidence_candidate_enricher: ModelPipelineInputKind.extraction_context,
        ModelPipelineRole.artifact_classifier: ModelPipelineInputKind.artifact_reference,
        ModelPipelineRole.extraction_helper: ModelPipelineInputKind.extraction_context,
        ModelPipelineRole.routing_hint_generator: ModelPipelineInputKind.routing_context,
    }[role]


class ModelPipelinePurposeConfig(BaseModel):
    """Per-purpose knobs (no provider base URL — use :class:`Settings` at resolution)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    enabled: bool = False
    adapter: ModelPipelinePurposeAdapterName = "not_configured"
    model: str | None = None
    timeout_seconds: float | None = None
    output_kind: ModelOutputKind

    @model_validator(mode="after")
    def _enabled_requires_adapter_and_model(self) -> ModelPipelinePurposeConfig:
        if not self.enabled:
            return self
        if self.adapter == "not_configured":
            msg = "enabled purpose requires adapter other than not_configured"
            raise ValueError(msg)
        if self.model is None or str(self.model).strip() == "":
            msg = "enabled purpose requires a non-empty model"
            raise ValueError(msg)
        if self.timeout_seconds is not None and not (0.0 < self.timeout_seconds <= 300.0):
            msg = "timeout_seconds must satisfy 0 < value <= 300 when set"
            raise ValueError(msg)
        return self


class ModelPipelinePurposeRegistry(BaseModel):
    """Typed registry of all standard purposes."""

    model_config = ConfigDict(extra="forbid")

    configs: dict[ModelPipelineRole, ModelPipelinePurposeConfig]

    @model_validator(mode="after")
    def _every_purpose_present(self) -> ModelPipelinePurposeRegistry:
        for role in ModelPipelineRole:
            if role not in self.configs:
                msg = f"registry missing purpose config for {role.value}"
                raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _phase_policy_only_enricher_may_be_enabled(self) -> ModelPipelinePurposeRegistry:
        allowed = ModelPipelineRole.evidence_candidate_enricher
        for role, cfg in self.configs.items():
            if not cfg.enabled:
                continue
            if role != allowed:
                msg = (
                    f"Purpose {role.value!r} cannot be enabled under Phase 1–8 Track D4 policy "
                    f"(only {allowed.value!r} may be enabled; routing hints remain blocked)."
                )
                raise ModelPipelinePurposePolicyError(CODE_PURPOSE_POLICY_BLOCKED, msg)
            if cfg.adapter != "ollama":
                msg = (
                    "Track D4 allows only adapter 'ollama' when evidence_candidate_enricher "
                    f"is enabled (got {cfg.adapter!r})."
                )
                raise ModelPipelinePurposePolicyError(CODE_PURPOSE_POLICY_BLOCKED, msg)
        return self

    @model_validator(mode="after")
    def _role_output_matrix(self) -> ModelPipelinePurposeRegistry:
        for role, cfg in self.configs.items():
            ModelPipelineTask(
                role=role,
                input_kind=_default_input_kind(role),
                output_kind=cfg.output_kind,
                payload={},
                metadata={},
            )
        return self


class ModelPipelinePurposeResolution(BaseModel):
    """Outcome of resolving one purpose against registry + settings (no adapter instances)."""

    model_config = ConfigDict(extra="forbid")

    purpose: ModelPipelineRole
    disabled: bool
    role: ModelPipelineRole | None = None
    input_kind: ModelPipelineInputKind | None = None
    output_kind: ModelOutputKind | None = None
    adapter: ModelPipelinePurposeAdapterName | None = None
    model: str | None = None
    timeout_seconds: float | None = None
    base_url: str | None = None


def build_default_model_pipeline_purpose_registry(
    settings: Settings,
) -> ModelPipelinePurposeRegistry:
    """Build registry from settings (Track D6).

    By default every purpose is disabled. When
    ``settings.model_pipeline_evidence_enricher_enabled`` is true (validated in
    :class:`~app.core.config.Settings`), ``evidence_candidate_enricher`` is enabled with
    adapter ``ollama``, model from ``settings.model_pipeline_evidence_enricher_model``,
    optional per-purpose timeout, and default ``derived_metadata`` output kind.

    Callers may still merge explicit :class:`ModelPipelinePurposeConfig` for tests.
    """

    ec = ModelPipelineRole.evidence_candidate_enricher
    configs: dict[ModelPipelineRole, ModelPipelinePurposeConfig] = {
        role: ModelPipelinePurposeConfig(
            enabled=False,
            adapter="not_configured",
            model=None,
            timeout_seconds=None,
            output_kind=_default_output_kind(role),
        )
        for role in ModelPipelineRole
    }

    if settings.model_pipeline_evidence_enricher_enabled:
        pm = settings.model_pipeline_evidence_enricher_model
        if pm is None or not str(pm).strip():
            msg = "model_pipeline_evidence_enricher_model required when enricher enabled"
            raise ModelPipelinePurposeResolutionError(CODE_PURPOSE_RESOLUTION_FAILED, msg)
        configs[ec] = ModelPipelinePurposeConfig(
            enabled=True,
            adapter="ollama",
            model=str(cast(str, pm)).strip(),
            timeout_seconds=settings.model_pipeline_evidence_enricher_timeout_seconds,
            output_kind=_default_output_kind(ec),
        )

    return ModelPipelinePurposeRegistry(configs=configs)


def resolve_model_pipeline_purpose(
    registry: ModelPipelinePurposeRegistry,
    purpose: ModelPipelineRole,
    settings: Settings,
) -> ModelPipelinePurposeResolution:
    """Resolve ``purpose`` to structured fields or a disabled marker.

    Performs **no** HTTP and does **not** build adapter instances.
    """

    cfg = registry.configs[purpose]
    if not cfg.enabled:
        return ModelPipelinePurposeResolution(
            purpose=purpose,
            disabled=True,
            role=None,
            input_kind=None,
            output_kind=None,
            adapter=None,
            model=None,
            timeout_seconds=None,
            base_url=None,
        )

    timeout = cfg.timeout_seconds
    if timeout is None:
        timeout = float(settings.model_pipeline_timeout_seconds)

    if not (0.0 < timeout <= 300.0):
        msg = f"resolved timeout {timeout} out of bounds (0, 300]"
        raise ModelPipelinePurposeResolutionError(CODE_PURPOSE_RESOLUTION_FAILED, msg)

    if cfg.adapter == "ollama":
        base = settings.model_pipeline_base_url
        if base is None or str(base).strip() == "":
            msg = (
                "Ollama resolution requires GRAPHCLERK_MODEL_PIPELINE_BASE_URL in Settings "
                "when evidence_candidate_enricher is enabled"
            )
            raise ModelPipelinePurposeResolutionError(CODE_PURPOSE_RESOLUTION_FAILED, msg)
        model = cfg.model
        if model is None or str(model).strip() == "":
            msg = "enabled Ollama purpose requires non-empty model in purpose config"
            raise ModelPipelinePurposeResolutionError(CODE_PURPOSE_RESOLUTION_FAILED, msg)

        return ModelPipelinePurposeResolution(
            purpose=purpose,
            disabled=False,
            role=purpose,
            input_kind=_default_input_kind(purpose),
            output_kind=cfg.output_kind,
            adapter="ollama",
            model=str(model).strip(),
            timeout_seconds=timeout,
            base_url=str(base).strip(),
        )

    msg = f"adapter {cfg.adapter!r} is not resolvable in Track D4"
    raise ModelPipelinePurposeResolutionError(CODE_PURPOSE_RESOLUTION_FAILED, msg)


__all__ = [
    "CODE_PURPOSE_POLICY_BLOCKED",
    "CODE_PURPOSE_RESOLUTION_FAILED",
    "ModelPipelinePurposeAdapterName",
    "ModelPipelinePurposeConfig",
    "ModelPipelinePurposeDisabledError",
    "ModelPipelinePurposePolicyError",
    "ModelPipelinePurposeRegistry",
    "ModelPipelinePurposeResolution",
    "ModelPipelinePurposeResolutionError",
    "build_default_model_pipeline_purpose_registry",
    "resolve_model_pipeline_purpose",
]
