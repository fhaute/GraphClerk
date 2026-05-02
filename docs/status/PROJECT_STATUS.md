# Project Status

## Summary
- **Pre–Phase 9 completion program (tracking only):** [`docs/plans/phase_1_8_completion_program.md`](../plans/phase_1_8_completion_program.md) — active plan to finish **intended** Phase 1–8 scope before Phase 9; **not** a claim that full completion is done.
- **Current phase**: Phase 7 — Context Intelligence (**baseline implemented**; audit **`pass_with_notes`** — [`docs/audits/PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md), **2026-05-02**). Phase 5 — Multimodal ingestion remains **in progress** / **partial** (audit **`pass_with_notes`** — `docs/audits/PHASE_5_AUDIT.md`). Phase 6 — Productization / UI remains **`pass_with_notes`** (`docs/audits/PHASE_6_AUDIT.md`). **`POST /answer`** remains **deferred**. **Phase 8** — specialized model pipeline: **baseline implemented**; audit **`pass_with_notes`** — [`docs/audits/PHASE_8_AUDIT.md`](../audits/PHASE_8_AUDIT.md) (**2026-05-03**); **not** full specialized-model production (no production inference adapter, no registry). **Phase 9**: **`not_started`** (spec-only).
- **Prior milestones**: Phase 4 File Clerk (**pass_with_notes**); Phase 7 baseline builds on Phases 4–6 without replacing evidence-grounded retrieval.

## High-level status
- **Governance baseline**: implemented
- **Phase 1 foundation**: implemented
- **Phase 2 text-first ingestion**: implemented
- **Phase 3 semantic index + graph layer**: implemented (pass_with_notes)
- **Phase 4 File Clerk + retrieval packets**: implemented (pass_with_notes)
- **Phase 5 multimodal ingestion**: **in progress** / **partially implemented** (see Phase 5 section below; audit **`pass_with_notes`**)
- **Phase 6 productization / UI**: **implemented (`pass_with_notes`)** — React/Vite app in `frontend/`; explorers and query playground wired to **live** APIs; audit `docs/audits/PHASE_6_AUDIT.md` records accepted gaps (no production SLA, no frontend test harness, script-only demo loader, optional hardening). **Not** a claim of full phase-doc closure.
- **Phase 7 — Context Intelligence**: **baseline implemented (`pass_with_notes`)** — [`docs/audits/PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md); Slices **7A–7H** + **7J** (docs/status honesty per working plan) shipped; **Slice 7K** (audit) complete; **Slice 7I** boosting remains **deferred / cancelled** pending separate approval. Working plan: `.cursor/plans/phase_7_context_intelligence_b9e4f2a1.plan.md`; phase contract: [`docs/phases/graph_clerk_phase_7_context_intelligence.md`](../phases/graph_clerk_phase_7_context_intelligence.md).
- **Phase 8 — Specialized Model Pipeline**: **baseline implemented** (**audit `pass_with_notes`**) — [`docs/audits/PHASE_8_AUDIT.md`](../audits/PHASE_8_AUDIT.md); contracts/envelopes/validation/projection/fixtures + **8G design-only**; **`NotConfigured`** default; **no** production inference, **no** `/answer`, **no** ingestion/enrichment/FileClerk wiring for model output. **Completion Program Track D — Slice D1:** full-completion **design** decisions — [`docs/decisions/phase_8_model_pipeline_completion_decisions.md`](../decisions/phase_8_model_pipeline_completion_decisions.md) (**no implementation yet**). Working plan: [`.cursor/plans/phase_8_specialized_model_pipeline_1b9d495c.plan.md`](../../.cursor/plans/phase_8_specialized_model_pipeline_1b9d495c.plan.md); phase contract: [`docs/phases/graph_clerk_phase_8_specialized_model_pipeline.md`](../phases/graph_clerk_phase_8_specialized_model_pipeline.md).
- **Phase 9 — IDE integration**: **`not_started`** (spec-only).
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

## Implemented (Phase 7 — agreed Phase 1–8 completion scope; full-completion audit **`pass`**)
- **`EvidenceEnrichmentService`** — **default** identity enrichment; optional injected **`LanguageDetectionService`** (**Track C4**)
- Language metadata on **`EvidenceUnitCandidate`** / EU persistence via **`metadata_json`** (contract path)
- **`LanguageDetectionService`** — **`NotConfigured`** default adapter; optional **Lingua** when **`GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER=lingua`** + **`language-detector`** extra (**Track C3**)
- **`POST /artifacts`** wires **`build_evidence_enrichment_service`** — **`not_configured`** (default) vs **`lingua`** (**Track C8**; **503** if **`lingua`** set but Lingua cannot be constructed — **no** silent fallback); same enrichment instance for **text/markdown** and **multimodal** ingest
- **`ArtifactLanguageAggregationService`** — ingest persists **`graphclerk_language_aggregation`** on **`Artifact.metadata_json`** (**Track C5**)
- **`RetrievalPacket.language_context`** from **selected** evidence **`metadata_json`** only (**not** translation; **not** detection inside packet assembly)
- Optional **`actor_context`** on **`POST /retrieve`**; **`RetrievalPacket.actor_context`** recording (**`PacketActorContextRecording`**) — **no** route or evidence boost (**7I** not implemented)
- Phase 7 UI: artifact **Language aggregation** readout + packet **`language_context`** / **`actor_context`** copy (**Track C7** + minor Query Playground honesty)
- Phase 7 tests: `backend/tests/test_phase7_*.py` (see `docs/status/PHASE_STATUS.md`)
- **Audits**: **[`docs/audits/PHASE_7_FULL_COMPLETION_AUDIT.md`](../audits/PHASE_7_FULL_COMPLETION_AUDIT.md)** — **`pass`** (**Track C Slice C9**, 2026-05-01) — **closure** for agreed Phase 1–8 scope. **Baseline history:** [`docs/audits/PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md) — **`pass_with_notes`** (2026-05-02); **not** erased.

## Implemented (Phase 8 — baseline; audit **`pass_with_notes`**)
- **8A — Model pipeline contracts**: typed roles/tasks/results; role ↔ output matrix — [`backend/app/services/model_pipeline_contracts.py`](../../backend/app/services/model_pipeline_contracts.py)
- **8B — Request/response envelopes**: `ModelPipelineRequestEnvelope`, `ModelPipelineResponseEnvelope`, `ModelPipelineError`; success vs failure shape rules — same module
- **8C — Adapters**: `ModelPipelineAdapter` protocol; **`NotConfiguredModelPipelineAdapter`** (default explicit unavailable semantics); **`DeterministicTestModelPipelineAdapter`** (**tests only**)
- **8D — Output validation**: `ModelPipelineOutputValidationService` — recursive semantic checks (no FileClerk/retrieval) — [`backend/app/services/model_pipeline_output_validation_service.py`](../../backend/app/services/model_pipeline_output_validation_service.py)
- **8E — Projection (standalone)**: `ModelPipelineCandidateMetadataProjectionService` → metadata subtree **`graphclerk_model_pipeline`** only; **not** wired to ingestion/enrichment — [`backend/app/services/model_pipeline_candidate_projection_service.py`](../../backend/app/services/model_pipeline_candidate_projection_service.py)
- **8F — Evaluation fixtures**: deterministic builders + tests — [`backend/tests/fixtures/phase8_model_pipeline_cases.py`](../../backend/tests/fixtures/phase8_model_pipeline_cases.py), `backend/tests/test_phase8_model_pipeline_evaluation_fixtures.py`
- **8G — Local inference adapter**: **design-only** in working plan (optional future Ollama/vLLM HTTP adapters); **no** implementation, **no** new dependencies
- **Tests**: `backend/tests/test_phase8_*.py` (contracts, validation, projection, evaluation fixtures)
- **Honesty**: **No** real model adapter in app code; **no** inference by default; **no** model calls on core paths; **model output is not evidence**; projection is **metadata-only** under **`graphclerk_model_pipeline`**.

## Phase 8 limitations (explicit)
- **Not** full Phase 8 phase-doc “north star” (e.g. registry, production routing UI, specialized inference fleet) — only the **contract / validation / projection baseline** above.
- **Slice 8I** — Phase **8** audit: **`pass_with_notes`** — [`docs/audits/PHASE_8_AUDIT.md`](../audits/PHASE_8_AUDIT.md) (**2026-05-03**); north-star phase-doc objectives (registry, fleet, UI) remain largely future work.
- **No** production local inference adapter (Ollama/vLLM/etc.); **8G** is recommendations only.
- **No** adapter registry; **no** model settings in product config for pipeline inference.
- **No** wiring of model pipeline into **`POST /retrieve`**, FileClerk, text/multimodal ingestion, or **`EvidenceEnrichmentService`** for merge/persist.
- **No** **`POST /answer`** / answer synthesis; **no** LLM calls in ingestion/retrieval paths.
- **No** mutation of **`EvidenceUnit`** / **`EvidenceUnitCandidate.text`** / **`source_fidelity`** from model pipeline code.
- **No** **`RetrievalPacket`** selected-source evidence mutation via model output.

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
- **Track B Slice B1:** `SemanticIndexVectorIndexingService` + operator script [`scripts/backfill_semantic_indexes.py`](../scripts/backfill_semantic_indexes.py) — explicit **`pending`/`failed` → `indexed`/`failed`** (no silent `pending`); dev embeddings only until a production adapter is wired for this path

## Implemented (Phase 4)
- `POST /retrieve` returns a validated `RetrievalPacket` JSON object for every request (including empty semantic matches)
- `FileClerkService` orchestrates intent, route selection (which owns semantic search), bounded traversal, graph-linked evidence selection, budgeting, and packet assembly
- `RetrievalLog.retrieval_packet` stores the canonical JSON snapshot (plus existing summary JSON fields)

## Phase 3 limitations (explicit)
- production embedding adapter not wired
- SemanticIndex creation does not auto-index vectors into Qdrant
- **Manual dev/operator vector backfill** (Track B Slice B1): `SemanticIndexVectorIndexingService` + [`scripts/backfill_semantic_indexes.py`](../scripts/backfill_semantic_indexes.py) — uses **deterministic fake** embeddings for dev; **not** automatic indexing or a background job system
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

