"""EvidenceUnitCandidate schema — extractor output before EvidenceUnit persistence.

Phase 7 Slice 7B: optional **language routing metadata** may appear under ``metadata``
using the canonical keys below. Language metadata is not evidence and must never
replace or rewrite ``text`` or ``source_fidelity``. This slice validates shape only;
it does not detect or infer language.

Canonical optional metadata keys (all optional; omit any unused field):

- ``language`` — ``str`` or ``None``
- ``language_confidence`` — finite ``float`` or ``int`` in ``[0.0, 1.0]``, or ``None``
- ``language_detection_method`` — ``str`` or ``None``
- ``language_warnings`` — ``list[str]`` (empty list allowed)

Other metadata keys are ignored by language validation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from app.models.enums import Modality, SourceFidelity
from app.services.errors import (
    InvalidEvidenceUnitCandidateError,
    InvalidLanguageMetadataError,
    InvalidSourceFidelityError,
)

LANGUAGE_METADATA_KEY_LANGUAGE = "language"
LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE = "language_confidence"
LANGUAGE_METADATA_KEY_LANGUAGE_DETECTION_METHOD = "language_detection_method"
LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS = "language_warnings"


def validate_optional_language_metadata(metadata: dict[str, Any] | None) -> None:
    """Validate Phase 7 language-related entries inside ``metadata``, if any.

    Callers may omit all language keys; behavioral parity with pre–Phase 7 candidates
    is preserved. Does not mutate ``metadata``.

    Raises:
        InvalidLanguageMetadataError: When a present language key has an illegal type or value.
    """

    if metadata is None:
        return

    lk = LANGUAGE_METADATA_KEY_LANGUAGE
    if lk in metadata:
        v = metadata[lk]
        if v is not None and not isinstance(v, str):
            raise InvalidLanguageMetadataError(
                f"metadata[{lk!r}] must be str or None, not {type(v).__name__}.",
            )

    lck = LANGUAGE_METADATA_KEY_LANGUAGE_CONFIDENCE
    if lck in metadata:
        v = metadata[lck]
        if v is None:
            pass
        elif isinstance(v, bool):
            raise InvalidLanguageMetadataError(
                f"metadata[{lck!r}] must be a finite number in [0.0, 1.0] or None.",
            )
        elif isinstance(v, (int, float)):
            x = float(v)
            if not math.isfinite(x) or x < 0.0 or x > 1.0:
                raise InvalidLanguageMetadataError(
                    f"metadata[{lck!r}] must be between 0.0 and 1.0 (got {v!r}).",
                )
        else:
            raise InvalidLanguageMetadataError(
                f"metadata[{lck!r}] must be a finite number in [0.0, 1.0] or None.",
            )

    lmk = LANGUAGE_METADATA_KEY_LANGUAGE_DETECTION_METHOD
    if lmk in metadata:
        v = metadata[lmk]
        if v is not None and not isinstance(v, str):
            raise InvalidLanguageMetadataError(
                f"metadata[{lmk!r}] must be str or None, not {type(v).__name__}.",
            )

    lwk = LANGUAGE_METADATA_KEY_LANGUAGE_WARNINGS
    if lwk in metadata:
        v = metadata[lwk]
        if not isinstance(v, list):
            raise InvalidLanguageMetadataError(
                f"metadata[{lwk!r}] must be a list[str], not {type(v).__name__}.",
            )
        for i, item in enumerate(v):
            if not isinstance(item, str):
                raise InvalidLanguageMetadataError(
                    f"metadata[{lwk!r}][{i}] must be str, not {type(item).__name__}.",
                )


@dataclass(frozen=True)
class EvidenceUnitCandidate:
    """Internal parser output before persistence (Phase 2+).

    Phase 5: ``text`` is always required and must be non-empty after stripping
    whitespace (every extractor must emit a text representation). ``source_fidelity``
    must be one of: verbatim, extracted, derived, computed.

    Phase 7: optional language routing metadata may live in ``metadata`` under the
    canonical keys documented at module level; see ``validate_optional_language_metadata``.
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

        validate_optional_language_metadata(self.metadata)
