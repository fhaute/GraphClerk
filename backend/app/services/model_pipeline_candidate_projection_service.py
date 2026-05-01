"""Phase 8 Slice 8E — candidate metadata projection (pure; no ingestion wiring).

Maps a **validated successful** :class:`~app.services.model_pipeline_contracts.ModelPipelineResponseEnvelope`
plus :class:`~app.services.model_pipeline_output_validation_service.ModelPipelineOutputValidationReport`
into a single merge-ready subtree keyed :data:`GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY` for future attachment
under ``EvidenceUnitCandidate.metadata_json``.

This module **does not** call adapters or models, **does not** validate (Slice **8D** owns validation),
**does not** merge into candidates, **does not** touch ingestion, enrichment, FileClerk, retrieval, DB,
or API surfaces. It returns **deep copies** only and never mutates inputs.

Non-negotiable:
    Model output is **not** evidence; ``proposed`` carries pipeline payload copies only; callers must
    not flatten ``proposed`` into first-class evidence fields without separate normalization.
"""

from __future__ import annotations

import copy
from typing import Any

from app.services.model_pipeline_contracts import (
    ModelPipelineResponseEnvelope,
    ModelPipelineStatus,
)
from app.services.model_pipeline_output_validation_service import (
    ModelPipelineOutputValidationReport,
)

GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY: str = "graphclerk_model_pipeline"


class ModelPipelineCandidateMetadataProjectionService:
    """Produce namespaced metadata subtree from pipeline response + validation report."""

    __slots__ = ()

    def project(
        self,
        response: ModelPipelineResponseEnvelope,
        validation: ModelPipelineOutputValidationReport,
    ) -> dict[str, Any] | None:
        """Return ``{ graphclerk_model_pipeline: {...} }`` or ``None`` when projection is disallowed.

        Returns ``None`` when validation failed, envelope is not a clean success shape, or an error
        slot is populated (including pathological ``model_construct`` payloads).
        """

        if not validation.ok:
            return None
        if response.status != ModelPipelineStatus.success:
            return None
        if response.result is None:
            return None
        if response.error is not None:
            return None

        result = response.result
        issues_payload: list[dict[str, Any]] = [
            {
                "code": issue.code,
                "message": issue.message,
                "path": issue.path,
                "severity": issue.severity,
            }
            for issue in validation.issues
        ]

        inner: dict[str, Any] = {
            "schema_version": response.schema_version,
            "model_pipeline_request_id": response.request_id,
            "role": result.role,
            "output_kind": result.output_kind,
            "status": response.status,
            "provenance": copy.deepcopy(result.provenance),
            "validation": {
                "ok": validation.ok,
                "issues": copy.deepcopy(issues_payload),
            },
            "proposed": copy.deepcopy(result.payload),
        }
        return {GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY: inner}
