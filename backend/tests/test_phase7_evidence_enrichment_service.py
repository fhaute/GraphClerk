"""Unit tests for Phase 7 Slice 7A shell and Track C4 language metadata on enrichment."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import Modality, SourceFidelity
from app.schemas.evidence_unit_candidate import (
    LANGUAGE_METADATA_KEY_LANGUAGE,
    LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE,
    LANGUAGE_METADATA_KEY_LANGUAGE_DETECTION_METHOD,
    LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS,
    EvidenceUnitCandidate,
)
from app.services.errors import LanguageDetectionError
from app.services.evidence_enrichment_service import EvidenceEnrichmentService
from app.services.language_detection_service import (
    DeterministicTestLanguageDetectionAdapter,
    LanguageDetectionResult,
    LanguageDetectionService,
    NotConfiguredLanguageDetectionAdapter,
)


@dataclass
class _FakeCandidate:
    """Minimal stand-in for an evidence candidate (no DB, no ORM)."""

    text: str
    source_fidelity: str


def test_enrich_returns_same_count_and_order_and_identities() -> None:
    svc = EvidenceEnrichmentService()
    a = _FakeCandidate("hello", "verbatim")
    b = _FakeCandidate("world", "extracted")
    out = svc.enrich([a, b])

    assert len(out) == 2
    assert out[0] is a
    assert out[1] is b


def test_enrich_preserves_text_and_source_fidelity() -> None:
    svc = EvidenceEnrichmentService()
    c = _FakeCandidate("unchanged body", "verbatim")
    before_text = c.text
    before_sf = c.source_fidelity

    out = svc.enrich([c])

    assert len(out) == 1
    assert out[0] is c
    assert c.text == before_text
    assert c.source_fidelity == before_sf


def test_enrich_empty_returns_empty_list() -> None:
    svc = EvidenceEnrichmentService()
    assert svc.enrich([]) == []
    assert svc.enrich(()) == []


def test_enrich_accepts_tuple_input() -> None:
    svc = EvidenceEnrichmentService()
    x = _FakeCandidate("x", "verbatim")
    out = svc.enrich((x,))
    assert isinstance(out, list)
    assert out == [x]
    assert out[0] is x


def test_enrich_accepts_list_input() -> None:
    svc = EvidenceEnrichmentService()
    x = _FakeCandidate("y", "extracted")
    out = svc.enrich([x])
    assert out == [x]
    assert out[0] is x


def test_enrich_does_not_mutate_original_list() -> None:
    svc = EvidenceEnrichmentService()
    inner = [_FakeCandidate("1", "verbatim")]
    snapshot_id = id(inner)
    out = svc.enrich(inner)
    assert id(inner) == snapshot_id
    assert out is not inner


def _euc(
    text: str = "Hello there",
    *,
    metadata: dict | None = None,
    source_fidelity: SourceFidelity = SourceFidelity.verbatim,
) -> EvidenceUnitCandidate:
    return EvidenceUnitCandidate(
        modality=Modality.text,
        content_type="paragraph",
        text=text,
        location={"line_start": 1},
        source_fidelity=source_fidelity,
        confidence=1.0,
        metadata=metadata,
    )


def _det_svc(**adapter_kw) -> LanguageDetectionService:
    return LanguageDetectionService(
        adapter=DeterministicTestLanguageDetectionAdapter(**adapter_kw),
    )


def test_default_enrichment_pass_through_with_detection_none_unchanged_euc_identities() -> None:
    svc = EvidenceEnrichmentService()
    a = _euc(text="One block")
    b = _euc(text="Two block")
    out = svc.enrich([a, b])
    assert out == [a, b]
    assert out[0] is a
    assert out[1] is b


def test_injected_detection_adds_language_metadata() -> None:
    det = _det_svc(default_language="fr", short_text_max_chars=0)
    svc = EvidenceEnrichmentService(language_detection=det)
    c = _euc(text="Long enough text")
    out = svc.enrich([c])
    assert len(out) == 1
    assert out[0] is not c
    assert out[0].text == c.text
    assert out[0].source_fidelity == c.source_fidelity
    meta = out[0].metadata or {}
    assert meta[LANGUAGE_METADATA_KEY_LANGUAGE] == "fr"
    assert meta[LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE] == 0.95
    assert meta[LANGUAGE_METADATA_KEY_LANGUAGE_DETECTION_METHOD] == "deterministic_test"


def test_detection_preserves_non_language_metadata() -> None:
    det = _det_svc(default_language="de", short_text_max_chars=0)
    svc = EvidenceEnrichmentService(language_detection=det)
    c = _euc(text="Some longer body", metadata={"note": "keep", "pages": 3})
    out = svc.enrich([c])[0]
    assert out.metadata["note"] == "keep"
    assert out.metadata["pages"] == 3
    assert out.metadata[LANGUAGE_METADATA_KEY_LANGUAGE] == "de"


def test_existing_nonempty_language_string_not_overwritten() -> None:
    det = _det_svc(default_language="xx", short_text_max_chars=0)
    svc = EvidenceEnrichmentService(language_detection=det)
    c = _euc(text="Body", metadata={LANGUAGE_METADATA_KEY_LANGUAGE: "de"})
    out = svc.enrich([c])
    assert out[0] is c
    assert (out[0].metadata or {}).get(LANGUAGE_METADATA_KEY_LANGUAGE) == "de"


def test_partial_language_fields_skip_detection_and_warn() -> None:
    det = _det_svc(default_language="xx", short_text_max_chars=0)
    svc = EvidenceEnrichmentService(language_detection=det)
    c = _euc(
        text="Body text here",
        metadata={LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE: 0.5},
    )
    out = svc.enrich([c])[0]
    assert out is not c
    warns = (out.metadata or {}).get(LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS, [])
    assert "language_metadata_partial" in warns
    assert LANGUAGE_METADATA_KEY_LANGUAGE not in (out.metadata or {})


def test_detection_merges_detector_warnings_sorted_unique() -> None:
    """Caller ``language_warnings`` without ``language`` skips detection (partial path)."""

    class _WarnAdapter:
        def detect(self, text: str) -> LanguageDetectionResult:
            _ = text
            return LanguageDetectionResult(
                language="en",
                confidence=0.9,
                method="stub_warn",
                warnings=["detector_side", "extra"],
            )

    svc = EvidenceEnrichmentService(
        language_detection=LanguageDetectionService(adapter=_WarnAdapter())
    )
    c = _euc(text="Long text block", metadata={"note": "only"})
    out = svc.enrich([c])[0]
    w = out.metadata[LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS]
    assert w == ["detector_side", "extra"]


def test_partial_metadata_merges_language_metadata_partial_with_existing_warnings() -> None:
    det = _det_svc(default_language="xx", short_text_max_chars=0)
    svc = EvidenceEnrichmentService(language_detection=det)
    c = _euc(
        text="Body text here",
        metadata={LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS: ["prior"]},
    )
    out = svc.enrich([c])[0]
    w = out.metadata[LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS]
    assert w == ["language_metadata_partial", "prior"]


def test_language_detection_error_records_warning_does_not_drop() -> None:
    class _BoomAdapter:
        def detect(self, text: str) -> LanguageDetectionResult:
            raise LanguageDetectionError("language_detection_test_boom")

    boom = LanguageDetectionService(adapter=_BoomAdapter())
    svc = EvidenceEnrichmentService(language_detection=boom)
    a = _euc(text="First paragraph block")
    b = _euc(text="Second paragraph block")
    out = svc.enrich([a, b])
    assert len(out) == 2
    for item in out:
        warns = (item.metadata or {}).get(LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS, [])
        assert "language_detection_failed" in warns


def test_unexpected_exception_records_language_detection_failed() -> None:
    class _KaboomAdapter:
        def detect(self, text: str) -> LanguageDetectionResult:
            raise RuntimeError("surprise")

    kab = LanguageDetectionService(adapter=_KaboomAdapter())
    svc = EvidenceEnrichmentService(language_detection=kab)
    out = svc.enrich([_euc(text="Enough characters")])[0]
    assert "language_detection_failed" in out.metadata[LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS]


def test_not_configured_adapter_records_unavailable_warning() -> None:
    svc = EvidenceEnrichmentService(
        language_detection=LanguageDetectionService(
            adapter=NotConfiguredLanguageDetectionAdapter()
        ),
    )
    out = svc.enrich([_euc(text="Paragraph one here")])[0]
    assert "language_detection_unavailable" in out.metadata[LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS]


def test_no_language_service_injected_no_metadata_side_effects_on_not_configured_path() -> None:
    """Without injection, enrichment does not touch metadata (no implicit NotConfigured)."""

    svc = EvidenceEnrichmentService()
    c = _euc(text="X", metadata={"k": 1})
    assert svc.enrich([c])[0] is c


def test_text_and_source_fidelity_immutable_under_detection() -> None:
    svc = EvidenceEnrichmentService(language_detection=_det_svc(short_text_max_chars=0))
    c = _euc(text="Hold fidelity", source_fidelity=SourceFidelity.extracted, metadata=None)
    before_t, before_sf = c.text, c.source_fidelity
    out = svc.enrich([c])[0]
    assert c.text == before_t and c.source_fidelity == before_sf
    assert out.text == before_t and out.source_fidelity == before_sf


def test_tuple_input_with_detection_returns_list() -> None:
    svc = EvidenceEnrichmentService(language_detection=_det_svc(short_text_max_chars=0))
    x = _euc(text="Tuple case text")
    out = svc.enrich((x,))
    assert isinstance(out, list)
    assert out[0].metadata[LANGUAGE_METADATA_KEY_LANGUAGE] == "en"


def test_mixed_non_candidate_and_candidate_order_preserved() -> None:
    svc = EvidenceEnrichmentService(language_detection=_det_svc(short_text_max_chars=0))
    f = _FakeCandidate("fake", "verbatim")
    e = _euc(text="Real candidate text")
    out = svc.enrich([f, e])
    assert out[0] is f
    assert out[1] is not e
    assert out[1].metadata[LANGUAGE_METADATA_KEY_LANGUAGE] == "en"
