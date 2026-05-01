"""Phase 8 — typed contracts, envelopes, and adapter shells for specialized model helpers.

Slices **8A–8C** in this module: task/result contracts (8A), request/response envelopes
(8B), and :class:`ModelPipelineAdapter` plus :class:`NotConfiguredModelPipelineAdapter`
and **tests-only** :class:`DeterministicTestModelPipelineAdapter` (8C). This code does
**not** invoke real models, load weights, perform remote inference, touch the database,
or integrate with FileClerk or retrieval services. Envelopes do **not** imply that
inference is configured or successful unless an adapter explicitly returns success.

Invariants (non-negotiable):
    - **Model output is not evidence.** Contracts never declare results as
      verbatim source truth; payloads, provenance, and (for 8B) error ``details``
      are rejected if they carry forbidden top-level truth claims (e.g.
      ``source_fidelity: "verbatim"``, ``is_evidence: true``). **Deeper recursive
      scrubbing** of nested dicts belongs to **Slice 8D**.
    - Outputs are **candidate** or **derived** metadata, routing hints, or
      validation signals — never a substitute for ``EvidenceUnit`` /
      ``RetrievalPacket`` evidence without separate normalization.

Error semantics:
    Invalid shapes or boundary violations raise ``pydantic.ValidationError``
    (standard Pydantic v2 validation for these models).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Callable, ClassVar, Protocol, Self, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

# Default wire format version for Phase 8 pipeline JSON envelopes (not an inference claim).
SCHEMA_VERSION_PHASE8_V1: str = "phase8.v1"

# Stable error code when no real pipeline adapter is wired (explicit, no silent fallback).
MODEL_PIPELINE_NOT_CONFIGURED_CODE: str = "model_pipeline_not_configured"

# --- Controlled vocabularies (string enums, project style) ---


class ModelPipelineRole(StrEnum):
    """Specialized helper role; each role is allowed only certain output kinds."""

    artifact_classifier = "artifact_classifier"
    evidence_candidate_enricher = "evidence_candidate_enricher"
    routing_hint_generator = "routing_hint_generator"
    extraction_helper = "extraction_helper"


class ModelPipelineInputKind(StrEnum):
    """High-level description of task inputs (references / context blobs only)."""

    artifact_reference = "artifact_reference"
    evidence_batch = "evidence_batch"
    routing_context = "routing_context"
    extraction_context = "extraction_context"


class ModelOutputKind(StrEnum):
    """Explicit output semantics — never ``verbatim`` source truth."""

    candidate_metadata = "candidate_metadata"
    derived_metadata = "derived_metadata"
    routing_hint = "routing_hint"
    validation_signal = "validation_signal"


class ModelPipelineStatus(StrEnum):
    """Lifecycle of a single pipeline step result (no silent success on failure)."""

    success = "success"
    rejected = "rejected"
    unavailable = "unavailable"
    error = "error"


# --- Role ↔ output matrix (bounded combinations) ---

_ROLE_TO_OUTPUT_KINDS: ClassVar[dict[ModelPipelineRole, frozenset[ModelOutputKind]]] = {
    ModelPipelineRole.artifact_classifier: frozenset(
        {
            ModelOutputKind.candidate_metadata,
            ModelOutputKind.validation_signal,
        },
    ),
    ModelPipelineRole.evidence_candidate_enricher: frozenset(
        {
            ModelOutputKind.candidate_metadata,
            ModelOutputKind.derived_metadata,
        },
    ),
    ModelPipelineRole.routing_hint_generator: frozenset(
        {
            ModelOutputKind.routing_hint,
            ModelOutputKind.candidate_metadata,
        },
    ),
    ModelPipelineRole.extraction_helper: frozenset(
        {
            ModelOutputKind.candidate_metadata,
            ModelOutputKind.derived_metadata,
            ModelOutputKind.validation_signal,
        },
    ),
}


def _assert_json_like_dict(value: Any, *, field_name: str) -> dict[str, Any]:
    if value is None:
        raise ValueError(f"{field_name} must be a dict, not None.")
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a dict[str, Any], not {type(value).__name__}.")
    return value


def _forbid_truth_claims_top_level(mapping: dict[str, Any], *, label: str) -> None:
    """Reject top-level claims that equate model output with source evidence.

    Deeper nested validation is intentionally deferred to Slice 8D.
    """

    if mapping.get("is_evidence") is True:
        msg = f"{label} must not claim is_evidence=true (model output is not evidence)."
        raise ValueError(msg)
    sf = mapping.get("source_fidelity")
    if sf == "verbatim":
        msg = (
            f"{label} must not set source_fidelity to verbatim "
            "(model pipeline output cannot assert verbatim source truth)."
        )
        raise ValueError(msg)


def _validate_role_output_pair(role: ModelPipelineRole, output_kind: ModelOutputKind) -> None:
    allowed = _ROLE_TO_OUTPUT_KINDS.get(role)
    if allowed is None or output_kind not in allowed:
        allowed_list = sorted(o.value for o in (allowed or frozenset()))
        raise ValueError(
            f"output_kind {output_kind.value!r} is not allowed for role {role.value!r}. "
            f"Allowed: {allowed_list}.",
        )


def _warnings_list_str(v: Any) -> list[str]:
    if not isinstance(v, list):
        raise ValueError("warnings must be a list[str].")
    out: list[str] = []
    for i, item in enumerate(v):
        if not isinstance(item, str):
            raise ValueError(f"warnings[{i}] must be str, not {type(item).__name__}.")
        out.append(item)
    return out


def _non_empty_stripped_str(v: str, *, field_name: str) -> str:
    if not isinstance(v, str):
        raise ValueError(f"{field_name} must be a string.")
    s = v.strip()
    if s == "":
        raise ValueError(f"{field_name} must be a non-empty string.")
    return s


class ModelPipelineTask(BaseModel):
    """A single future model-helper task envelope (no execution).

    ``payload`` and ``metadata`` are JSON-like dicts only; list/str roots are rejected.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: ModelPipelineRole
    input_kind: ModelPipelineInputKind
    output_kind: ModelOutputKind
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("payload", "metadata", mode="before")
    @classmethod
    def _coerce_dict_only(cls, v: Any, info: ValidationInfo) -> dict[str, Any]:
        return _assert_json_like_dict(v, field_name=info.field_name or "field")

    @model_validator(mode="after")
    def _validate_role_matrix(self) -> ModelPipelineTask:
        _validate_role_output_pair(self.role, self.output_kind)
        _forbid_truth_claims_top_level(self.payload, label="ModelPipelineTask.payload")
        _forbid_truth_claims_top_level(self.metadata, label="ModelPipelineTask.metadata")
        return self


