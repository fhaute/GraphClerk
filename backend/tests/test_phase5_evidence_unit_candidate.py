from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core import config as config_module
from app.models.artifact import Artifact
from app.models.enums import Modality, SourceFidelity
from app.models.evidence_unit import EvidenceUnit
from app.schemas.evidence_unit_candidate import EvidenceUnitCandidate
from app.services.errors import InvalidEvidenceUnitCandidateError, InvalidSourceFidelityError
from app.services.evidence_unit_service import EvidenceUnitService
from app.services.parsers.markdown_parser import MarkdownParser
from app.services.parsers.plain_text_parser import PlainTextParser
from app.services.text_ingestion_service import TextIngestionService


def _session() -> Session:
    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    return Session(engine, expire_on_commit=False)


def _minimal_candidate(**overrides) -> EvidenceUnitCandidate:
    base = dict(
        modality=Modality.text,
        content_type="paragraph",
        text="body",
        location={"line_start": 1, "line_end": 1, "block_index": 0, "section_path": []},
        source_fidelity=SourceFidelity.verbatim,
        confidence=1.0,
    )
    base.update(overrides)
    return EvidenceUnitCandidate(**base)


def test_candidate_requires_non_empty_text() -> None:
    with pytest.raises(InvalidEvidenceUnitCandidateError):
        _minimal_candidate(text="")
    with pytest.raises(InvalidEvidenceUnitCandidateError):
        _minimal_candidate(text="   \n\t  ")


def test_candidate_accepts_each_source_fidelity() -> None:
    for fid in SourceFidelity:
        c = _minimal_candidate(source_fidelity=fid, text=f"x-{fid.value}")
        assert c.source_fidelity == fid


def test_candidate_accepts_string_source_fidelity_values() -> None:
    c = _minimal_candidate(source_fidelity="extracted")
    assert c.source_fidelity == SourceFidelity.extracted


def test_candidate_rejects_invalid_source_fidelity_string() -> None:
    with pytest.raises(InvalidSourceFidelityError):
        _minimal_candidate(source_fidelity="ocr_magic")


def test_candidate_rejects_non_string_non_enum_source_fidelity() -> None:
    with pytest.raises(InvalidSourceFidelityError):
        _minimal_candidate(source_fidelity=123)  # type: ignore[arg-type]


def test_candidate_preserves_core_fields() -> None:
    loc = {"slide": 3, "bbox": [0, 0, 1, 1]}
    c = EvidenceUnitCandidate(
        modality=Modality.pdf,
        content_type="pdf_page_text",
        text="Page content",
        location=loc,
        source_fidelity=SourceFidelity.extracted,
        confidence=0.9,
    )
    assert c.modality == Modality.pdf
    assert c.content_type == "pdf_page_text"
    assert c.text == "Page content"
    assert c.location == loc
    assert c.source_fidelity == SourceFidelity.extracted
    assert c.confidence == 0.9
    assert c.metadata is None


def test_candidate_optional_metadata() -> None:
    meta = {"pages": 2}
    c = _minimal_candidate(metadata=meta)
    assert c.metadata == meta


def test_evidence_unit_service_maps_parser_candidates(db_ready: None) -> None:
    with _session() as session:
        aid = uuid.uuid4()
        art = Artifact(
            id=aid,
            filename="t.txt",
            title=None,
            artifact_type="text",
            mime_type="text/plain",
            storage_uri="localdb://test",
            checksum="abc",
            size_bytes=3,
            raw_text=None,
            metadata_json=None,
        )
        session.add(art)
        session.flush()

        plain = PlainTextParser().parse("Alpha\n\nBeta\n")
        svc = EvidenceUnitService(session=session)
        created = svc.create_from_candidates(artifact_id=aid, candidates=plain)
        session.commit()

        assert len(created) == 2
        assert {e.text for e in created} == {"Alpha", "Beta"}
        for e in created:
            assert e.modality == Modality.text
            assert e.source_fidelity == SourceFidelity.verbatim
            assert e.metadata_json is None


def test_evidence_unit_service_maps_markdown_parser_candidates(db_ready: None) -> None:
    with _session() as session:
        aid = uuid.uuid4()
        art = Artifact(
            id=aid,
            filename="t.md",
            title=None,
            artifact_type="markdown",
            mime_type="text/markdown",
            storage_uri="localdb://test-md",
            checksum="def",
            size_bytes=10,
            raw_text=None,
            metadata_json=None,
        )
        session.add(art)
        session.flush()

        md = "# H1\n\nParagraph line.\n"
        cands = MarkdownParser().parse(md)
        svc = EvidenceUnitService(session=session)
        svc.create_from_candidates(artifact_id=aid, candidates=cands)
        session.commit()

        evs = session.execute(select(EvidenceUnit).where(EvidenceUnit.artifact_id == aid)).scalars().all()
        types = {e.content_type for e in evs}
        assert "heading" in types
        assert "paragraph" in types
        assert all(e.text and e.text.strip() for e in evs)


def test_phase2_text_ingestion_still_passes(db_ready: None) -> None:
    config_module.get_settings.cache_clear()
    settings = config_module.get_settings()
    svc = TextIngestionService(settings=settings)
    with _session() as session:
        result = svc.ingest(
            session=session,
            filename="slice_a.txt",
            artifact_type="text",
            mime_type="text/plain",
            content_bytes=b"Hello\n\nWorld\n",
        )
    assert result.evidence_unit_count == 2
