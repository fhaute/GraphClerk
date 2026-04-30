from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path

import pytest

from app.core import config as config_module
from app.models.artifact import Artifact
from app.models.enums import Modality, SourceFidelity
from app.services.errors import (
    ExtractionReturnedNoEvidenceError,
    ExtractorUnavailableError,
    PdfExtractionError,
)
from app.services.extraction.pdf_extractor import PdfExtractor
from app.services.raw_source_store import RawSourceStore

# Minimal 1-page PDF with selectable "Hello" (pypdf reads text; xref may warn).
_MINIMAL_HELLO_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
    b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n"
    b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n"
    b"4 0 obj<< /Length 44 >>stream\n"
    b"BT /F1 24 Tf 100 700 Td (Hello) Tj ET\n"
    b"endstream\n"
    b"endobj\n"
    b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n"
    b"xref\n"
    b"0 6\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"0000000266 00000 n \n"
    b"0000000355 00000 n \n"
    b"trailer<< /Size 6 /Root 1 0 R >>\n"
    b"startxref\n"
    b"433\n"
    b"%%EOF"
)


def _settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> object:
    monkeypatch.setenv("APP_NAME", "GraphClerk")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ.get("DATABASE_URL", "postgresql://graphclerk:graphclerk@127.0.0.1:5432/graphclerk"),
    )
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    config_module.get_settings.cache_clear()
    return config_module.get_settings()


def _artifact_for_pdf(*, raw: object, pdf_bytes: bytes) -> Artifact:
    ck = hashlib.sha256(pdf_bytes).hexdigest()
    return Artifact(
        id=uuid.uuid4(),
        filename="unit.pdf",
        title=None,
        artifact_type="pdf",
        mime_type="application/pdf",
        storage_uri=raw.storage_uri,
        checksum=ck,
        size_bytes=len(pdf_bytes),
        raw_text=raw.raw_text,
        metadata_json=None,
    )


@pytest.fixture()
def pypdf_available() -> None:
    pytest.importorskip("pypdf")


def test_pdf_extractor_requires_pypdf_extra(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    settings = _settings(monkeypatch, tmp_path)
    monkeypatch.setattr("app.services.extraction.pdf_extractor.PdfReader", None)
    with pytest.raises(ExtractorUnavailableError) as ei:
        PdfExtractor(settings=settings)
    assert "pdf" in str(ei.value).lower()


def test_pdf_extractor_extracts_page_text_and_metadata(pypdf_available: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    settings = _settings(monkeypatch, tmp_path)
    store = RawSourceStore(settings)
    raw = store.persist(filename="unit.pdf", content_bytes=_MINIMAL_HELLO_PDF)
    artifact = _artifact_for_pdf(raw=raw, pdf_bytes=_MINIMAL_HELLO_PDF)

    ext = PdfExtractor(settings=settings)
    cands = ext.extract(artifact)

    assert len(cands) == 1
    c = cands[0]
    assert c.modality == Modality.pdf
    assert c.content_type == "pdf_page_text"
    assert c.source_fidelity == SourceFidelity.extracted
    assert "Hello" in c.text
    assert c.location.get("page") == 1
    assert c.metadata is not None
    assert c.metadata.get("extractor") == "pypdf"
    assert c.metadata.get("page_count") == 1


def test_pdf_extractor_bad_bytes_raises(pypdf_available: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    settings = _settings(monkeypatch, tmp_path)
    bad = b"not a pdf"
    store = RawSourceStore(settings)
    raw = store.persist(filename="bad.pdf", content_bytes=bad)
    artifact = _artifact_for_pdf(raw=raw, pdf_bytes=bad)

    ext = PdfExtractor(settings=settings)
    with pytest.raises(PdfExtractionError):
        ext.extract(artifact)


def test_pdf_extractor_blank_pages_skipped_then_no_evidence(pypdf_available: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from io import BytesIO

    from pypdf import PdfWriter

    settings = _settings(monkeypatch, tmp_path)
    buf = BytesIO()
    w = PdfWriter()
    w.add_blank_page(width=72, height=72)
    w.add_blank_page(width=72, height=72)
    w.write(buf)
    blank_pdf = buf.getvalue()
    store = RawSourceStore(settings)
    raw = store.persist(filename="blank.pdf", content_bytes=blank_pdf)
    artifact = _artifact_for_pdf(raw=raw, pdf_bytes=blank_pdf)

    ext = PdfExtractor(settings=settings)
    with pytest.raises(ExtractionReturnedNoEvidenceError):
        ext.extract(artifact)


@pytest.mark.asyncio
async def test_post_pdf_returns_503_when_pypdf_unavailable(db_ready: None, monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx
    from httpx import ASGITransport

    import app.services.extraction.pdf_extractor as pe

    monkeypatch.setattr(pe, "PdfReader", None)
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            files={"file": ("hello.pdf", _MINIMAL_HELLO_PDF, "application/pdf")},
        )
    assert res.status_code == 503
    assert "pdf" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_post_pdf_creates_artifact_and_evidence(db_ready: None) -> None:
    pytest.importorskip("pypdf")
    import httpx
    from httpx import ASGITransport

    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            files={"file": ("hello.pdf", _MINIMAL_HELLO_PDF, "application/pdf")},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["artifact_type"] == "pdf"
    assert data["evidence_unit_count"] >= 1

    aid = data["artifact_id"]
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        ev = await client.get(f"/artifacts/{aid}/evidence")
    assert ev.status_code == 200
    items = ev.json()["items"]
    assert len(items) >= 1
    assert any("Hello" in (it.get("text") or "") for it in items)
