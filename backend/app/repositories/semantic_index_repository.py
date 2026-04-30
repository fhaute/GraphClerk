from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import SemanticIndexVectorStatus
from app.models.semantic_index import SemanticIndex


class SemanticIndexRepository:
    """Database access for `SemanticIndex` records (Phase 3)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, semantic_index: SemanticIndex) -> None:
        """Add a semantic index to the current session."""

        self._session.add(semantic_index)

    def get(self, semantic_index_id: uuid.UUID) -> SemanticIndex | None:
        """Fetch a semantic index by id."""

        return self._session.get(SemanticIndex, semantic_index_id)

    def list(self, limit: int = 100, offset: int = 0) -> list[SemanticIndex]:
        """List semantic indexes ordered by creation time descending."""

        stmt = select(SemanticIndex).order_by(SemanticIndex.created_at.desc()).limit(limit).offset(offset)
        return list(self._session.execute(stmt).scalars().all())

    def list_by_vector_status(
        self,
        status: SemanticIndexVectorStatus,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SemanticIndex]:
        """List semantic indexes filtered by vector_status."""

        stmt = (
            select(SemanticIndex)
            .where(SemanticIndex.vector_status == status)
            .order_by(SemanticIndex.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.execute(stmt).scalars().all())

