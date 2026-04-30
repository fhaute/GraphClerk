from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.enums import SemanticIndexVectorStatus
from app.models.semantic_index import SemanticIndex
from app.models.semantic_index_entry_node import SemanticIndexEntryNode
from app.repositories.graph_node_repository import GraphNodeRepository
from app.repositories.semantic_index_entry_node_repository import SemanticIndexEntryNodeRepository
from app.repositories.semantic_index_repository import SemanticIndexRepository
from app.services.errors import (
    DuplicateEntryNodeIdError,
    GraphNodeNotFoundError,
    SemanticIndexNotFoundError,
    SemanticIndexRequiresEntryNodesError,
)


class SemanticIndexService:
    """SemanticIndex orchestration for Phase 3 Slice E (no vector indexing)."""

    def __init__(self, *, session: Session) -> None:
        self._session = session
        self._idx_repo = SemanticIndexRepository(session)
        self._entry_repo = SemanticIndexEntryNodeRepository(session)
        self._node_repo = GraphNodeRepository(session)

    def create(
        self,
        *,
        meaning: str,
        summary: str | None,
        embedding_text: str | None,
        entry_node_ids: list[uuid.UUID],
        metadata: dict[str, Any] | None,
    ) -> SemanticIndex:
        if not entry_node_ids:
            raise SemanticIndexRequiresEntryNodesError("semantic_index_requires_entry_node")

        unique_ids = set(entry_node_ids)
        if len(unique_ids) != len(entry_node_ids):
            raise DuplicateEntryNodeIdError("duplicate_entry_node_id")

        # Validate all entry nodes exist.
        missing = [nid for nid in unique_ids if self._node_repo.get(nid) is None]
        if missing:
            # Be explicit; later slices may add richer error payloads.
            raise GraphNodeNotFoundError(f"entry_node_id not found: {missing[0]}")

        idx = SemanticIndex(
            meaning=meaning,
            summary=summary,
            embedding_text=embedding_text,
            entry_node_ids=None,  # legacy field; not source of truth
            vector_status=SemanticIndexVectorStatus.pending,
            metadata_json=metadata,
        )
        self._idx_repo.add(idx)
        self._session.flush()  # ensure idx.id exists for link rows

        for nid in unique_ids:
            self._entry_repo.add(SemanticIndexEntryNode(semantic_index_id=idx.id, graph_node_id=nid))

        return idx

    def get(self, semantic_index_id: uuid.UUID) -> SemanticIndex:
        idx = self._idx_repo.get(semantic_index_id)
        if idx is None:
            raise SemanticIndexNotFoundError(f"SemanticIndex not found: {semantic_index_id}")
        return idx

    def get_entry_nodes(self, semantic_index_id: uuid.UUID) -> list[uuid.UUID]:
        idx = self._idx_repo.get(semantic_index_id)
        if idx is None:
            raise SemanticIndexNotFoundError(f"SemanticIndex not found: {semantic_index_id}")
        links = self._entry_repo.list_by_semantic_index(semantic_index_id, limit=1000, offset=0)
        return [l.graph_node_id for l in links]

