from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.models.artifact import Artifact
from app.schemas.evidence_unit_candidate import EvidenceUnitCandidate


@runtime_checkable
class ArtifactExtractor(Protocol):
    """Multimodal extraction contract (Phase 5).

    Implementations return ``EvidenceUnitCandidate`` rows only; they must not
    persist data or mutate ``Artifact``. Optional deps must surface as
    ``ExtractorUnavailableError`` from the implementation (Slice B has no
    orchestration here). Source bytes/path context is out of scope for Slice B
    and may be introduced in Slice C via an explicit orchestration type.
    """

    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        """Produce evidence candidates from ``artifact`` without side effects."""
