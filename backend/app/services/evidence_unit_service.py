from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.evidence_unit import EvidenceUnit
from app.repositories.evidence_unit_repository import EvidenceUnitRepository
from app.schemas.evidence_unit_candidate import EvidenceUnitCandidate


class EvidenceUnitService:
    """Create EvidenceUnits from parser candidates (Phase 2)."""

    def __init__(self, *, session: Session) -> None:
        self._session = session
        self._repo = EvidenceUnitRepository(session)

    def create_from_candidates(
        self,
        *,
        artifact_id,
        candidates: list[EvidenceUnitCandidate],
    ) -> list[EvidenceUnit]:
        """Persist EvidenceUnits for an Artifact from candidates."""

        created: list[EvidenceUnit] = []
        for c in candidates:
            ev = EvidenceUnit(
                artifact_id=artifact_id,
                modality=c.modality,
                content_type=c.content_type,
                text=c.text,
                location=c.location,
                source_fidelity=c.source_fidelity,
                confidence=c.confidence,
                metadata_json=None,
            )
            self._repo.add(ev)
            created.append(ev)
        return created

