"""Phase 8 Slice 8F — deterministic evaluation fixtures (not production model outputs).

Typed builders return **fresh** objects per call. These payloads are synthetic JSON-like blobs
for exercising contracts, validation (8D), and projection (8E) only — **not** evidence and
**not** outputs from real inference.

No filesystem, DB, network, or adapter execution lives here.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from app.services.model_pipeline_candidate_projection_service import (
    GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY,
)
from app.services.model_pipeline_contracts import (
    MODEL_PIPELINE_NOT_CONFIGURED_CODE,
    SCHEMA_VERSION_PHASE8_V1,
    ModelOutputKind,
    ModelPipelineError,
    ModelPipelineInputKind,
    ModelPipelineRequestEnvelope,
    ModelPipelineResponseEnvelope,
    ModelPipelineResult,
    ModelPipelineRole,
    ModelPipelineStatus,
    ModelPipelineTask,
)

# Synthetic provenance — explicitly **not** ``deterministic_test`` (adapter tests-only source).
_EVAL_FIXTURE_SOURCE = "phase8_evaluation_fixture"


def _task_candidate_meta(**overrides: Any) -> ModelPipelineTask:
    base: dict[str, Any] = {
        "role": ModelPipelineRole.extraction_helper,
        "input_kind": ModelPipelineInputKind.extraction_context,
        "output_kind": ModelOutputKind.candidate_metadata,
        "payload": {},
        "metadata": {},
    }
    base.update(overrides)
    return ModelPipelineTask(**base)


def _task_derived_meta(**overrides: Any) -> ModelPipelineTask:
    base: dict[str, Any] = {
        "role": ModelPipelineRole.evidence_candidate_enricher,
        "input_kind": ModelPipelineInputKind.evidence_batch,
        "output_kind": ModelOutputKind.derived_metadata,
        "payload": {},
        "metadata": {},
    }
    base.update(overrides)
    return ModelPipelineTask(**base)


def _success_result_for_task(
    task: ModelPipelineTask,
    *,
    payload: dict[str, Any],
    provenance_extra: dict[str, Any] | None = None,
) -> ModelPipelineResult:
    prov: dict[str, Any] = {"source": _EVAL_FIXTURE_SOURCE, "case": "evaluation"}
    if provenance_extra:
        prov = {**prov, **provenance_extra}
    return ModelPipelineResult(
        role=task.role,
        output_kind=task.output_kind,
        status=ModelPipelineStatus.success,
        payload=deepcopy(payload),
        warnings=[],
        provenance=deepcopy(prov),
    )


def _request_for(task: ModelPipelineTask, *, request_id: str) -> ModelPipelineRequestEnvelope:
    return ModelPipelineRequestEnvelope(
        request_id=request_id,
        task=task,
        metadata={},
        trace={},
        schema_version=SCHEMA_VERSION_PHASE8_V1,
    )


def _success_response(
    request: ModelPipelineRequestEnvelope,
    result: ModelPipelineResult,
    *,
    metadata: dict[str, Any] | None = None,
) -> ModelPipelineResponseEnvelope:
    return ModelPipelineResponseEnvelope(
        request_id=request.request_id,
        status=ModelPipelineStatus.success,
        result=result,
        error=None,
        warnings=list(result.warnings),
        metadata=deepcopy(metadata or {"pipeline_adapter": "evaluation_fixture"}),
        schema_version=request.schema_version,
    )


@dataclass(frozen=True)
class ValidCandidateMetadataCase:
    task: ModelPipelineTask
    success_result: ModelPipelineResult
    request_envelope: ModelPipelineRequestEnvelope
    response_envelope: ModelPipelineResponseEnvelope
    expected_validation_ok: bool
    expected_projection: dict[str, Any]


def valid_candidate_metadata_case() -> ValidCandidateMetadataCase:
    """Clean candidate_metadata success path with golden projection subtree."""

    task = _task_candidate_meta()
    rid = "phase8-fixture-candidate-meta-1"
    req = _request_for(task, request_id=rid)
    payload = {"labels": ["invoice"], "hints": ["tabular"]}
    res = _success_result_for_task(task, payload=payload)
    resp = _success_response(req, res)
    golden_inner: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION_PHASE8_V1,
        "model_pipeline_request_id": rid,
        "role": task.role,
        "output_kind": task.output_kind,
        "status": ModelPipelineStatus.success,
        "provenance": deepcopy(res.provenance),
        "validation": {"ok": True, "issues": []},
        "proposed": deepcopy(payload),
    }
    golden: dict[str, Any] = {GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY: golden_inner}
    return ValidCandidateMetadataCase(
        task=task,
        success_result=res,
        request_envelope=req,
        response_envelope=resp,
        expected_validation_ok=True,
        expected_projection=golden,
    )


@dataclass(frozen=True)
class ValidDerivedMetadataCase:
    task: ModelPipelineTask
    success_result: ModelPipelineResult
    request_envelope: ModelPipelineRequestEnvelope
    response_envelope: ModelPipelineResponseEnvelope
    expected_validation_ok: bool
    expected_projection: dict[str, Any]


def valid_derived_metadata_case() -> ValidDerivedMetadataCase:
    """Derived metadata allows bounded prose keys (e.g. ``summary``) under Slice 8D rules."""

    task = _task_derived_meta()
    rid = "phase8-fixture-derived-meta-1"
    req = _request_for(task, request_id=rid)
    payload = {
        "summary": "Bounded explanation for evaluation fixtures only (not evidence).",
        "confidence_bucket": "medium",
    }
    res = _success_result_for_task(task, payload=payload)
    resp = _success_response(req, res)
    golden_inner: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION_PHASE8_V1,
        "model_pipeline_request_id": rid,
        "role": task.role,
        "output_kind": task.output_kind,
        "status": ModelPipelineStatus.success,
        "provenance": deepcopy(res.provenance),
        "validation": {"ok": True, "issues": []},
        "proposed": deepcopy(payload),
    }
    golden: dict[str, Any] = {GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY: golden_inner}
    return ValidDerivedMetadataCase(
        task=task,
        success_result=res,
        request_envelope=req,
        response_envelope=resp,
        expected_validation_ok=True,
        expected_projection=golden,
    )


@dataclass(frozen=True)
class InvalidIsEvidenceCase:
    task: ModelPipelineTask
    success_result: ModelPipelineResult
    request_envelope: ModelPipelineRequestEnvelope
    response_envelope: ModelPipelineResponseEnvelope
    expected_validation_ok: bool
    expected_issue_code: str
    expected_path_substring: str


def invalid_is_evidence_case() -> InvalidIsEvidenceCase:
    task = _task_candidate_meta()
    req = _request_for(task, request_id="phase8-fixture-bad-is-evidence")
    payload = {"nested": {"is_evidence": True}}
    res = _success_result_for_task(task, payload=payload)
    resp = _success_response(req, res)
    return InvalidIsEvidenceCase(
        task=task,
        success_result=res,
        request_envelope=req,
        response_envelope=resp,
        expected_validation_ok=False,
        expected_issue_code="nested_is_evidence_true",
        expected_path_substring="result.payload.nested.is_evidence",
    )


@dataclass(frozen=True)
class InvalidVerbatimFidelityCase:
    task: ModelPipelineTask
    success_result: ModelPipelineResult
    request_envelope: ModelPipelineRequestEnvelope
    response_envelope: ModelPipelineResponseEnvelope
    expected_validation_ok: bool
    expected_issue_code: str
    expected_path_substring: str


def invalid_verbatim_fidelity_case() -> InvalidVerbatimFidelityCase:
    """Nested ``source_fidelity: verbatim`` under provenance (top-level is contract-forbidden)."""

    task = _task_candidate_meta()
    req = _request_for(task, request_id="phase8-fixture-bad-verbatim")
    payload = {"ok": True}
    res = ModelPipelineResult(
        role=task.role,
        output_kind=task.output_kind,
        status=ModelPipelineStatus.success,
        payload=deepcopy(payload),
        warnings=[],
        provenance={
            "source": _EVAL_FIXTURE_SOURCE,
            "nested": {"source_fidelity": "verbatim"},
        },
    )
    resp = _success_response(req, res)
    return InvalidVerbatimFidelityCase(
        task=task,
        success_result=res,
        request_envelope=req,
        response_envelope=resp,
        expected_validation_ok=False,
        expected_issue_code="nested_source_fidelity_verbatim",
        expected_path_substring="result.provenance.nested.source_fidelity",
    )


@dataclass(frozen=True)
class InvalidAnswerShapedCandidateCase:
    task: ModelPipelineTask
    success_result: ModelPipelineResult
    request_envelope: ModelPipelineRequestEnvelope
    response_envelope: ModelPipelineResponseEnvelope
    expected_validation_ok: bool
    expected_issue_code: str


def invalid_answer_shaped_candidate_case() -> InvalidAnswerShapedCandidateCase:
    """candidate_metadata payload with disallowed prose-shaped key ``answer``."""

    task = _task_candidate_meta()
    req = _request_for(task, request_id="phase8-fixture-answer-shaped")
    payload = {"answer": "must not appear as synthetic answer."}
    res = _success_result_for_task(task, payload=payload)
    resp = _success_response(req, res)
    return InvalidAnswerShapedCandidateCase(
        task=task,
        success_result=res,
        request_envelope=req,
        response_envelope=resp,
        expected_validation_ok=False,
        expected_issue_code="forbidden_prose_field",
    )


@dataclass(frozen=True)
class UnavailableAdapterCase:
    request_envelope: ModelPipelineRequestEnvelope
    response_envelope: ModelPipelineResponseEnvelope
    expected_projection_none: bool


def unavailable_adapter_case() -> UnavailableAdapterCase:
    """Mirrors :class:`NotConfiguredModelPipelineAdapter` wire shape without invoking an adapter."""

    task = _task_candidate_meta()
    req = _request_for(task, request_id="phase8-fixture-unavailable")
    err = ModelPipelineError(
        code=MODEL_PIPELINE_NOT_CONFIGURED_CODE,
        message="Model pipeline adapter is not configured.",
        retryable=False,
        details={"source": "not_configured"},
    )
    resp = ModelPipelineResponseEnvelope(
        request_id=req.request_id,
        status=ModelPipelineStatus.unavailable,
        result=None,
        error=err,
        warnings=[MODEL_PIPELINE_NOT_CONFIGURED_CODE],
        metadata={"pipeline_adapter": "not_configured"},
        schema_version=req.schema_version,
    )
    return UnavailableAdapterCase(
        request_envelope=req,
        response_envelope=resp,
        expected_projection_none=True,
    )
