# Pre-Phase-8 Code Cleanliness Sweep

## Metadata

| Field | Value |
|--------|--------|
| **Date** | 2026-05-01 |
| **Current git commit** | `ffeb02e` — *docs: pre-phase-8 verification report — baseline-era framing* |
| **Baseline git status** | Clean working tree (no dirty or untracked files before this report was added). |
| **Scope** | Read-only inspection of: `backend/app/**/*.py`, `backend/tests/**/*.py`, `frontend/src/**/*.{ts,tsx}`, `scripts/**/*.py`, with awareness of `docs/governance/CODING_STANDARDS.md` and `docs/governance/ARCHITECTURAL_INVARIANTS.md`. |
| **Files modified during sweep** | **This report only** (`docs/reports/pre_phase_8_code_cleanliness_sweep.md`). No application code, tests, dependencies, or other docs were edited as part of the sweep. |

---

## Executive summary

| Severity | Count | Meaning |
|----------|-------|---------|
| **A** (must fix before Phase 8) | **0** | No static evidence of two production paths implementing the same business rule with **contradictory** behavior, or stale callable paths that would corrupt retrieval/evidence semantics. |
| **B** (should fix soon) | **5** | Duplicated constants/helpers that increase drift risk (language metadata keys; explorer UI formatters; script vs app env naming; repeated HTTP test harness; route pagination boilerplate). |
| **C** (optional polish) | **4** | Symmetric extractor shells, minor route/HTTPException patterns, intentional phase-test repetition. |

**Is Phase 8 blocked by this sweep alone?** **No.** This sweep is hygiene and seam clarity; official Phase 8 gates remain status/phase kickoff per `docs/phases/graph_clerk_phase_8_specialized_model_pipeline.md` (see **Project Manager Agent** handoff below).

**Recommended correction strategy:** **Apply non-blocking cleanup after Phase 8 kickoff** (or in small parallel hygiene slices): centralize language key constants, optional shared frontend `formatError` / `formatJson`, optional pytest ASGI client fixture. **No must-fix code cleanup is required solely on the basis of this sweep** before Phase 8 planning/kickoff.

---

## Inventory

| Area | Notable modules | Apparent owner / responsibility | Possible overlap |
|------|-----------------|--------------------------------|------------------|
| **Backend services** (`backend/app/services/`, ~44 `.py`) | `retrieval_packet_builder.py`, `evidence_selection_service.py`, `route_selection_service.py`, `semantic_index_search_service.py`, `file_clerk_service.py`, `multimodal_ingestion_service.py`, `text_ingestion_service.py`, `artifact_language_aggregation_service.py`, `language_detection_service.py`, `evidence_enrichment_service.py`, `embedding_service.py` / `embedding_adapter.py`, `raw_source_store.py`, graph services, `context_budget_service.py`, `query_intent_service.py` | **Retrieval path:** builder + selection + route vs semantic search factory. **Ingestion:** multimodal + text + type resolver. **Evidence:** units, enrichment, graph evidence. **Language:** detection vs aggregation vs packet `language_context`. | **Language:** aggregation reads EU `metadata` keys that duplicate string literals in `evidence_unit_candidate` (**B**). **Retrieval:** route selection vs semantic search are adjacent concerns but different steps — boundary is clear if maintained. |
| **Backend schemas** (`backend/app/schemas/`, 15 `.py`) | `retrieval_packet.py`, `retrieval.py`, `evidence_unit*.py`, `artifact.py`, graph/semantic schemas | API and internal DTO contracts; single source for OpenAPI-aligned shapes. | Some overlap between `retrieval` vs `retrieval_packet` naming — **document/mental model**, not duplicate implementations. |
| **API routes** (`backend/app/api/routes/`, 13 modules) | `retrieve.py`, `artifacts.py`, `evidence_units.py`, `semantic_indexes.py`, `retrieval_logs.py`, graph + traversal + evidence routes, `health.py`, `version.py` | HTTP surface; maps to services/repos. | Repeated `limit`/`offset` + `HTTPException` patterns (**C** boilerplate). |
| **Repositories** (`backend/app/repositories/`, 10 `.py`) | Artifact, evidence unit, retrieval log, semantic index (+ entry/node), graph node/edge (+ evidence link repos) | Persistence only; no business rules. | **None** — thin, non-overlapping tables of concern. |
| **Frontend API** (`frontend/src/api/`, 9 files) | `client.ts` (HTTP, `ApiError`, JSON helpers), thin modules per domain (`retrieval.ts`, `graph.ts`, …) | Central HTTP + error parsing in `client.ts`. | **None** at API layer; duplication is **UI-local** (see findings). |
| **Frontend types** (`frontend/src/types/`, 8 files) | Mirrors backend DTOs: `retrievalPacket.ts`, `evidenceUnit.ts`, `retrievalLog.ts`, etc. | Contract alignment with backend. | **Mild** field overlap between packet / log / evidence views — expected; drift risk if backend changes without TS update (**B** process, not duplicate code paths). |
| **Frontend components** (`frontend/src/components/`, 7 `.tsx`) | Explorers (`Graph`, `Artifacts`, `RetrievalLogs`, `SemanticIndexes`), `RetrievalPacketPanel`, `QueryPlayground`, `EvaluationDashboard` | Admin/debug UI for Phase 6–7 surfaces. | Repeated `formatError` / `formatJson` and JSON `<pre>` blocks (**B**). |
| **Scripts** (`scripts/`) | `load_phase6_demo.py` only | Demo loader; env for API base URL. | `GRAPHCLERK_API_BASE_URL` plus legacy typo alias `GRAPHCLE_API_BASE_URL` (**B** consistency). |

