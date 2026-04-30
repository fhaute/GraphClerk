from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core import config as config_module
from app.models.artifact import Artifact
from app.models.evidence_unit import EvidenceUnit
from app.services.text_ingestion_service import TextIngestionService


def _session() -> Session:
    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    return Session(engine, expire_on_commit=False)


def test_create_text_artifact(db_ready: None) -> None:
    config_module.get_settings.cache_clear()
    settings = config_module.get_settings()
    svc = TextIngestionService(settings=settings)

    with _session() as session:
        result = svc.ingest(
            session=session,
            filename="a.txt",
            artifact_type="text",
            mime_type="text/plain",
            content_bytes=b"Hello\n\nWorld\nLine2\n",
        )

    assert result.artifact.checksum
    assert result.artifact.storage_uri
    assert result.evidence_unit_count == 2


def test_artifact_checksum_is_stored(db_ready: None) -> None:
    settings = config_module.get_settings()
    svc = TextIngestionService(settings=settings)

    with _session() as session:
        result = svc.ingest(
            session=session,
            filename="a.md",
            artifact_type="markdown",
            mime_type="text/markdown",
            content_bytes=b"# H1\n\nPara\n",
        )

        a = session.get(Artifact, result.artifact.id)
        assert a is not None
        assert a.checksum is not None
        assert a.size_bytes > 0
        assert a.storage_uri.startswith("localdb://")  # small source stored in DB
        assert a.raw_text is not None


def test_plain_text_ingestion_creates_evidence_units(db_ready: None) -> None:
    settings = config_module.get_settings()
    svc = TextIngestionService(settings=settings)
    with _session() as session:
        result = svc.ingest(
            session=session,
            filename="x.txt",
            artifact_type="text",
            mime_type="text/plain",
            content_bytes=b"A\n\nB\n",
        )

        evs = session.execute(select(EvidenceUnit).where(EvidenceUnit.artifact_id == result.artifact.id)).scalars().all()
        assert len(evs) == 2


def test_verbatim_evidence_matches_source_text(db_ready: None) -> None:
    settings = config_module.get_settings()
    svc = TextIngestionService(settings=settings)
    src = "Hello\n\nWorld\nLine2\n"
    with _session() as session:
        result = svc.ingest(
            session=session,
            filename="x.txt",
            artifact_type="text",
            mime_type="text/plain",
            content_bytes=src.encode("utf-8"),
        )

        evs = (
            session.execute(select(EvidenceUnit).where(EvidenceUnit.artifact_id == result.artifact.id).order_by(EvidenceUnit.created_at))
            .scalars()
            .all()
        )
        assert evs[0].text == "Hello"
        assert evs[1].text == "World\nLine2"


def test_evidence_unit_location_metadata_exists(db_ready: None) -> None:
    settings = config_module.get_settings()
    svc = TextIngestionService(settings=settings)
    with _session() as session:
        result = svc.ingest(
            session=session,
            filename="x.md",
            artifact_type="markdown",
            mime_type="text/markdown",
            content_bytes=b"# H1\n\nPara\n",
        )

        ev = (
            session.execute(select(EvidenceUnit).where(EvidenceUnit.artifact_id == result.artifact.id).limit(1))
            .scalars()
            .one()
        )
        assert ev.location is not None
        assert "line_start" in ev.location
        assert "line_end" in ev.location
        assert "block_index" in ev.location


def test_evidence_unit_links_to_artifact(db_ready: None) -> None:
    settings = config_module.get_settings()
    svc = TextIngestionService(settings=settings)
    with _session() as session:
        result = svc.ingest(
            session=session,
            filename="x.txt",
            artifact_type="text",
            mime_type="text/plain",
            content_bytes=b"A\n",
        )

        ev = session.execute(select(EvidenceUnit).where(EvidenceUnit.artifact_id == result.artifact.id)).scalars().first()
        assert ev is not None
        assert ev.artifact_id == result.artifact.id

