"""Track D Slice D5 — model pipeline metadata enrichment (orchestration only).

Builds replacement :class:`~app.schemas.evidence_unit_candidate.EvidenceUnitCandidate`
values that may add or replace the ``graphclerk_model_pipeline`` metadata subtree.

Does not call ingestion, enrichment, FileClerk, retrieval, or persistence; does not
mutate ``text`` or ``source_fidelity``; does not read global settings.
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any

from app.schemas.evidence_unit_candidate import EvidenceUnitCandidate
from app.services.model_pipeline_candidate_projection_service import (
    GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY,
    ModelPipelineCandidateMetadataProjectionService,
)
from app.services.model_pipeline_contracts import (
    ModelPipelineAdapter,
    ModelPipelineRequestEnvelope,
    ModelPipelineStatus,
    ModelPipelineTask,
)
from app.services.model_pipeline_output_validation_service import (
    ModelPipelineOutputValidationService,
)

if TYPE_CHECKING:
    from app.services.model_pipeline_purpose_registry import ModelPipelinePurposeResolution


CODE_ADAPTER_EXCEPTION = "model_pipeline_adapter_exception"
CODE_NON_SUCCESS = "model_pipeline_non_success"
CODE_PROJECTION_NONE = "model_pipeline_projection_none"


@dataclass
class ModelPipelineMetadataEnrichmentResult:
    """Aggregate outcome of a candidate enrichment pass (for future D6 wiring)."""

    candidates: list[EvidenceUnitCandidate]
    attempted_count: int = 0
    projected_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    warnings: list[str] = field(default_factory=list)


class ModelPipelineMetadataEnrichmentService:
    """Run validate → project → merge for each candidate when purpose resolution is enabled."""

    __slots__ = ("_adapter", "_output_validator", "_projection_service")

    def __init__(
        self,
        *,
        adapter: ModelPipelineAdapter,
        output_validator: ModelPipelineOutputValidationService,
        projection_service: ModelPipelineCandidateMetadataProjectionService,
    ) -> None:
        self._adapter = adapter
        self._output_validator = output_validator
        self._projection_service = projection_service

    def enrich_candidates(
        self,
        *,
        candidates: Sequence[EvidenceUnitCandidate],
        purpose_resolution: ModelPipelinePurposeResolution,
        request_id_prefix: str = "model-pipeline",
    ) -> ModelPipelineMetadataEnrichmentResult:
        """Return enriched candidates and counts.

        Does not mutate the input sequence or original ``metadata`` dicts.
        """

        if purpose_resolution.disabled:
            return ModelPipelineMetadataEnrichmentResult(
                candidates=list(candidates),
                attempted_count=0,
                projected_count=0,
                skipped_count=len(candidates),
                failed_count=0,
                warnings=[],
            )

        role = purpose_resolution.role
        input_kind = purpose_resolution.input_kind
        output_kind = purpose_resolution.output_kind
        if role is None or input_kind is None or output_kind is None:
            msg = "enabled purpose_resolution requires role, input_kind, and output_kind"
            raise ValueError(msg)

        warnings_acc: list[str] = []
        out_rows: list[EvidenceUnitCandidate] = []
        attempted = 0
        projected = 0
        failed = 0

        prefix = request_id_prefix.strip()
        if not prefix:
            msg = "request_id_prefix must be non-empty"
            raise ValueError(msg)

        for index, candidate in enumerate(candidates):
            attempted += 1
            request_id = f"{prefix}-{index}"
            task_payload = _safe_task_payload(candidate=candidate, candidate_index=index)
            task = ModelPipelineTask(
                role=role,
                input_kind=input_kind,
                output_kind=output_kind,
                payload=task_payload,
                metadata={},
            )
            envelope = ModelPipelineRequestEnvelope(request_id=request_id, task=task)

            try:
                response = self._adapter.run(envelope)
            except Exception:
                failed += 1
                warnings_acc.append(CODE_ADAPTER_EXCEPTION)
                out_rows.append(candidate)
                continue

            validation = self._output_validator.validate_response(response)
            projection = self._projection_service.project(response, validation)
            merged = None
            if projection is not None:
                merged = _merge_model_pipeline_metadata(candidate, projection)

            if merged is not None:
                projected += 1
                out_rows.append(merged)
                continue

            failed += 1
            if not validation.ok:
                warnings_acc.extend(issue.code for issue in validation.issues)
            elif response.status != ModelPipelineStatus.success:
                if response.error is not None:
                    warnings_acc.append(response.error.code)
                else:
                    warnings_acc.append(CODE_NON_SUCCESS)
            else:
                warnings_acc.append(CODE_PROJECTION_NONE)

            out_rows.append(candidate)

        return ModelPipelineMetadataEnrichmentResult(
            candidates=out_rows,
            attempted_count=attempted,
            projected_count=projected,
            skipped_count=0,
            failed_count=failed,
            warnings=warnings_acc,
        )


def _safe_task_payload(*, candidate: EvidenceUnitCandidate, candidate_index: int) -> dict[str, Any]:
    """Build ``ModelPipelineTask.payload`` without forbidden top-level truth-claim fields."""

    sf = candidate.source_fidelity
    fidelity_token = sf.value if hasattr(sf, "value") else str(sf)

    meta_copy: dict[str, Any] | None
    if candidate.metadata is None:
        meta_copy = {}
    else:
        meta_copy = copy.deepcopy(candidate.metadata)

    return {
        "text": candidate.text,
        "candidate_index": candidate_index,
        "candidate_context": {
            "modality": candidate.modality.value,
            "content_type": candidate.content_type,
            "source_fidelity": fidelity_token,
            "confidence": candidate.confidence,
            "location": copy.deepcopy(candidate.location),
        },
        "metadata": meta_copy,
    }


def _merge_model_pipeline_metadata(
    candidate: EvidenceUnitCandidate,
    projection: dict[str, Any],
) -> EvidenceUnitCandidate | None:
    """Merge only ``graphclerk_model_pipeline``; return a new candidate or ``None``."""

    if GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY not in projection:
        return None

    subtree = projection.get(GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY)
    base: dict[str, Any]
    if candidate.metadata is None:
        base = {}
    else:
        base = copy.deepcopy(candidate.metadata)

    base[GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY] = copy.deepcopy(subtree)
    return replace(candidate, metadata=base)


__all__ = [
    "CODE_ADAPTER_EXCEPTION",
    "CODE_NON_SUCCESS",
    "CODE_PROJECTION_NONE",
    "ModelPipelineMetadataEnrichmentResult",
    "ModelPipelineMetadataEnrichmentService",
]
