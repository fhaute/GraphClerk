from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query

from app.db.session import get_sessionmaker
from app.schemas.semantic_index import (
    SemanticIndexCreateRequest,
    SemanticIndexEntryPointsResponse,
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
    # Slice H: keep wiring explicit and easily overridable in tests.
    # Default behavior is "not configured" for embeddings; tests can override.
    from app.services.embedding_adapter import NotConfiguredEmbeddingAdapter
    from app.services.embedding_service import EmbeddingService
    from app.services.vector_index_service import VectorIndexService

    from qdrant_client import QdrantClient

    from app.core.config import get_settings

    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

    # Phase 3: explicit expected dimension. Until a real adapter exists, this remains a fixed constant.
    expected_dimension = 8
    embedding = EmbeddingService(
        adapter=NotConfiguredEmbeddingAdapter(dimension=expected_dimension),
        expected_dimension=expected_dimension,
    )
    vector = VectorIndexService(qdrant_client=client, expected_dimension=expected_dimension)
    return SemanticIndexSearchService(session=session, embedding_service=embedding, vector_index_service=vector)


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

