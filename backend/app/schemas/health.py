from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response for the `GET /health` endpoint."""

    status: str

