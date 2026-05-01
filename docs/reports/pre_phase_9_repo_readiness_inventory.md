# Pre-Phase-9 Repository Readiness Inventory

## Metadata

| Field | Value |
|-------|--------|
| **Date** | 2026-05-04 |
| **Current git commit** | `ce01ecd` — `docs: reconcile phase 8 plan after audit` |
| **Baseline git status** | Clean working tree (`git status --short` empty at inventory time). |
| **Scope** | Read-only review of `backend/app/**`, `backend/tests/**`, `frontend/src/**`, `scripts/**`, `docs/**` (excluding forbidden edits), `.cursor/plans/**`, `.cursor/rules/**` (read-only). |
| **Files modified by this task** | **One file created:** this report (`docs/reports/pre_phase_9_repo_readiness_inventory.md`). No code, status, phase docs, audits, or plans were edited. |
| **Tests run** | **None** (inventory/report-only per charter). |

---

## Executive summary

| Question | Answer |
|----------|--------|
| **Is Phase 9 kickoff blocked by this inventory?** | **No.** No Severity **A** issues identified that require fixes before **opening Phase 9 planning**. Implementation of Phase 9 remains **`not_started`** until explicitly approved. |
| **Severity counts** | **A:** 0 · **B:** 4 · **C:** 5 |
| **Biggest readiness risks** | (1) **UI / TypeScript** drift: Phase 7 packet fields exist on the wire but are **not** modeled in `frontend/src/types/retrievalPacket.ts`, weakening typed inspection and future Phase 9 IDE tooling. (2) **Stale audit narrative**: `docs/audits/PHASE_7_AUDIT.md` still states Phase **8** was **not started** — superseded by **`PHASE_8_AUDIT.md`**; readers must prefer **`docs/status/*`** + latest audits. (3) **Concept drift risk**: `AnswerMode` / intent names in UI types resemble answer semantics; docs/README correctly defer **`POST /answer`** — keep UI copy aligned. |
| **Recommended next action** | **Open Phase 9 planning now** (documentation/working-plan slice), optionally parallel **small UI readiness** (extend packet types + optional playground fields for `actor_context`) as **non-blocking** polish. |

---

## Implementation inventory

Legend: **A** finished baseline · **B** `pass_with_notes` baseline · **C** intentional placeholder/shell · **D** draft/incomplete · **E** spec/design-only · **F** potential orphan/dead

