# GraphClerk

GraphClerk is a **local-first, graph-guided evidence-routing layer for RAG systems**.

It is not a chatbot by itself. It does not try to replace RAG frameworks, vector databases, or LLMs.
It improves the layer between user intent and LLM context by returning **structured evidence packets**
with traceability to original source artifacts.

## Project principle
**Search meaning first, then retrieve evidence.**

## What’s implemented (honest status)
- **Phase 0**: governance baseline (`docs/governance/*`)
- **Phase 1**: backend foundation (FastAPI, SQLAlchemy/Alembic, Docker Compose, `/health`, `/version`)
- **Phase 2**: text/Markdown ingestion → `Artifact` + `EvidenceUnit` with location metadata
- **Phase 3 (in progress)**: graph nodes/edges + evidence support links + semantic index CRUD (no vector search yet)

## What is explicitly not implemented yet
- **FileClerk** / RetrievalPacket assembly
- answer synthesis / LLM calls
- automatic graph extraction / claim extraction
- multimodal ingestion (PDF/PPTX/images/audio/video)
- semantic index vector search (Qdrant search endpoints) and bounded traversal are Phase 3 items but may be incomplete until Phase 3 audit says otherwise
- UI

## Governance first
This repository starts with Phase 0 governance guardrails. Technical implementation must not begin
until the governance baseline is present and committed.

- `docs/graph_clerk_phase_0_governance_baseline.md`: Phase 0 initialization document (source)
- `docs/governance/`: split governance documents used by prompts, reviews, and audits
- `docs/phases/PHASE_1_FOUNDATION.md`: Phase 1 implementation status and non-features
- `docs/phases/PHASE_2_TEXT_FIRST_INGESTION.md`: Phase 2 ingestion behavior (text/Markdown only)
- `docs/phases/graph_clerk_phase_3_semantic_index_and_graph_layer.md`: Phase 3 definition (meaning layer)
- `docs/status/`: status tracking (honesty rules)
- `docs/adr/`: architecture decision records (ADRs)

## Quickstart (Docker)
Start API + Postgres + Qdrant:

```bash
docker compose up -d --build
```

API runs on `http://localhost:8000`.

## Quickstart (local dev)
From `backend/`:

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m uvicorn app.main:app --reload
```

## Running tests
- **Default** (fast, no external services): `python -m pytest`
- **Integration tests** (opt-in): set:
  - `RUN_INTEGRATION_TESTS=1`
  - `DATABASE_URL=...`
  - `QDRANT_URL=...` (only for Qdrant tests)

## API surface (current)
Infrastructure:
- `GET /health`
- `GET /version`

Artifacts / Evidence (Phase 2):
- `POST /artifacts` (multipart or JSON inline text)
- `GET /artifacts`
- `GET /artifacts/{artifact_id}`
- `GET /artifacts/{artifact_id}/evidence`
- `GET /evidence-units/{evidence_unit_id}`

Graph (Phase 3, in progress):
- `POST /graph/nodes`
- `GET /graph/nodes/{node_id}`
- `GET /graph/nodes`
- `POST /graph/edges`
- `GET /graph/edges/{edge_id}`
- `GET /graph/edges`
- `POST /graph/nodes/{node_id}/evidence`
- `POST /graph/edges/{edge_id}/evidence`

Semantic indexes (Phase 3, in progress; **no vector search yet**):
- `POST /semantic-indexes`
- `GET /semantic-indexes/{semantic_index_id}`
- `GET /semantic-indexes/{semantic_index_id}/entry-points`

