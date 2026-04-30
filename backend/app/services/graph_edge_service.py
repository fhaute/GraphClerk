from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.enums import GraphRelationType
from app.models.graph_edge import GraphEdge
from app.repositories.graph_edge_repository import GraphEdgeRepository
from app.repositories.graph_node_repository import GraphNodeRepository
from app.services.errors import GraphEdgeNotFoundError, GraphNodeNotFoundError, InvalidRelationTypeError


class GraphEdgeService:
    """Graph edge orchestration and validation for Phase 3.

    This service validates relation types and node existence. It does not commit;
    callers own transaction boundaries.
    """

    def __init__(self, *, session: Session) -> None:
        self._edge_repo = GraphEdgeRepository(session)
        self._node_repo = GraphNodeRepository(session)

    def create(
        self,
        *,
        from_node_id: uuid.UUID,
        to_node_id: uuid.UUID,
        relation_type: str,
        summary: str | None,
        confidence: float | None,
        metadata: dict[str, Any] | None,
    ) -> GraphEdge:
        try:
            relation_enum = GraphRelationType(relation_type)
        except ValueError as e:
            raise InvalidRelationTypeError(f"Invalid relation_type: {relation_type!r}") from e

        if self._node_repo.get(from_node_id) is None:
            raise GraphNodeNotFoundError(f"from_node_id not found: {from_node_id}")
        if self._node_repo.get(to_node_id) is None:
            raise GraphNodeNotFoundError(f"to_node_id not found: {to_node_id}")

        edge = GraphEdge(
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            relation_type=relation_enum,
            summary=summary,
            confidence=confidence,
            metadata_json=metadata,
        )
        self._edge_repo.add(edge)
        return edge

    def get(self, edge_id: uuid.UUID) -> GraphEdge:
        edge = self._edge_repo.get(edge_id)
        if edge is None:
            raise GraphEdgeNotFoundError(f"GraphEdge not found: {edge_id}")
        return edge

    def list(self, limit: int = 100, offset: int = 0) -> list[GraphEdge]:
        return self._edge_repo.list(limit=limit, offset=offset)

