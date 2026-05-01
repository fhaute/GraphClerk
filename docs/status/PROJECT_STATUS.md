# Project Status

## Summary
- **Current phase**: Phase 7 — Context Intelligence (**baseline implemented**; audit **`pass_with_notes`** — [`docs/audits/PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md), **2026-05-02**). Phase 5 — Multimodal ingestion remains **in progress** / **partial** (audit **`pass_with_notes`** — `docs/audits/PHASE_5_AUDIT.md`). Phase 6 — Productization / UI remains **`pass_with_notes`** (`docs/audits/PHASE_6_AUDIT.md`). **`POST /answer`** remains **deferred**. Phases **8** / **9**: **not_started** (spec-only).
- **Prior milestones**: Phase 4 File Clerk (**pass_with_notes**); Phase 7 baseline builds on Phases 4–6 without replacing evidence-grounded retrieval.

## High-level status
- **Governance baseline**: implemented
- **Phase 1 foundation**: implemented
- **Phase 2 text-first ingestion**: implemented
- **Phase 3 semantic index + graph layer**: implemented (pass_with_notes)
- **Phase 4 File Clerk + retrieval packets**: implemented (pass_with_notes)
- **Phase 5 multimodal ingestion**: **in progress** / **partially implemented** (see Phase 5 section below; audit **`pass_with_notes`**)
- **Phase 6 productization / UI**: **implemented (`pass_with_notes`)** — React/Vite app in `frontend/`; explorers and query playground wired to **live** APIs; audit `docs/audits/PHASE_6_AUDIT.md` records accepted gaps (no production SLA, no frontend test harness, script-only demo loader, optional hardening). **Not** a claim of full phase-doc closure.
- **Phase 7 — Context Intelligence**: **baseline implemented (`pass_with_notes`)** — [`docs/audits/PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md); Slices **7A–7H** shipped; **Slice 7K** (audit) complete; **Slice 7I** boosting remains **deferred / cancelled** pending separate approval. Working plan: `.cursor/plans/phase_7_context_intelligence_b9e4f2a1.plan.md`; phase contract: [`docs/phases/graph_clerk_phase_7_context_intelligence.md`](../phases/graph_clerk_phase_7_context_intelligence.md). **Phase 8** / **Phase 9**: **not_started** (phase docs only; no implementation claimed).
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

## Implemented (Phase 7 — baseline; audit `pass_with_notes`)
- **`EvidenceEnrichmentService`** no-op shell (candidates unchanged unless a future adapter is wired)
- Language metadata on **`EvidenceUnitCandidate`** / EU persistence via **`metadata_json`** (contract path)
- **`LanguageDetectionService`** adapter shell (**NotConfigured** / deterministic test adapters)
- Enrichment seam in **text** and **multimodal** ingest paths with **no-op** default enrichment
- **`ArtifactLanguageAggregationService`** pure aggregation helper (artifact **`metadata_json`** persistence / ingestion merge deferred)
- **`RetrievalPacket.language_context`** from **selected** evidence **`metadata_json`** only (no translation / no detection in packet assembly)
- Optional **`actor_context`** on **`POST /retrieve`** request schema; **`RetrievalPacket.actor_context`** recording (**`PacketActorContextRecording`**) with explicit **`influence`** — **no** route or evidence boost in this baseline
- Phase 7 tests under `backend/tests/test_phase7_*.py` (see `docs/status/PHASE_STATUS.md`)
- **Audit**: [`docs/audits/PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md) — **`pass_with_notes`** (2026-05-02); explicit notes: no production detector-by-default, no translation, no boosting (**7I**), aggregation ingest wiring deferred

## Implemented (Phase 6 — baseline; `pass_with_notes`)
- **Web UI** (`frontend/`): React/Vite/TypeScript; health + optional **`GET /version`** line; tabbed **query playground** (retrieval + readable/raw packet), **artifacts and evidence**, **semantic indexes**, **graph**, **retrieval logs**, **evaluation** — all against **live** backend contracts (no in-app mock corpus)
- **Honesty**: UI and docs align with Phase 5 limits (no OCR/ASR/caption/video claims; no `/answer`; evaluation = observability metrics per `docs/evaluation/EVALUATION_METHOD.md`)
- **Audit**: `docs/audits/PHASE_6_AUDIT.md` — **`pass_with_notes`** (2026-05-01); see audit for verification commands and explicit non-goals

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

## Phase 7 limitations (explicit)
- **Audit notes**: Phase 7 is **`pass_with_notes`**, not unconditional **`pass`** — see [`docs/audits/PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md) for deferred detector, translation, boosting (**7I**), and UI gaps.
- **Language detection**: adapter shell exists; **no** automatic production detector wired by default on ingest.
- **Translation / query translation**: **not implemented**.
- **ActorContext**: recorded on **`RetrievalPacket`** only; **does not** change route selection, evidence ranking, traversal, budget, warnings, confidence, or **`answer_mode`**.
- **Deterministic context boosting** (**Slice 7I**): **not implemented** — deferred / separate approval.
- **UI**: Phase 6 playground may show new packet JSON fields where exposed; **no** dedicated Phase 7 context product surfaces claimed.

## Phase 4 limitations (explicit)
- query intent + ambiguity handling are deterministic/heuristic (not ML-tuned)
- confidence is a simple heuristic (not calibrated)
- optional `/answer` path is intentionally not implemented in this repository state

## Phase 6 limitations (explicit; still true after `pass_with_notes`)
- **Not production enterprise software** — no first-class auth/RBAC/SLA; UI is inspection / demo productization.
- Phase doc **stretch** items may remain (non-exhaustive): in-product demo loader UX, deeper API hardening, automated frontend/E2E tests — tracked in roadmap/gaps as applicable.
- **Slice K + Slice L**: onboarding docs, release checklist, Phase 6 audit artifact delivered; **`pass_with_notes`** explicitly accepts remaining gaps above.
- **`POST /answer`** / packet-grounded answer viewer remains out of scope until `/answer` is approved and implemented

