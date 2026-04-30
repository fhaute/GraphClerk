from __future__ import annotations

"""Infrastructure version/phase metadata endpoint.

This endpoint is a lightweight introspection surface for clients/tests and
should reflect real phase state (not aspirational roadmap claims).
"""

from fastapi import APIRouter

from app.schemas.version import VersionResponse

router = APIRouter(tags=["infrastructure"])


@router.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    """Report GraphClerk version metadata for Phase 2."""

    return VersionResponse(name="GraphClerk", version="0.1.0", phase="phase_2_text_first_ingestion")

