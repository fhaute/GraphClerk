"""Phase 8 Slices 8A–8C — model pipeline contracts, envelopes, and adapter shells (no inference)."""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.services import model_pipeline_contracts as mpc
from app.services.model_pipeline_contracts import (
    MODEL_PIPELINE_NOT_CONFIGURED_CODE,
    SCHEMA_VERSION_PHASE8_V1,
    DeterministicTestModelPipelineAdapter,
    ModelOutputKind,
    ModelPipelineAdapter,
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


def _minimal_task(**kwargs: Any) -> ModelPipelineTask:
    d: dict[str, Any] = {
        "role": ModelPipelineRole.extraction_helper,
        "input_kind": ModelPipelineInputKind.extraction_context,
        "output_kind": ModelOutputKind.candidate_metadata,
        "payload": {},
        "metadata": {},
    }
    d.update(kwargs)
    return ModelPipelineTask(**d)


def _success_result(**kwargs: Any) -> ModelPipelineResult:
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


def _request_envelope(**kwargs: Any) -> ModelPipelineRequestEnvelope:
    d: dict[str, Any] = {
        "request_id": "req-default",
        "task": _minimal_task(),
    }
    d.update(kwargs)
    return ModelPipelineRequestEnvelope(**d)


def test_contracts_import_successfully() -> None:
    assert ModelPipelineRole.artifact_classifier.value == "artifact_classifier"
    assert ModelOutputKind.candidate_metadata.value == "candidate_metadata"


def test_valid_task_validates() -> None:
    t = ModelPipelineTask(
        role=ModelPipelineRole.extraction_helper,
        input_kind=ModelPipelineInputKind.extraction_context,
        output_kind=ModelOutputKind.candidate_metadata,
        payload={"hint": "x"},
        metadata={"k": 1},
    )
    assert t.payload == {"hint": "x"}
    assert t.metadata == {"k": 1}


def test_valid_result_validates() -> None:
    r = ModelPipelineResult(
        role=ModelPipelineRole.routing_hint_generator,
        output_kind=ModelOutputKind.routing_hint,
        status=ModelPipelineStatus.success,
        payload={"routes": []},
        warnings=["ok"],
        provenance={"source": "deterministic_test"},
    )
    assert r.status == ModelPipelineStatus.success
    assert r.warnings == ["ok"]


def test_invalid_role_rejected() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineTask.model_validate(
            {
                "role": "not_a_real_role",
                "input_kind": "artifact_reference",
                "output_kind": "candidate_metadata",
                "payload": {},
                "metadata": {},
            },
        )


def test_invalid_output_kind_for_role_rejected() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineTask(
            role=ModelPipelineRole.artifact_classifier,
            input_kind=ModelPipelineInputKind.artifact_reference,
            output_kind=ModelOutputKind.routing_hint,
            payload={},
            metadata={},
        )


def test_warnings_must_be_list_str() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineResult(
            role=ModelPipelineRole.evidence_candidate_enricher,
            output_kind=ModelOutputKind.derived_metadata,
            status=ModelPipelineStatus.success,
            payload={},
            warnings=[1, 2],
            provenance={"source": "x"},
        )
    with pytest.raises(ValidationError):
        ModelPipelineResult(
            role=ModelPipelineRole.evidence_candidate_enricher,
            output_kind=ModelOutputKind.derived_metadata,
            status=ModelPipelineStatus.success,
            payload={},
            warnings="not-a-list",
            provenance={"source": "x"},
        )


def test_payload_must_be_dict() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineTask(
            role=ModelPipelineRole.extraction_helper,
            input_kind=ModelPipelineInputKind.extraction_context,
            output_kind=ModelOutputKind.candidate_metadata,
            payload=[],
            metadata={},
        )


def test_metadata_must_be_dict() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineTask(
            role=ModelPipelineRole.extraction_helper,
            input_kind=ModelPipelineInputKind.extraction_context,
            output_kind=ModelOutputKind.candidate_metadata,
            payload={},
            metadata="no",
        )


def test_provenance_must_be_dict() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineResult(
            role=ModelPipelineRole.extraction_helper,
            output_kind=ModelOutputKind.candidate_metadata,
            status=ModelPipelineStatus.success,
            payload={},
            warnings=[],
            provenance=None,
        )


def test_result_rejects_is_evidence_true_in_payload() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineResult(
            role=ModelPipelineRole.extraction_helper,
            output_kind=ModelOutputKind.candidate_metadata,
            status=ModelPipelineStatus.success,
            payload={"is_evidence": True},
            warnings=[],
            provenance={"source": "deterministic_test"},
        )


def test_result_rejects_source_fidelity_verbatim_in_payload() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineResult(
            role=ModelPipelineRole.extraction_helper,
            output_kind=ModelOutputKind.candidate_metadata,
            status=ModelPipelineStatus.success,
            payload={"source_fidelity": "verbatim"},
            warnings=[],
            provenance={"source": "deterministic_test"},
        )


def test_result_rejects_source_fidelity_verbatim_in_provenance() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineResult(
            role=ModelPipelineRole.extraction_helper,
            output_kind=ModelOutputKind.candidate_metadata,
            status=ModelPipelineStatus.success,
            payload={},
            warnings=[],
            provenance={"source": "deterministic_test", "source_fidelity": "verbatim"},
        )


def test_result_accepts_candidate_metadata_output_kind() -> None:
    r = ModelPipelineResult(
        role=ModelPipelineRole.artifact_classifier,
        output_kind=ModelOutputKind.candidate_metadata,
        status=ModelPipelineStatus.success,
        payload={"labels": ["a"]},
        warnings=[],
        provenance={"source": "not_configured"},
    )
    assert r.output_kind == ModelOutputKind.candidate_metadata


def test_result_accepts_derived_metadata_output_kind() -> None:
    r = ModelPipelineResult(
        role=ModelPipelineRole.evidence_candidate_enricher,
        output_kind=ModelOutputKind.derived_metadata,
        status=ModelPipelineStatus.success,
        payload={"note": "derived only"},
        warnings=[],
        provenance={"source": "deterministic_test"},
    )
    assert r.output_kind == ModelOutputKind.derived_metadata


def test_module_has_no_forbidden_service_imports() -> None:
    path = Path(mpc.__file__).resolve()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden_modules = frozenset(
        {
            "app.services.file_clerk_service",
            "app.services.retrieval_packet_builder",
            "app.services.route_selection_service",
            "app.services.evidence_selection_service",
            "app.services.text_ingestion_service",
            "app.services.multimodal_ingestion_service",
            "app.services.language_detection_service",
        },
    )
    forbidden_from_app_services = frozenset(
        {
            "file_clerk_service",
            "retrieval_packet_builder",
            "route_selection_service",
            "evidence_selection_service",
            "text_ingestion_service",
            "multimodal_ingestion_service",
            "language_detection_service",
        },
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module in forbidden_modules:
                pytest.fail(f"Forbidden import: from {node.module!r}")
            if node.module == "app.services":
                for alias in node.names:
                    if alias.name in forbidden_from_app_services:
                        pytest.fail(
                            f"Forbidden import: from app.services import {alias.name!r}",
                        )
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in forbidden_modules:
                    pytest.fail(f"Forbidden import: import {alias.name!r}")


def test_contract_module_imports_clean_in_fresh_subprocess() -> None:
    """Ensure importing contracts does not pull heavy model stacks (baseline: stdlib + pydantic only)."""
    code = """
import sys
m = __import__("app.services.model_pipeline_contracts", fromlist=["*"])
# torch / transformers are not required for this slice
for name in ("torch", "transformers", "openai"):
    assert name not in sys.modules
print("ok")
"""
    backend_dir = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend_dir) + os.pathsep + env.get("PYTHONPATH", "")
    import subprocess

    r = subprocess.run(
        [sys.executable, "-c", code],
        cwd=backend_dir,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout


def test_provenance_requires_nonempty_source() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineResult(
            role=ModelPipelineRole.extraction_helper,
            output_kind=ModelOutputKind.candidate_metadata,
            status=ModelPipelineStatus.success,
            payload={},
            warnings=[],
            provenance={},
        )


# --- Slice 8B: request/response envelopes ---


def test_valid_request_envelope_validates() -> None:
    env = ModelPipelineRequestEnvelope(
        request_id="req-1",
        task=_minimal_task(),
        metadata={"client": "test"},
        trace={"span": "a"},
    )
    assert env.request_id == "req-1"
    assert env.schema_version == SCHEMA_VERSION_PHASE8_V1
    assert env.task.role == ModelPipelineRole.extraction_helper


def test_request_id_is_stripped_and_nonempty() -> None:
    env = ModelPipelineRequestEnvelope(request_id="  rid-42  ", task=_minimal_task())
    assert env.request_id == "rid-42"
    with pytest.raises(ValidationError):
        ModelPipelineRequestEnvelope(request_id="   ", task=_minimal_task())
    with pytest.raises(ValidationError):
        ModelPipelineRequestEnvelope(request_id="", task=_minimal_task())


def test_request_metadata_and_trace_must_be_dicts() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineRequestEnvelope(request_id="x", task=_minimal_task(), metadata=[])
    with pytest.raises(ValidationError):
        ModelPipelineRequestEnvelope(request_id="x", task=_minimal_task(), trace="nope")


def test_valid_success_response_envelope() -> None:
    res = _success_result()
    env = ModelPipelineResponseEnvelope(
        request_id="req-1",
        status=ModelPipelineStatus.success,
        result=res,
        error=None,
        warnings=["note"],
        metadata={"k": 1},
    )
    assert env.status == ModelPipelineStatus.success
    assert env.error is None
    assert env.result is not None
    assert env.result.status == ModelPipelineStatus.success


def test_success_response_rejects_missing_result() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineResponseEnvelope(
            request_id="r",
            status=ModelPipelineStatus.success,
            result=None,
            error=None,
        )


def test_success_response_rejects_error_present() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineResponseEnvelope(
            request_id="r",
            status=ModelPipelineStatus.success,
            result=_success_result(),
            error=ModelPipelineError(code="E", message="m"),
        )


def test_non_success_response_requires_error_and_no_result() -> None:
    for st in (
        ModelPipelineStatus.rejected,
        ModelPipelineStatus.unavailable,
        ModelPipelineStatus.error,
    ):
        env = ModelPipelineResponseEnvelope(
            request_id="r1",
            status=st,
            result=None,
            error=ModelPipelineError(code="c", message="msg"),
        )
        assert env.result is None
        assert env.error is not None

    with pytest.raises(ValidationError):
        ModelPipelineResponseEnvelope(
            request_id="r",
            status=ModelPipelineStatus.rejected,
            result=None,
            error=None,
        )
    with pytest.raises(ValidationError):
        ModelPipelineResponseEnvelope(
            request_id="r",
            status=ModelPipelineStatus.unavailable,
            result=_success_result(),
            error=ModelPipelineError(code="c", message="m"),
        )


def test_response_status_must_match_result_status_when_result_present() -> None:
    bad = _success_result(status=ModelPipelineStatus.rejected)
    with pytest.raises(ValidationError):
        ModelPipelineResponseEnvelope(
            request_id="r",
            status=ModelPipelineStatus.success,
            result=bad,
            error=None,
        )


def test_error_code_and_message_nonempty() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineError(code="", message="x")
    with pytest.raises(ValidationError):
        ModelPipelineError(code="c", message="   ")


def test_error_details_must_be_dict() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineError(code="c", message="m", details=[])


def test_error_details_reject_is_evidence_true() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineError(code="c", message="m", details={"is_evidence": True})


def test_error_details_reject_source_fidelity_verbatim() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineError(code="c", message="m", details={"source_fidelity": "verbatim"})


def test_response_warnings_must_be_list_str() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineResponseEnvelope(
            request_id="r",
            status=ModelPipelineStatus.success,
            result=_success_result(),
            warnings=[1],
        )


def test_schema_version_nonempty_on_envelopes() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineRequestEnvelope(request_id="x", task=_minimal_task(), schema_version="")
    with pytest.raises(ValidationError):
        ModelPipelineResponseEnvelope(
            request_id="x",
            status=ModelPipelineStatus.success,
            result=_success_result(),
            schema_version="   ",
        )


def test_response_metadata_rejects_top_level_truth_claims() -> None:
    with pytest.raises(ValidationError):
        ModelPipelineResponseEnvelope(
            request_id="r",
            status=ModelPipelineStatus.success,
            result=_success_result(),
            metadata={"is_evidence": True},
        )


# --- Slice 8C: adapter protocol + NotConfigured + deterministic test adapter ---


def test_model_pipeline_adapter_protocol_runtime_checkable() -> None:
    assert isinstance(NotConfiguredModelPipelineAdapter(), ModelPipelineAdapter)
    assert isinstance(DeterministicTestModelPipelineAdapter(result=_success_result()), ModelPipelineAdapter)


def test_not_configured_adapter_returns_unavailable_envelope() -> None:
    req = _request_envelope(request_id="corr-1")
    out = NotConfiguredModelPipelineAdapter().run(req)
    assert out.status == ModelPipelineStatus.unavailable
    assert out.result is None
    assert out.error is not None
    assert out.error.code == MODEL_PIPELINE_NOT_CONFIGURED_CODE
    assert out.error.retryable is False
    assert MODEL_PIPELINE_NOT_CONFIGURED_CODE in out.warnings


def test_not_configured_adapter_preserves_request_id_and_schema_version() -> None:
    req = _request_envelope(request_id="  keep-me  ", schema_version="phase8.v1")
    out = NotConfiguredModelPipelineAdapter().run(req)
    assert out.request_id == "keep-me"
    assert out.schema_version == req.schema_version


def test_not_configured_adapter_does_not_fake_success() -> None:
    out = NotConfiguredModelPipelineAdapter().run(_request_envelope())
    assert out.status != ModelPipelineStatus.success
    assert out.result is None


def test_deterministic_test_adapter_returns_success_envelope() -> None:
    req = _request_envelope(request_id="t-1")
    out = DeterministicTestModelPipelineAdapter(result=_success_result()).run(req)
    assert out.status == ModelPipelineStatus.success
    assert out.error is None
    assert out.result is not None
    assert out.result.status == ModelPipelineStatus.success


def test_deterministic_test_adapter_preserves_request_id() -> None:
    req = _request_envelope(request_id="preserve-me")
    out = DeterministicTestModelPipelineAdapter(result=_success_result()).run(req)
    assert out.request_id == "preserve-me"


def test_deterministic_test_adapter_result_status_matches_envelope() -> None:
    req = _request_envelope()
    out = DeterministicTestModelPipelineAdapter(result=_success_result()).run(req)
    assert out.result is not None
    assert out.result.status == out.status == ModelPipelineStatus.success


def test_deterministic_test_adapter_does_not_mutate_request_envelope() -> None:
    req = _request_envelope(
        request_id="immutable",
        metadata={"n": 1},
        trace={"span": "x"},
    )
    before = req.model_dump(mode="json")
    DeterministicTestModelPipelineAdapter(result=_success_result()).run(req)
    assert req.model_dump(mode="json") == before


def test_deterministic_test_adapter_factory_mode() -> None:
    def _factory(ev: ModelPipelineRequestEnvelope) -> ModelPipelineResult:
        assert ev.request_id == "factory-req"
        return _success_result()

    req = _request_envelope(request_id="factory-req")
    out = DeterministicTestModelPipelineAdapter(factory=_factory).run(req)
    assert out.status == ModelPipelineStatus.success
    assert out.result is not None


def test_deterministic_test_adapter_rejects_both_result_and_factory() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        DeterministicTestModelPipelineAdapter(
            result=_success_result(),
            factory=lambda e: _success_result(),
        )


def test_deterministic_test_adapter_rejects_neither_result_nor_factory() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        DeterministicTestModelPipelineAdapter()


def test_deterministic_test_adapter_rejects_non_success_result_template() -> None:
    bad = ModelPipelineResult(
        role=ModelPipelineRole.extraction_helper,
        output_kind=ModelOutputKind.candidate_metadata,
        status=ModelPipelineStatus.rejected,
        payload={},
        warnings=[],
        provenance={"source": "deterministic_test"},
    )
    with pytest.raises(ValueError, match="success"):
        DeterministicTestModelPipelineAdapter(result=bad).run(_request_envelope())


def test_deterministic_test_adapter_rejects_role_mismatch() -> None:
    bad = _success_result(role=ModelPipelineRole.artifact_classifier)
    with pytest.raises(ValueError, match="role/output_kind"):
        DeterministicTestModelPipelineAdapter(result=bad).run(_request_envelope())


def test_deterministic_test_adapter_rejects_wrong_provenance_source() -> None:
    bad = _success_result(provenance={"source": "not_configured"})
    with pytest.raises(ValueError, match="deterministic_test"):
        DeterministicTestModelPipelineAdapter(result=bad).run(_request_envelope())