class ModelPipelineResult(BaseModel):
    """Structured outcome of a pipeline step (contracts only — no adapter yet).

    ``provenance`` must include string key ``source`` (e.g. ``not_configured``,
    ``deterministic_test``, or a future adapter id) for traceability.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: ModelPipelineRole
    output_kind: ModelOutputKind
    status: ModelPipelineStatus
    payload: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)

    @field_validator("payload", "provenance", mode="before")
    @classmethod
    def _coerce_dict_only_result(cls, v: Any, info: ValidationInfo) -> dict[str, Any]:
        return _assert_json_like_dict(v, field_name=info.field_name or "field")

    @field_validator("warnings", mode="before")
    @classmethod
    def _warnings_must_be_str_list(cls, v: Any) -> list[str]:
        return _warnings_list_str(v)

    @model_validator(mode="after")
    def _validate_matrix_and_truth_bounds(self) -> ModelPipelineResult:
        _validate_role_output_pair(self.role, self.output_kind)
        _forbid_truth_claims_top_level(self.payload, label="ModelPipelineResult.payload")
        _forbid_truth_claims_top_level(self.provenance, label="ModelPipelineResult.provenance")

        src = self.provenance.get("source")
        if not isinstance(src, str) or src.strip() == "":
            raise ValueError(
                "provenance['source'] must be a non-empty str "
                "(e.g. 'not_configured', 'deterministic_test', or adapter id).",
            )
        return self


class ModelPipelineError(BaseModel):
    """Structured error for pipeline responses (no stack traces required here).

    ``details`` is a JSON-like dict only; top-level truth-claim bans match Slice 8A.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    code: str
    message: str
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)

    @field_validator("code", "message", mode="after")
    @classmethod
    def _code_message_nonempty(cls, v: str, info: ValidationInfo) -> str:
        return _non_empty_stripped_str(v, field_name=info.field_name or "field")

    @field_validator("details", mode="before")
    @classmethod
    def _details_dict(cls, v: Any, info: ValidationInfo) -> dict[str, Any]:
        return _assert_json_like_dict(v, field_name=info.field_name or "details")

    @model_validator(mode="after")
    def _forbid_truth_in_details(self) -> ModelPipelineError:
        _forbid_truth_claims_top_level(self.details, label="ModelPipelineError.details")
        return self


