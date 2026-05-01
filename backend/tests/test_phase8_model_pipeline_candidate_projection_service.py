"""Phase 8 Slice 8E — ``ModelPipelineCandidateMetadataProjectionService`` (projection only)."""

from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from app.services import model_pipeline_candidate_projection_service as mpcps
from app.services.model_pipeline_candidate_projection_service import (
    GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY,
    ModelPipelineCandidateMetadataProjectionService,
)
from app.services.model_pipeline_contracts import (
    DeterministicTestModelPipelineAdapter,
    ModelOutputKind,
    ModelPipelineError,
    ModelPipelineInputKind,
    ModelPipelineRequestEnvelope,
    ModelPipelineResponseEnvelope,
    ModelPipelineResult,
    ModelPipelineRole,
    ModelPipelineStatus,
    ModelPipelineTask,
    NotConfiguredModelPipelineAdapter,
)
from app.services.model_pipeline_output_validation_service import (
    ModelPipelineOutputValidationReport,
    ModelPipelineOutputValidationService,
)


def _task(**kwargs: Any) -> ModelPipelineTask:
    d: dict[str, Any] = {
        "role": ModelPipelineRole.extraction_helper,
        "input_kind": ModelPipelineInputKind.extraction_context,
        "output_kind": ModelOutputKind.candidate_metadata,
        "payload": {},
        "metadata": {},
    }
    d.update(kwargs)
    return ModelPipelineTask(**d)


def _request(**kwargs: Any) -> ModelPipelineRequestEnvelope:
    d: dict[str, Any] = {"request_id": "proj-req-1", "task": _task()}
    d.update(kwargs)
    return ModelPipelineRequestEnvelope(**d)


def _success_result(**kwargs: Any) -> ModelPipelineResult:
    d: dict[str, Any] = {
        "role": ModelPipelineRole.extraction_helper,
        "output_kind": ModelOutputKind.candidate_metadata,
        "status": ModelPipelineStatus.success,
        "payload": {"labels": ["a"], "hints": ["keep-small"]},
        "warnings": [],
        "provenance": {"source": "deterministic_test", "run": "t1"},
    }
    d.update(kwargs)
    return ModelPipelineResult(**d)


def test_successful_validated_response_produces_graphclerk_model_pipeline_subtree() -> None:
    svc_val = ModelPipelineOutputValidationService()
    svc_proj = ModelPipelineCandidateMetadataProjectionService()
    req = _request(request_id="exact-1", schema_version="phase8.v1")
    env = DeterministicTestModelPipelineAdapter(result=_success_result()).run(req)
    rep = svc_val.validate_response(env)
    assert rep.ok
    out = svc_proj.project(env, rep)
    assert out is not None
    inner = out[GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY]
    expected_inner: dict[str, Any] = {
        "schema_version": "phase8.v1",
        "model_pipeline_request_id": "exact-1",
        "role": ModelPipelineRole.extraction_helper,
        "output_kind": ModelOutputKind.candidate_metadata,
        "status": ModelPipelineStatus.success,
        "provenance": {"source": "deterministic_test", "run": "t1"},
        "validation": {"ok": True, "issues": []},
        "proposed": {"labels": ["a"], "hints": ["keep-small"]},
    }
    assert inner == expected_inner
    assert list(out.keys()) == [GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY]


def test_projection_includes_provenance_validation_issues_and_proposed() -> None:
    svc_val = ModelPipelineOutputValidationService()
    svc_proj = ModelPipelineCandidateMetadataProjectionService()
    req = _request()
    res = _success_result(payload={"x": 1})
    env = DeterministicTestModelPipelineAdapter(result=res).run(req)
    rep = svc_val.validate_response(env)
    out = svc_proj.project(env, rep)
    assert out is not None
    inner = out[GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY]
    assert inner["provenance"] == {"source": "deterministic_test", "run": "t1"}
    assert inner["validation"]["ok"] is True
    assert inner["validation"]["issues"] == []
    assert inner["proposed"] == {"x": 1}


def test_validation_issues_are_deep_copied_and_serializable() -> None:
    svc_val = ModelPipelineOutputValidationService()
    svc_proj = ModelPipelineCandidateMetadataProjectionService()
    req = _request()
    long_preview = "x" * 2001  # validator warns above 2000 chars (Slice 8D)
    res = _success_result(payload={"preview": long_preview})
    env = DeterministicTestModelPipelineAdapter(result=res).run(req)
    rep = svc_val.validate_response(env)
    assert rep.ok
    assert len(rep.issues) == 1
    assert rep.issues[0].severity == "warning"
    out = svc_proj.project(env, rep)
    assert out is not None
    inner = out[GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY]
    issues_out = inner["validation"]["issues"]
    assert len(issues_out) == 1
    assert isinstance(issues_out[0], dict)
    msg_before = rep.issues[0].message
    issues_out[0]["message"] = "mutated"
    assert rep.issues[0].message == msg_before


