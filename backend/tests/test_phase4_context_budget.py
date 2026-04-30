from __future__ import annotations

import uuid

from app.services.context_budget_service import ContextBudgetService
from app.services.evidence_selection_service import EvidenceCandidate


def _c(text: str | None, fid: str = "verbatim") -> EvidenceCandidate:
    return EvidenceCandidate(
        evidence_unit_id=uuid.uuid4(),
        artifact_id=uuid.uuid4(),
        modality="text",
        content_type="paragraph",
        source_fidelity=fid,
        text=text,
        location=None,
        unit_confidence=0.5,
        support_confidence=0.5,
        selection_reason="test",
    )


def test_context_budget_respects_max_evidence_units() -> None:
    svc = ContextBudgetService()
    ranked = [_c("a"), _c("b"), _c("c")]
    out = svc.apply(ranked_evidence=ranked, max_evidence_units=2, max_tokens_estimate=None)
    assert len(out.selected) == 2
    assert out.pruned_count == 1


def test_context_budget_duplicate_support() -> None:
    svc = ContextBudgetService()
    ranked = [_c("same"), _c("same")]
    out = svc.apply(ranked_evidence=ranked, max_evidence_units=8, max_tokens_estimate=None)
    assert len(out.selected) == 1
    assert "duplicate_support" in out.pruning_reasons
