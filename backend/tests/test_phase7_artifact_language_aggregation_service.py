"""Unit tests for ArtifactLanguageAggregationService (Phase 7 Slice 7E)."""

from __future__ import annotations

import pytest

from app.schemas.evidence_unit_candidate import (
    LANGUAGE_METADATA_KEY_LANGUAGE,
    LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE,
)
from app.services.artifact_language_aggregation_service import (
    CONFIDENCE_KEY,
    GRAPHCLERK_LANGUAGE_AGGREGATION_KEY,
    LANGUAGE_KEY,
    WARNING_LANGUAGE_CONFIDENCE_INVALID,
    WARNING_LANGUAGE_CONFIDENCE_MISSING,
    WARNING_LANGUAGE_MISSING_OR_NULL,
    WARNING_NO_LANGUAGE_METADATA,
    ArtifactLanguageAggregationService,
)


def _eu(**kwargs: object) -> dict[str, object]:
    return dict(kwargs)


def test_aggregation_module_keys_match_schema_canonicals() -> None:
    """Aggregation must read the same metadata keys the candidate schema documents."""
    assert LANGUAGE_KEY == LANGUAGE_METADATA_KEY_LANGUAGE
    assert CONFIDENCE_KEY == LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE


def test_single_language_with_confidence_stats() -> None:
    svc = ArtifactLanguageAggregationService()
    ev = [
        _eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 0.8}),
        _eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 1.0}),
        _eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 0.95}),
        _eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 0.9}),
    ]
    out = svc.aggregate(artifact_metadata=None, evidence_metadata_projections=ev)
    agg = out[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]
    assert agg["distinct_language_count"] == 1
    assert agg["primary_language"] == "en"
    assert agg["evidence_units_without_language_metadata_count"] == 0
    assert len(agg["languages"]) == 1
    row = agg["languages"][0]
    assert row["language"] == "en"
    assert row["evidence_unit_count"] == 4
    assert row["average_confidence"] == pytest.approx(0.9125)
    assert row["min_confidence"] == pytest.approx(0.8)
    assert row["max_confidence"] == pytest.approx(1.0)


def test_mixed_languages() -> None:
    svc = ArtifactLanguageAggregationService()
    ev = [
        _eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 0.9}),
        _eu(**{LANGUAGE_KEY: "fr", CONFIDENCE_KEY: 0.85}),
        _eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 0.95}),
    ]
    out = svc.aggregate(artifact_metadata={}, evidence_metadata_projections=ev)
    agg = out[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]
    assert agg["distinct_language_count"] == 2
    langs = {r["language"]: r for r in agg["languages"]}
    assert langs["en"]["evidence_unit_count"] == 2
    assert langs["fr"]["evidence_unit_count"] == 1


def test_primary_language_tie_break_by_count() -> None:
    svc = ArtifactLanguageAggregationService()
    ev = [
        _eu(**{LANGUAGE_KEY: "fr", CONFIDENCE_KEY: 0.99}),
        _eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 0.5}),
        _eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 0.5}),
    ]
    out = svc.aggregate(artifact_metadata=None, evidence_metadata_projections=ev)
    assert out[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]["primary_language"] == "en"


def test_primary_language_tie_break_by_average_confidence() -> None:
    svc = ArtifactLanguageAggregationService()
    ev = [
        _eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 0.5}),
        _eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 0.5}),
        _eu(**{LANGUAGE_KEY: "fr", CONFIDENCE_KEY: 0.91}),
        _eu(**{LANGUAGE_KEY: "fr", CONFIDENCE_KEY: 0.91}),
    ]
    out = svc.aggregate(artifact_metadata=None, evidence_metadata_projections=ev)
    assert out[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]["primary_language"] == "fr"


def test_primary_language_tie_break_lexical() -> None:
    svc = ArtifactLanguageAggregationService()
    ev = [
        _eu(**{LANGUAGE_KEY: "fr", CONFIDENCE_KEY: 0.7}),
        _eu(**{LANGUAGE_KEY: "fr", CONFIDENCE_KEY: 0.7}),
        _eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 0.7}),
        _eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 0.7}),
    ]
    out = svc.aggregate(artifact_metadata=None, evidence_metadata_projections=ev)
    assert out[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]["primary_language"] == "en"


def test_missing_and_null_language_increment_without_metadata_count() -> None:
    svc = ArtifactLanguageAggregationService()
    ev = [
        _eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 1.0}),
        _eu(),
        _eu(**{LANGUAGE_KEY: None}),
        _eu(**{LANGUAGE_KEY: ""}),
        _eu(**{LANGUAGE_KEY: "   "}),
    ]
    out = svc.aggregate(artifact_metadata=None, evidence_metadata_projections=ev)
    agg = out[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]
    assert agg["evidence_units_without_language_metadata_count"] == 4
    assert agg["distinct_language_count"] == 1


def test_invalid_confidence_warning_and_excluded_from_stats() -> None:
    svc = ArtifactLanguageAggregationService()
    ev = [
        _eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 1.5}),
        _eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 0.5}),
    ]
    out = svc.aggregate(artifact_metadata=None, evidence_metadata_projections=ev)
    agg = out[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]
    assert WARNING_LANGUAGE_CONFIDENCE_INVALID in agg["warnings"]
    row = agg["languages"][0]
    assert row["evidence_unit_count"] == 2
    assert row["average_confidence"] == pytest.approx(0.5)
    assert row["min_confidence"] == pytest.approx(0.5)
    assert row["max_confidence"] == pytest.approx(0.5)


