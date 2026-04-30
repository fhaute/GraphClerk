from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GraphEdgeCreateRequest(BaseModel):
    from_node_id: str
    to_node_id: str
    relation_type: str = Field(min_length=1, max_length=32)
    summary: str | None = None
    confidence: float | None = None
    metadata: dict[str, Any] | None = None


class GraphEdgeResponse(BaseModel):
    id: str
    from_node_id: str
    to_node_id: str
    relation_type: str
    summary: str | None
    confidence: float | None
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class GraphEdgeListResponse(BaseModel):
    items: list[GraphEdgeResponse]

