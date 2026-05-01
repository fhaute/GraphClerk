"""Phase 8 Slice 8A — typed contracts for future specialized model helpers.

This module defines **only** Pydantic contracts and validation rules. It does **not**
invoke models, load weights, perform inference, touch the database, or integrate
with FileClerk or retrieval services.

Invariants (non-negotiable):
    - **Model output is not evidence.** Contracts never declare results as
      verbatim source truth; payloads and provenance are rejected if they
      carry ``source_fidelity: "verbatim"`` at the **top level** (deeper
      recursive scrubbing belongs to Slice 8D).
    - Outputs are **candidate** or **derived** metadata, routing hints, or
      validation signals — never a substitute for ``EvidenceUnit`` /
      ``RetrievalPacket`` evidence without separate normalization.

Error semantics:
    Invalid shapes or boundary violations raise ``pydantic.ValidationError``
    (standard Pydantic v2 validation for these models).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

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
        if not isinstance(v, list):
            raise ValueError("warnings must be a list[str].")
        out: list[str] = []
        for i, item in enumerate(v):
            if not isinstance(item, str):
                raise ValueError(f"warnings[{i}] must be str, not {type(item).__name__}.")
            out.append(item)
        return out

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
