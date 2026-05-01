"""Phase 8 Slice 8D — ``ModelPipelineOutputValidationService`` (pure, no I/O)."""

from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from app.services import model_pipeline_output_validation_service as mpovs
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
from app.services.model_pipeline_output_validation_service import ModelPipelineOutputValidationService


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


def _result(**kwargs: Any) -> ModelPipelineResult:
    d: dict[str, Any] = {
        "role": ModelPipelineRole.extraction_helper,
        "output_kind": ModelOutputKind.candidate_metadata,
        "status": ModelPipelineStatus.success,
        "payload": {},
        "warnings": [],
        "provenance": {"source": "deterministic_test"},
    }
    d.update(kwargs)
    return ModelPipelineResult(**d)


def _request(**kwargs: Any) -> ModelPipelineRequestEnvelope:
    d: dict[str, Any] = {"request_id": "rid", "task": _task()}
    d.update(kwargs)
    return ModelPipelineRequestEnvelope(**d)


def test_clean_result_validates_ok() -> None:
    svc = ModelPipelineOutputValidationService()
    r = _result()
    rep = svc.validate_result(r)
    assert rep.ok
    assert rep.issues == []


def test_nested_is_evidence_true_fails_with_path() -> None:
    svc = ModelPipelineOutputValidationService()
    r = _result(payload={"items": [{"is_evidence": True}]})
    rep = svc.validate_result(r)
    assert not rep.ok
    assert any(i.code == "nested_is_evidence_true" and "items[0].is_evidence" in i.path for i in rep.issues)


def test_nested_source_fidelity_verbatim_fails_with_path() -> None:
    svc = ModelPipelineOutputValidationService()
    r = _result(payload={"nested": {"source_fidelity": "verbatim"}})
    rep = svc.validate_result(r)
    assert not rep.ok
    assert any(i.code == "nested_source_fidelity_verbatim" for i in rep.issues)


def test_nested_source_truth_true_fails() -> None:
    svc = ModelPipelineOutputValidationService()
    r = _result(provenance={"source": "deterministic_test", "extra": {"source_truth": True}})
    rep = svc.validate_result(r)
    assert not rep.ok
    assert any(i.code == "nested_source_truth_true" for i in rep.issues)


def test_forbidden_prose_rejected_for_candidate_metadata() -> None:
    svc = ModelPipelineOutputValidationService()
    r = _result(payload={"summary": "not allowed here"})
    rep = svc.validate_result(r)
    assert not rep.ok
    assert any(i.code == "forbidden_prose_field" and "payload.summary" in i.path for i in rep.issues)


def test_forbidden_prose_rejected_for_routing_hint() -> None:
    svc = ModelPipelineOutputValidationService()
    r = _result(
        output_kind=ModelOutputKind.routing_hint,
        role=ModelPipelineRole.routing_hint_generator,
        payload={"final_answer": "no"},
    )
    rep = svc.validate_result(r)
    assert not rep.ok


def test_derived_metadata_allows_summary_explanation() -> None:
    svc = ModelPipelineOutputValidationService()
    r = _result(
        output_kind=ModelOutputKind.derived_metadata,
        role=ModelPipelineRole.evidence_candidate_enricher,
        payload={"summary": "bounded explanation for derived metadata"},
    )
    rep = svc.validate_result(r)
    assert rep.ok
    assert not any(i.code == "forbidden_prose_field" for i in rep.issues)


def test_validation_report_does_not_mutate_result_payload() -> None:
    svc = ModelPipelineOutputValidationService()
    inner = {"a": 1, "nested": {"b": 2}}
    r = _result(payload=inner)
    payload_id = id(r.payload)
    snapshot = deepcopy(r.payload)
    rep = svc.validate_result(r)
    assert rep.ok
    assert id(r.payload) == payload_id
    assert r.payload == snapshot


def test_validate_response_catches_nested_truth_in_error_details() -> None:
    svc = ModelPipelineOutputValidationService()
    err = ModelPipelineError(
        code="x",
        message="m",
        details={"nested": {"is_evidence": True}},
    )
    env = ModelPipelineResponseEnvelope.model_construct(
        request_id="r1",
        status=ModelPipelineStatus.unavailable,
        result=None,
        error=err,
        warnings=[],
        metadata={},
        schema_version="phase8.v1",
    )
    rep = svc.validate_response(env)
    assert not rep.ok
    assert any("error.details" in i.path and i.code == "nested_is_evidence_true" for i in rep.issues)


def test_validate_response_passes_clean_not_configured() -> None:
    svc = ModelPipelineOutputValidationService()
    env = NotConfiguredModelPipelineAdapter().run(_request())
    rep = svc.validate_response(env)
    assert rep.ok


def test_validate_response_passes_deterministic_success() -> None:
    svc = ModelPipelineOutputValidationService()
    req = _request(request_id="ok-1")
    env = DeterministicTestModelPipelineAdapter(result=_result()).run(req)
    rep = svc.validate_response(env)
    assert rep.ok


def test_ok_false_when_error_issue_exists() -> None:
    svc = ModelPipelineOutputValidationService()
    r = _result(payload={"deep": {"is_evidence": True}})
    rep = svc.validate_result(r)
    assert not rep.ok


def test_warning_issue_does_not_make_ok_false() -> None:
    svc = ModelPipelineOutputValidationService()
    long_preview = "x" * (mpovs._PREVIEW_WARN_LENGTH + 50)
    r = _result(payload={"preview": long_preview})
    rep = svc.validate_result(r)
    assert rep.ok
    assert any(i.severity == "warning" and i.code == "long_preview_string" for i in rep.issues)


def test_envelope_shape_issue_via_model_construct() -> None:
    svc = ModelPipelineOutputValidationService()
    env = ModelPipelineResponseEnvelope.model_construct(
        request_id="bad",
        status=ModelPipelineStatus.success,
        result=None,
        error=None,
        warnings=[],
        metadata={},
        schema_version="phase8.v1",
    )
    rep = svc.validate_response(env)
    assert not rep.ok
    assert any(i.code == "envelope_success_missing_result" for i in rep.issues)


def test_warnings_not_str_list_on_result() -> None:
    svc = ModelPipelineOutputValidationService()
    env = ModelPipelineResult.model_construct(
        role=ModelPipelineRole.extraction_helper,
        output_kind=ModelOutputKind.candidate_metadata,
        status=ModelPipelineStatus.success,
        payload={},
        warnings=[1, 2],
        provenance={"source": "deterministic_test"},
    )
    rep = svc.validate_result(env)
    assert not rep.ok
    assert any(i.code == "warnings_item_not_str" for i in rep.issues)


def test_validation_service_module_has_no_forbidden_imports() -> None:
    path = Path(mpovs.__file__).resolve()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = frozenset(
        {
            "app.services.file_clerk_service",
            "app.services.retrieval_packet_builder",
            "torch",
            "openai",
            "ollama",
        },
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module in forbidden:
            pytest.fail(f"Forbidden import: from {node.module!r}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                base = alias.name.split(".")[0]
                if base in ("torch", "openai", "ollama"):
                    pytest.fail(f"Forbidden import: {alias.name!r}")
