from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query

from app.db.session import get_sessionmaker
from app.repositories.semantic_index_repository import SemanticIndexRepository
from app.schemas.semantic_index import (
    SemanticIndexCreateRequest,
    SemanticIndexEntryPointsResponse,
    SemanticIndexListPageResponse,
    SemanticIndexResponse,
    SemanticIndexSearchResponse,
)
from app.services.errors import (
    DuplicateEntryNodeIdError,
    EmbeddingAdapterNotConfiguredError,
    EmbeddingDimensionMismatchError,
    EmbeddingInvalidVectorError,
    EmbeddingTextEmptyError,
    GraphNodeNotFoundError,
    SemanticIndexNotFoundError,
    SemanticIndexRequiresEntryNodesError,
    SemanticIndexSearchInconsistentIndexError,
    VectorIndexDimensionMismatchError,
    VectorIndexOperationError,
    VectorIndexUnavailableError,
)
from app.services.semantic_index_service import SemanticIndexService
from app.services.semantic_index_search_service import SemanticIndexSearchService

router = APIRouter(prefix="", tags=["semantic_indexes"])


def _build_search_service(*, session) -> SemanticIndexSearchService:
    """Delegate to shared factory (tests may monkeypatch this symbol)."""

    from app.services.semantic_index_search_factory import build_semantic_index_search_service

    return build_semantic_index_search_service(session=session)


@router.post("/semantic-indexes", response_model=SemanticIndexResponse)
def create_semantic_index(payload: SemanticIndexCreateRequest) -> SemanticIndexResponse:
    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        svc = SemanticIndexService(session=session)
        try:
            entry_ids = [uuid.UUID(x) for x in payload.entry_node_ids]
            idx = svc.create(
                meaning=payload.meaning,
                summary=payload.summary,
                embedding_text=payload.embedding_text,
                entry_node_ids=entry_ids,
                metadata=payload.metadata,
            )
            session.commit()
            # Source of truth: read from join table after persistence.
            entry_node_ids = [str(x) for x in svc.get_entry_nodes(idx.id)]
            return SemanticIndexResponse(
                id=str(idx.id),
                meaning=idx.meaning,
                summary=idx.summary,
                embedding_text=idx.embedding_text,
                entry_node_ids=entry_node_ids,
                vector_status=str(idx.vector_status),
                metadata=idx.metadata_json,
                created_at=idx.created_at,
                updated_at=idx.updated_at,
            )
        except (SemanticIndexRequiresEntryNodesError, DuplicateEntryNodeIdError) as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e)) from e
        except GraphNodeNotFoundError as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e)) from e
        except ValueError as e:
            session.rollback()
            raise HTTPException(status_code=400, detail="invalid_entry_node_id") from e


@router.get("/semantic-indexes/search", response_model=SemanticIndexSearchResponse)
def search_semantic_indexes(
    q: str = Query(...),
    limit: int = Query(5, ge=1, le=50),
) -> SemanticIndexSearchResponse:
    if q.strip() == "":
        raise HTTPException(status_code=422, detail="embedding_text_empty")

    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        svc = _build_search_service(session=session)
        try:
            results = svc.search(q=q, limit=limit)
            return SemanticIndexSearchResponse(
                results=[
                    {
                        "id": str(r.semantic_index.id),
                        "meaning": r.semantic_index.meaning,
                        "summary": r.semantic_index.summary,
                        "embedding_text": r.semantic_index.embedding_text,
                        "entry_node_ids": [str(x) for x in r.entry_node_ids],
                        "vector_status": str(r.semantic_index.vector_status),
                        "metadata": r.semantic_index.metadata_json,
                        "created_at": r.semantic_index.created_at,
                        "updated_at": r.semantic_index.updated_at,
                        "score": r.score,
                    }
                    for r in results
                ]
            )
        except EmbeddingAdapterNotConfiguredError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e
        except EmbeddingTextEmptyError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        except (EmbeddingInvalidVectorError, EmbeddingDimensionMismatchError) as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
        except VectorIndexUnavailableError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e
        except VectorIndexOperationError as e:
            raise HTTPException(status_code=502, detail=str(e)) from e
        except VectorIndexDimensionMismatchError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
        except SemanticIndexSearchInconsistentIndexError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/semantic-indexes", response_model=SemanticIndexListPageResponse)
def list_semantic_indexes(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> SemanticIndexListPageResponse:
    """List semantic indexes (newest ``created_at`` first). Entry node ids come from the join table."""

    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        repo = SemanticIndexRepository(session)
        svc = SemanticIndexService(session=session)
        total = repo.count_all()
        rows = repo.list(limit=limit, offset=offset)
        items = []
        for idx in rows:
            entry_node_ids = [str(x) for x in svc.get_entry_nodes(idx.id)]
            items.append(
                SemanticIndexResponse(
                    id=str(idx.id),
                    meaning=idx.meaning,
                    summary=idx.summary,
                    embedding_text=idx.embedding_text,
                    entry_node_ids=entry_node_ids,
                    vector_status=str(idx.vector_status),
                    metadata=idx.metadata_json,
                    created_at=idx.created_at,
                    updated_at=idx.updated_at,
                )
            )
        return SemanticIndexListPageResponse(items=items, limit=limit, offset=offset, count=total)


@router.get("/semantic-indexes/{semantic_index_id}", response_model=SemanticIndexResponse)
def get_semantic_index(semantic_index_id: str) -> SemanticIndexResponse:
    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        svc = SemanticIndexService(session=session)
        try:
            idx = svc.get(uuid.UUID(semantic_index_id))
            entry_node_ids = [str(x) for x in svc.get_entry_nodes(idx.id)]
            return SemanticIndexResponse(
                id=str(idx.id),
                meaning=idx.meaning,
                summary=idx.summary,
                embedding_text=idx.embedding_text,
                entry_node_ids=entry_node_ids,
                vector_status=str(idx.vector_status),
                metadata=idx.metadata_json,
                created_at=idx.created_at,
                updated_at=idx.updated_at,
            )
        except SemanticIndexNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/semantic-indexes/{semantic_index_id}/entry-points", response_model=SemanticIndexEntryPointsResponse)
def resolve_semantic_index_entry_points(semantic_index_id: str) -> SemanticIndexEntryPointsResponse:
    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        svc = SemanticIndexService(session=session)
        try:
            ids = [str(x) for x in svc.get_entry_nodes(uuid.UUID(semantic_index_id))]
            return SemanticIndexEntryPointsResponse(entry_node_ids=ids)
        except SemanticIndexNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

