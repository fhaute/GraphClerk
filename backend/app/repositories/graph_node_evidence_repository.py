from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.graph_node_evidence import GraphNodeEvidence


class GraphNodeEvidenceRepository:
    """Database access for `GraphNodeEvidence` records (Phase 3)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, link: GraphNodeEvidence) -> None:
        """Add a graph node evidence link to the current session."""

        self._session.add(link)

    def get(self, link_id: uuid.UUID) -> GraphNodeEvidence | None:
        """Fetch a graph node evidence link by id."""

        return self._session.get(GraphNodeEvidence, link_id)

    def list_by_graph_node(
        self,
        graph_node_id: uuid.UUID,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[GraphNodeEvidence]:
        """List evidence links for a graph node ordered by creation time ascending."""

        stmt = (
            select(GraphNodeEvidence)
            .where(GraphNodeEvidence.graph_node_id == graph_node_id)
            .order_by(GraphNodeEvidence.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.execute(stmt).scalars().all())

    def list_by_evidence_unit(
        self,
        evidence_unit_id: uuid.UUID,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[GraphNodeEvidence]:
        """List graph node links for an evidence unit ordered by creation time ascending."""

        stmt = (
            select(GraphNodeEvidence)
            .where(GraphNodeEvidence.evidence_unit_id == evidence_unit_id)
            .order_by(GraphNodeEvidence.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.execute(stmt).scalars().all())