---

## Findings

Each row: **severity**, **files**, **issue**, **recommended action**, **tests**, **Phase 8 blocker**.

| Sev | File(s) / module | Duplicated / overlapping behavior | Why it matters | Recommended action | Tests | Phase 8 blocker |
|-----|------------------|-------------------------------------|----------------|-------------------|-------|-----------------|
| **B** | `backend/app/schemas/evidence_unit_candidate.py` + `backend/app/services/artifact_language_aggregation_service.py` | Same string keys for language / confidence defined in two places; parallel confidence handling (strict validation vs aggregation warnings). | Rename or typo in one module can silently desync aggregation from persisted EU metadata. | Single module for key constants imported by both; or re-export from schema; optional contract test asserting key equality. | Phase 7 language metadata / aggregation tests exist — **extend** if consolidating keys. | **No** |
| **B** | `frontend/src/components/*Explorer.tsx`, `EvaluationDashboard.tsx`, `QueryPlayground.tsx` (+ `RetrievalPacketPanel.tsx` for JSON display) | Identical or near-identical `formatError` (ApiError / Error / string) and `formatJson` (`JSON.stringify(..., null, 2)` + catch). | UI message and fallback JSON formatting can drift file-by-file. | Add `frontend/src/lib/uiFormatters.ts` (or export from a UI util) and replace locals when touching UI. | No dedicated UI unit tests noted — **optional** snapshot or component test later. | **No** |
| **B** | `scripts/load_phase6_demo.py` | API base URL resolution: `GRAPHCLERK_API_BASE_URL` and typo alias `GRAPHCLE_API_BASE_URL`; default `http://localhost:8000`. | Operators may hit wrong port vs frontend/vite defaults if docs are not read; legacy alias persists. | Document single canonical env in README/scripts header; long-term deprecate typo alias with warning. | N/A for script | **No** |
| **B** | `backend/tests/test_phase*.py` (many files) | Repeated `create_app()` + `ASGITransport` + `httpx.AsyncClient(..., base_url="http://test")`. | Future divergence (timeouts, headers) could hide in one file. | Optional shared pytest fixture for ASGI client; keep `db_ready` centralized (already in `conftest.py`). | Broad phase coverage — **no gap** identified from duplication alone. | **No** |
| **B** | `frontend/src/types/*.ts` vs backend schemas | Parallel type definitions for packet / log / evidence. | Normal for TS; risk is **contract drift** not duplicate runtime logic. | Regenerate or verify types when Phase 8 API changes; optional OpenAPI codegen later. | Backend tests enforce API behavior. | **No** |
| **C** | `backend/app/services/extraction/image_extractor.py`, `audio_extractor.py`, (+ pdf/pptx siblings) | Same “Phase 5 shell”: optional dep guard, `RawSourceStore`, type check, read bytes, validate, `ExtractorUnavailableError` placeholder. | Maintenance DRY opportunity only; behavior is intentionally parallel per modality. | Leave as-is unless a fourth sibling forces a tiny shared helper. | Per-modality extractor tests. | **No** |
| **C** | `backend/app/api/routes/*.py` | Similar pagination (`limit`/`offset`) and `HTTPException(detail=...)` mapping. | FastAPI boilerplate; low risk if limits stay consistent. | Extract shared dependency or helper only if routes proliferate. | Route tests per module. | **No** |
| **C** | Phase tests repeating ASGI recipe | Intentional clarity per phase file (readable contracts). | Can obscure a **future** one-line harness change. | Treat as **B** only if copy-paste causes real incidents; otherwise acceptable. | See **B** row for `ASGITransport`. | **No** |

