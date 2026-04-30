from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ArtifactCreateInlineRequest(BaseModel):
    """Create an artifact from inline text (Phase 2)."""

    filename: str
    artifact_type: Literal["text", "markdown"]
    text: str = Field(min_length=0)
    title: str | None = None
    mime_type: str | None = None


class ArtifactCreateResponse(BaseModel):
    """Response for `POST /artifacts`."""

    artifact_id: str
    status: Literal["ingested"]
    artifact_type: str
    evidence_unit_count: int


class ArtifactResponse(BaseModel):
    """Artifact metadata response."""

    id: str
    filename: str
    title: str | None
    artifact_type: str
    mime_type: str | None
    storage_uri: str
    checksum: str | None
    size_bytes: int
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] | None = None


class ArtifactListResponse(BaseModel):
    """List artifacts response."""

    items: list[ArtifactResponse]

