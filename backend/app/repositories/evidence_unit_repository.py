from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence_unit import EvidenceUnit


class EvidenceUnitRepository:
    """Database access for `EvidenceUnit` records (Phase 2)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, evidence_unit: EvidenceUnit) -> None:
        """Add an evidence unit to the current session."""

        self._session.add(evidence_unit)

    def get(self, evidence_unit_id: uuid.UUID) -> EvidenceUnit | None:
        """Fetch an evidence unit by id."""

        return self._session.get(EvidenceUnit, evidence_unit_id)

    def list_by_artifact(
        self,
        artifact_id: uuid.UUID,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[EvidenceUnit]:
        """List evidence units for an artifact ordered by creation time ascending."""

        stmt = (
            select(EvidenceUnit)
            .where(EvidenceUnit.artifact_id == artifact_id)
            .order_by(EvidenceUnit.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.execute(stmt).scalars().all())

    def list_by_ids(self, evidence_unit_ids: list[uuid.UUID]) -> list[EvidenceUnit]:
        """Fetch evidence units by id (order not guaranteed)."""

        if not evidence_unit_ids:
            return []
        stmt = select(EvidenceUnit).where(EvidenceUnit.id.in_(evidence_unit_ids))
        return list(self._session.execute(stmt).scalars().all())

