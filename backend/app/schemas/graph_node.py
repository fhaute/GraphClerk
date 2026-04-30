from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import GraphNodeType


class GraphNodeCreateRequest(BaseModel):
    node_type: GraphNodeType
    label: str = Field(min_length=1, max_length=512)
    summary: str | None = None
    metadata: dict[str, Any] | None = None


class GraphNodeResponse(BaseModel):
    id: str
    node_type: str
    label: str
    summary: str | None
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class GraphNodeListResponse(BaseModel):
    items: list[GraphNodeResponse]

