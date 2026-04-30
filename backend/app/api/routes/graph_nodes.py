from __future__ import annotations

"""Graph node APIs (Phase 3).

This module exposes CRUD-lite endpoints for graph nodes in the Phase 3 graph
layer. These endpoints are intentionally small and delegate validation to
services and persistence to repositories.

Scope and invariants:
- Nodes are created and read through this API surface.
- Pagination uses `limit`/`offset` (offset-based, deterministic ordering owned by
  the repository).
- Identifiers are UUIDs provided as strings at the HTTP boundary.
- Transaction boundaries are owned by the route layer (service does not commit).

Error semantics:
- Unknown node IDs return HTTP 404.
- Invalid UUID strings raise a 422 validation error via FastAPI/Starlette.
"""

import uuid

from fastapi import APIRouter, HTTPException

from app.db.session import get_sessionmaker
from app.schemas.graph_node import GraphNodeCreateRequest, GraphNodeListResponse, GraphNodeResponse
from app.services.errors import GraphNodeNotFoundError
from app.services.graph_node_service import GraphNodeService

router = APIRouter(prefix="/graph", tags=["graph"])


def _to_response(n) -> GraphNodeResponse:
    """Convert a GraphNode ORM model into its API response schema."""
    return GraphNodeResponse(
        id=str(n.id),
        node_type=str(n.node_type),
        label=n.label,
        summary=n.summary,
        metadata=n.metadata_json,
        created_at=n.created_at,
        updated_at=n.updated_at,
    )


@router.post("/nodes", response_model=GraphNodeResponse)
def create_graph_node(payload: GraphNodeCreateRequest) -> GraphNodeResponse:
    """Create a graph node.

    Notes:
    - This endpoint commits its transaction on success.
    - Validation/orchestration is delegated to `GraphNodeService`.
    """
    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        svc = GraphNodeService(session=session)
        node = svc.create(
            node_type=payload.node_type,
            label=payload.label,
            summary=payload.summary,
            metadata=payload.metadata,
        )
        session.commit()
        return _to_response(node)


@router.get("/nodes/{node_id}", response_model=GraphNodeResponse)
def get_graph_node(node_id: str) -> GraphNodeResponse:
    """Fetch a single graph node by id.

    Returns 404 if the node does not exist.
    """
    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        svc = GraphNodeService(session=session)
        try:
            node = svc.get(uuid.UUID(node_id))
        except GraphNodeNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return _to_response(node)


@router.get("/nodes", response_model=GraphNodeListResponse)
def list_graph_nodes(limit: int = 100, offset: int = 0) -> GraphNodeListResponse:
    """List graph nodes (newest-first ordering is defined by the repository)."""
    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        svc = GraphNodeService(session=session)
        items = svc.list(limit=limit, offset=offset)
        return GraphNodeListResponse(items=[_to_response(n) for n in items])

