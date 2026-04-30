from __future__ import annotations

import pytest
import httpx
from httpx import ASGITransport

from app.api.routes import artifacts as artifacts_routes
from app.main import create_app
from app.models.artifact import Artifact
from app.models.enums import Modality, SourceFidelity
from app.schemas.evidence_unit_candidate import EvidenceUnitCandidate
from app.services.errors import ExtractorUnavailableError
from app.services.extraction import ExtractorRegistry


class _PdfStubExtractor:
    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        return [
            EvidenceUnitCandidate(
                modality=Modality.pdf,
                content_type="stub_unit",
                text="stub extracted body",
                location={"page": 1},
                source_fidelity=SourceFidelity.extracted,
                confidence=1.0,
            )
        ]


class _UnavailableExtractor:
    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        raise ExtractorUnavailableError("extractor stub unavailable")


class _EmptyListExtractor:
    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        return []


@pytest.mark.asyncio
async def test_phase2_text_json_ingestion_unchanged(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            json={"filename": "a.txt", "artifact_type": "text", "text": "Hello\n\nWorld\n"},
        )
    assert res.status_code == 200
    assert res.json()["evidence_unit_count"] == 2


@pytest.mark.asyncio
async def test_phase2_markdown_json_ingestion_unchanged(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            json={
                "filename": "a.md",
                "artifact_type": "markdown",
                "text": "# H1\n\nParagraph.\n",
            },
        )
    assert res.status_code == 200
    assert res.json()["evidence_unit_count"] >= 1


@pytest.mark.asyncio
async def test_multimodal_pdf_without_registered_extractor_returns_400(db_ready: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(artifacts_routes, "get_multimodal_extractor_registry", lambda: ExtractorRegistry())
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/artifacts", files={"file": ("x.pdf", b"%PDF-1.4 minimal", "application/pdf")})
    assert res.status_code == 400
    body = res.json()
    assert "detail" in body
    assert "pdf" in body["detail"].lower() or "extractor" in body["detail"].lower()


@pytest.mark.asyncio
async def test_multimodal_pptx_without_registered_extractor_returns_400(
    db_ready: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        artifacts_routes,
        "get_multimodal_extractor_registry",
        lambda: ExtractorRegistry(),
    )
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            files={
                "file": (
                    "x.pptx",
                    b"PK\x03\x04",
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                )
            },
        )
    assert res.status_code == 400
    body = res.json()
    assert "detail" in body
    assert "slide" in body["detail"].lower() or "extractor" in body["detail"].lower()


@pytest.mark.asyncio
async def test_multimodal_image_without_registered_extractor_returns_400(
    db_ready: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        artifacts_routes,
        "get_multimodal_extractor_registry",
        lambda: ExtractorRegistry(),
    )
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            files={
                "file": (
                    "x.png",
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01",
                    "image/png",
                )
            },
        )
    assert res.status_code == 400
    body = res.json()
    assert "detail" in body
    assert "image" in body["detail"].lower() or "extractor" in body["detail"].lower()


@pytest.mark.asyncio
async def test_multimodal_pdf_with_stub_extractor_succeeds(db_ready: None, monkeypatch: pytest.MonkeyPatch) -> None:
    reg = ExtractorRegistry()
    reg.register(Modality.pdf, _PdfStubExtractor())
    monkeypatch.setattr(artifacts_routes, "get_multimodal_extractor_registry", lambda: reg)

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/artifacts", files={"file": ("doc.pdf", b"%PDF-1.4 stub", "application/pdf")})
    assert res.status_code == 200
    data = res.json()
    assert data["artifact_type"] == "pdf"
    assert data["evidence_unit_count"] == 1


@pytest.mark.asyncio
async def test_extractor_unavailable_returns_503(db_ready: None, monkeypatch: pytest.MonkeyPatch) -> None:
    reg = ExtractorRegistry()
    reg.register(Modality.image, _UnavailableExtractor())
    monkeypatch.setattr(artifacts_routes, "get_multimodal_extractor_registry", lambda: reg)

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            files={"file": ("p.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01", "image/png")},
        )
    assert res.status_code == 503


@pytest.mark.asyncio
async def test_extractor_empty_candidates_returns_400(db_ready: None, monkeypatch: pytest.MonkeyPatch) -> None:
    reg = ExtractorRegistry()
    reg.register(Modality.audio, _EmptyListExtractor())
    monkeypatch.setattr(artifacts_routes, "get_multimodal_extractor_registry", lambda: reg)

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/artifacts", files={"file": ("a.wav", b"RIFF\x24\x00\x00\x00WAVEfmt ", "audio/wav")})
    assert res.status_code == 400
    assert res.json()["detail"] == "extraction_returned_no_evidence"


@pytest.mark.asyncio
async def test_unsupported_extension_returns_400(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/artifacts", files={"file": ("x.exe", b"MZ", "application/octet-stream")})
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_video_returns_400(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/artifacts", files={"file": ("v.mp4", b"\x00\x00\x00", "video/mp4")})
    assert res.status_code == 400
    assert "video" in res.json()["detail"].lower()
