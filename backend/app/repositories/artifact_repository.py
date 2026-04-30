from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.artifact import Artifact


class ArtifactRepository:
    """Database access for `Artifact` records (Phase 2)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, artifact: Artifact) -> None:
        """Add an artifact to the current session."""

        self._session.add(artifact)

    def get(self, artifact_id: uuid.UUID) -> Artifact | None:
        """Fetch an artifact by id."""

        return self._session.get(Artifact, artifact_id)

    def list(self, limit: int = 100, offset: int = 0) -> list[Artifact]:
        """List artifacts ordered by creation time descending."""

        stmt = select(Artifact).order_by(Artifact.created_at.desc()).limit(limit).offset(offset)
        return list(self._session.execute(stmt).scalars().all())

