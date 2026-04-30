from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.graph_node import GraphNode


class GraphNodeRepository:
    """Database access for `GraphNode` records (Phase 3)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, node: GraphNode) -> None:
        """Add a graph node to the current session."""

        self._session.add(node)

    def get(self, node_id: uuid.UUID) -> GraphNode | None:
        """Fetch a graph node by id."""

        return self._session.get(GraphNode, node_id)

    def list(self, limit: int = 100, offset: int = 0) -> list[GraphNode]:
        """List graph nodes ordered by creation time descending."""

        stmt = select(GraphNode).order_by(GraphNode.created_at.desc()).limit(limit).offset(offset)
        return list(self._session.execute(stmt).scalars().all())