class ModelPipelineRequestEnvelope(BaseModel):
    """Wire-in request wrapper around a :class:`ModelPipelineTask` (no execution).

    Carries correlation ``request_id``, optional ``metadata`` / ``trace`` blobs,
    and a **schema version** string for forward compatibility. Does not imply that
    any model adapter is configured.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    request_id: str
    task: ModelPipelineTask
    metadata: dict[str, Any] = Field(default_factory=dict)
    trace: dict[str, Any] = Field(default_factory=dict)
    schema_version: str = Field(default=SCHEMA_VERSION_PHASE8_V1)

    @field_validator("request_id", mode="after")
    @classmethod
    def _request_id_nonempty(cls, v: str) -> str:
        return _non_empty_stripped_str(v, field_name="request_id")

    @field_validator("schema_version", mode="after")
    @classmethod
    def _schema_version_nonempty(cls, v: str) -> str:
        return _non_empty_stripped_str(v, field_name="schema_version")

    @field_validator("metadata", "trace", mode="before")
    @classmethod
    def _meta_trace_dicts(cls, v: Any, info: ValidationInfo) -> dict[str, Any]:
        return _assert_json_like_dict(v, field_name=info.field_name or "field")

    @model_validator(mode="after")
    def _forbid_truth_in_request_blobs(self) -> ModelPipelineRequestEnvelope:
        _forbid_truth_claims_top_level(self.metadata, label="ModelPipelineRequestEnvelope.metadata")
        _forbid_truth_claims_top_level(self.trace, label="ModelPipelineRequestEnvelope.trace")
        return self


class ModelPipelineResponseEnvelope(BaseModel):
    """Wire-out response wrapper: status, optional :class:`ModelPipelineResult`, or error.

    **Slice 8B rules:** ``status == success`` requires a non-``None`` ``result``,
    ``error`` must be ``None``, and ``result.status`` must match the envelope
    ``status``. Non-success statuses require a non-``None`` ``error`` and
    ``result`` must be ``None`` (no partial result payloads in this slice).
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    request_id: str
    status: ModelPipelineStatus
    result: ModelPipelineResult | None = None
    error: ModelPipelineError | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    schema_version: str = Field(default=SCHEMA_VERSION_PHASE8_V1)

    @field_validator("request_id", mode="after")
    @classmethod
    def _response_request_id_nonempty(cls, v: str) -> str:
        return _non_empty_stripped_str(v, field_name="request_id")

    @field_validator("schema_version", mode="after")
    @classmethod
    def _response_schema_nonempty(cls, v: str) -> str:
        return _non_empty_stripped_str(v, field_name="schema_version")

    @field_validator("metadata", mode="before")
    @classmethod
    def _response_metadata_dict(cls, v: Any, info: ValidationInfo) -> dict[str, Any]:
        return _assert_json_like_dict(v, field_name=info.field_name or "metadata")

    @field_validator("warnings", mode="before")
    @classmethod
    def _response_warnings(cls, v: Any) -> list[str]:
        return _warnings_list_str(v)

    @model_validator(mode="after")
    def _validate_success_vs_failure_shape(self) -> Self:
        _forbid_truth_claims_top_level(self.metadata, label="ModelPipelineResponseEnvelope.metadata")

        if self.status == ModelPipelineStatus.success:
            if self.error is not None:
                raise ValueError("success response must have error=None.")
            if self.result is None:
                raise ValueError("success response requires a non-None result.")
            if self.result.status != self.status:
                raise ValueError(
                    "result.status must match envelope status when result is present "
                    f"(envelope={self.status.value!r}, result={self.result.status.value!r}).",
                )
            return self

        # rejected | unavailable | error
        if self.error is None:
            raise ValueError(
                f"response with status {self.status.value!r} requires a non-None error.",
            )
        if self.result is not None:
            raise ValueError(
                "non-success response must have result=None (no partial results).",
            )
        return self