**Checked with no Severity-A signal in this pass (summary):**

- **Actor context serialization:** concentrated in retrieval packet builder path; no second competing serializer found in static review.
- **Artifact type / modality mapping:** `ingestion/artifact_type_resolver.py` as central resolver; extractors delegate to types — no parallel “second resolver” identified.
- **Extraction placeholder behavior:** pdf/pptx/image/audio share the same *pattern* but different libraries/messages — intentional, not contradictory rules.
- **Retrieval packet assembly:** `retrieval_packet_builder.py` is the primary assembly seam; File Clerk composes file slices — ownership split is intentional (see **Positive findings**).
- **Raw source read/write:** `raw_source_store.py` as single store abstraction — no duplicate store implementation found.
- **Route selection vs semantic search:** distinct services (`route_selection_service` vs `semantic_index_search_*`) — overlap is **pipeline ordering**, not duplicate implementations.
- **Artifact language aggregation vs packet `language_context`:** different output contracts (aggregation block vs packet field) — **do not merge** without design review.

---

## Positive findings / do not refactor now

- **Multimodal extractors (PDF / PPTX / image / audio):** Structural symmetry is **intentional** (Phase 5 shells); different error types and validation steps are appropriate.
- **`frontend/src/api/client.ts`:** Centralizes `ApiError`, `parseBackendDetail`, and HTTP JSON helpers — a **clean seam**; duplication is UI-local only.
- **`db_ready` in `backend/tests/conftest.py`:** Single fixture owns DB lifecycle for integration tests — **reduces** drift vs per-file schema setup.
- **`RetrievalPacketBuilder` vs `FileClerkService`:** Builder orchestrates packet; File Clerk supplies file-linked evidence slices — **separate responsibilities**; merging would blur boundaries before Phase 8.
- **`ArtifactLanguageAggregationService` vs `RetrievalPacket.language_context`:** Aggregation summarizes artifacts; packet language context is a **different contract** for routing/display — overlap in *inputs* is expected; merging services without a spec would be risky.
- **Phase-organized tests:** Repetition of ASGI client setup can be **intentional** for readable phase contracts; optional fixture is a **later** hygiene win, not a correctness fix.

---

## Recommended next steps

**Choose one (this sweep recommends):** **Apply non-blocking cleanup after Phase 8 kickoff** (or in parallel small PRs).

Rationale: **zero Severity-A** items; Phase 8 is **not** blocked by code cleanliness alone. Address **B** items when touching those areas or in a dedicated “hygiene” PR after kickoff.

