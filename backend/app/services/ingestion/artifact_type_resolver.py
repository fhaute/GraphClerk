from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.models.enums import Modality
from app.services.errors import UnsupportedArtifactTypeError

_VIDEO_MESSAGE = "Video ingestion is not supported."

_MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})
_VIDEO_SUFFIXES = frozenset({".mp4", ".webm", ".mov", ".mkv", ".avi"})
_IMAGE_SUFFIXES = frozenset({
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff",
    ".svg",
})
_AUDIO_SUFFIXES = frozenset({
    ".mp3",
    ".wav",
    ".m4a",
    ".ogg",
    ".flac",
    ".aac",
    ".opus",
})
_GENERIC_SUFFIXES = frozenset({".dat", ".bin"})
_PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

_SUPPORTED = frozenset({"text", "markdown", "pdf", "pptx", "image", "audio"})


@dataclass(frozen=True)
class ResolvedArtifactType:
    """Multipart classification: persisted ``artifact_type`` and routing ``Modality``."""

    artifact_type: str
    modality: Modality


def supported_artifact_types() -> frozenset[str]:
    return _SUPPORTED


def modality_for_artifact_type(artifact_type: str) -> Modality:
    """Map ``artifact_type`` to ``Modality`` (canonical table; same as multipart resolution)."""

    mapping: dict[str, Modality] = {
        "text": Modality.text,
        "markdown": Modality.text,
        "pdf": Modality.pdf,
        "pptx": Modality.slide,
        "image": Modality.image,
        "audio": Modality.audio,
    }
    try:
        return mapping[artifact_type]
    except KeyError as e:
        raise UnsupportedArtifactTypeError(
            f"Unsupported artifact_type for modality mapping: {artifact_type!r}.",
        ) from e


def _suffix_lower(filename: str) -> str:
    return Path(filename.strip().lower()).suffix


def _suffix_binds_known_non_video_type(filename: str) -> ResolvedArtifactType | None:
    """Return a type when the suffix alone is authoritative; ``None`` if MIME should decide."""

    suffix = _suffix_lower(filename)

    if suffix in _VIDEO_SUFFIXES:
        raise UnsupportedArtifactTypeError(_VIDEO_MESSAGE)
    if suffix in _MARKDOWN_SUFFIXES:
        return ResolvedArtifactType("markdown", Modality.text)
    if suffix == ".txt":
        return ResolvedArtifactType("text", Modality.text)
    if suffix == ".pdf":
        return ResolvedArtifactType("pdf", Modality.pdf)
    if suffix == ".pptx":
        return ResolvedArtifactType("pptx", Modality.slide)
    if suffix in _IMAGE_SUFFIXES:
        return ResolvedArtifactType("image", Modality.image)
    if suffix in _AUDIO_SUFFIXES:
        return ResolvedArtifactType("audio", Modality.audio)
    return None


def _suffix_is_missing_generic_or_unknown(filename: str) -> bool:
    """True when MIME may refine type (extension missing, generic, or not in our tables)."""

    suffix = _suffix_lower(filename)
    if suffix == "":
        return True
    if suffix in _GENERIC_SUFFIXES:
        return True
    known = (
        _MARKDOWN_SUFFIXES
        | {".txt", ".pdf", ".pptx"}
        | _IMAGE_SUFFIXES
        | _AUDIO_SUFFIXES
        | _VIDEO_SUFFIXES
    )
    return suffix not in known


def _resolve_from_mime(*, filename: str, mime_lower: str) -> ResolvedArtifactType:
    if mime_lower.startswith("video/"):
        raise UnsupportedArtifactTypeError(_VIDEO_MESSAGE)
    if mime_lower in ("text/markdown", "text/x-markdown"):
        return ResolvedArtifactType("markdown", Modality.text)
    if mime_lower == "text/plain":
        return ResolvedArtifactType("text", Modality.text)
    if mime_lower == "application/pdf":
        return ResolvedArtifactType("pdf", Modality.pdf)
    if mime_lower == _PPTX_MIME:
        return ResolvedArtifactType("pptx", Modality.slide)
    if mime_lower.startswith("image/"):
        return ResolvedArtifactType("image", Modality.image)
    if mime_lower.startswith("audio/"):
        return ResolvedArtifactType("audio", Modality.audio)
    raise UnsupportedArtifactTypeError(f"Unsupported file type for ingestion: {filename!r}.")


def resolve_from_filename_and_mime(*, filename: str, mime_type: str | None) -> ResolvedArtifactType:
    """Classify multipart upload: known extension wins; MIME refines when extension is unhelpful."""

    mime_lower = (mime_type or "").strip().lower()

    bound = _suffix_binds_known_non_video_type(filename)
    if bound is not None:
        return bound

    if _suffix_is_missing_generic_or_unknown(filename):
        return _resolve_from_mime(filename=filename, mime_lower=mime_lower)

    return _resolve_from_mime(filename=filename, mime_lower=mime_lower)
