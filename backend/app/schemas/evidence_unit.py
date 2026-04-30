from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class EvidenceUnitResponse(BaseModel):
    """EvidenceUnit response (Phase 2 inspection)."""

    id: str
    artifact_id: str
    modality: str
    content_type: str
    text: str | None
    location: dict[str, Any] | None
    source_fidelity: str
    confidence: float | None
    created_at: datetime
    updated_at: datetime


class EvidenceUnitListResponse(BaseModel):
    """List evidence units response."""

    items: list[EvidenceUnitResponse]

