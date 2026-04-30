from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path

import pytest

from app.core import config as config_module
from app.models.artifact import Artifact
from app.models.enums import Modality
from app.services.errors import ExtractorUnavailableError, ImageExtractionError
from app.services.extraction.image_extractor import ImageExtractor
from app.services.ingestion.artifact_type_resolver import resolve_from_filename_and_mime
from app.services.raw_source_store import RawSourceStore

# Minimal valid 1x1 RGBA PNG (Pillow can decode).
_MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
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


def _artifact_for_image(*, raw: object, png_bytes: bytes) -> Artifact:
    ck = hashlib.sha256(png_bytes).hexdigest()
    return Artifact(
        id=uuid.uuid4(),
        filename="unit.png",
        title=None,
        artifact_type="image",
        mime_type="image/png",
        storage_uri=raw.storage_uri,
        checksum=ck,
        size_bytes=len(png_bytes),
        raw_text=raw.raw_text,
        metadata_json=None,
    )


@pytest.fixture()
def pillow_available() -> None:
    pytest.importorskip("PIL")


def test_image_extractor_requires_image_extra(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    settings = _settings(monkeypatch, tmp_path)
    monkeypatch.setattr("app.services.extraction.image_extractor.Image", None)
    with pytest.raises(ExtractorUnavailableError) as ei:
        ImageExtractor(settings=settings)
    assert "image" in str(ei.value).lower()


def test_image_extractor_validates_png_then_raises_extractor_unavailable(
    pillow_available: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    settings = _settings(monkeypatch, tmp_path)
    store = RawSourceStore(settings)
    raw = store.persist(filename="unit.png", content_bytes=_MINIMAL_PNG)
    artifact = _artifact_for_image(raw=raw, png_bytes=_MINIMAL_PNG)

    ext = ImageExtractor(settings=settings)
    with pytest.raises(ExtractorUnavailableError) as ei:
        ext.extract(artifact)
    msg = str(ei.value).lower()
    assert "ocr" in msg or "caption" in msg
    assert "not configured" in msg or "later slice" in msg


def test_image_extractor_corrupt_bytes_raises(
    pillow_available: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    settings = _settings(monkeypatch, tmp_path)
    bad = b"not a real png"
    store = RawSourceStore(settings)
    raw = store.persist(filename="bad.png", content_bytes=bad)
    artifact = _artifact_for_image(raw=raw, png_bytes=bad)

    ext = ImageExtractor(settings=settings)
    with pytest.raises(ImageExtractionError):
        ext.extract(artifact)


def test_image_extractor_wrong_artifact_type_raises(
    pillow_available: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    settings = _settings(monkeypatch, tmp_path)
    ext = ImageExtractor(settings=settings)
    wrong = Artifact(
        id=uuid.uuid4(),
        filename="x.pdf",
        title=None,
        artifact_type="pdf",
        mime_type="application/pdf",
        storage_uri="x",
        checksum="a" * 64,
        size_bytes=1,
        raw_text=None,
        metadata_json=None,
    )
    with pytest.raises(ImageExtractionError):
        ext.extract(wrong)


def test_resolver_maps_png_to_image_modality() -> None:
    r = resolve_from_filename_and_mime(filename="a.png", mime_type="image/png")
    assert r.artifact_type == "image"
    assert r.modality == Modality.image


@pytest.mark.asyncio
async def test_post_png_returns_503_ocr_not_configured(db_ready: None) -> None:
    pytest.importorskip("PIL")
    import httpx
    from httpx import ASGITransport

    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            files={"file": ("p.png", _MINIMAL_PNG, "image/png")},
        )
    assert res.status_code == 503
    detail = res.json()["detail"].lower()
    assert "ocr" in detail or "caption" in detail


@pytest.mark.asyncio
async def test_post_png_returns_503_when_pillow_unavailable(
    db_ready: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    import httpx
    from httpx import ASGITransport

    import app.services.extraction.image_extractor as ie

    monkeypatch.setattr(ie, "Image", None)
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            files={"file": ("p.png", _MINIMAL_PNG, "image/png")},
        )
    assert res.status_code == 503
    assert "image" in res.json()["detail"].lower()
