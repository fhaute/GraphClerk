from __future__ import annotations

from io import BytesIO

from app.core.config import Settings
from app.models.artifact import Artifact
from app.schemas.evidence_unit_candidate import EvidenceUnitCandidate
from app.services.errors import AudioExtractionError, ExtractorUnavailableError
from app.services.raw_source_store import RawSourceStore

try:
    from mutagen import File as MutagenFile
    from mutagen import MutagenError
except ImportError:
    MutagenFile = None  # type: ignore[misc, assignment]
    MutagenError = OSError  # type: ignore[misc, assignment]

_TRANSCRIPTION_NOT_CONFIGURED = (
    "Audio transcription is not configured. "
    "Enable an approved transcription backend in a later slice."
)


class AudioExtractor:
    """Validate audio bytes with mutagen (Phase 5 Slice G shell).

    Does not emit ``EvidenceUnitCandidate`` yet: after validation raises
    ``ExtractorUnavailableError`` until an ASR/transcription backend is approved.

    Reserved future ``content_type``: ``audio_transcript_segment`` (not used in this slice).
    Future ASR evidence should use ``SourceFidelity.extracted``.

    Requires the ``audio`` optional extra (mutagen). Does not persist or mutate ``Artifact``.
    """

    def __init__(self, *, settings: Settings) -> None:
        if MutagenFile is None:
            raise ExtractorUnavailableError(
                "Audio handling requires the optional `audio` dependency "
                "(e.g. pip install -e '.[audio]' for graphclerk-backend).",
            )
        self._settings = settings
        self._raw_store = RawSourceStore(settings)

    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        if artifact.artifact_type != "audio":
            raise AudioExtractionError(
                f"AudioExtractor expected artifact_type 'audio', got {artifact.artifact_type!r}.",
            )

        audio_bytes = self._raw_store.read_persisted_bytes(
            storage_uri=artifact.storage_uri,
            checksum=artifact.checksum,
            filename=artifact.filename,
            raw_text=artifact.raw_text,
        )

        hint_name = artifact.filename or "upload.wav"
        buf = BytesIO(audio_bytes)
        try:
            mut = MutagenFile(buf, filename=hint_name)
        except MutagenError as e:
            raise AudioExtractionError(f"Invalid or unreadable audio: {e}") from e

        if mut is None:
            raise AudioExtractionError("Unsupported or unreadable audio format.")

        # Probed for future ASR metadata: format class, optional duration from mutagen.info.
        _ = type(mut).__name__, (
            getattr(mut.info, "length", None) if getattr(mut, "info", None) is not None else None
        )

        raise ExtractorUnavailableError(_TRANSCRIPTION_NOT_CONFIGURED)
