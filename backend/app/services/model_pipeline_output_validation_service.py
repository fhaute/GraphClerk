"""Phase 8 Slice 8D — deep semantic validation for model pipeline outputs.

Pure, side-effect-free checks on :class:`~app.services.model_pipeline_contracts.ModelPipelineResult`
and :class:`~app.services.model_pipeline_contracts.ModelPipelineResponseEnvelope`. This service
does **not** call adapters, models, or persistence; it does **not** touch FileClerk, retrieval,
or evidence tables. It only returns a :class:`ModelPipelineOutputValidationReport` and never
mutates input objects.

Validation goes beyond Pydantic top-level rules (Slice 8A) by **recursively** scanning JSON-like
dict/list trees for forbidden truth claims and (for selected output kinds) obvious prose fields
that look like answer synthesis smuggled into structured metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.services.model_pipeline_contracts import (
    ModelOutputKind,
    ModelPipelineResponseEnvelope,
    ModelPipelineResult,
    ModelPipelineStatus,
)

Severity = Literal["error", "warning"]

# Keys that look like unbounded answer synthesis in structured pipeline payloads.
_PROSE_LIKE_KEYS: frozenset[str] = frozenset({"answer", "final_answer", "summary", "generated_text"})

# Output kinds where prose-like keys in ``payload`` are treated as errors (not ``derived_metadata``).
_PROSE_RESTRICTED_KINDS: frozenset[ModelOutputKind] = frozenset(
    {
        ModelOutputKind.candidate_metadata,
        ModelOutputKind.routing_hint,
        ModelOutputKind.validation_signal,
    },
)

# Long ``preview`` strings are suspicious but not always fatal — warn only.
_PREVIEW_WARN_LENGTH: int = 2000


@dataclass(frozen=True)
class ModelPipelineOutputValidationIssue:
    """Single finding from a validation pass."""

    code: str
    message: str
    path: str
    severity: Severity


@dataclass
class ModelPipelineOutputValidationReport:
    """Aggregate report; ``ok`` is ``False`` when any issue has ``severity == \"error\"``."""

    ok: bool
    issues: list[ModelPipelineOutputValidationIssue] = field(default_factory=list)


def _report_from_issues(issues: list[ModelPipelineOutputValidationIssue]) -> ModelPipelineOutputValidationReport:
    ok = not any(i.severity == "error" for i in issues)
    return ModelPipelineOutputValidationReport(ok=ok, issues=list(issues))


def _validate_str_list(value: Any, *, path: str, issues: list[ModelPipelineOutputValidationIssue]) -> None:
    if not isinstance(value, list):
        issues.append(
            ModelPipelineOutputValidationIssue(
                code="warnings_not_str_list",
                message=f"Expected list[str] at {path}.",
                path=path,
                severity="error",
            ),
        )
        return
    for i, item in enumerate(value):
        if not isinstance(item, str):
            issues.append(
                ModelPipelineOutputValidationIssue(
                    code="warnings_item_not_str",
                    message=f"Expected str at {path}[{i}].",
                    path=f"{path}[{i}]",
                    severity="error",
                ),
            )


def _truth_and_prose_scan(
    obj: Any,
    path: str,
    *,
    issues: list[ModelPipelineOutputValidationIssue],
    apply_prose_scan: bool,
) -> None:
    """Recursively walk dict/list structures; record issues with dotted / bracket paths."""

    if isinstance(obj, dict):
        for key, val in obj.items():
            seg = f"{path}.{key}" if path else str(key)
            if key == "is_evidence" and val is True:
                issues.append(
                    ModelPipelineOutputValidationIssue(
                        code="nested_is_evidence_true",
                        message="Model pipeline output must not claim is_evidence=true.",
                        path=seg,
                        severity="error",
                    ),
                )
            if key == "source_fidelity" and val == "verbatim":
                issues.append(
                    ModelPipelineOutputValidationIssue(
                        code="nested_source_fidelity_verbatim",
                        message='Model pipeline output must not assert source_fidelity "verbatim".',
                        path=seg,
                        severity="error",
                    ),
                )
            if key == "source_truth" and val is True:
                issues.append(
                    ModelPipelineOutputValidationIssue(
                        code="nested_source_truth_true",
                        message="Model pipeline output must not claim source_truth=true.",
                        path=seg,
                        severity="error",
                    ),
                )
            if apply_prose_scan and key in _PROSE_LIKE_KEYS and isinstance(val, str) and val.strip() != "":
                issues.append(
                    ModelPipelineOutputValidationIssue(
                        code="forbidden_prose_field",
                        message=(
                            f"Disallowed prose-like field {key!r} for this output_kind "
                            "(use derived_metadata for bounded explanations)."
                        ),
                        path=seg,
                        severity="error",
                    ),
                )
            if key == "preview" and isinstance(val, str) and len(val) > _PREVIEW_WARN_LENGTH:
                issues.append(
                    ModelPipelineOutputValidationIssue(
                        code="long_preview_string",
                        message="Very long preview string; review for accidental prose dump.",
                        path=seg,
                        severity="warning",
                    ),
                )
            _truth_and_prose_scan(val, seg, issues=issues, apply_prose_scan=apply_prose_scan)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            seg = f"{path}[{idx}]"
            _truth_and_prose_scan(item, seg, issues=issues, apply_prose_scan=apply_prose_scan)


