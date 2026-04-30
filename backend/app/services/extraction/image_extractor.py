from __future__ import annotations

from io import BytesIO

from app.core.config import Settings
from app.models.artifact import Artifact
from app.schemas.evidence_unit_candidate import EvidenceUnitCandidate
from app.services.errors import ExtractorUnavailableError, ImageExtractionError
from app.services.raw_source_store import RawSourceStore

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore[misc, assignment]

_OCR_NOT_CONFIGURED = (
    "Image OCR/caption extraction is not configured. "
    "Install/enable an OCR or caption backend in a later slice."
)


class ImageExtractor:
    """Validate image bytes with Pillow (Phase 5 Slice F shell).

    Does not emit ``EvidenceUnitCandidate`` yet: after validation raises
    ``ExtractorUnavailableError`` until an OCR/caption backend is approved.

    Reserved future ``content_type`` values: ``image_ocr_text``, ``image_caption``,
    ``image_visual_summary`` (not used in this slice).

    Requires the ``image`` optional extra (Pillow). Does not persist or mutate ``Artifact``.
    """

    def __init__(self, *, settings: Settings) -> None:
        if Image is None:
            raise ExtractorUnavailableError(
                "Image handling requires the optional `image` dependency "
                "(e.g. pip install -e '.[image]' for graphclerk-backend).",
            )
        self._settings = settings
        self._raw_store = RawSourceStore(settings)

    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        if artifact.artifact_type != "image":
            raise ImageExtractionError(
                f"ImageExtractor expected artifact_type 'image', got {artifact.artifact_type!r}.",
            )

        image_bytes = self._raw_store.read_persisted_bytes(
            storage_uri=artifact.storage_uri,
            checksum=artifact.checksum,
            filename=artifact.filename,
            raw_text=artifact.raw_text,
        )

        buf = BytesIO(image_bytes)
        try:
            with Image.open(buf) as im:
                im.load()
                width, height = im.size
        except (OSError, ValueError) as e:
            raise ImageExtractionError(f"Invalid or unreadable image: {e}") from e

        if width < 1 or height < 1:
            raise ImageExtractionError("Invalid image dimensions.")

        raise ExtractorUnavailableError(_OCR_NOT_CONFIGURED)
