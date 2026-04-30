# Phase 1 — Foundation and Core Architecture (Implemented)

## Purpose
Phase 1 establishes the technical spine for GraphClerk:
- FastAPI backend skeleton
- Docker Compose for local boot
- PostgreSQL connectivity
- Qdrant connectivity
- Alembic migrations
- Core persistence models (shape only)
- Basic tests

## What Phase 1 implements
- **Backend skeleton**: `backend/app/main.py` with infrastructure routes
- **Infrastructure endpoints**:
  - `GET /health` → `{"status":"ok"}`
  - `GET /version` → `{"name":"GraphClerk","version":"0.1.0","phase":"phase_1_foundation"}`
- **Config layer**: typed settings in `backend/app/core/config.py`
- **Local services**: `docker-compose.yml` spins up `api`, `postgres`, `qdrant`
- **Database foundation**:
  - SQLAlchemy base/session: `backend/app/db/*`
  - Alembic configured via `DATABASE_URL`: `backend/alembic.ini`, `backend/app/db/migrations/*`
  - Initial migration: `backend/app/db/migrations/versions/0001_phase1_core_models.py`
- **Core persistence models (schema only)**:
  - `Artifact`, `EvidenceUnit`, `GraphNode`, `GraphEdge`, `SemanticIndex`, `RetrievalLog`

## What Phase 1 explicitly does NOT implement
GraphClerk still cannot:
- ingest documents
- parse Markdown/PDF/PPTX/images/audio/video
- create evidence units from real files
- generate embeddings
- perform semantic search
- traverse the graph
- assemble retrieval packets
- implement FileClerk logic
- call LLMs or synthesize answers
- provide a UI

This is intentional and enforced by governance.

## How to run (local)
1. Start services:
   - `docker compose up -d --build`
2. Call endpoints:
   - `GET http://localhost:8000/health`
   - `GET http://localhost:8000/version`

## Tests
- Unit/API tests run without external services.\n- Integration tests for DB/models/Qdrant are gated behind `RUN_INTEGRATION_TESTS=1` and require `DATABASE_URL` / `QDRANT_URL`.

