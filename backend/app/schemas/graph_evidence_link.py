from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class GraphEvidenceLinkCreateRequest(BaseModel):
    evidence_unit_id: str
    support_type: str = Field(min_length=1, max_length=32)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class GraphNodeEvidenceLinkResponse(BaseModel):
    id: str
    graph_node_id: str
    evidence_unit_id: str
    support_type: str
    confidence: float | None
    created_at: datetime
    updated_at: datetime


class GraphEdgeEvidenceLinkResponse(BaseModel):
    id: str
    graph_edge_id: str
    evidence_unit_id: str
    support_type: str
    confidence: float | None
    created_at: datetime
    updated_at: datetime