| Area | Paths | Class | Evidence | Risk | Recommended action |
|------|-------|-------|----------|------|---------------------|
| Governance / docs | `docs/governance/*`, phase docs, audits | **A/B** | Rules + audits exist; phase docs separate baseline vs north-star where maintained | Low | Keep phase docs honest when Phase 9 scopes land |
| Phase 2 text ingestion | `text_ingestion_service.py`, `artifacts.py`, parsers | **A** | `test_phase2_*`, implemented | Low | Maintain on multimodal touch |
| Phase 5 multimodal | `multimodal_ingestion_service.py`, `extraction/*`, `artifact_type_resolver.py` | **B** | Partial PDF/PPTX EUs; image/audio **503** shells; `test_phase5_*` | Medium | Do not market as OCR/ASR complete |
| Phase 3 graph | `graph_*` routes/services, models | **B** | Audited `pass_with_notes`; tests | Low | Traversal/index population gaps documented |
| Semantic index + vectors | `semantic_index_*`, `vector_index_service.py`, `embedding_*` | **B/C** | **NotConfigured** / fake embedding path; Qdrant integration gated | Medium | Production embedding still debt |
| Phase 4 File Clerk | `file_clerk_service.py`, `retrieve.py`, `retrieval_packet_builder.py`, selection/route services | **B** | Packet contracts tested; no `/answer` | Medium | Keep retrieval deterministic/explicit |
| Retrieval logs | `retrieval_logs.py`, `retrieval_log_repository.py` | **B** | Read APIs + tests | Low | OK |
| Phase 7 context | `evidence_enrichment_service.py`, `language_detection_service.py`, `artifact_language_aggregation_service.py`, schemas | **B/C** | Enrichment **no-op** default; **NotConfigured** language detection; aggregation pure; tests | Medium | Boosting **7I** deferred; UI surfaces thin |
| Phase 8 model pipeline | `model_pipeline_contracts.py`, `model_pipeline_output_validation_service.py`, `model_pipeline_candidate_projection_service.py` | **B** | **Not** wired in `main.py`; **`PHASE_8_AUDIT`** `pass_with_notes` | Low | Any adapter slice: validation → projection order |
| App wiring / CORS | `main.py`, `core/config.py` | **B** | Routers registered; CORS env documented | Low | `main.py` docstring lags Phases **7–8** (comment drift only) |
| Evidence / artifact schemas | `schemas/*`, `repositories/*`, `models/*` | **B** | Broad test coverage | Low | Schema changes need migration discipline |
| Frontend shell | `App.tsx`, `main.tsx` | **B** | Phase **6** baseline; no Vitest | Medium | Add tests when Phase 9 stabilizes API usage |
| Query playground | `QueryPlayground.tsx`, `api/retrieval.ts` | **B/C** | Live `POST /retrieve`; **no** `actor_context` request UI | Medium | Extend types + optional **Phase 7** request fields |
| Packet panel | `RetrievalPacketPanel.tsx` | **B/C** | Readable trace + **full JSON** (`JSON.stringify(packet)`) — Phase **7** fields visible in raw JSON if returned | Low | Align TS type with backend for IDE Phase **9** |
| Other explorers | `ArtifactsExplorer`, `SemanticIndexesExplorer`, `GraphExplorer`, `RetrievalLogsExplorer`, `EvaluationDashboard` | **B** | Live APIs; evaluation observability-only per docs | Medium | Avoid implying answer-quality metrics |
| API client | `api/client.ts`, `api/*.ts` | **B** | Shared error handling | Low | OK |
| Scripts | `scripts/load_phase6_demo.py` | **C** | Script-only demo loader (documented) | Low | Keep honest port/env notes |
| Phase 8 fixtures | `tests/fixtures/phase8_model_pipeline_cases.py` | **A** (test infra) | Deterministic; **no** adapter execution | Low | Reuse for future adapter mocks |

---

## Phase completion matrix

| Phase | Current status (status docs) | Audit result | Implemented baseline | Placeholders / shells | Deferred / remaining work | Blocks Phase 9? | Notes |
|-------|------------------------------|--------------|----------------------|------------------------|---------------------------|-----------------|-------|
| **0** | Implemented | (baseline narrative) | Governance docs | — | Ongoing maintenance | **No** | Living docs |
| **1** | Implemented | `pass_with_notes` (historic) | Docker, DB, models, `/health` `/version` | — | CI migration chain etc. | **No** | See `TECHNICAL_DEBT` |
| **2** | Implemented | `pass_with_notes` | Text/Markdown ingestion, EUs | — | Edge cases | **No** | |
| **3** | Implemented | **`pass_with_notes`** | Graph + semantic index APIs, traversal, Qdrant path | Embedding **NotConfigured** default | Auto vector backfill, prod embedding | **No** | Honest partials |
| **4** | Implemented | **`pass_with_notes`** | `POST /retrieve`, FileClerk, packets, logging column | — | Heuristic intent | **No** | **`/answer`** N/A |
| **5** | **In progress / partial** | **`pass_with_notes`** | PDF/PPTX extractors → EU | Image/audio validation **503** | OCR/ASR/video | **No** | Do not overclaim multimodal |
| **6** | Implemented baseline | **`pass_with_notes`** | Full UI tabs, live APIs | No E2E harness | Demo loader in-app, polish | **No** | Inspection product |
| **7** | Baseline implemented | **`pass_with_notes`** | Metadata recording, enrichment no-op, detection shell | **NotConfigured** detector | **7I** boosting, translation, detector policy | **No** | Context ≠ evidence |
| **8** | Baseline implemented | **`pass_with_notes`** (`2026-05-03`) | Contracts, validation, projection, fixtures | **NotConfigured** pipeline adapter | HTTP adapter, registry, merge to enrichment | **No** | Model output ≠ evidence |
| **9** | **`not_started`** | **N/A** | — | Spec under `docs/phases/` | Entire phase | **No** (planning can start) | No implementation claimed |

