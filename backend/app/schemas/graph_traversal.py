from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.graph_edge import GraphEdgeResponse
from app.schemas.graph_node import GraphNodeResponse


class GraphNodeEvidenceRef(BaseModel):
    node_id: str
    evidence_unit_id: str
    support_type: str
    confidence: float | None


class GraphEdgeEvidenceRef(BaseModel):
    edge_id: str
    evidence_unit_id: str
    support_type: str
    confidence: float | None


class GraphNeighborhoodResponse(BaseModel):
    start_node_id: str
    depth: int
    max_nodes: int
    max_edges: int
    relation_types: list[str] | None
    truncated: bool
    truncation_reasons: list[str]
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]
    node_evidence: list[GraphNodeEvidenceRef]
    edge_evidence: list[GraphEdgeEvidenceRef]

