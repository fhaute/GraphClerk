from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.artifacts import router as artifacts_router
from app.api.routes.evidence_units import router as evidence_router
from app.api.routes.graph_edges import router as graph_edges_router
from app.api.routes.graph_edge_evidence import router as graph_edge_evidence_router
from app.api.routes.graph_nodes import router as graph_nodes_router
from app.api.routes.graph_node_evidence import router as graph_node_evidence_router
from app.api.routes.graph_traversal import router as graph_traversal_router
from app.api.routes.health import router as health_router
from app.api.routes.semantic_indexes import router as semantic_indexes_router
from app.api.routes.version import router as version_router


def create_app() -> FastAPI:
    """Create the GraphClerk FastAPI application.

    Phase 0–2 scope: infrastructure plus text-first ingestion inspection routes.

    This app wires:
    - infrastructure endpoints (`/health`, `/version`)
    - Phase 2 artifact/evidence endpoints (`/artifacts`, `/evidence-units`)

    It must not expose FileClerk/retrieval packets,
    LLM calls/answer synthesis, multimodal ingestion, or UI behavior.
    """

    app = FastAPI(title="GraphClerk", version="0.1.0")

    app.include_router(health_router)
    app.include_router(version_router)
    app.include_router(artifacts_router)
    app.include_router(evidence_router)
    app.include_router(graph_nodes_router)
    app.include_router(graph_edges_router)
    app.include_router(graph_node_evidence_router)
    app.include_router(graph_edge_evidence_router)
    app.include_router(graph_traversal_router)
    app.include_router(semantic_indexes_router)

    return app


app = create_app()

