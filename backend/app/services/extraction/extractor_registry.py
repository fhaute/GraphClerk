from __future__ import annotations

from app.models.enums import Modality
from app.services.errors import ExtractorNotRegisteredError
from app.services.extraction.artifact_extractor import ArtifactExtractor


class ExtractorRegistry:
    """Maps ``Modality`` to multimodal ``ArtifactExtractor`` implementations.

    Starts empty: no video and no text/markdown extractors are registered by
    default (text/Markdown ingestion remains ``TextIngestionService``).
    """

    __slots__ = ("_extractors",)

    def __init__(self) -> None:
        self._extractors: dict[Modality, ArtifactExtractor] = {}

    def register(self, modality: Modality, extractor: ArtifactExtractor) -> None:
        self._extractors[modality] = extractor

    def get(self, modality: Modality) -> ArtifactExtractor:
        try:
            return self._extractors[modality]
        except KeyError:
            raise ExtractorNotRegisteredError(
                f"No extractor is registered for modality {modality.value!r}.",
            ) from None