---

## Doc/code alignment findings

| Sev | File | Section | Claim | Actual truth | Recommended correction |
|-----|------|---------|-------|--------------|------------------------|
| **B** | `docs/audits/PHASE_7_AUDIT.md` | Executive / scope | Phase **8** “not started” / out of scope | Phase **8** baseline **is** implemented and audited (`PHASE_8_AUDIT.md`) | Add archival note or supersede line in a future docs-only pass (do not rewrite audit verdict) |
| **B** | `frontend/src/types/retrievalPacket.ts` | `RetrievalPacket`, `RetrieveRequestPayload` | Implies packet is Phase **4**-only shape | Backend adds **`language_context`**, **`actor_context`** (Phase **7**) — fields appear at runtime / in raw JSON panel | Extend interfaces (optional fields) to match `app/schemas/retrieval_packet.py` + `retrieval.py` |
| **B** | `frontend/src/components/QueryPlayground.tsx` | Request payload | No **`actor_context`** UI | Backend accepts optional **`actor_context`** on retrieve | Optional advanced JSON / fields when Phase **9** needs operator clarity |
| **B** | `docs/status/PROJECT_STATUS.md` | Summary “**Current phase**” | Leads with Phase **7** | Phase **8** baseline also shipped (listed later in same paragraph) | Optional wording: “latest audited slices” — cosmetic |
| **C** | `backend/app/main.py` | `create_app` docstring | Mentions Phase **0–5**, Phase **4** retrieve | Phase **6** logs, Phase **7–8** code exists but not summarized here | Comment-only refresh when convenient |
| **C** | `README.md` | Governance bullet list | Lists phases **1–7** files | Omits **`graph_clerk_phase_8_*`** link | Add Phase **8** (and optional Phase **9** spec) to bullet list |
| **C** | `frontend/src/types/retrievalPacket.ts` | Header comment | “Phase 4 File Clerk” only | Phase **7** extensions shipped | Update comment |
| **C** | Historical audits | Cross-phase preamble | Older audits snapshot dependencies | Status docs are **current** source of truth for dependencies | PM: cite **`PHASE_STATUS`** first |

**Checks against required questions**

1. README overclaim? **No** multimodal/OCR/Phase **9**/`/answer`/production inference — aligned with code.  
2. Status vs audits? **Aligned** for Phase **5–8** primary paths.  
3. Gaps vs placeholders? **Aligned** (503 shells, **NotConfigured**).  
4. TECHNICAL_DEBT vs reality? **Aligned** — `TECHNICAL_DEBT.md` Phase **8** section reflects audit **`pass_with_notes`** and lists remaining integration/UI/registry debt.  
5. Phase docs baseline vs north-star? Phase **8** doc has **Implementation status**; large Phase **8** doc remains aspirational — OK if readers heed intro.  
6. Doc says feature exists while code is placeholder? **No critical mismatch** on inference (none shipped).  
7. Code undocumented? Phase **8** pipeline **not** in API — intentional; document when wired.  
8. Status “pending” after **`pass_with_notes`**? **No** stale Phase **8** audit-pending in `PROJECT_STATUS` / `PHASE_STATUS` (verified via grep).  
9. Phase **9** started? **No** in README/status.  
10. **`/answer`** exists? **No** route in `main.py` wiring; README defers.

---

## Core concept alignment

### Aligned areas

- **Evidence-first routing:** File Clerk + **`POST /retrieve`** return structured **`RetrievalPacket`** (backend + UI grounded on live JSON).
- **No answer synthesis:** No **`/answer`** router; README and status explicit.
- **Source traceability:** Evidence units carry modality, fidelity, selection reasons in packet assembly paths (tested).
- **Explicit failures:** Multimodal **503** for unsupported producer paths; **NotConfigured** patterns for optional adapters (embedding, language detection, model pipeline).
- **Model output ≠ evidence:** Phase **8** validates + projects metadata only; no EU/text/fidelity mutation in pipeline modules (audit-backed).
- **Context ≠ evidence:** Phase **7** recording semantics documented and tested for non-boosting baseline.

