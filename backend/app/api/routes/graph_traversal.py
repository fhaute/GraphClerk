from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query

from app.db.session import get_sessionmaker
from app.models.enums import GraphRelationType
from app.schemas.graph_edge import GraphEdgeResponse
from app.schemas.graph_node import GraphNodeResponse
from app.schemas.graph_traversal import (
    GraphEdgeEvidenceRef,
    GraphNeighborhoodResponse,
    GraphNodeEvidenceRef,
)
from app.services.errors import GraphNodeNotFoundError
from app.services.graph_traversal_service import GraphTraversalService

router = APIRouter(prefix="", tags=["graph_traversal"])


@router.get("/graph/nodes/{node_id}/neighborhood", response_model=GraphNeighborhoodResponse)
def get_neighborhood(
    node_id: str,
    depth: int = Query(1, ge=1, le=3),
    max_nodes: int = Query(25, ge=1, le=500),
    max_edges: int = Query(50, ge=1, le=5000),
    relation_types: list[str] | None = Query(default=None),
) -> GraphNeighborhoodResponse:
    try:
        start_id = uuid.UUID(node_id)
    except ValueError as e:
        # Locked: invalid start node returns 404.
        raise HTTPException(status_code=404, detail="GraphNode not found") from e

    if relation_types is not None:
        try:
            for rt in relation_types:
                GraphRelationType(rt)
        except ValueError as e:
            raise HTTPException(status_code=422, detail="invalid_relation_type") from e

    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        svc = GraphTraversalService(session=session)
        try:
            neigh = svc.neighborhood(
                start_node_id=start_id,
                depth=depth,
                max_nodes=max_nodes,
                max_edges=max_edges,
                relation_types=relation_types,
            )
        except GraphNodeNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

        nodes = [
            GraphNodeResponse(
                id=str(n.id),
                node_type=str(n.node_type),
                label=n.label,
                summary=n.summary,
                metadata=n.metadata_json,
                created_at=n.created_at,
                updated_at=n.updated_at,
            )
            for n in neigh.nodes
        ]
        edges = [
            GraphEdgeResponse(
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
            for e in neigh.edges
        ]
        node_evidence = [
            GraphNodeEvidenceRef(
                node_id=str(node_id),
                evidence_unit_id=str(ev_id),
                support_type=support_type,
                confidence=confidence,
            )
            for (node_id, ev_id, support_type, confidence) in neigh.node_evidence
        ]
        edge_evidence = [
            GraphEdgeEvidenceRef(
                edge_id=str(edge_id),
                evidence_unit_id=str(ev_id),
                support_type=support_type,
                confidence=confidence,
            )
            for (edge_id, ev_id, support_type, confidence) in neigh.edge_evidence
        ]

        return GraphNeighborhoodResponse(
            start_node_id=str(neigh.start_node_id),
            depth=neigh.depth,
            max_nodes=neigh.max_nodes,
            max_edges=neigh.max_edges,
            relation_types=neigh.relation_types,
            truncated=neigh.truncated,
            truncation_reasons=neigh.truncation_reasons,
            nodes=nodes,
            edges=edges,
            node_evidence=node_evidence,
            edge_evidence=edge_evidence,
        )

