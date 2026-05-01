"""Language detection adapter boundary (Phase 7, Slice 7C).

Provides ``LanguageDetectionService`` plus explicit adapters. Detection output is
**routing metadata only** — not evidence — and must never mutate input text.

Track C Slice C3: optional **Lingua** adapter behind
``GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER=lingua`` (install ``language-detector`` extra).
Default ``not_configured``. **Track C Slice C8:** when ``lingua`` is configured,
``POST /artifacts`` builds this adapter/service and passes it into
``EvidenceEnrichmentService`` (fail loud if the extra is missing).

Error semantics:
    ``LanguageDetectionUnavailableError`` — adapter explicitly not configured.
    ``LanguageDetectionError`` — invalid adapter result after ``detect`` returns.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Protocol

from app.core.config import Settings
from app.services.errors import LanguageDetectionError, LanguageDetectionUnavailableError

LINGUA_DETECTION_METHOD = "lingua_language_detector"


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
    warns = result.warnings
    if not isinstance(warns, list) or any(not isinstance(w, str) for w in warns):
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


def _import_lingua_and_build_detector() -> Any:
    """Import Lingua and build a default detector (heavy). Used only for ``lingua`` adapter."""

    try:
        from lingua import LanguageDetectorBuilder
    except ImportError as e:
        raise LanguageDetectionUnavailableError(
            "language_detection_lingua_extra_not_installed",
        ) from e
    return LanguageDetectorBuilder.from_all_languages().build()


def _language_to_language_code(detected: Any) -> str | None:
    """Map Lingua ``Language`` to a lowercase code for ``language``."""

    iso1 = getattr(detected, "iso_code_639_1", None)
    name = getattr(iso1, "name", None) if iso1 is not None else None
    if isinstance(name, str) and name.strip():
        return name.strip().lower()
    iso3 = getattr(detected, "iso_code_639_3", None)
    name3 = getattr(iso3, "name", None) if iso3 is not None else None
    if isinstance(name3, str) and name3.strip():
        return name3.strip().lower()
    return None


class LinguaLanguageDetectionAdapter:
    """Lingua-backed local language detection (optional ``language-detector`` extra).

    Does not mutate input text. No network I/O. Constructing this class imports
    and builds a ``LanguageDetector`` unless ``detector=`` is injected (tests).
    """

    __slots__ = ("_detector", "_low_confidence_threshold", "_short_text_max_chars")

    def __init__(
        self,
        *,
        detector: Any | None = None,
        short_text_max_chars: int = 3,
        low_confidence_threshold: float = 0.5,
    ) -> None:
        self._short_text_max_chars = short_text_max_chars
        self._low_confidence_threshold = low_confidence_threshold
        self._detector = detector if detector is not None else _import_lingua_and_build_detector()

    def detect(self, text: str) -> LanguageDetectionResult:
        stripped = text.strip()
        method = LINGUA_DETECTION_METHOD
        if not stripped:
            return LanguageDetectionResult(
                language=None,
                confidence=0.0,
                method=method,
                warnings=["language_text_empty"],
            )
        if len(stripped) <= self._short_text_max_chars:
            return LanguageDetectionResult(
                language=None,
                confidence=0.15,
                method=method,
                warnings=["language_text_too_short"],
            )
        sample = stripped
        try:
            detected = self._detector.detect_language_of(sample)
        except Exception as e:  # noqa: BLE001 — surface as explicit detection failure
            raise LanguageDetectionError("language_detection_lingua_runtime_error") from e

        if detected is None:
            return LanguageDetectionResult(
                language=None,
                confidence=0.0,
                method=method,
                warnings=[],
            )

        try:
            confidences = list(self._detector.compute_language_confidence_values(sample))
        except Exception as e:  # noqa: BLE001
            raise LanguageDetectionError("language_detection_lingua_runtime_error") from e

        top_conf: float | None = None
        for entry in confidences:
            if getattr(entry, "language", None) == detected:
                val = getattr(entry, "value", None)
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    xf = float(val)
                    if math.isfinite(xf):
                        top_conf = xf
                break
        if top_conf is None and confidences:
            val0 = getattr(confidences[0], "value", None)
            if isinstance(val0, (int, float)) and not isinstance(val0, bool):
                xf0 = float(val0)
                if math.isfinite(xf0):
                    top_conf = xf0

        if top_conf is not None:
            top_conf = max(0.0, min(1.0, top_conf))

        warnings: list[str] = []
        if top_conf is not None and top_conf < self._low_confidence_threshold:
            warnings.append("language_detector_low_confidence")

        lang_code = _language_to_language_code(detected)

        return LanguageDetectionResult(
            language=lang_code,
            confidence=top_conf,
            method=method,
            warnings=warnings,
        )


def build_language_detection_adapter(settings: Settings) -> LanguageDetectionAdapter:
    """Construct the configured ``LanguageDetectionAdapter`` (no global singleton)."""

    if settings.language_detection_adapter == "not_configured":
        return NotConfiguredLanguageDetectionAdapter()
    if settings.language_detection_adapter == "lingua":
        return LinguaLanguageDetectionAdapter()
    raise AssertionError("unexpected language_detection_adapter value")


def build_language_detection_service(settings: Settings) -> LanguageDetectionService:
    """Convenience: ``LanguageDetectionService`` using ``build_language_detection_adapter``."""

    return LanguageDetectionService(adapter=build_language_detection_adapter(settings))


class LanguageDetectionService:
    """Facade over ``LanguageDetectionAdapter`` with result validation."""

    def __init__(self, *, adapter: LanguageDetectionAdapter) -> None:
        self._adapter = adapter

    def detect(self, text: str) -> LanguageDetectionResult:
        """Run detection without mutating ``text``.

        Raises:
            LanguageDetectionUnavailableError: Adapter not configured.
            LanguageDetectionError: Bad ``text`` type or invalid adapter output.
        """

        if not isinstance(text, str):
            raise LanguageDetectionError("language_detection_text_must_be_str")
        result = self._adapter.detect(text)
        _validate_detection_result(result)
        return result