---

## Primary handoff summaries

Summaries below follow `docs/governance/AGENT_ROLES.md` → **Dedicated sub-agents** → **Handoff to primary / parent** (condensed from sub-agent runs).

### Project Manager Agent

**Mission recap:** Determine whether Sweep 3 (read-only duplication/seams inventory) blocks Phase 8.

**Plan files touched:** None by PM (read-only). Sequencing remains governed by phase doc + `docs/status/*` + pre–Phase 8 verification report.

**Drift / findings:** No contradictory dual-path business rules confirmed statically; explorer/helper duplication and test harness repetition are **maintainability**, not phase gates; `GRAPHCLE_*` vs `GRAPHCLERK_*` are documented compatibility concerns, not automatic blockers.

**Follow-ups:** **Yes**, optional backlog: shared frontend formatters; pytest ASGI fixture; policy on env alias deprecation.

**Recommended next actions:** Treat Sweep 3 as **non-blocking** for Phase 8 planning/kickoff; schedule remediation in parallel or post-kickoff as hygiene slices.

---

### Code Quality Agent

**Mission recap:** Assess duplication risks for (1) language keys schema vs aggregation, (2) image/audio extractor symmetry, (3) explorer TSX helpers; classify A/B/C.

**Scope touched:** `evidence_unit_candidate.py`, `artifact_language_aggregation_service.py`, `image_extractor.py`, `audio_extractor.py`, `frontend/src/api/client.ts`, multiple explorer components, spot-check `QueryPlayground.tsx`.

**Findings:** **(1) B** — duplicated string constants and overlapping confidence semantics; **(2) C** — deliberate symmetric shells; **(3) B** — repeated `formatError` / `formatJson`. **No A-grade** findings in this pass.

**Follow-ups:** **Yes** — consolidate language key constants; extract shared UI formatters; keep extractors as-is unless more siblings appear.

**Recommended next actions:** Import shared constants (or tiny `language_metadata` module); add `uiFormatters.ts`; optional test guarding key string parity if imports are awkward.

---

### Testing Agent

**Mission recap:** Read-only review of `ASGITransport` + `db_ready` duplication and drift risk across phase tests.

**Scope touched:** `backend/tests/conftest.py`, `test_phase*.py`, `test_health.py`, `test_version.py`, AsyncClient patterns.

**Findings:** `db_ready` is **centralized** (low DB drift). HTTP tests repeat the same ASGI client recipe (**B**); wiring is **consistent today** (`base_url="http://test"`). **C** caveat: future copy-paste could diverge; HTTP vs service/repo tests can miss full-stack drift if boundaries change.

**Follow-ups:** **Yes** — optional shared fixture for `create_app` + ASGI client; when changing middleware/deps, update both HTTP and service-level tests consciously.

**Recommended next actions:** Introduce small pytest fixture or helper for ASGI client; no test edits required for this sweep.

---

### Git Agent

**Mission recap:** Hygiene for version control around Sweep 3 deliverable.

**Plan files touched:** Expected single new file: `docs/reports/pre_phase_8_code_cleanliness_sweep.md`.

**Drift / findings:** Working tree was clean before report; after adding report, user should **review diff** before any commit.

**Follow-ups:** **Yes** — user may later commit with an accurate message; do **not** auto-commit.

**Recommended next actions:** After review: `git add docs/reports/pre_phase_8_code_cleanliness_sweep.md` and commit when explicitly requested. **Suggested one-line commit message:** `docs: add pre-phase-8 code cleanliness sweep report`.

---

## Appendix: Sub-agent delegation note

Dedicated GraphClerk sub-agents (**Project Manager**, **Code Quality**, **Testing**, **Git**) were invoked for this sweep; summaries above reflect their **Primary handoff** sections. No code or test files were modified by sub-agents.

---

## Tests

**Tests not run** (read-only sweep + report authoring only).
