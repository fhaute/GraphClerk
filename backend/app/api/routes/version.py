from __future__ import annotations

from fastapi import APIRouter

from app.schemas.version import VersionResponse

router = APIRouter(tags=["infrastructure"])


@router.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    """Report GraphClerk version metadata for Phase 1."""

    return VersionResponse(name="GraphClerk", version="0.1.0", phase="phase_1_foundation")

