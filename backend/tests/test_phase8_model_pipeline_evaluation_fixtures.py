"""Phase 8 Slice 8F — deterministic fixtures vs contracts, validation (8D), projection (8E)."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from app.services.model_pipeline_candidate_projection_service import (
    GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY,
    ModelPipelineCandidateMetadataProjectionService,
)
from app.services.model_pipeline_output_validation_service import ModelPipelineOutputValidationService

from tests.fixtures import phase8_model_pipeline_cases as p8fx
from tests.fixtures.phase8_model_pipeline_cases import (
    invalid_answer_shaped_candidate_case,
    invalid_is_evidence_case,
    invalid_verbatim_fidelity_case,
    unavailable_adapter_case,
    valid_candidate_metadata_case,
    valid_derived_metadata_case,
)


def test_fixture_module_has_no_forbidden_imports() -> None:
    path = Path(p8fx.__file__).resolve()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = frozenset(
        {
            "app.services.file_clerk_service",
            "app.services.text_ingestion_service",
            "app.services.multimodal_ingestion_service",
            "app.services.evidence_enrichment_service",
            "app.services.retrieval_packet_builder",
        },
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module in forbidden:
            pytest.fail(f"Forbidden import: from {node.module!r}")


@pytest.mark.parametrize(
    "builder",
    [
        valid_candidate_metadata_case,
        valid_derived_metadata_case,
        invalid_is_evidence_case,
        invalid_verbatim_fidelity_case,
        invalid_answer_shaped_candidate_case,
        unavailable_adapter_case,
    ],
)
def test_each_fixture_returns_fresh_objects(builder: Any) -> None:
    a = builder()
    b = builder()
    assert a is not b
    # Representative leaf identities — builders must not reuse mutable singletons.
    if hasattr(a, "response_envelope"):
        assert a.response_envelope is not b.response_envelope
        assert a.response_envelope.metadata is not b.response_envelope.metadata
    if hasattr(a, "task"):
        assert a.task is not b.task


def test_success_candidate_metadata_fixture_validates_and_projects_golden() -> None:
    fx = valid_candidate_metadata_case()
    val = ModelPipelineOutputValidationService()
    proj = ModelPipelineCandidateMetadataProjectionService()
    rep = val.validate_response(fx.response_envelope)
    assert rep.ok == fx.expected_validation_ok
    out = proj.project(fx.response_envelope, rep)
    assert out == fx.expected_projection
    assert list(out.keys()) == [GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY]


def test_derived_metadata_fixture_validates_ok_and_projects() -> None:
    fx = valid_derived_metadata_case()
    val = ModelPipelineOutputValidationService()
    proj = ModelPipelineCandidateMetadataProjectionService()
    rep = val.validate_response(fx.response_envelope)
    assert rep.ok is True
    assert rep.issues == []
    out = proj.project(fx.response_envelope, rep)
    assert out == fx.expected_projection
    inner = out[GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY]
    assert inner["output_kind"].value == "derived_metadata"
    assert "summary" in inner["proposed"]


def test_invalid_is_evidence_fixture_validation_path_and_no_projection() -> None:
    fx = invalid_is_evidence_case()
    val = ModelPipelineOutputValidationService()
    proj = ModelPipelineCandidateMetadataProjectionService()
    rep = val.validate_response(fx.response_envelope)
    assert rep.ok is fx.expected_validation_ok
    assert any(i.code == fx.expected_issue_code and fx.expected_path_substring in i.path for i in rep.issues)
    assert proj.project(fx.response_envelope, rep) is None


def test_invalid_verbatim_fidelity_fixture_validation_path_and_no_projection() -> None:
    fx = invalid_verbatim_fidelity_case()
    val = ModelPipelineOutputValidationService()
    proj = ModelPipelineCandidateMetadataProjectionService()
    rep = val.validate_response(fx.response_envelope)
    assert rep.ok is False
    assert any(i.code == fx.expected_issue_code and fx.expected_path_substring in i.path for i in rep.issues)
    assert proj.project(fx.response_envelope, rep) is None


def test_invalid_answer_shaped_fixture_validation_error_and_no_projection() -> None:
    fx = invalid_answer_shaped_candidate_case()
    val = ModelPipelineOutputValidationService()
    proj = ModelPipelineCandidateMetadataProjectionService()
    rep = val.validate_response(fx.response_envelope)
    assert rep.ok is False
    assert any(i.code == fx.expected_issue_code for i in rep.issues)
    assert proj.project(fx.response_envelope, rep) is None


def test_unavailable_fixture_no_projection() -> None:
    fx = unavailable_adapter_case()
    val = ModelPipelineOutputValidationService()
    proj = ModelPipelineCandidateMetadataProjectionService()
    rep = val.validate_response(fx.response_envelope)
    assert rep.ok is True
    assert fx.expected_projection_none is True
    assert proj.project(fx.response_envelope, rep) is None


def test_projection_from_fixture_is_deep_copy_safe() -> None:
    fx = valid_candidate_metadata_case()
    val = ModelPipelineOutputValidationService()
    proj = ModelPipelineCandidateMetadataProjectionService()
    rep = val.validate_response(fx.response_envelope)
    out = proj.project(fx.response_envelope, rep)
    assert out is not None
    inner = out[GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY]
    payload_before = dict(fx.response_envelope.result.payload)
    inner["proposed"]["labels"].append("mutated")
    assert fx.response_envelope.result.payload == payload_before
