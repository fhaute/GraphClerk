from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.enums import Modality, SourceFidelity
from app.services.errors import InvalidEvidenceUnitCandidateError, InvalidSourceFidelityError


@dataclass(frozen=True)
class EvidenceUnitCandidate:
    """Internal parser output before persistence (Phase 2+).

    Phase 5: ``text`` is always required and must be non-empty after stripping
    whitespace (every extractor must emit a text representation). ``source_fidelity``
    must be one of: verbatim, extracted, derived, computed.
    """

    modality: Modality
    content_type: str
    text: str
    location: dict[str, Any]
    source_fidelity: SourceFidelity | str
    confidence: float
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise InvalidEvidenceUnitCandidateError("EvidenceUnitCandidate.text must be a str.")
        if not self.text.strip():
            raise InvalidEvidenceUnitCandidateError(
                "EvidenceUnitCandidate.text must be non-empty (whitespace-only is not allowed).",
            )

        fid = self.source_fidelity
        if isinstance(fid, SourceFidelity):
            normalized = fid
        elif isinstance(fid, str):
            try:
                normalized = SourceFidelity(fid)
            except ValueError as e:
                raise InvalidSourceFidelityError(
                    f"Invalid source_fidelity {fid!r}; expected one of: "
                    f"{', '.join(repr(m.value) for m in SourceFidelity)}.",
                ) from e
            object.__setattr__(self, "source_fidelity", normalized)
        else:
            raise InvalidSourceFidelityError(
                f"source_fidelity must be str or SourceFidelity, not {type(fid).__name__}.",
            )
