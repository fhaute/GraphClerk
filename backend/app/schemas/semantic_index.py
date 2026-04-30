from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SemanticIndexCreateRequest(BaseModel):
    meaning: str = Field(min_length=1)
    summary: str | None = None
    embedding_text: str | None = None
    entry_node_ids: list[str] = Field(min_length=1)
    metadata: dict[str, Any] | None = None


class SemanticIndexResponse(BaseModel):
    id: str
    meaning: str
    summary: str | None
    embedding_text: str | None
    entry_node_ids: list[str]
    vector_status: str
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class SemanticIndexEntryPointsResponse(BaseModel):
    entry_node_ids: list[str]


class SemanticIndexSearchResult(BaseModel):
    id: str
    meaning: str
    summary: str | None
    embedding_text: str | None
    entry_node_ids: list[str]
    vector_status: str
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    score: float


class SemanticIndexSearchResponse(BaseModel):
    results: list[SemanticIndexSearchResult]

