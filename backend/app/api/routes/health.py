from __future__ import annotations

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(tags=["infrastructure"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report API health.

    Phase 1 health is infrastructure-only. Dependency checks (Postgres/Qdrant)
    are added once real connectivity is implemented, and must never be faked.
    """

    return HealthResponse(status="ok")