### Weak spots / drift risks

- **UI vocabulary:** `AnswerMode` and intent types can **sound** like an answer product — mitigated by README/playground copy but worth guarding in Phase **9** UX.
- **Typed frontend lag:** Weaker guarantees for Phase **7** packet fields — risk for IDE/evidence orchestration consumers.
- **Stale audit cross-references:** Older audit PDFs/text imply outdated dependency phase states — training/onboarding risk.

### Recommended guardrails before Phase 9

- Treat **`docs/status/PHASE_STATUS.md`** + latest **`PHASE_*_AUDIT`** as canonical for “what shipped.”
- Any Phase **9** API/tooling must preserve **packets-first**, **no silent inference**, **no retrieval mutation** unless separately approved.
- Extend **frontend types** when exposing packet subsets to external tools.

---

## Dedicated model fit

Uses Phase **8** contracts (`ModelPipelineRole`, `ModelOutputKind`) and audit discipline.

| # | Answer |
|---|--------|
| **1. Clean fit** | **Post-ingestion, pre-ranking assistance** as **typed proposals**: bounded **`candidate_metadata`** / **`derived_metadata`** merged only via explicit future enrichment slice — **not** inside FileClerk ranking loop today. |
| **2. Roles first** | **`extraction_helper`** + **`candidate_metadata`** (labels/hints) or **`artifact_classifier`** + **`validation_signal`** — narrow, inspectable JSON. |
| **3. Dangerous / premature** | **`routing_hint_generator`** if hints touch **`route_selection_service`** without governance; anything implying **`verbatim`** / **`is_evidence`** / prose **`answer`** fields (blocked by **8D**). |
| **4–6. First real adapter** | Safest: **`extraction_helper`** + **`candidate_metadata`** with strict validation + optional projection attach — **does not** replace ingest parsers. Defer ranking-changing **`routing_hint`** until evaluation harness exists. |
| **7. Allowed output** | Structured dicts under **`ModelPipelineResult.payload`** matching **`output_kind`**; **`derived_metadata`** allows bounded **`summary`** when validated. |
| **8. Rejected output** | Nested **`is_evidence: true`**, **`source_fidelity: verbatim`**, **`source_truth`**, prose-shaped keys on restricted kinds — **8D** errors. |
| **9. Validation** | Always **`ModelPipelineOutputValidationService.validate_response`** before projection (adapter orchestration responsibility per **`PHASE_8`** design). |
| **10. Projection** | **`ModelPipelineCandidateMetadataProjectionService.project`** only when **`validation.ok`** — metadata subtree **`graphclerk_model_pipeline`**. |
| **11. Must not wire yet** | FileClerk ranking, **`retrieval_packet_builder`** semantic boosting, **`text_ingestion_service`** body substitution, default-on HTTP adapters. |
| **12. UI for operators** | Pipeline run id, **`validation.issues`**, **`proposed`** vs merged metadata — none exists today; Phase **6** raw JSON insufficient for long-term. |

---

## UI update assessment

### Current coverage

- Tabs for playground, artifacts, semantic indexes, graph, logs, evaluation — all **live** APIs.
- **Phase 7** packet fields: visible via **raw JSON** stringify path in **`RetrievalPacketPanel`** if backend returns them; **readable** section omits dedicated context panels.

### Missing surfaces

- Typed **`language_context` / `actor_context`** in TS + optional readable sections (**B**).
- **Phase 8** pipeline visibility (**none**) — expected until wired.
- Frontend automated tests (**absent**).

### Classification

| Priority | Items |
|----------|--------|
| **A. Must do before Phase 9** | **None** identified for *planning* kickoff. |
| **B. Should do soon** | Align **`retrievalPacket.ts`** with backend; optional **`actor_context`** input in playground for demos. |
| **C. Optional later** | Dedicated “Pipeline inspection” tab once projection merge exists; Vitest/Playwright. |

