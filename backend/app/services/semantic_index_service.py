from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.models.enums import SemanticIndexVectorStatus
from app.models.semantic_index import SemanticIndex
from app.models.semantic_index_entry_node import SemanticIndexEntryNode
from app.repositories.graph_node_repository import GraphNodeRepository
from app.repositories.semantic_index_entry_node_repository import SemanticIndexEntryNodeRepository
from app.repositories.semantic_index_repository import SemanticIndexRepository
from app.services.embedding_service import EmbeddingService
from app.services.errors import (
    DuplicateEntryNodeIdError,
    EmbeddingAdapterNotConfiguredError,
    EmbeddingDimensionMismatchError,
    EmbeddingGenerationError,
    EmbeddingInvalidVectorError,
    EmbeddingTextEmptyError,
    GraphNodeNotFoundError,
    SemanticIndexNotFoundError,
    SemanticIndexRequiresEntryNodesError,
    VectorIndexDimensionMismatchError,
    VectorIndexOperationError,
    VectorIndexUnavailableError,
)
from app.services.vector_index_service import VectorIndexService


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


_VECTOR_INDEXING_META_KEY = "graphclerk_vector_indexing"


def _merge_vector_indexing_meta(
    existing: dict[str, Any] | None,
    *,
    outcome: Literal["indexed", "failed", "skipped"],
    error_code: str | None,
    message: str | None,
) -> dict[str, Any]:
    base: dict[str, Any] = dict(existing) if existing else {}
    prior = base.get(_VECTOR_INDEXING_META_KEY)
    block: dict[str, Any] = dict(prior) if isinstance(prior, dict) else {}
    block["last_attempt_at"] = datetime.now(timezone.utc).isoformat()
    block["last_outcome"] = outcome
    block["last_error_code"] = error_code
    block["last_message"] = message
    base[_VECTOR_INDEXING_META_KEY] = block
    return base


@dataclass(frozen=True)
class SemanticIndexVectorIndexOutcome:
    """Result of a single semantic-index vector upsert attempt (Track B Slice B1)."""

    semantic_index_id: uuid.UUID
    status: Literal["indexed", "skipped", "failed"]
    detail: str | None = None


class SemanticIndexVectorIndexingService:
    """Embed `embedding_text`, upsert into Qdrant, and transition `vector_status` explicitly.

    Callers **commit** the SQLAlchemy session after operations succeed.

    - ``pending`` / ``failed`` rows are eligible for indexing.
    - ``indexed`` rows are skipped unless ``force=True``.
    - Empty / missing ``embedding_text`` → ``failed`` (no silent pending).
    - On embedding or vector errors → ``failed`` with metadata (no fake ``indexed``).
    """

    def __init__(
        self,
        *,
        session: Session,
        embedding_service: EmbeddingService,
        vector_index_service: VectorIndexService,
        semantic_index_repo: SemanticIndexRepository | None = None,
    ) -> None:
        self._session = session
        self._embedding = embedding_service
        self._vector = vector_index_service
        self._idx_repo = semantic_index_repo or SemanticIndexRepository(session)

    def index_semantic_index(self, *, semantic_index_id: uuid.UUID, force: bool = False) -> SemanticIndexVectorIndexOutcome:
        idx = self._idx_repo.get(semantic_index_id)
        if idx is None:
            raise SemanticIndexNotFoundError(f"SemanticIndex not found: {semantic_index_id}")

        if idx.vector_status == SemanticIndexVectorStatus.indexed and not force:
            idx.metadata_json = _merge_vector_indexing_meta(
                idx.metadata_json,
                outcome="skipped",
                error_code=None,
                message="already_indexed",
            )
            self._session.flush()
            return SemanticIndexVectorIndexOutcome(semantic_index_id=semantic_index_id, status="skipped", detail="already_indexed")

        text = (idx.embedding_text or "").strip()
        if text == "":
            idx.vector_status = SemanticIndexVectorStatus.failed
            idx.metadata_json = _merge_vector_indexing_meta(
                idx.metadata_json,
                outcome="failed",
                error_code="embedding_text_empty",
                message="SemanticIndex.embedding_text is missing or whitespace-only; cannot compute embedding.",
            )
            self._session.flush()
            return SemanticIndexVectorIndexOutcome(
                semantic_index_id=semantic_index_id,
                status="failed",
                detail="embedding_text_empty",
            )

        try:
            self._vector.ensure_semantic_indexes_collection()
            vector = self._embedding.embed_text(text)
            payload: dict[str, Any] = {
                "meaning": idx.meaning,
            }
            if idx.summary:
                payload["summary"] = idx.summary
            self._vector.upsert_semantic_index_vector(
                semantic_index_id=semantic_index_id,
                vector=vector,
                payload=payload,
            )
        except (
            EmbeddingAdapterNotConfiguredError,
            EmbeddingTextEmptyError,
            EmbeddingInvalidVectorError,
            EmbeddingDimensionMismatchError,
            EmbeddingGenerationError,
        ) as e:
            idx.vector_status = SemanticIndexVectorStatus.failed
            code = type(e).__name__
            idx.metadata_json = _merge_vector_indexing_meta(
                idx.metadata_json,
                outcome="failed",
                error_code=code,
                message=str(e),
            )
            self._session.flush()
            return SemanticIndexVectorIndexOutcome(semantic_index_id=semantic_index_id, status="failed", detail=code)
        except (VectorIndexUnavailableError, VectorIndexOperationError, VectorIndexDimensionMismatchError) as e:
            idx.vector_status = SemanticIndexVectorStatus.failed
            code = type(e).__name__
            idx.metadata_json = _merge_vector_indexing_meta(
                idx.metadata_json,
                outcome="failed",
                error_code=code,
                message=str(e),
            )
            self._session.flush()
            return SemanticIndexVectorIndexOutcome(semantic_index_id=semantic_index_id, status="failed", detail=code)

        idx.vector_status = SemanticIndexVectorStatus.indexed
        idx.metadata_json = _merge_vector_indexing_meta(
            idx.metadata_json,
            outcome="indexed",
            error_code=None,
            message=None,
        )
        self._session.flush()
        return SemanticIndexVectorIndexOutcome(semantic_index_id=semantic_index_id, status="indexed", detail=None)

    def index_all_pending(self, *, limit: int = 100, force: bool = False) -> list[SemanticIndexVectorIndexOutcome]:
        """Index up to ``limit`` semantic indexes, preferring ``pending`` then ``failed`` (retries)."""

        pending_rows = self._idx_repo.list_by_vector_status(SemanticIndexVectorStatus.pending, limit=limit, offset=0)
        out: list[SemanticIndexVectorIndexOutcome] = []
        for r in pending_rows:
            out.append(self.index_semantic_index(semantic_index_id=r.id, force=force))
        if len(out) < limit:
            rem = limit - len(out)
            failed_rows = self._idx_repo.list_by_vector_status(SemanticIndexVectorStatus.failed, limit=rem, offset=0)
            for r in failed_rows:
                out.append(self.index_semantic_index(semantic_index_id=r.id, force=force))
        return out

