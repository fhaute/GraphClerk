"""Track D Slice D5 — metadata enrichment orchestration (no ingestion wiring)."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.models.enums import Modality, SourceFidelity
from app.schemas.evidence_unit_candidate import EvidenceUnitCandidate
from app.services.model_pipeline_candidate_projection_service import (
    GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY,
    ModelPipelineCandidateMetadataProjectionService,
)
from app.services.model_pipeline_contracts import (
    MODEL_PIPELINE_NOT_CONFIGURED_CODE,
    DeterministicTestModelPipelineAdapter,
    ModelOutputKind,
    ModelPipelineError,
    ModelPipelineInputKind,
    ModelPipelineRequestEnvelope,
    ModelPipelineResponseEnvelope,
    ModelPipelineResult,
    ModelPipelineRole,
    ModelPipelineStatus,
    NotConfiguredModelPipelineAdapter,
)
from app.services.model_pipeline_metadata_enrichment_service import (
    CODE_ADAPTER_EXCEPTION,
    CODE_PROJECTION_NONE,
    ModelPipelineMetadataEnrichmentService,
)
from app.services.model_pipeline_output_validation_service import (
    ModelPipelineOutputValidationService,
)
from app.services.model_pipeline_purpose_registry import ModelPipelinePurposeResolution


def _enabled_resolution(
    *,
    output_kind: ModelOutputKind = ModelOutputKind.derived_metadata,
) -> ModelPipelinePurposeResolution:
    return ModelPipelinePurposeResolution(
        purpose=ModelPipelineRole.evidence_candidate_enricher,
        disabled=False,
        role=ModelPipelineRole.evidence_candidate_enricher,
        input_kind=ModelPipelineInputKind.extraction_context,
        output_kind=output_kind,
        adapter="ollama",
        model="llama3.1:8b",
        timeout_seconds=30.0,
        base_url="http://127.0.0.1:11434",
    )


def _disabled_resolution() -> ModelPipelinePurposeResolution:
    return ModelPipelinePurposeResolution(
        purpose=ModelPipelineRole.evidence_candidate_enricher,
        disabled=True,
        role=None,
        input_kind=None,
        output_kind=None,
        adapter=None,
        model=None,
        timeout_seconds=None,
        base_url=None,
    )


def _candidate(**kwargs: Any) -> EvidenceUnitCandidate:
    base: dict[str, Any] = {
        "modality": Modality.text,
        "content_type": "text/plain",
        "text": "hello world",
        "location": {"line": 1},
        "source_fidelity": SourceFidelity.verbatim,
        "confidence": 0.9,
        "metadata": None,
    }
    base.update(kwargs)
    return EvidenceUnitCandidate(**base)


def _factory_success_payload(payload: dict[str, Any]):
    def _fn(envelope: ModelPipelineRequestEnvelope) -> ModelPipelineResult:
        return ModelPipelineResult(
            role=envelope.task.role,
            output_kind=envelope.task.output_kind,
            status=ModelPipelineStatus.success,
            payload=payload,
            warnings=[],
            provenance={"source": "deterministic_test", "run": envelope.request_id},
        )

    return _fn


class _CaptureAdapter:
    __slots__ = ("_inner", "calls")

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.calls: list[ModelPipelineRequestEnvelope] = []

    def run(self, envelope: ModelPipelineRequestEnvelope) -> ModelPipelineResponseEnvelope:
        self.calls.append(envelope)
        return self._inner.run(envelope)


class _RaisingAdapter:
    __slots__ = ()

    def run(self, envelope: ModelPipelineRequestEnvelope) -> ModelPipelineResponseEnvelope:
        raise RuntimeError("simulated adapter fault")


def test_disabled_purpose_returns_unchanged_without_adapter_calls() -> None:
    capture = _CaptureAdapter(NotConfiguredModelPipelineAdapter())
    svc = ModelPipelineMetadataEnrichmentService(
        adapter=capture,
        output_validator=ModelPipelineOutputValidationService(),
        projection_service=ModelPipelineCandidateMetadataProjectionService(),
    )
    c0 = _candidate(text="a")
    c1 = _candidate(text="b")
    res = svc.enrich_candidates(candidates=[c0, c1], purpose_resolution=_disabled_resolution())
    assert res.candidates == [c0, c1]
    assert res.candidates[0] is c0
    assert res.attempted_count == 0
    assert res.skipped_count == 2
    assert res.projected_count == 0
    assert res.failed_count == 0
    assert res.warnings == []
    assert capture.calls == []


def test_enabled_calls_adapter_once_per_candidate_with_stable_request_ids() -> None:
    inner = DeterministicTestModelPipelineAdapter(factory=_factory_success_payload({"k": 1}))
    capture = _CaptureAdapter(inner)
    svc = ModelPipelineMetadataEnrichmentService(
        adapter=capture,
        output_validator=ModelPipelineOutputValidationService(),
        projection_service=ModelPipelineCandidateMetadataProjectionService(),
    )
    c0 = _candidate(text="one")
    c1 = _candidate(text="two")
    svc.enrich_candidates(
        candidates=[c0, c1],
        purpose_resolution=_enabled_resolution(),
        request_id_prefix="mp-test",
    )
    assert len(capture.calls) == 2
    assert capture.calls[0].request_id == "mp-test-0"
    assert capture.calls[1].request_id == "mp-test-1"
    assert capture.calls[0].task.payload["text"] == "one"
    assert capture.calls[1].task.payload["text"] == "two"


def test_success_merges_graphclerk_model_pipeline_and_preserves_other_metadata() -> None:
    inner = DeterministicTestModelPipelineAdapter(
        factory=_factory_success_payload({"labels": ["x"], "hints": ["h"]}),
    )
    svc = ModelPipelineMetadataEnrichmentService(
        adapter=inner,
        output_validator=ModelPipelineOutputValidationService(),
        projection_service=ModelPipelineCandidateMetadataProjectionService(),
    )
    orig_meta = {"language": "en", "other": {"nested": True}}
    cand = _candidate(metadata=orig_meta)
    res = svc.enrich_candidates(candidates=[cand], purpose_resolution=_enabled_resolution())
    assert res.projected_count == 1
    assert res.failed_count == 0
    out = res.candidates[0]
    assert out.metadata is not None
    assert out.metadata["language"] == "en"
    assert out.metadata["other"] == {"nested": True}
    inner_mp = out.metadata[GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY]
    assert inner_mp["proposed"] == {"labels": ["x"], "hints": ["h"]}
    assert inner_mp["status"] == ModelPipelineStatus.success


def test_existing_graphclerk_model_pipeline_replaced() -> None:
    inner = DeterministicTestModelPipelineAdapter(factory=_factory_success_payload({"v": 2}))
    svc = ModelPipelineMetadataEnrichmentService(
        adapter=inner,
        output_validator=ModelPipelineOutputValidationService(),
        projection_service=ModelPipelineCandidateMetadataProjectionService(),
    )
    old_inner = {"schema_version": "old", "stale": True}
    cand = _candidate(metadata={"keep": 1, GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY: old_inner})
    res = svc.enrich_candidates(candidates=[cand], purpose_resolution=_enabled_resolution())
    out = res.candidates[0]
    assert out.metadata is not None
    assert out.metadata["keep"] == 1
    new_inner = out.metadata[GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY]
    assert "stale" not in new_inner
    assert new_inner["proposed"] == {"v": 2}


def test_text_and_source_fidelity_unchanged() -> None:
    inner = DeterministicTestModelPipelineAdapter(factory=_factory_success_payload({}))
    svc = ModelPipelineMetadataEnrichmentService(
        adapter=inner,
        output_validator=ModelPipelineOutputValidationService(),
        projection_service=ModelPipelineCandidateMetadataProjectionService(),
    )
    cand = _candidate(text="immutable text", source_fidelity=SourceFidelity.extracted)
    res = svc.enrich_candidates(candidates=[cand], purpose_resolution=_enabled_resolution())
    out = res.candidates[0]
    assert out.text == cand.text
    assert out.source_fidelity == cand.source_fidelity


def test_original_candidate_metadata_dict_not_mutated() -> None:
    inner = DeterministicTestModelPipelineAdapter(factory=_factory_success_payload({"z": 3}))
    svc = ModelPipelineMetadataEnrichmentService(
        adapter=inner,
        output_validator=ModelPipelineOutputValidationService(),
        projection_service=ModelPipelineCandidateMetadataProjectionService(),
    )
    meta = {"before": "yes"}
    cand = _candidate(metadata=meta)
    res = svc.enrich_candidates(candidates=[cand], purpose_resolution=_enabled_resolution())
    assert meta == {"before": "yes"}
    assert GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY not in meta
    assert res.candidates[0].metadata is not None
    assert GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY in res.candidates[0].metadata


def test_adapter_non_success_no_merge_counts_failed() -> None:
    svc = ModelPipelineMetadataEnrichmentService(
        adapter=NotConfiguredModelPipelineAdapter(),
        output_validator=ModelPipelineOutputValidationService(),
        projection_service=ModelPipelineCandidateMetadataProjectionService(),
    )
    cand = _candidate(metadata={"x": 1})
    res = svc.enrich_candidates(candidates=[cand], purpose_resolution=_enabled_resolution())
    assert res.failed_count == 1
    assert res.projected_count == 0
    assert res.candidates[0] is cand
    assert MODEL_PIPELINE_NOT_CONFIGURED_CODE in res.warnings


def test_adapter_exception_no_merge_warning_code() -> None:
    svc = ModelPipelineMetadataEnrichmentService(
        adapter=_RaisingAdapter(),
        output_validator=ModelPipelineOutputValidationService(),
        projection_service=ModelPipelineCandidateMetadataProjectionService(),
    )
    cand = _candidate()
    res = svc.enrich_candidates(candidates=[cand], purpose_resolution=_enabled_resolution())
    assert res.failed_count == 1
    assert res.candidates[0] is cand
    assert CODE_ADAPTER_EXCEPTION in res.warnings


def test_validation_failure_no_merge_issue_codes_in_warnings() -> None:
    def _bad(envelope: ModelPipelineRequestEnvelope) -> ModelPipelineResult:
        return ModelPipelineResult(
            role=envelope.task.role,
            output_kind=envelope.task.output_kind,
            status=ModelPipelineStatus.success,
            payload={"nested": {"is_evidence": True}},
            warnings=[],
            provenance={"source": "deterministic_test", "run": envelope.request_id},
        )

    inner = DeterministicTestModelPipelineAdapter(factory=_bad)
    svc = ModelPipelineMetadataEnrichmentService(
        adapter=inner,
        output_validator=ModelPipelineOutputValidationService(),
        projection_service=ModelPipelineCandidateMetadataProjectionService(),
    )
    cand = _candidate(metadata=None)
    res = svc.enrich_candidates(candidates=[cand], purpose_resolution=_enabled_resolution())
    assert res.failed_count == 1
    assert res.candidates[0] is cand
    assert "nested_is_evidence_true" in res.warnings


def test_projection_none_path_emits_projection_warning_when_success_but_merge_impossible() -> None:
    """Malformed projection dict (missing namespace key) yields no merge and a stable warning."""

    proj = MagicMock(spec=ModelPipelineCandidateMetadataProjectionService)
    proj.project.return_value = {"wrong_key": {}}

    inner = DeterministicTestModelPipelineAdapter(factory=_factory_success_payload({"ok": True}))
    svc = ModelPipelineMetadataEnrichmentService(
        adapter=inner,
        output_validator=ModelPipelineOutputValidationService(),
        projection_service=proj,
    )
    cand = _candidate()
    res = svc.enrich_candidates(candidates=[cand], purpose_resolution=_enabled_resolution())
    assert res.failed_count == 1
    assert res.candidates[0] is cand
    assert CODE_PROJECTION_NONE in res.warnings


def test_multiple_candidates_preserve_order() -> None:
    calls: list[str] = []

    def _factory(envelope: ModelPipelineRequestEnvelope) -> ModelPipelineResult:
        calls.append(envelope.task.payload["text"])
        return ModelPipelineResult(
            role=envelope.task.role,
            output_kind=envelope.task.output_kind,
            status=ModelPipelineStatus.success,
            payload={"i": envelope.task.payload["candidate_index"]},
            warnings=[],
            provenance={"source": "deterministic_test", "run": envelope.request_id},
        )

    inner = DeterministicTestModelPipelineAdapter(factory=_factory)
    svc = ModelPipelineMetadataEnrichmentService(
        adapter=inner,
        output_validator=ModelPipelineOutputValidationService(),
        projection_service=ModelPipelineCandidateMetadataProjectionService(),
    )
    a = _candidate(text="first")
    b = _candidate(text="second")
    c = _candidate(text="third")
    res = svc.enrich_candidates(candidates=[a, b, c], purpose_resolution=_enabled_resolution())
    assert calls == ["first", "second", "third"]
    assert [x.text for x in res.candidates] == ["first", "second", "third"]


def test_service_module_does_not_import_forbidden_areas() -> None:
    svc_dir = Path(__file__).resolve().parents[1] / "app" / "services"
    path = svc_dir / "model_pipeline_metadata_enrichment_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    banned = (
        "file_clerk",
        "retrieval_packet",
        "evidence_selection",
        "text_ingestion",
        "multimodal_ingestion",
        "evidence_enrichment",
    )
    mod_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod_names.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mod_names.append(node.module)
    joined = " ".join(mod_names)
    for fragment in banned:
        assert fragment not in joined


def test_success_payload_does_not_use_answer_like_keys() -> None:
    inner = DeterministicTestModelPipelineAdapter(
        factory=_factory_success_payload({"note": "meta"}),
    )
    svc = ModelPipelineMetadataEnrichmentService(
        adapter=inner,
        output_validator=ModelPipelineOutputValidationService(),
        projection_service=ModelPipelineCandidateMetadataProjectionService(),
    )
    res = svc.enrich_candidates(candidates=[_candidate()], purpose_resolution=_enabled_resolution())
    blob = res.candidates[0].metadata[GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY]["proposed"]
    assert "answer" not in blob
    assert "final_answer" not in blob


def test_enabled_resolution_missing_role_raises() -> None:
    bad = ModelPipelinePurposeResolution(
        purpose=ModelPipelineRole.evidence_candidate_enricher,
        disabled=False,
        role=None,
        input_kind=ModelPipelineInputKind.extraction_context,
        output_kind=ModelOutputKind.derived_metadata,
        adapter="ollama",
        model="m",
        timeout_seconds=1.0,
        base_url="http://x",
    )
    svc = ModelPipelineMetadataEnrichmentService(
        adapter=DeterministicTestModelPipelineAdapter(factory=_factory_success_payload({})),
        output_validator=ModelPipelineOutputValidationService(),
        projection_service=ModelPipelineCandidateMetadataProjectionService(),
    )
    with pytest.raises(ValueError, match="requires role"):
        svc.enrich_candidates(candidates=[_candidate()], purpose_resolution=bad)


def test_non_success_includes_error_code_from_response() -> None:
    class _FixedErrorAdapter:
        __slots__ = ()

        def run(self, envelope: ModelPipelineRequestEnvelope) -> ModelPipelineResponseEnvelope:
            err = ModelPipelineError(
                code="custom_pipeline_err",
                message="bad",
                retryable=False,
                details={"source": "test"},
            )
            return ModelPipelineResponseEnvelope(
                request_id=envelope.request_id,
                status=ModelPipelineStatus.error,
                result=None,
                error=err,
                warnings=[],
                schema_version=envelope.schema_version,
            )

    svc = ModelPipelineMetadataEnrichmentService(
        adapter=_FixedErrorAdapter(),
        output_validator=ModelPipelineOutputValidationService(),
        projection_service=ModelPipelineCandidateMetadataProjectionService(),
    )
    cand = _candidate()
    res = svc.enrich_candidates(candidates=[cand], purpose_resolution=_enabled_resolution())
    assert res.failed_count == 1
    assert "custom_pipeline_err" in res.warnings
