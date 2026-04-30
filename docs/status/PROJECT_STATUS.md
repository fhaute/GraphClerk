# Project Status

## Summary
- **Current phase**: Phase 4 — File Clerk & retrieval packets
- **Implementation status**: Phase 4 implemented (**pass_with_notes**; structured retrieval only; no `/answer` yet; see limitations below)

## High-level status
- **Governance baseline**: implemented
- **Phase 1 foundation**: implemented
- **Phase 2 text-first ingestion**: implemented
- **Phase 3 semantic index + graph layer**: implemented (pass_with_notes)
- **Phase 4 File Clerk + retrieval packets**: implemented (pass_with_notes)

## Implemented (Phase 1)
- FastAPI skeleton with infrastructure routes (`/health`, `/version`)
- Docker Compose for `api`, `postgres`, `qdrant`
- Typed configuration layer
- SQLAlchemy base/session and Alembic setup
- Core persistence models (schema shape only)

## Verification notes
- `docker compose up -d --build` starts API + Postgres + Qdrant.
- `/health` and `/version` return the expected JSON.
- Unit/API tests pass without external services.
- Integration tests exist and are **opt-in** (require `RUN_INTEGRATION_TESTS=1` plus `DATABASE_URL` / `QDRANT_URL`).

## Implemented (Phase 2)
- `POST /artifacts` ingestion for **text/Markdown**
- Hybrid raw source preservation (`raw_text` in DB for small sources; disk for large sources)
- EvidenceUnit creation with location metadata
- Inspection APIs (`GET /artifacts`, `GET /artifacts/{id}`, evidence listing and retrieval)

## Not implemented (by design)
- multimodal parsing (PDF/PPTX/images/audio/video)
- optional packet-only answer synthesis (`POST /answer`, LocalRAGConsumer) — deferred
- LLM calls / answer synthesis
- UI

## Implemented (Phase 3)
- Graph nodes/edges APIs and persistence
- Evidence support link tables + APIs (nodes and edges)
- SemanticIndex APIs + normalized entry nodes (`semantic_index_entry_node` is source of truth)
- `SemanticIndex.vector_status` (`pending | indexed | failed`)
- Embedding adapter interface + deterministic fake + explicit “not configured” adapter
- Qdrant VectorIndexService (collection management, upsert, search) with explicit error behavior
- `GET /semantic-indexes/search` (Postgres-backed metadata + Qdrant score; returns only `vector_status=indexed`)
- Bounded graph traversal: `GET /graph/nodes/{node_id}/neighborhood` with truncation reporting

## Implemented (Phase 4)
- `POST /retrieve` returns a validated `RetrievalPacket` JSON object for every request (including empty semantic matches)
- `FileClerkService` orchestrates intent, route selection (which owns semantic search), bounded traversal, graph-linked evidence selection, budgeting, and packet assembly
- `RetrievalLog.retrieval_packet` stores the canonical JSON snapshot (plus existing summary JSON fields)

## Phase 3 limitations (explicit)
- production embedding adapter not wired
- SemanticIndex creation does not auto-index vectors into Qdrant
- no indexing job/backfill
- integration tests are opt-in/gated (`RUN_INTEGRATION_TESTS=1` + env vars)

## Phase 4 limitations (explicit)
- query intent + ambiguity handling are deterministic/heuristic (not ML-tuned)
- confidence is a simple heuristic (not calibrated)
- optional `/answer` path is intentionally not implemented in this repository state

