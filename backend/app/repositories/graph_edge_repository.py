from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.graph_edge import GraphEdge


class GraphEdgeRepository:
    """Database access for `GraphEdge` records (Phase 3)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, edge: GraphEdge) -> None:
        """Add a graph edge to the current session."""

        self._session.add(edge)

    def get(self, edge_id: uuid.UUID) -> GraphEdge | None:
        """Fetch a graph edge by id."""

        return self._session.get(GraphEdge, edge_id)

    def list(self, limit: int = 100, offset: int = 0) -> list[GraphEdge]:
        """List graph edges ordered by creation time descending."""

        stmt = select(GraphEdge).order_by(GraphEdge.created_at.desc()).limit(limit).offset(offset)
        return list(self._session.execute(stmt).scalars().all())

    def list_by_node(self, node_id: uuid.UUID, limit: int = 1000, offset: int = 0) -> list[GraphEdge]:
        """List edges where a node is either endpoint."""

        stmt = (
            select(GraphEdge)
            .where(or_(GraphEdge.from_node_id == node_id, GraphEdge.to_node_id == node_id))
            .order_by(GraphEdge.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.execute(stmt).scalars().all())

