from __future__ import annotations

from io import BytesIO
from typing import Any

from app.core.config import Settings
from app.models.artifact import Artifact
from app.models.enums import Modality, SourceFidelity
from app.schemas.evidence_unit_candidate import EvidenceUnitCandidate
from app.services.errors import (
    ExtractionReturnedNoEvidenceError,
    ExtractorUnavailableError,
    PdfExtractionError,
)
from app.services.raw_source_store import RawSourceStore

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None  # type: ignore[misc, assignment]


class PdfExtractor:
    """Extract selectable text from PDF pages using pypdf (Phase 5 Slice D).

    Requires the ``pdf`` optional extra. Does not persist or mutate ``Artifact``.
    """

    def __init__(self, *, settings: Settings) -> None:
        if PdfReader is None:
            raise ExtractorUnavailableError(
                "PDF extraction requires the optional `pdf` dependency "
                "(e.g. pip install -e '.[pdf]' for graphclerk-backend).",
            )
        self._settings = settings
        self._raw_store = RawSourceStore(settings)

    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        if artifact.artifact_type != "pdf":
            raise PdfExtractionError(f"PdfExtractor expected artifact_type 'pdf', got {artifact.artifact_type!r}.")

        pdf_bytes = self._raw_store.read_persisted_bytes(
            storage_uri=artifact.storage_uri,
            checksum=artifact.checksum,
            filename=artifact.filename,
            raw_text=artifact.raw_text,
        )

        try:
            reader = PdfReader(BytesIO(pdf_bytes), strict=False)
        except Exception as e:
            raise PdfExtractionError(f"Invalid or unreadable PDF: {e}") from e

        page_count = len(reader.pages)
        candidates: list[EvidenceUnitCandidate] = []

        for i, page in enumerate(reader.pages):
            try:
                raw_page_text = page.extract_text() or ""
            except Exception as e:
                raise PdfExtractionError(f"Failed to extract text from PDF page {i + 1}: {e}") from e
            text = raw_page_text.strip()
            if not text:
                continue
            page_num = i + 1
            meta: dict[str, Any] = {"page_count": page_count, "extractor": "pypdf"}
            candidates.append(
                EvidenceUnitCandidate(
                    modality=Modality.pdf,
                    content_type="pdf_page_text",
                    text=text,
                    location={"page": page_num},
                    source_fidelity=SourceFidelity.extracted,
                    confidence=1.0,
                    metadata=meta,
                )
            )

        if not candidates:
            raise ExtractionReturnedNoEvidenceError()

        return candidates
