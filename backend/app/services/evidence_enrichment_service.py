"""Evidence enrichment pipeline for ingestion candidates (Phase 7).

Slice 7A introduces ``EvidenceEnrichmentService`` as a **no-op shell**: callers
receive the same candidate instances in order without mutation. Slice 7D wires
this service into ``TextIngestionService`` and ``MultimodalIngestionService``
immediately before ``EvidenceUnitService.create_from_candidates`` (default:
no-op). Track C Slice C4 optionally injects ``LanguageDetectionService`` to add
language routing metadata on ``EvidenceUnitCandidate`` while preserving
``text`` and ``source_fidelity``.

Ownership:
    Extractors produce candidates; enrichment annotates; persistence layers own
    EvidenceUnit creation. This module performs **no** DB I/O, retrieval, or LLM
    calls. Language detection runs **only** when a ``LanguageDetectionService`` is
    injected; there is **no** hidden global detector.

Error semantics:
    Enrichment does **not** fail ingestion on per-candidate detection errors;
    failures are recorded under ``language_warnings``. ``EvidenceEnrichmentEmptiedCandidatesError``
    remains possible only if a future enricher returns an empty list for non-empty input.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from typing import Any, TypeVar

from app.schemas.evidence_unit_candidate import (
    LANGUAGE_METADATA_KEY_LANGUAGE,
    LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE,
    LANGUAGE_METADATA_KEY_LANGUAGE_DETECTION_METHOD,
    LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS,
    EvidenceUnitCandidate,
    validate_optional_language_metadata,
)
from app.services.errors import (
    GraphClerkError,
    LanguageDetectionError,
    LanguageDetectionUnavailableError,
)
from app.services.language_detection_service import (
    LanguageDetectionResult,
    LanguageDetectionService,
)

T = TypeVar("T")


class EvidenceEnrichmentEmptiedCandidatesError(GraphClerkError):
    """Raised when enrichment drops every candidate while the input list was non-empty."""


def _metadata_as_dict(metadata: dict[str, Any] | None) -> dict[str, Any]:
    return dict(metadata) if metadata else {}


def _has_nonempty_language_string(meta: dict[str, Any]) -> bool:
    v = meta.get(LANGUAGE_METADATA_KEY_LANGUAGE)
    return isinstance(v, str) and v.strip() != ""


def _caller_other_language_fields_without_language_string(meta: dict[str, Any]) -> bool:
    """True when caller set confidence/method/warnings but not a usable ``language`` string."""

    if _has_nonempty_language_string(meta):
        return False
    if LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE in meta:
        return True
    if LANGUAGE_METADATA_KEY_LANGUAGE_DETECTION_METHOD in meta:
        return True
    w = meta.get(LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS)
    return isinstance(w, list) and len(w) > 0


def _merge_language_warnings(meta: dict[str, Any], extra: list[str]) -> dict[str, Any]:
    merged = {**meta}
    existing = list(merged.get(LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS, []) or [])
    combined = sorted(set(existing + list(extra)))
    merged[LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS] = combined
    validate_optional_language_metadata(merged)
    return merged


def _apply_detection_result(
    meta: dict[str, Any],
    result: LanguageDetectionResult,
) -> dict[str, Any]:
    merged = {**meta}
    merged[LANGUAGE_METADATA_KEY_LANGUAGE] = result.language
    merged[LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE] = result.confidence
    merged[LANGUAGE_METADATA_KEY_LANGUAGE_DETECTION_METHOD] = result.method
    existing = list(merged.get(LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS, []) or [])
    combined = sorted(set(existing + list(result.warnings)))
    merged[LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS] = combined
    validate_optional_language_metadata(merged)
    return merged


class EvidenceEnrichmentService:
    """Apply enrichment steps to evidence candidates before persistence.

    Default (no ``language_detection``): identity enrichment — same objects, same
    order, no reads or writes of candidate fields.

    With ``language_detection``: for each ``EvidenceUnitCandidate``, may merge
    language metadata from ``LanguageDetectionService.detect`` into a **new**
    candidate via ``dataclasses.replace``. Non-candidates pass through unchanged.

    Forbidden: database access, EvidenceUnit creation, extractors, retrieval,
    mutation of ``text`` or ``source_fidelity``.
    """

    def __init__(self, *, language_detection: LanguageDetectionService | None = None) -> None:
        self._language_detection = language_detection

    def enrich(self, candidates: Sequence[T]) -> list[T]:
        """Return candidates as a list, optionally annotating language metadata.

        Accepts any ``Sequence``. Does not mutate the input sequence object. When
        ``language_detection`` is ``None``, returns ``list(candidates)`` with the
        same element identities as today.

        Language metadata merge (``EvidenceUnitCandidate`` only):

        - If ``metadata`` already has a non-empty ``language`` string, the
          candidate is unchanged (caller wins).
        - If other language keys exist without a usable ``language`` string,
          detection is skipped and ``language_metadata_partial`` is appended to
          ``language_warnings`` (once merged).
        - On ``LanguageDetectionUnavailableError`` (e.g. ``NotConfigured`` adapter),
          ingestion continues with ``language_detection_unavailable`` in warnings.
        - On ``LanguageDetectionError`` or unexpected errors, append
          ``language_detection_failed``.
        - Successful detection merges ``language``, ``language_confidence``,
          ``language_detection_method``, and merges ``language_warnings`` with any
          detector warnings.
        """

        if self._language_detection is None:
            return list(candidates)

        out: list[T] = []
        for item in candidates:
            if not isinstance(item, EvidenceUnitCandidate):
                out.append(item)
                continue

            meta = _metadata_as_dict(item.metadata)

            if _has_nonempty_language_string(meta):
                out.append(item)
                continue

            if _caller_other_language_fields_without_language_string(meta):
                new_meta = _merge_language_warnings(meta, ["language_metadata_partial"])
                if new_meta == meta:
                    out.append(item)
                else:
                    out.append(replace(item, metadata=new_meta))  # type: ignore[arg-type]
                continue

            try:
                result = self._language_detection.detect(item.text)
            except LanguageDetectionUnavailableError:
                new_meta = _merge_language_warnings(meta, ["language_detection_unavailable"])
                out.append(replace(item, metadata=new_meta))  # type: ignore[arg-type]
            except LanguageDetectionError:
                new_meta = _merge_language_warnings(meta, ["language_detection_failed"])
                out.append(replace(item, metadata=new_meta))  # type: ignore[arg-type]
            except Exception:  # noqa: BLE001 — per-candidate detection must not abort ingestion
                new_meta = _merge_language_warnings(meta, ["language_detection_failed"])
                out.append(replace(item, metadata=new_meta))  # type: ignore[arg-type]
            else:
                new_meta = _apply_detection_result(meta, result)
                out.append(replace(item, metadata=new_meta))  # type: ignore[arg-type]

        return out
