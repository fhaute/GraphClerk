from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.graph_edge_evidence import GraphEdgeEvidence


class GraphEdgeEvidenceRepository:
    """Database access for `GraphEdgeEvidence` records (Phase 3)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, link: GraphEdgeEvidence) -> None:
        """Add a graph edge evidence link to the current session."""

        self._session.add(link)

    def get(self, link_id: uuid.UUID) -> GraphEdgeEvidence | None:
        """Fetch a graph edge evidence link by id."""

        return self._session.get(GraphEdgeEvidence, link_id)

    def list_by_graph_edge(
        self,
        graph_edge_id: uuid.UUID,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[GraphEdgeEvidence]:
        """List evidence links for a graph edge ordered by creation time ascending."""

        stmt = (
            select(GraphEdgeEvidence)
            .where(GraphEdgeEvidence.graph_edge_id == graph_edge_id)
            .order_by(GraphEdgeEvidence.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.execute(stmt).scalars().all())

    def list_by_evidence_unit(
        self,
        evidence_unit_id: uuid.UUID,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[GraphEdgeEvidence]:
        """List graph edge links for an evidence unit ordered by creation time ascending."""

        stmt = (
            select(GraphEdgeEvidence)
            .where(GraphEdgeEvidence.evidence_unit_id == evidence_unit_id)
            .order_by(GraphEdgeEvidence.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.execute(stmt).scalars().all())

    def list_by_graph_edges(self, graph_edge_ids: list[uuid.UUID], limit: int = 5000) -> list[GraphEdgeEvidence]:
        """List evidence links for multiple graph edges deterministically."""

        if not graph_edge_ids:
            return []
        stmt = (
            select(GraphEdgeEvidence)
            .where(GraphEdgeEvidence.graph_edge_id.in_(graph_edge_ids))
            .order_by(GraphEdgeEvidence.created_at.asc(), GraphEdgeEvidence.id.asc())
            .limit(limit)
        )
        return list(self._session.execute(stmt).scalars().all())

