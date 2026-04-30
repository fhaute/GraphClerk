from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.artifacts import router as artifacts_router
from app.api.routes.evidence_units import router as evidence_router
from app.api.routes.health import router as health_router
from app.api.routes.version import router as version_router


def create_app() -> FastAPI:
    """Create the GraphClerk FastAPI application.

    Phase 1 provides infrastructure endpoints only. This app must not expose
    ingestion, retrieval, or graph traversal behavior.
    """

    app = FastAPI(title="GraphClerk", version="0.1.0")

    app.include_router(health_router)
    app.include_router(version_router)
    app.include_router(artifacts_router)
    app.include_router(evidence_router)

    return app


app = create_app()

