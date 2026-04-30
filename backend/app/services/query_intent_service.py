"""Deterministic query intent classification (Phase 4)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.retrieval_packet import InterpretedIntent


@dataclass(frozen=True)
class QueryIntentResult:
    """Structured intent output prior to packet assembly."""

    intent: InterpretedIntent


class QueryIntentService:
    """Local-first intent classification using simple keyword heuristics."""

    _COMPARE_PAT = re.compile(r"\b(compare|vs\.?|versus|difference between)\b", re.IGNORECASE)
    _LOCATE_PAT = re.compile(r"\b(where|which file|find|locate|path to)\b", re.IGNORECASE)
    _SUMMARIZE_PAT = re.compile(r"\b(summarize|summary|tl;dr|tldr)\b", re.IGNORECASE)
    _DEBUG_PAT = re.compile(r"\b(why does this fail|stack trace|debug|error:|exception)\b", re.IGNORECASE)
    _RECOMMEND_PAT = re.compile(r"\b(should i|what do you recommend|recommend|best practice)\b", re.IGNORECASE)
    _EXPLAIN_PAT = re.compile(r"\b(what is|what are|how does|explain|describe|why)\b", re.IGNORECASE)

    def classify(self, question: str) -> QueryIntentResult:
        """Classify a user question into a controlled intent vocabulary."""

        q = question.strip()
        if q == "":
            return QueryIntentResult(
                intent=InterpretedIntent(intent_type="unknown", confidence=0.0, notes=["empty_question"])
            )

        lowered = q.lower()

        if self._COMPARE_PAT.search(lowered):
            return QueryIntentResult(intent=InterpretedIntent(intent_type="compare", confidence=0.72, notes=[]))
        if self._LOCATE_PAT.search(lowered):
            return QueryIntentResult(intent=InterpretedIntent(intent_type="locate", confidence=0.70, notes=[]))
        if self._SUMMARIZE_PAT.search(lowered):
            return QueryIntentResult(intent=InterpretedIntent(intent_type="summarize", confidence=0.74, notes=[]))
        if self._DEBUG_PAT.search(lowered):
            return QueryIntentResult(intent=InterpretedIntent(intent_type="debug", confidence=0.71, notes=[]))
        if self._RECOMMEND_PAT.search(lowered):
            return QueryIntentResult(intent=InterpretedIntent(intent_type="recommend", confidence=0.69, notes=[]))
        if self._EXPLAIN_PAT.search(lowered):
            return QueryIntentResult(intent=InterpretedIntent(intent_type="explain", confidence=0.78, notes=[]))

        # Default: short questions often seek explanation; very long questions may be exploratory.
        if len(lowered) < 40:
            return QueryIntentResult(intent=InterpretedIntent(intent_type="explain", confidence=0.55, notes=["default_short_question"]))
        return QueryIntentResult(intent=InterpretedIntent(intent_type="unknown", confidence=0.45, notes=["no_keyword_match"]))