# --- Slice 8C — adapter protocol and explicit shells (no registry, no real inference) ---


@runtime_checkable
class ModelPipelineAdapter(Protocol):
    """Pluggable boundary for a future model pipeline step.

    Implementations return only :class:`ModelPipelineResponseEnvelope` values built
    from typed contracts — never raw evidence, never silent success on failure.
    """

    def run(self, envelope: ModelPipelineRequestEnvelope) -> ModelPipelineResponseEnvelope:
        """Execute (or simulate) the pipeline step for ``envelope`` and return a response."""


class NotConfiguredModelPipelineAdapter:
    """Explicit adapter placeholder: always **unavailable**, never fakes success.

    Use when no real model stack is configured. Does not raise for valid envelopes;
    returns a structured :class:`ModelPipelineError` with ``retryable=False``.
    """

    __slots__ = ()

    def run(self, envelope: ModelPipelineRequestEnvelope) -> ModelPipelineResponseEnvelope:
        err = ModelPipelineError(
            code=MODEL_PIPELINE_NOT_CONFIGURED_CODE,
            message="Model pipeline adapter is not configured.",
            retryable=False,
            details={"source": "not_configured"},
        )
        return ModelPipelineResponseEnvelope(
            request_id=envelope.request_id,
            status=ModelPipelineStatus.unavailable,
            result=None,
            error=err,
            warnings=[MODEL_PIPELINE_NOT_CONFIGURED_CODE],
            metadata={"pipeline_adapter": "not_configured"},
            schema_version=envelope.schema_version,
        )


class DeterministicTestModelPipelineAdapter:
    """**Tests-only** adapter returning a fixed success :class:`ModelPipelineResult`.

    Provide exactly one of ``result=`` (template copied per call) or ``factory=``
    (callable invoked per call). The produced/returned result must:

    - have ``status == success``
    - match ``envelope.task.role`` and ``envelope.task.output_kind``
    - use ``provenance['source'] == 'deterministic_test'``

    Raises :class:`ValueError` on misconfiguration — no hidden fallback.

    Do **not** wire this adapter into production code paths.
    """

    __slots__ = ("_factory", "_template")

    def __init__(
        self,
        *,
        result: ModelPipelineResult | None = None,
        factory: Callable[[ModelPipelineRequestEnvelope], ModelPipelineResult] | None = None,
    ) -> None:
        if (result is None) == (factory is None):
            raise ValueError("Provide exactly one of result= or factory=.")
        self._template = result
        self._factory = factory

    def run(self, envelope: ModelPipelineRequestEnvelope) -> ModelPipelineResponseEnvelope:
        if self._factory is not None:
            built = self._factory(envelope)
        else:
            tpl = self._template
            if tpl is None:
                raise ValueError("DeterministicTestModelPipelineAdapter internal state is invalid.")
            built = tpl.model_copy(deep=True)

        if built.status != ModelPipelineStatus.success:
            raise ValueError(
                "DeterministicTestModelPipelineAdapter requires result.status == success.",
            )
        if built.role != envelope.task.role or built.output_kind != envelope.task.output_kind:
            raise ValueError(
                "DeterministicTestModelPipelineAdapter result role/output_kind must match "
                "envelope.task.",
            )
        src = built.provenance.get("source")
        if src != "deterministic_test":
            raise ValueError(
                "DeterministicTestModelPipelineAdapter requires provenance['source'] "
                "== 'deterministic_test'.",
            )

        return ModelPipelineResponseEnvelope(
            request_id=envelope.request_id,
            status=ModelPipelineStatus.success,
            result=built,
            error=None,
            warnings=list(built.warnings),
            metadata={"pipeline_adapter": "deterministic_test"},
            schema_version=envelope.schema_version,
        )
