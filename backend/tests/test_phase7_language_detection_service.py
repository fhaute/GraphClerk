"""Phase 7 Slice 7C — LanguageDetectionService and adapter shell."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from app.core import config as config_module
from app.core.config import Settings
from app.services import language_detection_service as lds
from app.services.errors import LanguageDetectionError, LanguageDetectionUnavailableError
from app.services.language_detection_service import (
    DeterministicTestLanguageDetectionAdapter,
    LanguageDetectionResult,
    LanguageDetectionService,
    LinguaLanguageDetectionAdapter,
    NotConfiguredLanguageDetectionAdapter,
    build_language_detection_adapter,
    build_language_detection_service,
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
    adapter = DeterministicTestLanguageDetectionAdapter(short_text_max_chars=3)
    svc = LanguageDetectionService(adapter=adapter)
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
        return LanguageDetectionResult(
            language=None,
            confidence=self.value,
            method="bad",
            warnings=[],
        )


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
        return LanguageDetectionResult(
            language=None,
            confidence=None,
            method="ok",
            warnings=["a", 2],  # type: ignore[list-item]
        )


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


def _minimal_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "GraphClerk")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/db")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "optional")
    monkeypatch.delenv("GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER", raising=False)
    monkeypatch.delenv("GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER", raising=False)
    config_module.get_settings.cache_clear()


def test_build_adapter_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_settings_env(monkeypatch)
    settings = Settings()
    adapter = build_language_detection_adapter(settings)
    assert isinstance(adapter, NotConfiguredLanguageDetectionAdapter)


def test_build_adapter_lingua_raises_when_extra_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_settings_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER", "lingua")

    def _boom() -> Any:
        # Simulates ``_import_lingua_and_build_detector`` after a failed optional install.
        raise LanguageDetectionUnavailableError("language_detection_lingua_extra_not_installed")

    monkeypatch.setattr(lds, "_import_lingua_and_build_detector", _boom)
    settings = Settings()
    with pytest.raises(LanguageDetectionUnavailableError) as exc:
        build_language_detection_adapter(settings)
    assert "language_detection_lingua_extra_not_installed" in str(exc.value)


def test_build_service_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    _minimal_settings_env(monkeypatch)
    settings = Settings()
    svc = build_language_detection_service(settings)
    with pytest.raises(LanguageDetectionUnavailableError):
        svc.detect("hello")


@dataclass
class _FakeConfEntry:
    language: object
    value: float


@dataclass
class _FakeLang:
    iso_code_639_1: Any | None = None
    iso_code_639_3: Any | None = None


@dataclass
class _FakeIso:
    name: str


class _FakeLinguaDetector:
    def __init__(
        self,
        *,
        detected: Any,
        confidences: list[_FakeConfEntry],
        exc: Exception | None = None,
    ) -> None:
        self._detected = detected
        self._confidences = confidences
        self._exc = exc

    def detect_language_of(self, text: str) -> Any:
        if self._exc is not None:
            raise self._exc
        _ = text
        return self._detected

    def compute_language_confidence_values(self, text: str) -> list[_FakeConfEntry]:
        _ = text
        return list(self._confidences)


def test_lingua_adapter_fake_success_maps_result() -> None:
    lang = _FakeLang(iso_code_639_1=_FakeIso("EN"))
    det = _FakeLinguaDetector(
        detected=lang,
        confidences=[_FakeConfEntry(language=lang, value=0.92)],
    )
    adapter = LinguaLanguageDetectionAdapter(
        detector=det,
        short_text_max_chars=2,
        low_confidence_threshold=0.5,
    )
    svc = LanguageDetectionService(adapter=adapter)
    r = svc.detect("hello there")
    assert r.language == "en"
    assert r.confidence == pytest.approx(0.92)
    assert r.method == "lingua_language_detector"
    assert r.warnings == []


def test_lingua_adapter_fake_low_confidence_emits_warning() -> None:
    lang = _FakeLang(iso_code_639_1=_FakeIso("DE"))
    det = _FakeLinguaDetector(
        detected=lang,
        confidences=[_FakeConfEntry(language=lang, value=0.2)],
    )
    adapter = LinguaLanguageDetectionAdapter(
        detector=det,
        short_text_max_chars=2,
        low_confidence_threshold=0.5,
    )
    svc = LanguageDetectionService(adapter=adapter)
    r = svc.detect("guten tag freunde")
    assert r.language == "de"
    assert r.confidence == pytest.approx(0.2)
    assert "language_detector_low_confidence" in r.warnings


def test_lingua_adapter_empty_text() -> None:
    fake = _FakeLinguaDetector(detected=None, confidences=[])
    adapter = LinguaLanguageDetectionAdapter(detector=fake)
    svc = LanguageDetectionService(adapter=adapter)
    r = svc.detect("  \t ")
    assert r.language is None
    assert r.confidence == 0.0
    assert r.warnings == ["language_text_empty"]


def test_lingua_adapter_short_text() -> None:
    adapter = LinguaLanguageDetectionAdapter(
        detector=_FakeLinguaDetector(detected=None, confidences=[]),
        short_text_max_chars=3,
    )
    svc = LanguageDetectionService(adapter=adapter)
    r = svc.detect("ab")
    assert r.language is None
    assert r.confidence == 0.15
    assert "language_text_too_short" in r.warnings


def test_lingua_adapter_runtime_error_wraps() -> None:
    det = _FakeLinguaDetector(detected=None, confidences=[], exc=RuntimeError("boom"))
    adapter = LinguaLanguageDetectionAdapter(detector=det, short_text_max_chars=1)
    svc = LanguageDetectionService(adapter=adapter)
    with pytest.raises(LanguageDetectionError, match="language_detection_lingua_runtime_error"):
        svc.detect("something long enough")


def test_lingua_adapter_does_not_mutate_input_text() -> None:
    lang = _FakeLang(iso_code_639_1=_FakeIso("FR"))
    det = _FakeLinguaDetector(detected=lang, confidences=[_FakeConfEntry(language=lang, value=0.9)])
    adapter = LinguaLanguageDetectionAdapter(detector=det, short_text_max_chars=1)
    svc = LanguageDetectionService(adapter=adapter)
    original = "  bonjour  "
    before = original
    svc.detect(original)
    assert original == before


def test_lingua_smoke_if_extra_installed() -> None:
    pytest.importorskip("lingua")
    adapter = LinguaLanguageDetectionAdapter(short_text_max_chars=1)
    svc = LanguageDetectionService(adapter=adapter)
    r = svc.detect("This is clearly English prose for detection.")
    assert r.method == "lingua_language_detector"
    assert isinstance(r.warnings, list)


def test_confidence_none_allowed() -> None:
    @dataclass(frozen=True)
    class _NoneConfidenceAdapter:
        def detect(self, text: str) -> LanguageDetectionResult:
            _ = text
            return LanguageDetectionResult(
                language=None,
                confidence=None,
                method="none_conf",
                warnings=[],
            )

    svc = LanguageDetectionService(adapter=_NoneConfidenceAdapter())
    r = svc.detect("anything")
    assert r.confidence is None
