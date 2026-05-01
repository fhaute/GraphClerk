"""Unit tests for Phase 7 Slice 7A — EvidenceEnrichmentService shell."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.evidence_enrichment_service import EvidenceEnrichmentService


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
