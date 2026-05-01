"""Artifact-level language aggregation from EvidenceUnit metadata projections (Phase 7).

Pure helper: **no database**, **no persistence**, **no ingestion wiring**. Consumes
read-only ``Mapping`` projections shaped like ``EvidenceUnit.metadata_json`` and
returns a **new** artifact ``metadata_json``-style dict with language summaries
under ``graphclerk_language_aggregation``.

Aggregated language is **routing metadata**, not evidence; absence of language
metadata must never be interpreted as a definite natural language.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from app.schemas.evidence_unit_candidate import (
    LANGUAGE_METADATA_KEY_LANGUAGE,
    LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE,
)

# Aliases for readability and stable imports; string values are defined only on the schema module.
LANGUAGE_KEY = LANGUAGE_METADATA_KEY_LANGUAGE
CONFIDENCE_KEY = LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE
GRAPHCLERK_LANGUAGE_AGGREGATION_KEY = "graphclerk_language_aggregation"

WARNING_NO_LANGUAGE_METADATA = "no_language_metadata"
WARNING_LANGUAGE_MISSING_OR_NULL = "language_missing_or_null"
WARNING_LANGUAGE_CONFIDENCE_MISSING = "language_confidence_missing"
WARNING_LANGUAGE_CONFIDENCE_INVALID = "language_confidence_invalid"


class ArtifactLanguageAggregationService:
    """Build ``graphclerk_language_aggregation`` subtree from evidence metadata rows."""

    def aggregate(
        self,
        *,
        artifact_metadata: dict[str, Any] | None,
        evidence_metadata_projections: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Return new artifact metadata with language aggregation merged in.

        Copies ``artifact_metadata`` shallowly, replaces only
        ``graphclerk_language_aggregation``, and leaves sibling keys untouched.
        Does not mutate ``artifact_metadata`` or any evidence mapping.

        Args:
            artifact_metadata: Existing artifact metadata dict or ``None`` (treated as empty).
            evidence_metadata_projections: Sequence of metadata dicts (e.g. EU ``metadata_json``).

        Returns:
            New dict suitable for ``Artifact.metadata_json`` merge by a future caller.
        """

        result: dict[str, Any] = dict(artifact_metadata) if artifact_metadata else {}

        buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "valid_confidences": list[float]()})
        without_language = 0
        warnings: set[str] = set()

        for meta in evidence_metadata_projections:
            lang_raw = meta.get(LANGUAGE_KEY)

            valid_lang = isinstance(lang_raw, str) and lang_raw.strip() != ""
            if not valid_lang:
                without_language += 1
                warnings.add(WARNING_LANGUAGE_MISSING_OR_NULL)
                self._maybe_capture_invalid_confidence(meta, warnings)
                continue

            lang = lang_raw.strip()
            b = buckets[lang]
            b["count"] += 1

            conf_result = self._classify_confidence(meta)
            if conf_result == "missing":
                warnings.add(WARNING_LANGUAGE_CONFIDENCE_MISSING)
            elif conf_result == "invalid":
                warnings.add(WARNING_LANGUAGE_CONFIDENCE_INVALID)
            elif isinstance(conf_result, float):
                b["valid_confidences"].append(conf_result)

        if not buckets:
            warnings.add(WARNING_NO_LANGUAGE_METADATA)

        languages_out = self._build_language_entries(buckets)
        primary = self._primary_language(buckets)

        subtree: dict[str, Any] = {
            "version": 1,
            "source": "evidence_unit_metadata_json",
            "languages": languages_out,
            "primary_language": primary,
            "distinct_language_count": len(buckets),
            "evidence_units_without_language_metadata_count": without_language,
            "warnings": sorted(warnings),
        }

        result[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY] = subtree
        return result

    def _maybe_capture_invalid_confidence(self, meta: Mapping[str, Any], warnings: set[str]) -> None:
        """If a confidence key exists but is malformed, record invalid warning."""

        if CONFIDENCE_KEY not in meta:
            return
        cls = self._classify_confidence_value(meta.get(CONFIDENCE_KEY))
        if cls == "invalid":
            warnings.add(WARNING_LANGUAGE_CONFIDENCE_INVALID)

    def _classify_confidence(self, meta: Mapping[str, Any]) -> float | str:
        """Return float confidence, ``missing``, or ``invalid``."""

        if CONFIDENCE_KEY not in meta:
            return "missing"
        return self._classify_confidence_value(meta.get(CONFIDENCE_KEY))

    @staticmethod
    def _classify_confidence_value(val: Any) -> float | str:
        if val is None:
            return "missing"
        if isinstance(val, bool):
            return "invalid"
        if isinstance(val, (int, float)):
            x = float(val)
            if math.isfinite(x) and 0.0 <= x <= 1.0:
                return x
            return "invalid"
        return "invalid"

    @staticmethod
    def _build_language_entries(buckets: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for lang in sorted(buckets.keys()):
            b = buckets[lang]
            count = b["count"]
            vals: list[float] = b["valid_confidences"]
            if not vals:
                rows.append(
                    {
                        "language": lang,
                        "evidence_unit_count": count,
                        "average_confidence": None,
                        "min_confidence": None,
                        "max_confidence": None,
                    },
                )
                continue
            avg = sum(vals) / len(vals)
            rows.append(
                {
                    "language": lang,
                    "evidence_unit_count": count,
                    "average_confidence": avg,
                    "min_confidence": min(vals),
                    "max_confidence": max(vals),
                },
            )
        return rows

    @staticmethod
    def _primary_language(buckets: dict[str, dict[str, Any]]) -> str | None:
        if not buckets:
            return None

        def avg_component(lang: str) -> float:
            vals: list[float] = buckets[lang]["valid_confidences"]
            if not vals:
                return -1.0
            return sum(vals) / len(vals)

        langs = sorted(
            buckets.keys(),
            key=lambda L: (-buckets[L]["count"], -avg_component(L), L),
        )
        return langs[0]
