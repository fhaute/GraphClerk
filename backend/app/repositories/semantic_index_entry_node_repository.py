from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.semantic_index_entry_node import SemanticIndexEntryNode


class SemanticIndexEntryNodeRepository:
    """Database access for `SemanticIndexEntryNode` records (Phase 3)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, link: SemanticIndexEntryNode) -> None:
        """Add a semantic index entry node link to the current session."""

        self._session.add(link)

    def get(self, link_id: uuid.UUID) -> SemanticIndexEntryNode | None:
        """Fetch a semantic index entry node link by id."""

        return self._session.get(SemanticIndexEntryNode, link_id)

    def list_by_semantic_index(
        self,
        semantic_index_id: uuid.UUID,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[SemanticIndexEntryNode]:
        """List entry nodes for a semantic index ordered by creation time ascending."""

        stmt = (
            select(SemanticIndexEntryNode)
            .where(SemanticIndexEntryNode.semantic_index_id == semantic_index_id)
            .order_by(SemanticIndexEntryNode.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.execute(stmt).scalars().all())

    def list_by_graph_node(
        self,
        graph_node_id: uuid.UUID,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[SemanticIndexEntryNode]:
        """List semantic index links for a graph node ordered by creation time ascending."""

        stmt = (
            select(SemanticIndexEntryNode)
            .where(SemanticIndexEntryNode.graph_node_id == graph_node_id)
            .order_by(SemanticIndexEntryNode.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.execute(stmt).scalars().all())

