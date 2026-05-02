from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.artifacts import router as artifacts_router
from app.api.routes.evidence_units import router as evidence_router
from app.api.routes.graph_edge_evidence import router as graph_edge_evidence_router
from app.api.routes.graph_edges import router as graph_edges_router
from app.api.routes.graph_node_evidence import router as graph_node_evidence_router
from app.api.routes.graph_nodes import router as graph_nodes_router
from app.api.routes.graph_traversal import router as graph_traversal_router
from app.api.routes.health import router as health_router
from app.api.routes.model_pipeline import router as model_pipeline_router
from app.api.routes.retrieval_logs import router as retrieval_logs_router
from app.api.routes.retrieve import router as retrieve_router
from app.api.routes.semantic_indexes import router as semantic_indexes_router
from app.api.routes.version import router as version_router


def create_app() -> FastAPI:
    """Create the GraphClerk FastAPI application.

    Phase 0–2 scope: infrastructure plus text-first ingestion inspection routes.

    This app wires:
    - infrastructure endpoints (`/health`, `/version`)
    - Phase 2 artifact/evidence endpoints (`/artifacts`, `/evidence-units`)
    - Phase 5 shell: `POST /artifacts` multimodal types via
      ``MultimodalIngestionService`` + ``ExtractorRegistry``.

    It exposes Phase 4 `POST /retrieve` (structured packets only) and Phase 6 read-only
    retrieval log inspection (`GET /retrieval-logs`, `GET /retrieval-logs/{id}`).
    Phase 7 optional language detection for ingestion is wired in ``POST /artifacts``
    (see ``app.api.routes.artifacts``) when ``GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER`` is set;
    default remains ``not_configured``.
    It must not expose LLM calls/answer synthesis, UI behavior, or automatic graph extraction.
    """

    app = FastAPI(title="GraphClerk", version="0.1.0")

    # Browser UI (Vite, etc.) runs on another origin than the API; without CORS, fetches fail
    # with "Failed to fetch" / status 0. Allow loopback dev hosts by default; pin origins in
    # production via GRAPHCLERK_CORS_ORIGINS="https://app.example,https://...".
    # GRAPHCLE_CORS_ORIGINS is a backward-compatible alias (legacy typo in shipped env name).
    _cors_raw = (
        os.environ.get("GRAPHCLERK_CORS_ORIGINS", "").strip()
        or os.environ.get("GRAPHCLE_CORS_ORIGINS", "").strip()
    )
    if _cors_raw:
        _origins = [o.strip() for o in _cors_raw.split(",") if o.strip()]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(health_router)
    app.include_router(version_router)
    app.include_router(model_pipeline_router)
    app.include_router(artifacts_router)
    app.include_router(evidence_router)
    app.include_router(graph_nodes_router)
    app.include_router(graph_edges_router)
    app.include_router(graph_node_evidence_router)
    app.include_router(graph_edge_evidence_router)
    app.include_router(graph_traversal_router)
    app.include_router(semantic_indexes_router)
    app.include_router(retrieve_router)
    app.include_router(retrieval_logs_router)

    return app


app = create_app()

