from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RetrievalLogSummary(BaseModel):
    """List view for a retrieval log row (no full packet payload)."""

    id: str
    question: str
    confidence: float | None = None
    warnings: list[str] | None = None
    latency_ms: int | None = None
    token_estimate: int | None = None
    evidence_unit_count: int = 0
    has_retrieval_packet: bool = False
    created_at: datetime


class RetrievalLogListResponse(BaseModel):
    """Paginated list of retrieval logs (newest first)."""

    items: list[RetrievalLogSummary]


class RetrievalLogDetailResponse(BaseModel):
    """Single retrieval log including optional canonical `retrieval_packet` JSON."""

    id: str
    question: str
    selected_indexes: list[dict[str, Any]] | None = None
    graph_path: dict[str, Any] | None = None
    evidence_unit_ids: list[str] | None = None
    confidence: float | None = None
    warnings: list[str] | None = None
    latency_ms: int | None = None
    token_estimate: int | None = None
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Row metadata (DB column `metadata`).",
    )
    retrieval_packet: dict[str, Any] | None = None
    created_at: datetime
