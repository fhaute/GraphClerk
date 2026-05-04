# Project Status

## Summary
- **Pre–Phase 9 completion program (tracking only):** [`docs/plans/phase_1_8_completion_program.md`](../plans/phase_1_8_completion_program.md) — Phase **8** Track **D** closure recorded (**D8** audit **`pass`** — [`PHASE_8_FULL_COMPLETION_AUDIT.md`](../audits/PHASE_8_FULL_COMPLETION_AUDIT.md)); optional **Track E–H** / Phase **9** work remains **separate**. **Readiness / drift (Control C0):** [`docs/reports/phase_1_8_global_completion_audit_inventory.md`](../reports/phase_1_8_global_completion_audit_inventory.md), [`docs/reports/phase_1_8_thorough_code_verification_audit.md`](../reports/phase_1_8_thorough_code_verification_audit.md).
- **Current phase**: Phase 7 — Context Intelligence (**full-completion `pass`** — [`PHASE_7_FULL_COMPLETION_AUDIT.md`](../audits/PHASE_7_FULL_COMPLETION_AUDIT.md); baseline history [`PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md)). Phase 5 — Multimodal ingestion remains **in progress** / **partial** (**`pass_with_notes`**). Phase 6 — **`pass_with_notes`**. **`POST /answer`** remains **deferred**. **Phase 8** — specialized model pipeline: **implemented for the agreed Phase 1–8 completion scope**; full-completion audit **`pass`** — [`docs/audits/PHASE_8_FULL_COMPLETION_AUDIT.md`](../audits/PHASE_8_FULL_COMPLETION_AUDIT.md) (**2026-05-02**, **Track D D8**); baseline history [`docs/audits/PHASE_8_AUDIT.md`](../audits/PHASE_8_AUDIT.md) (**2026-05-03**). **Phase 9**: **`not_started`** (spec-only).
- **Prior milestones**: Phase 4 File Clerk (**pass_with_notes**); Phase 7 baseline builds on Phases 4–6 without replacing evidence-grounded retrieval.

## High-level status
- **Governance baseline**: implemented
- **Phase 1 foundation**: implemented
- **Phase 2 text-first ingestion**: implemented
- **Phase 3 semantic index + graph layer**: implemented (pass_with_notes)
- **Phase 4 File Clerk + retrieval packets**: implemented (pass_with_notes)
- **Phase 5 multimodal ingestion**: **in progress** / **partially implemented** (see Phase 5 section below; audit **`pass_with_notes`**)
- **Phase 6 productization / UI**: **implemented (`pass_with_notes`)** — React/Vite app in `frontend/`; explorers and query playground wired to **live** APIs; audit `docs/audits/PHASE_6_AUDIT.md` records accepted gaps (no production SLA, no frontend test harness, script-only demo loader, optional hardening). **Not** a claim of full phase-doc closure.
- **Phase 7 — Context Intelligence**: **implemented for the agreed Phase 1–8 completion scope** — [`docs/audits/PHASE_7_FULL_COMPLETION_AUDIT.md`](../audits/PHASE_7_FULL_COMPLETION_AUDIT.md) (**`pass`**); baseline history [`docs/audits/PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md). **Slice 7I** boosting remains **deferred / cancelled** pending separate approval. Phase contract: [`docs/phases/graph_clerk_phase_7_context_intelligence.md`](../phases/graph_clerk_phase_7_context_intelligence.md).
- **Phase 8 — Specialized Model Pipeline**: **implemented for the agreed Phase 1–8 completion scope** — [`docs/audits/PHASE_8_FULL_COMPLETION_AUDIT.md`](../audits/PHASE_8_FULL_COMPLETION_AUDIT.md) (**`pass`**, **Track D D8**, **2026-05-02**). **Completion Program Track D** (**D1–D8**) **complete** for this scope. **Baseline history:** [`docs/audits/PHASE_8_AUDIT.md`](../audits/PHASE_8_AUDIT.md) (**`pass_with_notes`**, **2026-05-03**). **Not claimed:** **`openai_compatible`** adapter, writable selector/persistence/auth, **`/answer`**, **`routing_hint_generator`** enablement, Phase **9**. Phase contract: [`docs/phases/graph_clerk_phase_8_specialized_model_pipeline.md`](../phases/graph_clerk_phase_8_specialized_model_pipeline.md).
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
- The bundled **`api`** Compose service sets **`RUN_INTEGRATION_TESTS=1`** and **`GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER=deterministic_fake`** so local semantic search / **`POST /retrieve`** can use the stack’s Qdrant with **non-semantic** 8-d test vectors only (see `docs/governance/TESTING_RULES.md`; not a production embedding path).
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

## Implemented (Phase 8 — agreed Phase 1–8 completion scope; full-completion audit **`pass`**)
- **8A–8F** — Contracts, envelopes, **`NotConfigured`** + **tests-only** deterministic adapters, validation, **metadata-only** projection, evaluation fixtures — [`backend/app/services/model_pipeline_contracts.py`](../../backend/app/services/model_pipeline_contracts.py) et al.; tests `backend/tests/test_phase8_model_pipeline_*.py`.
- **Track D (Completion Program)** — Settings + [`model_pipeline_registry.py`](../../backend/app/services/model_pipeline_registry.py) (**`ollama`** build path; **`openai_compatible`** reserved/not implemented); **`OllamaModelPipelineAdapter`**; **`model_pipeline_purpose_registry.py`**; **`ModelPipelineMetadataEnrichmentService`**; optional ingest merge via [`artifacts.py`](../../backend/app/api/routes/artifacts.py) + [`evidence_enrichment_service.py`](../../backend/app/services/evidence_enrichment_service.py); read-only **[`GET /model-pipeline/config`](../../backend/app/api/routes/model_pipeline.py)**.
- **UI** — **`ArtifactsExplorer`** (**D7a**); **`EvaluationDashboard`** config table (**D7b**).
- **8G** — Broader adapter/fleet narratives in phase/working plans; **agreed scope** is **Ollama** path + env gates — not **`openai_compatible`**.
- **Audits** — **[`docs/audits/PHASE_8_FULL_COMPLETION_AUDIT.md`](../audits/PHASE_8_FULL_COMPLETION_AUDIT.md)** (**`pass`**, **Track D D8**, **2026-05-02**). **Baseline history:** [`docs/audits/PHASE_8_AUDIT.md`](../audits/PHASE_8_AUDIT.md).

## Phase 8 — explicit non-goals (still true after closure)
- **`openai_compatible`** / **vLLM** adapter; **writable** selector + **config persistence** + **admin/auth** (**D7c**).
- **`routing_hint_generator`** / **`artifact_classifier`** / **`extraction_helper`** enablement under current policy.
- **`POST /answer`**; Phase **9**; model output treated as **verbatim evidence**; **FileClerk** / **`POST /retrieve`** wiring for pipeline adapters; **retrieval ranking** changes from model metadata.
- Phase-doc **north-star** items beyond the Completion Program agreed scope — see [`docs/phases/graph_clerk_phase_8_specialized_model_pipeline.md`](../phases/graph_clerk_phase_8_specialized_model_pipeline.md) vs [`PHASE_8_FULL_COMPLETION_AUDIT.md`](../audits/PHASE_8_FULL_COMPLETION_AUDIT.md).

## Implemented (Phase 6 — baseline; `pass_with_notes`)
- **Web UI** (`frontend/`): React/Vite/TypeScript; health + optional **`GET /version`** line; tabbed **query playground** (retrieval + readable/raw packet), **artifacts and evidence**, **semantic indexes**, **graph** (includes **XYFlow** neighborhood diagram after **Load neighborhood**), **retrieval logs**, **evaluation** — all against **live** backend contracts (no in-app mock corpus)
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
- `GET /semantic-indexes/search` (Postgres-backed metadata + Qdrant score; returns only `vector_status=indexed`; **drops** Qdrant hits whose index id is absent in Postgres — stale/orphan vectors)
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
- **Closure (agreed Phase 1–8 scope):** Phase 7 is **implemented** for that scope — **[`docs/audits/PHASE_7_FULL_COMPLETION_AUDIT.md`](../audits/PHASE_7_FULL_COMPLETION_AUDIT.md)** (**`pass`**, **Track C Slice C9**). **[`docs/audits/PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md)** (**`pass_with_notes`**) remains **historical baseline only** — deferred items there are **not** the current closure bar.
- **Language detection**: **default** **`not_configured`** (no implicit detector). Optional **Lingua** when **`GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER=lingua`** + **`language-detector`** extra; **`POST /artifacts`** wires **`build_evidence_enrichment_service`** (**Track C8**); **503** if **`lingua`** requested but unavailable — **no** silent fallback.
- **Translation / query translation**: **not implemented** — **future / out of scope** for agreed closure unless reopened.
- **ActorContext**: recorded on **`RetrievalPacket`** only; **does not** change route selection, evidence ranking, traversal, budget, warnings, confidence, or **`answer_mode`**.
- **Deterministic context boosting** (**Slice 7I**): **not implemented** — **deferred / cancelled** pending separate approval (**future / out of scope** for agreed Track **C** closure).
- **UI:** **Track C7** surfaces — artifact **Language aggregation** readout; packet **`language_context`** / **`actor_context`** clarity in the UI; not a claim of enterprise context product beyond inspection tooling.

## Phase 4 limitations (explicit)
- query intent + ambiguity handling are deterministic/heuristic (not ML-tuned)
- confidence is a simple heuristic (not calibrated)
- optional `/answer` path is intentionally not implemented in this repository state

## Phase 6 limitations (explicit; still true after `pass_with_notes`)
- **Not production enterprise software** — no first-class auth/RBAC/SLA; UI is inspection / demo productization.
- Phase doc **stretch** items may remain (non-exhaustive): in-product demo loader UX, deeper API hardening, automated frontend/E2E tests — tracked in roadmap/gaps as applicable.
- **Slice K + Slice L**: onboarding docs, release checklist, Phase 6 audit artifact delivered; **`pass_with_notes`** explicitly accepts remaining gaps above.
- **`POST /answer`** / packet-grounded answer viewer remains out of scope until `/answer` is approved and implemented

