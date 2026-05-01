"""Phase 7 Slice 7C — LanguageDetectionService and adapter shell."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pytest

from app.services.errors import LanguageDetectionError, LanguageDetectionUnavailableError
from app.services.language_detection_service import (
    DeterministicTestLanguageDetectionAdapter,
    LanguageDetectionResult,
    LanguageDetectionService,
    NotConfiguredLanguageDetectionAdapter,
)


def test_not_configured_adapter_raises() -> None:
    svc = LanguageDetectionService(adapter=NotConfiguredLanguageDetectionAdapter())
    with pytest.raises(LanguageDetectionUnavailableError):
        svc.detect("hello")


def test_deterministic_adapter_empty_text() -> None:
    svc = LanguageDetectionService(adapter=DeterministicTestLanguageDetectionAdapter())
    r = svc.detect("   \n\t  ")
    assert r.language is None
    assert r.confidence == 0.0
    assert r.method == "deterministic_test"
    assert r.warnings == ["language_text_empty"]


def test_deterministic_adapter_short_text() -> None:
    svc = LanguageDetectionService(adapter=DeterministicTestLanguageDetectionAdapter(short_text_max_chars=3))
    r = svc.detect("xx")
    assert r.language is None
    assert r.confidence == 0.15
    assert "language_text_too_short" in r.warnings


def test_deterministic_adapter_longer_text_uses_defaults() -> None:
    svc = LanguageDetectionService(
        adapter=DeterministicTestLanguageDetectionAdapter(
            default_language="fr",
            default_confidence=0.8,
            short_text_max_chars=2,
        ),
    )
    r = svc.detect("bonjour")
    assert r.language == "fr"
    assert r.confidence == 0.8
    assert r.warnings == []


def test_service_does_not_modify_input_text() -> None:
    svc = LanguageDetectionService(adapter=DeterministicTestLanguageDetectionAdapter())
    original = "  padded content  "
    before = original
    svc.detect(original)
    assert original == before


def test_service_rejects_non_str_text() -> None:
    svc = LanguageDetectionService(adapter=DeterministicTestLanguageDetectionAdapter())
    with pytest.raises(LanguageDetectionError, match="language_detection_text_must_be_str"):
        svc.detect(123)  # type: ignore[arg-type]


@dataclass(frozen=True)
class _BadConfidenceAdapter:
    value: float

    def detect(self, text: str) -> LanguageDetectionResult:
        _ = text
        return LanguageDetectionResult(language=None, confidence=self.value, method="bad", warnings=[])


def test_service_rejects_confidence_above_one() -> None:
    svc = LanguageDetectionService(adapter=_BadConfidenceAdapter(1.01))
    with pytest.raises(LanguageDetectionError, match="language_detection_invalid_confidence_range"):
        svc.detect("hello")


def test_service_rejects_confidence_below_zero() -> None:
    svc = LanguageDetectionService(adapter=_BadConfidenceAdapter(-0.001))
    with pytest.raises(LanguageDetectionError, match="language_detection_invalid_confidence_range"):
        svc.detect("hello")


def test_service_rejects_nan_confidence() -> None:
    svc = LanguageDetectionService(adapter=_BadConfidenceAdapter(float("nan")))
    with pytest.raises(LanguageDetectionError, match="language_detection_invalid_confidence_range"):
        svc.detect("hello")


def test_service_rejects_inf_confidence() -> None:
    svc = LanguageDetectionService(adapter=_BadConfidenceAdapter(float("inf")))
    with pytest.raises(LanguageDetectionError, match="language_detection_invalid_confidence_range"):
        svc.detect("hello")


@dataclass(frozen=True)
class _BadWarningsAdapter:
    def detect(self, text: str) -> LanguageDetectionResult:
        _ = text
        return LanguageDetectionResult(language=None, confidence=None, method="ok", warnings="no")  # type: ignore[arg-type]


def test_service_rejects_non_list_warnings() -> None:
    svc = LanguageDetectionService(adapter=_BadWarningsAdapter())
    with pytest.raises(LanguageDetectionError, match="language_detection_invalid_warnings"):
        svc.detect("x")


@dataclass(frozen=True)
class _BadWarningEntryAdapter:
    def detect(self, text: str) -> LanguageDetectionResult:
        _ = text
        return LanguageDetectionResult(language=None, confidence=None, method="ok", warnings=["a", 2])  # type: ignore[list-item]


def test_service_rejects_non_string_warning_entries() -> None:
    svc = LanguageDetectionService(adapter=_BadWarningEntryAdapter())
    with pytest.raises(LanguageDetectionError, match="language_detection_invalid_warnings"):
        svc.detect("x")


@dataclass(frozen=True)
class _EmptyMethodAdapter:
    def detect(self, text: str) -> LanguageDetectionResult:
        _ = text
        return LanguageDetectionResult(language=None, confidence=None, method="", warnings=[])


def test_service_rejects_empty_method() -> None:
    svc = LanguageDetectionService(adapter=_EmptyMethodAdapter())
    with pytest.raises(LanguageDetectionError, match="language_detection_invalid_method"):
        svc.detect("x")


@dataclass(frozen=True)
class _WhitespaceMethodAdapter:
    def detect(self, text: str) -> LanguageDetectionResult:
        _ = text
        return LanguageDetectionResult(language=None, confidence=None, method="   ", warnings=[])


def test_service_rejects_whitespace_only_method() -> None:
    svc = LanguageDetectionService(adapter=_WhitespaceMethodAdapter())
    with pytest.raises(LanguageDetectionError, match="language_detection_invalid_method"):
        svc.detect("x")


def test_confidence_none_allowed() -> None:
    @dataclass(frozen=True)
    class _NoneConfidenceAdapter:
        def detect(self, text: str) -> LanguageDetectionResult:
            _ = text
            return LanguageDetectionResult(language=None, confidence=None, method="none_conf", warnings=[])

    svc = LanguageDetectionService(adapter=_NoneConfidenceAdapter())
    r = svc.detect("anything")
    assert r.confidence is None
