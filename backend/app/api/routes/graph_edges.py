from __future__ import annotations

"""Graph edge APIs (Phase 3).

This module exposes CRUD-lite endpoints for graph edges (directed relations)
between graph nodes in the Phase 3 graph layer.

Scope and invariants:
- Edges are created and read through this API surface.
- Relation types are validated by `GraphEdgeService` against `GraphRelationType`.
- Pagination uses `limit`/`offset` (offset-based, deterministic ordering owned by
  the repository).
- Identifiers are UUIDs provided as strings at the HTTP boundary.
- Transaction boundaries are owned by the route layer (service does not commit).

Error semantics:
- Invalid relation types and missing node references return HTTP 400.
- Unknown edge IDs return HTTP 404.
- Invalid UUID strings raise a 422 validation error via FastAPI/Starlette.
"""

import uuid

from fastapi import APIRouter, HTTPException

from app.db.session import get_sessionmaker
from app.schemas.graph_edge import GraphEdgeCreateRequest, GraphEdgeListResponse, GraphEdgeResponse
from app.services.errors import GraphEdgeNotFoundError, GraphNodeNotFoundError, InvalidRelationTypeError
from app.services.graph_edge_service import GraphEdgeService

router = APIRouter(prefix="/graph", tags=["graph"])


def _to_response(e) -> GraphEdgeResponse:
    """Convert a GraphEdge ORM model into its API response schema."""
    return GraphEdgeResponse(
        id=str(e.id),
        from_node_id=str(e.from_node_id),
        to_node_id=str(e.to_node_id),
        relation_type=str(e.relation_type),
        summary=e.summary,
        confidence=e.confidence,
        metadata=e.metadata_json,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


@router.post("/edges", response_model=GraphEdgeResponse)
def create_graph_edge(payload: GraphEdgeCreateRequest) -> GraphEdgeResponse:
    """Create a graph edge.

    Returns HTTP 400 if:
    - `relation_type` is invalid
    - either referenced node id does not exist
    """
    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        svc = GraphEdgeService(session=session)
        try:
            edge = svc.create(
                from_node_id=uuid.UUID(payload.from_node_id),
                to_node_id=uuid.UUID(payload.to_node_id),
                relation_type=payload.relation_type,
                summary=payload.summary,
                confidence=payload.confidence,
                metadata=payload.metadata,
            )
            session.commit()
            return _to_response(edge)
        except (InvalidRelationTypeError, GraphNodeNotFoundError) as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/edges/{edge_id}", response_model=GraphEdgeResponse)
def get_graph_edge(edge_id: str) -> GraphEdgeResponse:
    """Fetch a single graph edge by id.

    Returns 404 if the edge does not exist.
    """
    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        svc = GraphEdgeService(session=session)
        try:
            edge = svc.get(uuid.UUID(edge_id))
        except GraphEdgeNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return _to_response(edge)


@router.get("/edges", response_model=GraphEdgeListResponse)
def list_graph_edges(limit: int = 100, offset: int = 0) -> GraphEdgeListResponse:
    """List graph edges (newest-first ordering is defined by the repository)."""
    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        svc = GraphEdgeService(session=session)
        items = svc.list(limit=limit, offset=offset)
        return GraphEdgeListResponse(items=[_to_response(e) for e in items])

