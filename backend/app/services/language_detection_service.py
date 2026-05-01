"""Language detection adapter boundary (Phase 7, Slice 7C).

Provides ``LanguageDetectionService`` plus explicit adapters. Detection output is
**routing metadata only** — not evidence — and must never mutate input text.

Slice 7C does **not** wire detection into ingestion or retrieval; it only defines
the boundary where a future implementation can plug in (still without remote
services or third-party language-ID libraries in-repo unless separately scoped).

Error semantics:
    ``LanguageDetectionUnavailableError`` — adapter explicitly not configured.
    ``LanguageDetectionError`` — invalid adapter result after ``detect`` returns.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from app.services.errors import LanguageDetectionError, LanguageDetectionUnavailableError


@dataclass(frozen=True)
class LanguageDetectionResult:
    """Structured output of a language detection step.

    Attributes:
        language: Detected language code or label, or ``None`` when unknown.
        confidence: Score in ``[0.0, 1.0]``, or ``None`` when not applicable.
        method: Non-empty label naming how detection was performed (e.g. adapter id).
        warnings: Diagnostic strings (e.g. empty input); never silent ambiguity.
    """

    language: str | None
    confidence: float | None
    method: str
    warnings: list[str]


class LanguageDetectionAdapter(Protocol):
    """Pluggable language detector; implementations must not mutate ``text``."""

    def detect(self, text: str) -> LanguageDetectionResult:
        """Return detection metadata for ``text`` (may raise explicit errors)."""


def _validate_detection_result(result: LanguageDetectionResult) -> None:
    """Ensure adapter output meets contract before exposing it from the service."""

    if not isinstance(result.method, str) or result.method.strip() == "":
        raise LanguageDetectionError("language_detection_invalid_method")
    if not isinstance(result.warnings, list) or any(not isinstance(w, str) for w in result.warnings):
        raise LanguageDetectionError("language_detection_invalid_warnings")
    if result.language is not None and not isinstance(result.language, str):
        raise LanguageDetectionError("language_detection_invalid_language_type")
    conf = result.confidence
    if conf is None:
        return
    if isinstance(conf, bool) or not isinstance(conf, (int, float)):
        raise LanguageDetectionError("language_detection_invalid_confidence_type")
    xf = float(conf)
    if not math.isfinite(xf) or xf < 0.0 or xf > 1.0:
        raise LanguageDetectionError("language_detection_invalid_confidence_range")


@dataclass(frozen=True)
class NotConfiguredLanguageDetectionAdapter:
    """Placeholder adapter: detection is explicitly unavailable."""

    def detect(self, text: str) -> LanguageDetectionResult:
        _ = text
        raise LanguageDetectionUnavailableError("language_detection_not_configured")


@dataclass(frozen=True)
class DeterministicTestLanguageDetectionAdapter:
    """Deterministic local rules for tests — not a real linguistics engine.

    Rules:
        Whitespace-only → ``language=None``, ``confidence=0.0``, warning ``language_text_empty``.
        Stripped length ≤ ``short_text_max_chars`` → ``language=None``, low confidence,
        warning ``language_text_too_short``.
        Otherwise → ``default_language`` / ``default_confidence`` with empty warnings.
    """

    default_language: str | None = "en"
    default_confidence: float = 0.95
    short_text_max_chars: int = 3

    def detect(self, text: str) -> LanguageDetectionResult:
        stripped = text.strip()
        method = "deterministic_test"
        if stripped == "":
            return LanguageDetectionResult(
                language=None,
                confidence=0.0,
                method=method,
                warnings=["language_text_empty"],
            )
        if len(stripped) <= self.short_text_max_chars:
            return LanguageDetectionResult(
                language=None,
                confidence=0.15,
                method=method,
                warnings=["language_text_too_short"],
            )
        return LanguageDetectionResult(
            language=self.default_language,
            confidence=self.default_confidence,
            method=method,
            warnings=[],
        )


class LanguageDetectionService:
    """Facade over ``LanguageDetectionAdapter`` with result validation."""

    def __init__(self, *, adapter: LanguageDetectionAdapter) -> None:
        self._adapter = adapter

    def detect(self, text: str) -> LanguageDetectionResult:
        """Run detection without mutating ``text``.

        Raises:
            LanguageDetectionUnavailableError: When the adapter is not configured.
            LanguageDetectionError: When ``text`` is not a str or the adapter returns an invalid result.
        """

        if not isinstance(text, str):
            raise LanguageDetectionError("language_detection_text_must_be_str")
        result = self._adapter.detect(text)
        _validate_detection_result(result)
        return result