def test_bool_confidence_invalid() -> None:
    svc = ArtifactLanguageAggregationService()
    ev = [_eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: True})]  # type: ignore[arg-type]
    out = svc.aggregate(artifact_metadata=None, evidence_metadata_projections=ev)
    assert WARNING_LANGUAGE_CONFIDENCE_INVALID in out[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]["warnings"]
    row = out[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]["languages"][0]
    assert row["average_confidence"] is None


def test_missing_confidence_warning_when_language_present() -> None:
    svc = ArtifactLanguageAggregationService()
    ev = [_eu(**{LANGUAGE_KEY: "de"})]
    out = svc.aggregate(artifact_metadata=None, evidence_metadata_projections=ev)
    agg = out[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]
    assert WARNING_LANGUAGE_CONFIDENCE_MISSING in agg["warnings"]
    row = agg["languages"][0]
    assert row["evidence_unit_count"] == 1
    assert row["average_confidence"] is None
    assert row["min_confidence"] is None
    assert row["max_confidence"] is None


def test_explicit_none_confidence_missing() -> None:
    svc = ArtifactLanguageAggregationService()
    ev = [_eu(**{LANGUAGE_KEY: "de", CONFIDENCE_KEY: None})]
    out = svc.aggregate(artifact_metadata=None, evidence_metadata_projections=ev)
    assert WARNING_LANGUAGE_CONFIDENCE_MISSING in out[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]["warnings"]


def test_no_language_metadata_empty_evidence() -> None:
    svc = ArtifactLanguageAggregationService()
    out = svc.aggregate(artifact_metadata=None, evidence_metadata_projections=[])
    agg = out[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]
    assert agg["languages"] == []
    assert agg["primary_language"] is None
    assert agg["distinct_language_count"] == 0
    assert agg["evidence_units_without_language_metadata_count"] == 0
    assert WARNING_NO_LANGUAGE_METADATA in agg["warnings"]


def test_no_language_metadata_all_rows_bad() -> None:
    svc = ArtifactLanguageAggregationService()
    ev = [_eu(), _eu(**{LANGUAGE_KEY: None})]
    out = svc.aggregate(artifact_metadata=None, evidence_metadata_projections=ev)
    agg = out[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]
    assert agg["languages"] == []
    assert WARNING_NO_LANGUAGE_METADATA in agg["warnings"]
    assert WARNING_LANGUAGE_MISSING_OR_NULL in agg["warnings"]
    assert agg["evidence_units_without_language_metadata_count"] == 2


def test_preserves_unrelated_artifact_metadata_keys() -> None:
    svc = ArtifactLanguageAggregationService()
    meta = {"user_note": "keep-me", "pages": 3}
    out = svc.aggregate(
        artifact_metadata=meta,
        evidence_metadata_projections=[_eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 1.0})],
    )
    assert out["user_note"] == "keep-me"
    assert out["pages"] == 3


def test_replaces_only_graphclerk_subtree() -> None:
    svc = ArtifactLanguageAggregationService()
    old_sub = {"version": 0, "legacy": True}
    meta = {"keep": 1, GRAPHCLERK_LANGUAGE_AGGREGATION_KEY: old_sub}
    out = svc.aggregate(
        artifact_metadata=meta,
        evidence_metadata_projections=[_eu(**{LANGUAGE_KEY: "es", CONFIDENCE_KEY: 0.8})],
    )
    assert out["keep"] == 1
    new_sub = out[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]
    assert new_sub["version"] == 1
    assert "legacy" not in new_sub


def test_does_not_mutate_input_artifact_metadata() -> None:
    svc = ArtifactLanguageAggregationService()
    meta = {"x": 1}
    meta_copy = dict(meta)
    svc.aggregate(
        artifact_metadata=meta,
        evidence_metadata_projections=[_eu(**{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 1.0})],
    )
    assert meta == meta_copy
    assert GRAPHCLERK_LANGUAGE_AGGREGATION_KEY not in meta


def test_does_not_mutate_evidence_projections() -> None:
    svc = ArtifactLanguageAggregationService()
    ev = [{LANGUAGE_KEY: "en", CONFIDENCE_KEY: 0.5, "extra": [1, 2]}]
    ev_before = {k: (list(v) if k == "extra" else v) for k, v in ev[0].items()}
    svc.aggregate(artifact_metadata=None, evidence_metadata_projections=ev)
    assert ev[0][LANGUAGE_KEY] == ev_before[LANGUAGE_KEY]
    assert ev[0][CONFIDENCE_KEY] == ev_before[CONFIDENCE_KEY]
    assert ev[0]["extra"] == [1, 2]


def test_language_string_trimmed_for_bucket() -> None:
    svc = ArtifactLanguageAggregationService()
    ev = [_eu(**{LANGUAGE_KEY: "  en  ", CONFIDENCE_KEY: 1.0})]
    out = svc.aggregate(artifact_metadata=None, evidence_metadata_projections=ev)
    assert out[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]["languages"][0]["language"] == "en"


def test_non_string_language_counts_as_without_metadata() -> None:
    svc = ArtifactLanguageAggregationService()
    ev = [_eu(**{LANGUAGE_KEY: 404})]  # type: ignore[arg-type]
    agg = svc.aggregate(artifact_metadata=None, evidence_metadata_projections=ev)[GRAPHCLERK_LANGUAGE_AGGREGATION_KEY]
    assert agg["evidence_units_without_language_metadata_count"] == 1
    assert WARNING_LANGUAGE_MISSING_OR_NULL in agg["warnings"]
