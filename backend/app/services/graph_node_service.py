from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.graph_node import GraphNode
from app.repositories.graph_node_repository import GraphNodeRepository
from app.services.errors import GraphNodeNotFoundError


class GraphNodeService:
    """Graph node orchestration and validation for Phase 3.

    This service does not commit; callers own transaction boundaries.
    """

    def __init__(self, *, session: Session) -> None:
        self._repo = GraphNodeRepository(session)

    def create(
        self,
        *,
        node_type,
        label: str,
        summary: str | None,
        metadata: dict[str, Any] | None,
    ) -> GraphNode:
        node = GraphNode(node_type=node_type, label=label, summary=summary, metadata_json=metadata)
        self._repo.add(node)
        return node

    def get(self, node_id: uuid.UUID) -> GraphNode:
        node = self._repo.get(node_id)
        if node is None:
            raise GraphNodeNotFoundError(f"GraphNode not found: {node_id}")
        return node

    def list(self, limit: int = 100, offset: int = 0) -> list[GraphNode]:
        return self._repo.list(limit=limit, offset=offset)

