# Project Status

## Summary
- **Current phase**: Phase 5 — Multimodal ingestion (**in progress**, **partially implemented**, **not fully complete**; Phase 5 audit **`pass_with_notes`** — see `docs/audits/PHASE_5_AUDIT.md`). Phase 6 — Productization / UI (**in progress**, **partial**; no Phase 6 audit yet — see `docs/phases/graph_clerk_phase_6_productization_ui_evaluation_hardening.md`).
- **Prior milestone**: Phase 4 implemented (**pass_with_notes**; structured retrieval only; no `/answer` yet; see limitations below)

## High-level status
- **Governance baseline**: implemented
- **Phase 1 foundation**: implemented
- **Phase 2 text-first ingestion**: implemented
- **Phase 3 semantic index + graph layer**: implemented (pass_with_notes)
- **Phase 4 File Clerk + retrieval packets**: implemented (pass_with_notes)
- **Phase 5 multimodal ingestion**: **in progress** / **partially implemented** (see Phase 5 section below; audit **`pass_with_notes`**)
- **Phase 6 productization / UI**: **in progress** / **partially implemented** (React/Vite app in `frontend/`; main explorers and query playground wired to live APIs; Phase 6 audit and several phase-doc deliverables still open — see Phase 6 section below)
- **Phase 6 readiness (Slice 6.0):** Per [`docs/phases/graph_clerk_phase_6_productization_ui_evaluation_hardening.md`](docs/phases/graph_clerk_phase_6_productization_ui_evaluation_hardening.md) (**Slice 6.0**), productization/UI work may proceed without Phase 5 being fully complete, provided the documented baseline and UI honesty rules are followed.

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

## Implemented (Phase 5 — partial; not fully complete)
- **`EvidenceUnitCandidate`** contract hardening
- **`ArtifactExtractor`** protocol + **`ExtractorRegistry`**
- Multimodal **routing shell** for `POST /artifacts` multipart uploads
- **`ArtifactTypeResolver`** (filename + MIME → artifact type / modality)
- **PDF** basic text extraction via optional **`pdf`** extra (pypdf) → `EvidenceUnit`s with location metadata
- **PPTX** basic slide text via optional **`pptx`** extra (python-pptx) → `EvidenceUnit`s
- **Image** / **audio** **validation shells** only (optional **`image`** / Pillow, **`audio`** / mutagen): bytes validated; **no** OCR, captioning, or transcription; **no** `EvidenceUnit`s from image/audio (API returns **503** after validation)
- **Tests**: File Clerk + graph compatibility for PDF/PPTX multimodal evidence in `POST /retrieve` packets; HTTP error matrix for multimodal `POST /artifacts`

## Implemented (Phase 6 — partial; not fully complete)
- **Web UI** (`frontend/`): React/Vite/TypeScript; health check against configured API base; tabbed **query playground** (retrieval + readable/raw packet), **artifacts and evidence** explorer, **semantic indexes** explorer, **graph** explorer, **retrieval logs** explorer, **evaluation** dashboard — all against **live** backend contracts (no in-app mock corpus)
- **Honesty**: UI copy and behavior align with Phase 5 limits (no OCR/ASR/caption/video claims; image/audio text evidence remains unavailable where the API returns shell/503 semantics)

## Not implemented (by design) — unchanged global items
- optional packet-only answer synthesis (`POST /answer`, LocalRAGConsumer) — deferred
- LLM calls / answer synthesis

## Phase 5 limitations (explicit)
- **OCR / image captioning / visual summaries**: not implemented
- **Audio transcription / ASR**: not implemented
- **Image and audio** do **not** currently emit `EvidenceUnit`s
- **Video** ingestion: rejected (**400**); deferred / not supported
- **No** automatic multimodal graph extraction
- **No** FileClerk redesign and **no** `RetrievalPacket` schema redesign for multimodal (existing packet path carries PDF/PPTX evidence as tested)
- Optional extras and extraction quality remain **known constraints**; Phase 5 audit is **`pass_with_notes`** (partial implementation accepted — not full phase completion)

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

## Phase 6 limitations (explicit)
- Phase 6 **audit** not completed; phase treated as **in progress**
- Phase doc items still open at a high level (non-exhaustive): public demo sample data workflow in-product, onboarding/release checklist polish, optional API hardening pass, optional automated frontend/E2E test coverage
- **`POST /answer`** / packet-grounded answer viewer remains out of scope until `/answer` is approved and implemented

