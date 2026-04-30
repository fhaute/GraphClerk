from __future__ import annotations

import hashlib
import io
import os
import uuid
import wave
from pathlib import Path

import pytest

from app.core import config as config_module
from app.models.artifact import Artifact
from app.models.enums import Modality
from app.services.errors import AudioExtractionError, ExtractorUnavailableError
from app.services.extraction.audio_extractor import AudioExtractor
from app.services.ingestion.artifact_type_resolver import resolve_from_filename_and_mime
from app.services.raw_source_store import RawSourceStore


def _minimal_wav_bytes() -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(8000)
        wf.writeframes(b"\x00\x00" * 8)
    return buf.getvalue()


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


def _artifact_for_audio(*, raw: object, audio_bytes: bytes, filename: str = "unit.wav") -> Artifact:
    ck = hashlib.sha256(audio_bytes).hexdigest()
    return Artifact(
        id=uuid.uuid4(),
        filename=filename,
        title=None,
        artifact_type="audio",
        mime_type="audio/wav",
        storage_uri=raw.storage_uri,
        checksum=ck,
        size_bytes=len(audio_bytes),
        raw_text=raw.raw_text,
        metadata_json=None,
    )


@pytest.fixture()
def mutagen_available() -> None:
    pytest.importorskip("mutagen")


def test_audio_extractor_requires_audio_extra(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    settings = _settings(monkeypatch, tmp_path)
    monkeypatch.setattr("app.services.extraction.audio_extractor.MutagenFile", None)
    with pytest.raises(ExtractorUnavailableError) as ei:
        AudioExtractor(settings=settings)
    assert "audio" in str(ei.value).lower()


def test_audio_extractor_validates_wav_then_raises_extractor_unavailable(
    mutagen_available: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    settings = _settings(monkeypatch, tmp_path)
    wav = _minimal_wav_bytes()
    store = RawSourceStore(settings)
    raw = store.persist(filename="unit.wav", content_bytes=wav)
    artifact = _artifact_for_audio(raw=raw, audio_bytes=wav)

    ext = AudioExtractor(settings=settings)
    with pytest.raises(ExtractorUnavailableError) as ei:
        ext.extract(artifact)
    msg = str(ei.value).lower()
    assert "transcription" in msg
    assert "not configured" in msg or "later slice" in msg


def test_audio_extractor_corrupt_bytes_raises(
    mutagen_available: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    settings = _settings(monkeypatch, tmp_path)
    bad = b"not valid audio"
    store = RawSourceStore(settings)
    raw = store.persist(filename="bad.wav", content_bytes=bad)
    artifact = _artifact_for_audio(raw=raw, audio_bytes=bad)

    ext = AudioExtractor(settings=settings)
    with pytest.raises(AudioExtractionError):
        ext.extract(artifact)


def test_audio_extractor_wrong_artifact_type_raises(
    mutagen_available: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    settings = _settings(monkeypatch, tmp_path)
    ext = AudioExtractor(settings=settings)
    wrong = Artifact(
        id=uuid.uuid4(),
        filename="x.png",
        title=None,
        artifact_type="image",
        mime_type="image/png",
        storage_uri="x",
        checksum="a" * 64,
        size_bytes=1,
        raw_text=None,
        metadata_json=None,
    )
    with pytest.raises(AudioExtractionError):
        ext.extract(wrong)


def test_resolver_maps_wav_and_audio_mime() -> None:
    r = resolve_from_filename_and_mime(filename="a.wav", mime_type="audio/wav")
    assert r.artifact_type == "audio"
    assert r.modality == Modality.audio
    r2 = resolve_from_filename_and_mime(filename="track", mime_type="audio/mpeg")
    assert r2.artifact_type == "audio"
    assert r2.modality == Modality.audio


@pytest.mark.asyncio
async def test_post_wav_returns_503_transcription_not_configured(db_ready: None) -> None:
    pytest.importorskip("mutagen")
    import httpx
    from httpx import ASGITransport

    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    payload = _minimal_wav_bytes()
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            files={"file": ("a.wav", payload, "audio/wav")},
        )
    assert res.status_code == 503
    detail = res.json()["detail"].lower()
    assert "transcription" in detail


@pytest.mark.asyncio
async def test_post_wav_returns_503_when_mutagen_unavailable(
    db_ready: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    import httpx
    from httpx import ASGITransport

    import app.services.extraction.audio_extractor as ae

    monkeypatch.setattr(ae, "MutagenFile", None)
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    payload = _minimal_wav_bytes()
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            files={"file": ("a.wav", payload, "audio/wav")},
        )
    assert res.status_code == 503
    assert "audio" in res.json()["detail"].lower()
