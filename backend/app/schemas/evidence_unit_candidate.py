from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.enums import Modality, SourceFidelity


@dataclass(frozen=True)
class EvidenceUnitCandidate:
    """Internal parser output before persistence (Phase 2)."""

    modality: Modality
    content_type: str
    text: str
    location: dict[str, Any]
    source_fidelity: SourceFidelity
    confidence: float

