from __future__ import annotations

import pytest

from app.models.enums import Modality
from app.services.errors import UnsupportedArtifactTypeError
from app.services.ingestion.artifact_type_resolver import (
    modality_for_artifact_type,
    resolve_from_filename_and_mime,
    supported_artifact_types,
)

_PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def _r(filename: str, mime: str | None = None) -> tuple[str, Modality]:
    x = resolve_from_filename_and_mime(filename=filename, mime_type=mime)
    return x.artifact_type, x.modality


def test_txt_and_text_plain() -> None:
    assert _r("a.txt", "text/plain") == ("text", Modality.text)
    assert _r("a.txt", None) == ("text", Modality.text)


def test_markdown_extensions_and_mime() -> None:
    assert _r("a.md", None) == ("markdown", Modality.text)
    assert _r("a.markdown", "text/plain") == ("markdown", Modality.text)
    assert _r("notes", "text/markdown") == ("markdown", Modality.text)
    assert _r("notes", "text/x-markdown") == ("markdown", Modality.text)


def test_pdf_and_application_pdf() -> None:
    assert _r("report.pdf", "application/pdf") == ("pdf", Modality.pdf)
    assert _r("report.pdf", "application/octet-stream") == ("pdf", Modality.pdf)


def test_pptx_and_ooxml_mime() -> None:
    assert _r("slides.pptx", _PPTX_MIME) == ("pptx", Modality.slide)
    assert _r("slides.pptx", "application/octet-stream") == ("pptx", Modality.slide)


def test_image_extension_and_image_mime() -> None:
    assert _r("x.png", "image/png") == ("image", Modality.image)
    assert _r("x.gif", "application/octet-stream") == ("image", Modality.image)
    assert _r("file.dat", "image/jpeg") == ("image", Modality.image)


def test_audio_extension_and_audio_mime() -> None:
    assert _r("a.mp3", "audio/mpeg") == ("audio", Modality.audio)
    assert _r("file.bin", "audio/mpeg") == ("audio", Modality.audio)


def test_known_extension_wins_over_wrong_mime() -> None:
    assert _r("notes.md", "text/plain") == ("markdown", Modality.text)


def test_dat_with_pdf_mime() -> None:
    assert _r("file.dat", "application/pdf") == ("pdf", Modality.pdf)


def test_video_extension_with_octet_stream() -> None:
    with pytest.raises(UnsupportedArtifactTypeError) as ei:
        resolve_from_filename_and_mime(filename="movie.mp4", mime_type="application/octet-stream")
    assert "video" in str(ei.value).lower()


def test_video_mime_with_dat_extension() -> None:
    with pytest.raises(UnsupportedArtifactTypeError) as ei:
        resolve_from_filename_and_mime(filename="movie.dat", mime_type="video/mp4")
    assert "video" in str(ei.value).lower()


def test_unknown_with_octet_stream() -> None:
    with pytest.raises(UnsupportedArtifactTypeError) as ei:
        resolve_from_filename_and_mime(filename="x.exe", mime_type="application/octet-stream")
    assert "unsupported" in str(ei.value).lower() or "ingestion" in str(ei.value).lower()


def test_supported_artifact_types() -> None:
    s = supported_artifact_types()
    assert s == frozenset({"text", "markdown", "pdf", "pptx", "image", "audio"})
    assert "video" not in s


@pytest.mark.parametrize(
    ("artifact_type", "expected_modality"),
    [
        ("text", Modality.text),
        ("markdown", Modality.text),
        ("pdf", Modality.pdf),
        ("pptx", Modality.slide),
        ("image", Modality.image),
        ("audio", Modality.audio),
    ],
)
def test_modality_for_artifact_type_matches_resolve(
    artifact_type: str, expected_modality: Modality
) -> None:
    assert modality_for_artifact_type(artifact_type) == expected_modality


def test_modality_for_artifact_type_unknown() -> None:
    with pytest.raises(UnsupportedArtifactTypeError) as ei:
        modality_for_artifact_type("video")
    assert "modality" in str(ei.value).lower() or "unsupported" in str(ei.value).lower()


def test_modality_for_artifact_type_typo() -> None:
    with pytest.raises(UnsupportedArtifactTypeError):
        modality_for_artifact_type("pdff")