def test_validation_ok_false_returns_none() -> None:
    svc_proj = ModelPipelineCandidateMetadataProjectionService()
    req = _request()
    bad = ModelPipelineResult(
        role=ModelPipelineRole.extraction_helper,
        output_kind=ModelOutputKind.candidate_metadata,
        status=ModelPipelineStatus.success,
        payload={"deep": {"is_evidence": True}},
        warnings=[],
        provenance={"source": "deterministic_test"},
    )
    env = DeterministicTestModelPipelineAdapter(result=bad).run(req)
    rep = ModelPipelineOutputValidationService().validate_response(env)
    assert rep.ok is False
    assert svc_proj.project(env, rep) is None


def test_unavailable_returns_none() -> None:
    svc_val = ModelPipelineOutputValidationService()
    svc_proj = ModelPipelineCandidateMetadataProjectionService()
    env = NotConfiguredModelPipelineAdapter().run(_request())
    rep = svc_val.validate_response(env)
    assert svc_proj.project(env, rep) is None


def test_rejected_returns_none() -> None:
    svc_proj = ModelPipelineCandidateMetadataProjectionService()
    env = ModelPipelineResponseEnvelope.model_construct(
        request_id="r",
        status=ModelPipelineStatus.rejected,
        result=None,
        error=ModelPipelineError(code="c", message="m"),
        warnings=[],
        metadata={},
        schema_version="phase8.v1",
    )
    rep = ModelPipelineOutputValidationReport(ok=True, issues=[])
    assert svc_proj.project(env, rep) is None


def test_error_envelope_returns_none() -> None:
    svc_proj = ModelPipelineCandidateMetadataProjectionService()
    env = ModelPipelineResponseEnvelope.model_construct(
        request_id="r",
        status=ModelPipelineStatus.error,
        result=None,
        error=ModelPipelineError(code="e", message="m"),
        warnings=[],
        metadata={},
        schema_version="phase8.v1",
    )
    assert svc_proj.project(env, ModelPipelineOutputValidationReport(ok=True, issues=[])) is None


def test_success_with_missing_result_returns_none() -> None:
    svc_proj = ModelPipelineCandidateMetadataProjectionService()
    env = ModelPipelineResponseEnvelope.model_construct(
        request_id="r",
        status=ModelPipelineStatus.success,
        result=None,
        error=None,
        warnings=[],
        metadata={},
        schema_version="phase8.v1",
    )
    assert svc_proj.project(env, ModelPipelineOutputValidationReport(ok=True, issues=[])) is None


def test_success_with_error_constructed_returns_none() -> None:
    svc_proj = ModelPipelineCandidateMetadataProjectionService()
    res = _success_result()
    env = ModelPipelineResponseEnvelope.model_construct(
        request_id="r",
        status=ModelPipelineStatus.success,
        result=res,
        error=ModelPipelineError(code="phantom", message="should block projection"),
        warnings=[],
        metadata={},
        schema_version="phase8.v1",
    )
    assert svc_proj.project(env, ModelPipelineOutputValidationReport(ok=True, issues=[])) is None


def test_projection_does_not_mutate_response_or_validation() -> None:
    svc_val = ModelPipelineOutputValidationService()
    svc_proj = ModelPipelineCandidateMetadataProjectionService()
    req = _request()
    res = _success_result(payload={"n": 1}, provenance={"source": "deterministic_test", "k": [1, 2]})
    env = DeterministicTestModelPipelineAdapter(result=res).run(req)
    rep = svc_val.validate_response(env)
    env_snapshot = env.model_dump(mode="json")
    rep_issues_snapshot = deepcopy(rep.issues)
    out = svc_proj.project(env, rep)
    assert out is not None
    assert env.model_dump(mode="json") == env_snapshot
    assert rep.issues == rep_issues_snapshot


def test_projection_returns_deep_copies_not_shared_refs() -> None:
    svc_val = ModelPipelineOutputValidationService()
    svc_proj = ModelPipelineCandidateMetadataProjectionService()
    req = _request()
    res = _success_result(payload={"items": [{"id": 1}]}, provenance={"source": "deterministic_test"})
    env = DeterministicTestModelPipelineAdapter(result=res).run(req)
    rep = svc_val.validate_response(env)
    out = svc_proj.project(env, rep)
    assert out is not None
    inner = out[GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY]
    assert inner["proposed"] is not env.result.payload
    assert inner["provenance"] is not env.result.provenance
    inner["proposed"]["items"][0]["id"] = 999
    assert env.result.payload["items"][0]["id"] == 1


def test_projection_service_module_has_no_forbidden_imports() -> None:
    path = Path(mpcps.__file__).resolve()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = frozenset(
        {
            "app.services.file_clerk_service",
            "app.services.text_ingestion_service",
            "app.services.multimodal_ingestion_service",
            "app.services.evidence_enrichment_service",
        },
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module in forbidden:
            pytest.fail(f"Forbidden import: from {node.module!r}")
