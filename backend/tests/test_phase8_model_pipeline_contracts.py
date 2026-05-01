"""Phase 8 Slice 8A — model pipeline boundary contracts (no inference, no retrieval)."""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services import model_pipeline_contracts as mpc
from app.services.model_pipeline_contracts import (
    ModelOutputKind,
    ModelPipelineInputKind,
    ModelPipelineResult,
    ModelPipelineRole,
    ModelPipelineStatus,
    ModelPipelineTask,
)


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