def _envelope_shape_issues(envelope: ModelPipelineResponseEnvelope) -> list[ModelPipelineOutputValidationIssue]:
    out: list[ModelPipelineOutputValidationIssue] = []
    st = envelope.status
    if st == ModelPipelineStatus.success:
        if envelope.result is None:
            out.append(
                ModelPipelineOutputValidationIssue(
                    code="envelope_success_missing_result",
                    message="Success envelope must include a result.",
                    path="envelope",
                    severity="error",
                ),
            )
        if envelope.error is not None:
            out.append(
                ModelPipelineOutputValidationIssue(
                    code="envelope_success_has_error",
                    message="Success envelope must not include an error.",
                    path="error",
                    severity="error",
                ),
            )
        if envelope.result is not None and envelope.result.status != st:
            out.append(
                ModelPipelineOutputValidationIssue(
                    code="envelope_result_status_mismatch",
                    message="Envelope status must match result.status for success responses.",
                    path="result.status",
                    severity="error",
                ),
            )
    else:
        if envelope.error is None:
            out.append(
                ModelPipelineOutputValidationIssue(
                    code="envelope_failure_missing_error",
                    message="Non-success envelope must include an error.",
                    path="error",
                    severity="error",
                ),
            )
        if envelope.result is not None:
            out.append(
                ModelPipelineOutputValidationIssue(
                    code="envelope_failure_has_result",
                    message="Non-success envelope must not include a result payload.",
                    path="result",
                    severity="error",
                ),
            )
    return out


class ModelPipelineOutputValidationService:
    """Stateless deep validator for pipeline results and response envelopes."""

    __slots__ = ()

    def validate_result(self, result: ModelPipelineResult) -> ModelPipelineOutputValidationReport:
        """Deep-validate ``result`` without mutating it."""

        issues: list[ModelPipelineOutputValidationIssue] = []
        _validate_str_list(result.warnings, path="warnings", issues=issues)
        apply_prose = result.output_kind in _PROSE_RESTRICTED_KINDS
        _truth_and_prose_scan(result.payload, "payload", issues=issues, apply_prose_scan=apply_prose)
        _truth_and_prose_scan(result.provenance, "provenance", issues=issues, apply_prose_scan=False)
        return _report_from_issues(issues)

    def validate_response(self, envelope: ModelPipelineResponseEnvelope) -> ModelPipelineOutputValidationReport:
        """Deep-validate ``envelope`` (shape + nested blobs) without mutating it."""

        issues: list[ModelPipelineOutputValidationIssue] = []
        issues.extend(_envelope_shape_issues(envelope))
        _validate_str_list(envelope.warnings, path="warnings", issues=issues)
        _truth_and_prose_scan(envelope.metadata, "metadata", issues=issues, apply_prose_scan=False)
        if envelope.error is not None:
            _truth_and_prose_scan(envelope.error.details, "error.details", issues=issues, apply_prose_scan=False)
        if envelope.result is not None:
            sub = self.validate_result(envelope.result)
            for issue in sub.issues:
                prefixed = ModelPipelineOutputValidationIssue(
                    code=issue.code,
                    message=issue.message,
                    path=f"result.{issue.path}",
                    severity=issue.severity,
                )
                issues.append(prefixed)
        return _report_from_issues(issues)
