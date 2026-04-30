"""Context budgeting for retrieval packets (Phase 4)."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.evidence_selection_service import EvidenceCandidate


@dataclass(frozen=True)
class ContextBudgetResult:
    """Evidence subset after budgeting plus explicit pruning reasons."""

    selected: list[EvidenceCandidate]
    pruned_count: int
    pruning_reasons: list[str]


class ContextBudgetService:
    """Enforce caps and emit visible pruning reasons."""

    def apply(
        self,
        *,
        ranked_evidence: list[EvidenceCandidate],
        max_evidence_units: int,
        max_tokens_estimate: int | None = None,
    ) -> ContextBudgetResult:
        """Select up to `max_evidence_units` evidence rows in rank order."""

        if max_evidence_units < 1:
            return ContextBudgetResult(selected=[], pruned_count=len(ranked_evidence), pruning_reasons=["exceeds_context_budget"])

        selected: list[EvidenceCandidate] = []
        reasons: list[str] = []
        token_acc = 0

        def est_tokens(text: str | None) -> int:
            if not text:
                return 0
            return max(1, len(text) // 4)

        seen_text: set[str] = set()
        for cand in ranked_evidence:
            if len(selected) >= max_evidence_units:
                reasons.append("exceeds_context_budget")
                continue

            if cand.text:
                norm = cand.text.strip().lower()
                if norm in seen_text and norm != "":
                    reasons.append("duplicate_support")
                    continue
                seen_text.add(norm)

            add_tokens = est_tokens(cand.text)
            if max_tokens_estimate is not None and token_acc + add_tokens > max_tokens_estimate:
                reasons.append("exceeds_context_budget")
                continue

            selected.append(cand)
            token_acc += add_tokens

        pruned = max(0, len(ranked_evidence) - len(selected))
        # Attribute remaining drops coarsely when pruned > 0 after filling capacity.
        if pruned > 0 and len(selected) >= max_evidence_units:
            for _ in range(pruned):
                reasons.append("lower_confidence")

        return ContextBudgetResult(selected=selected, pruned_count=pruned, pruning_reasons=reasons)