### Recommended first UI slice (if any)

**Small:** extend **`RetrievalPacket`** / request types + document in UI that context fields are **metadata not evidence** — supports Phase **9** IDE packet inspection without claiming new product features.

---

## Blocking items before Phase 9

**None (Severity A).**

---

## Non-blocking follow-ups

- **B:** Refresh **`PHASE_7_AUDIT`** cross-phase preamble (docs-only) or add README pointer “historical snapshot.”  
- **B:** Frontend packet/request types vs Phase **7** backend schemas.  
- **B:** Optional **`actor_context`** in playground.  
- **C:** `main.py` docstring scope refresh; README phase doc index line; TS file header comments.

---

## Recommended next steps

**Choose one:** → **Open Phase 9 planning now** (working plan + scoped allowlists). Severity **A** is empty; **B** items can proceed in parallel as small chores.

Alternatives if product priorities differ:

- Fix **B** findings first (types + stale audit note).  
- Small **UI readiness** slice (packet typings).  
- Small **model-pipeline visibility** slice **after** backend wiring — **not** recommended before Phase **9** scope is fixed.

---

## Primary handoff summaries

### Project Manager Agent

1. **Mission recap:** Pre–Phase **9** readiness inventory complete; **no** blockers for planning.  
2. **Scope touched:** This report only.  
3. **Drift / findings:** **4×B**, **5×C** documentation/typing hygiene items; phases **5–8** audits coherent in **`docs/status/*`**.  
4. **Follow-ups:** **Y** — kick off Phase **9** planning task when approved.  
5. **Recommended next actions:** Charter Phase **9** slices; optionally schedule UI type alignment.

### Status Documentation Agent

1. **Mission recap:** Verified README/`PROJECT_STATUS`/`PHASE_STATUS`/`ROADMAP` consistency with **`PHASE_8`** audit (read-only).  
2. **Scope touched:** None modified.  
3. **Drift / findings:** **`PROJECT_STATUS` “current phase”** phrasing is Phase **7**-first — acceptable; optional polish only.  
4. **Follow-ups:** **N** mandatory.  
5. **Recommended next actions:** After Phase **9** scope fix, update status in same delivery.

### Audit Agent

1. **Mission recap:** Confirmed **`pass_with_notes`** baselines **5–8**; **no** `/answer`/inference/product Phase **9** claims in primary status paths.  
2. **Scope touched:** Read audits **5–8** + grep spot checks.  
3. **Drift / findings:** **`PHASE_7_AUDIT`** executive mentions Phase **8** **not started** — superseded.  
4. **Follow-ups:** **Y** — archival note on old audits (low priority).  
5. **Recommended next actions:** Phase **9** audit schedule when implementation lands.

### Code Quality Agent (read-only)

1. **Mission recap:** Pipeline modules remain free of FileClerk/retrieval imports (grep).  
2. **Scope touched:** N/A edits.  
3. **Drift / findings:** **`main.py`** comment drift only.  
4. **Follow-ups:** **N**.  
5. **Recommended next actions:** Keep Phase **8** services side-effect free.

### Testing Agent

1. **Mission recap:** **No tests executed** for this inventory per instructions.  
2. **Scope touched:** N/A.  
3. **Drift / findings:** Prior Phase **8** audits recorded pytest green; re-run before Phase **9** code.  
4. **Follow-ups:** **Y** when Phase **9** ships code.  
5. **Recommended next actions:** `cd backend && python -m pytest -q` on next backend change.

### Git Agent

1. **Mission recap:** **No commit/stage** per user — report file created locally only.  
2. **Scope touched:** User to review `docs/reports/pre_phase_9_repo_readiness_inventory.md`.  
3. **Drift / findings:** Expect **untracked** report until user commits.  
4. **Follow-ups:** **Y** — user may `git add` + commit when ready.  
5. **Recommended next actions:** `git status --short` after review.
