"""Semantic index vector search (Phase 3 Slice H).

Embeds the query, searches Qdrant for similar ``SemanticIndex`` vectors, hydrates
rows from Postgres (source of truth), and returns only ``vector_status=indexed``
indexes. Qdrant hits whose ids are missing in Postgres are dropped (stale vectors).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.enums import SemanticIndexVectorStatus
from app.models.semantic_index import SemanticIndex
from app.repositories.semantic_index_entry_node_repository import SemanticIndexEntryNodeRepository
from app.repositories.semantic_index_repository import SemanticIndexRepository
from app.services.embedding_service import EmbeddingService
from app.services.vector_index_service import SearchHit, VectorIndexService


@dataclass(frozen=True)
class SemanticIndexSearchResult:
    semantic_index: SemanticIndex
    entry_node_ids: list[uuid.UUID]
    score: float


class SemanticIndexSearchService:
    """SemanticIndex search wiring (Phase 3 Slice H).

    Postgres is the source of truth for SemanticIndex metadata.
    Qdrant is used only for similarity ranking and returns IDs + scores.
    """

    def __init__(
        self,
        *,
        session: Session,
        embedding_service: EmbeddingService,
        vector_index_service: VectorIndexService,
        semantic_index_repo: SemanticIndexRepository | None = None,
        entry_node_repo: SemanticIndexEntryNodeRepository | None = None,
    ) -> None:
        self._session = session
        self._embedding = embedding_service
        self._vector = vector_index_service
        self._idx_repo = semantic_index_repo or SemanticIndexRepository(session)
        self._entry_repo = entry_node_repo or SemanticIndexEntryNodeRepository(session)

    def search(self, *, q: str, limit: int = 5) -> list[SemanticIndexSearchResult]:
        # Query validation is handled at API boundary; EmbeddingService also rejects whitespace.
        query_vec = self._embedding.embed_text(q)

        hits: list[SearchHit] = self._vector.search_semantic_indexes(query_vector=query_vec, limit=limit)
        hit_ids = [h.semantic_index_id for h in hits]

        rows = self._idx_repo.list_by_ids(hit_ids)
        by_id = {r.id: r for r in rows}

        # Qdrant can retain vectors after a Postgres row was removed (or DB was restored
        # without Qdrant). Drop orphan hits; Postgres remains source of truth.
        missing = [sid for sid in hit_ids if sid not in by_id]
        if missing:
            hits = [h for h in hits if h.semantic_index_id in by_id]

        out: list[SemanticIndexSearchResult] = []
        for h in hits:
            row = by_id[h.semantic_index_id]
            if row.vector_status != SemanticIndexVectorStatus.indexed:
                continue  # only indexed are returned for honest search semantics

            links = self._entry_repo.list_by_semantic_index(row.id, limit=1000, offset=0)
            entry_node_ids = [l.graph_node_id for l in links]
            out.append(SemanticIndexSearchResult(semantic_index=row, entry_node_ids=entry_node_ids, score=h.score))

        return out

