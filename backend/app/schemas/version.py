from __future__ import annotations

from pydantic import BaseModel


class VersionResponse(BaseModel):
    """Response for the `GET /version` endpoint."""

    name: str
    version: str
    phase: str

