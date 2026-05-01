"""Phase 7 Slice 7B — optional language metadata on EvidenceUnitCandidate.metadata."""

from __future__ import annotations

import math
import os
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.artifact import Artifact
from app.models.enums import Modality, SourceFidelity
from app.models.evidence_unit import EvidenceUnit
from app.schemas.evidence_unit_candidate import (
    LANGUAGE_METADATA_KEY_LANGUAGE,
    LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE,
    LANGUAGE_METADATA_KEY_LANGUAGE_DETECTION_METHOD,
    LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS,
    EvidenceUnitCandidate,
    validate_optional_language_metadata,
)
from app.services.errors import InvalidLanguageMetadataError
from app.services.evidence_unit_service import EvidenceUnitService


def _session() -> Session:
    from sqlalchemy import create_engine

    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    return Session(engine, expire_on_commit=False)


def _base_meta() -> dict:
    return {
        "pages": 2,
        LANGUAGE_METADATA_KEY_LANGUAGE: "en",
        LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE: 0.85,
        LANGUAGE_METADATA_KEY_LANGUAGE_DETECTION_METHOD: "manual_test_fixture",
        LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS: [],
    }


def _minimal_candidate(**overrides) -> EvidenceUnitCandidate:
    base = dict(
        modality=Modality.text,
        content_type="paragraph",
        text="body text",
        location={"line_start": 1, "line_end": 1, "block_index": 0, "section_path": []},
        source_fidelity=SourceFidelity.verbatim,
        confidence=1.0,
    )
    base.update(overrides)
    return EvidenceUnitCandidate(**base)


def test_candidate_can_carry_language_metadata() -> None:
    meta = _base_meta()
    c = _minimal_candidate(metadata=meta)
    assert c.metadata == meta
    assert c.metadata[LANGUAGE_METADATA_KEY_LANGUAGE] == "en"
    assert c.metadata[LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE] == 0.85


def test_candidate_without_language_metadata_still_valid() -> None:
    c_none = _minimal_candidate(metadata=None)
    assert c_none.metadata is None

    c_plain = _minimal_candidate(metadata={"note": "no language keys"})
    assert c_plain.metadata == {"note": "no language keys"}


def test_language_metadata_does_not_change_text_or_source_fidelity() -> None:
    meta = _base_meta()
    c = _minimal_candidate(
        text="immutable",
        source_fidelity=SourceFidelity.extracted,
        metadata=meta,
    )
    assert c.text == "immutable"
    assert c.source_fidelity == SourceFidelity.extracted


def test_language_may_be_none_when_key_present() -> None:
    c = _minimal_candidate(metadata={LANGUAGE_METADATA_KEY_LANGUAGE: None})
    assert c.metadata[LANGUAGE_METADATA_KEY_LANGUAGE] is None


def test_language_confidence_boundary_values_accepted() -> None:
    for val in (0.0, 1.0, 0.5, 1):
        c = _minimal_candidate(metadata={LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE: val})
        assert c.metadata[LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE] == val


def test_language_confidence_rejects_below_zero() -> None:
    with pytest.raises(InvalidLanguageMetadataError):
        _minimal_candidate(metadata={LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE: -0.01})


def test_language_confidence_rejects_above_one() -> None:
    with pytest.raises(InvalidLanguageMetadataError):
        _minimal_candidate(metadata={LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE: 1.01})


def test_language_confidence_rejects_non_finite() -> None:
    with pytest.raises(InvalidLanguageMetadataError):
        _minimal_candidate(metadata={LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE: math.nan})
    with pytest.raises(InvalidLanguageMetadataError):
        _minimal_candidate(metadata={LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE: math.inf})


def test_language_confidence_rejects_bool() -> None:
    with pytest.raises(InvalidLanguageMetadataError):
        _minimal_candidate(metadata={LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE: True})  # type: ignore[arg-type]


def test_language_warnings_rejects_non_list() -> None:
    with pytest.raises(InvalidLanguageMetadataError):
        _minimal_candidate(metadata={LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS: "oops"})  # type: ignore[arg-type]


def test_language_warnings_rejects_non_string_entries() -> None:
    with pytest.raises(InvalidLanguageMetadataError):
        _minimal_candidate(metadata={LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS: ["ok", 99]})  # type: ignore[list-item]


def test_language_field_rejects_non_string() -> None:
    with pytest.raises(InvalidLanguageMetadataError):
        _minimal_candidate(metadata={LANGUAGE_METADATA_KEY_LANGUAGE: 404})  # type: ignore[arg-type]


def test_language_detection_method_rejects_non_string() -> None:
    with pytest.raises(InvalidLanguageMetadataError):
        _minimal_candidate(metadata={LANGUAGE_METADATA_KEY_LANGUAGE_DETECTION_METHOD: []})  # type: ignore[arg-type]


def test_validate_optional_language_metadata_accepts_none() -> None:
    validate_optional_language_metadata(None)


def test_language_metadata_persists_via_evidence_unit_service(db_ready: None) -> None:
    meta = _base_meta()
    aid = uuid.uuid4()
    with _session() as session:
        art = Artifact(
            id=aid,
            filename="lang.txt",
            title=None,
            artifact_type="text",
            mime_type="text/plain",
            storage_uri="localdb://lang-meta",
            checksum="lm",
            size_bytes=4,
            raw_text=None,
            metadata_json=None,
        )
        session.add(art)
        session.flush()

        cand = EvidenceUnitCandidate(
            modality=Modality.text,
            content_type="paragraph",
            text="hello",
            location={"line_start": 1, "line_end": 1, "block_index": 0, "section_path": []},
            source_fidelity=SourceFidelity.verbatim,
            confidence=1.0,
            metadata=meta,
        )
        svc = EvidenceUnitService(session=session)
        created = svc.create_from_candidates(artifact_id=aid, candidates=[cand])
        session.commit()

        assert len(created) == 1
        ev = created[0]
        assert ev.text == "hello"
        assert ev.source_fidelity == SourceFidelity.verbatim
        assert ev.metadata_json == meta

        loaded = session.execute(select(EvidenceUnit).where(EvidenceUnit.id == ev.id)).scalar_one()
        assert loaded.metadata_json[LANGUAGE_METADATA_KEY_LANGUAGE] == "en"
