# Phase 0–8 Completion Hardening Plan

## Metadata

| Field | Value |
|-------|--------|
| **Date** | 2026-05-04 |
| **Current commit** | `ce01ecd` — `docs: reconcile phase 8 plan after audit` |
| **Git status** | Working tree: **untracked** `docs/reports/pre_phase_9_repo_readiness_inventory.md` (from prior inventory); **this report** added as second untracked file until committed by maintainers. |
| **Scope** | Read-only synthesis from `docs/reports/pre_phase_9_repo_readiness_inventory.md`, `docs/status/*`, audits **5–8**, `README.md`, `docs/demo/PHASE_6_DEMO_CORPUS.md`, `scripts/load_phase6_demo.py`, `backend/app/services/file_clerk_service.py` + route/search wiring, `frontend/src/**` (types/playground/panel). **No** code, status, phase doc, audit, or plan edits in this task. |
| **Files modified** | **One new file:** this plan (`docs/reports/phase_0_8_completion_hardening_plan.md`). |

---

## Executive summary

| Question | Answer |
|----------|--------|
| **Can Phases 0–8 be exercised end-to-end *today*?** | **Yes for the control plane:** ingest → EU → graph (nodes/edges/node-evidence) → create SI row → **`POST /retrieve`** → **`RetrievalLog`** snapshot → UI tabs — **all callable** with Docker + API + UI + demo loader. **Caveat:** with the **stock** demo loader, semantic indexes are **`vector_status=pending`**; FileClerk route selection uses **vector search over `indexed` indexes only**, so **`POST /retrieve` often returns packets with zero evidence** while still returning a **valid** `RetrievalPacket`, warnings, and logs. That is **coherent and honest**, not broken — but it is **not** the same as “demo always shows ranked evidence snippets.” |
| **What blocks a *rich* evidence-filled demo without extra steps?** | **Indexed vectors** (or a separate, not-yet-built non-semantic traversal entry) are required for the **current** FileClerk design to attach traversal to the demo semantic index. |
| **Recommended completion slices before Phase 9** | **C0** (commit docs reports) · **C1** (frontend packet/request typings + readable Phase **7** fields) · **C3** (hardened demo checklist + optional loader follow-up or “index demo SI” dev recipe) · optional **C4** (gated backend E2E). **C5** is a **product decision**: document **non-blocking** path vs add **dev-only** indexing hook. **C6** release checklist cross-links. |
| **What remains explicitly deferred** | OCR/ASR/video, production inference (**Phase 8** merge), **`/answer`**, production language detector, **7I** boosting, full frontend test harness, north-star Phase **8** registry — see **Explicitly deferred** section. |

---

## End-to-end baseline definition

**Minimal coherent baseline (must hold):**

1. **Ingest** text artifact (`POST /artifacts` text/Markdown path).
2. **Evidence units** created and listable (`GET …/evidence`).
3. **Graph** nodes + edge + **node–evidence support link** (public graph APIs).
4. **Semantic index** row created (may stay `vector_status=pending`).
5. **`POST /retrieve`** returns a **schema-valid** `RetrievalPacket` + honest warnings (may include `no_semantic_index_match` / empty evidence).
6. **`RetrievalLog`** stores packet snapshot where logging succeeds; **`GET /retrieval-logs`** visible in UI.
7. **UI** can inspect playground + logs + raw packet JSON.
8. **No** **`POST /answer`** / answer synthesis on the path.

**Richer baseline (optional “demo wow” tier, not required for Phase 0–8 honesty):**

- Same as above **plus** at least one `SemanticIndex` with **`vector_status=indexed`** (dev backfill / Qdrant upsert / integration test harness) so `RouteSelectionService` yields entry nodes → traversal → **non-empty** `evidence_units` when the question matches.

---

## Completion blockers

**Severity A — must fix before calling the minimal baseline “broken”**

| Sev | Area | Finding | Why it would block E2E | Recommended slice | Likely allowed files (when implemented) |
|-----|------|---------|-------------------------|-------------------|------------------------------------------|
| *(none identified)* | — | Core APIs and UI exist; demo loader completes HTTP chain | — | — | — |

**Interpretation:** The repo is **not** structurally broken for a **minimal** E2E; the main “gap” is **expectation management** between *valid empty packets* vs *indexed semantic demo*.

---

## Should-fix before Phase 9

**Severity B — should fix for operator clarity / Phase 9 IDE consumers**

| Area | Finding | Why it matters | Recommended slice |
|------|---------|----------------|-------------------|
| Frontend types | `frontend/src/types/retrievalPacket.ts` omits **`language_context`**, **`actor_context`**, optional request fields | TypeScript consumers and future IDE tools lose compile-time truth; raw JSON is the only typed-safe view today | **C1** |
| Query playground | No structured **`actor_context`** / advanced retrieve fields | Cannot exercise Phase **7** request recording without hand-built JSON elsewhere | **C1** (optional JSON editor or collapsible “Advanced”) |
| Demo narrative | Loader + README already warn; easy to **misread** “demo loaded” as “retrieve shows evidence” | Support churn; false bug reports | **C3** — single **“Demo E2E expectations”** checklist (README + `PHASE_6_DEMO_CORPUS`) |
| Historical audits | `PHASE_7_AUDIT` preamble still mentions Phase **8** not started | Onboarding confusion | Small **docs-only** note (separate slice; **not** this file) |
| Release checklist | May not list **minimal vs rich** demo verification | Release managers may skip honest empty-packet case | **C6** |

---

## Optional polish

**Severity C**

| Area | Finding | Note |
|------|---------|------|
| `main.py` docstring | Lags Phases **6–8** | Comment-only refresh |
| README phase doc index | Phase **8** doc link optional in governance list | Cosmetic |
| Evaluation UI copy | Reinforce observability ≠ answer quality | Copy tweak |

---

## Explicitly deferred, not blocking

| Item | Class **D** rationale |
|------|----------------------|
| OCR / ASR / caption / video multimodal completion | Phase **5** north-star |
| Production model inference / Ollama/vLLM | Phase **8** design-only |
| **`POST /answer`** | Explicitly deferred product-wide |
| Production language detector-by-default | Phase **7** notes |
| Actor / language **boosting** (**7I**) | Cancelled/deferred |
| **Phase 8** merge of projection into ingestion/enrichment | Product slice, not Phase **9** prerequisite |
| Full Vitest/Playwright harness | Phase **6** stretch |
| Automatic vector backfill on SI create | Phase **3/4** debt |

---

## Recommended slice plan

| Slice | Goal | When needed |
|-------|------|-------------|
| **C0** | Commit `docs/reports/pre_phase_9_repo_readiness_inventory.md` + this plan (docs hygiene) | Immediately before sharing externally |
| **C1** | Align `RetrievalPacket` / `RetrieveRequestPayload` TS types with `app/schemas/retrieval_packet.py` + `retrieval.py`; add readable **language_context** / **actor_context** sections (or documented “expand raw JSON”) | Before Phase **9** IDE work consuming packets |
| **C2** | **`graphclerk_model_pipeline`** UI | **Defer** until metadata exists on real rows (post-merge). Optional: ensure **Artifacts/EU** JSON viewers surface `metadata_json` (likely already via raw views) — verify in **C1** scope |
| **C3** | **Manual demo checklist** + tighten `PHASE_6_DEMO_CORPUS` / README: steps = loader → **manual** `POST /retrieve` question → inspect packet + logs → explain empty evidence if `pending` | Always — low cost |
| **C4** | **Gated** `RUN_INTEGRATION_TESTS=1` E2E: ingest → graph link → retrieve → assert log row (assert **warnings** or **non-empty** evidence depending on env) | If CI wants proof |
| **C5** | **Decision doc**: (a) accept **minimal E2E** without Qdrant evidence, **or** (b) document **dev-only** steps to index demo SI (compose + embedding + upsert), **or** (c) schedule future product change for non-semantic bootstrap | PM + platform owner |
| **C6** | `docs/release/RELEASE_CHECKLIST.md` — add **two-tier** demo verification | Before next tagged release |

**Only C0–C3 + C6 are broadly “actually needed”** for coherence; **C4–C5** depend on CI/release appetite.

---

## Dedicated model fit before Phase 9

**Default recommendation:** keep **Phase 8** model pipeline **standalone** (library + tests only). **Do not** wire production inference or automatic merge into ingestion before Phase **9** scope is written.

- **Projection (`graphclerk_model_pipeline`)** may appear in UI **only** if operators manually inject JSON into `metadata_json` during experiments, or after a **separately approved** enrichment merge slice.
- **Tests** remain the primary consumer of **`DeterministicTestModelPipelineAdapter`**.
- **NotConfigured** remains the honest default for any future adapter registry.

---

## UI readiness before Phase 9

| Update | Priority | Detail |
|--------|----------|--------|
| Extend **`retrievalPacket.ts`** | **B** | Optional `language_context`, `actor_context`; align `RetrieveRequestPayload` with backend |
| **Query playground** advanced request | **B** | Optional `actor_context` JSON or form fields |
| **RetrievalPacketPanel** readable sections | **B** | Summarize context blocks (not evidence) with explicit labels |
| **Phase 8** pipeline tab | **D** | Wait for wired metadata |
| **Frontend tests** | **D** | Phase **6** debt; not gating Phase **9** planning |
| **Honest copy** on Evaluation tab | **C** | Reinforce metrics scope per `EVALUATION_METHOD.md` |

---

## Test plan

| Layer | Command / action |
|-------|------------------|
| Backend default | `cd backend && python -m pytest -q` |
| Phase **4** retrieve | `pytest tests/test_phase4_retrieve_api.py -q` (subset example) |
| Integration (optional) | `RUN_INTEGRATION_TESTS=1` + DB/Qdrant env per `TESTING_RULES.md` |
| Manual UI | Docker Compose → UI → loader (`docs/demo/PHASE_6_DEMO_CORPUS.md`) → playground question → logs tab |
| Demo loader | `python scripts/load_phase6_demo.py --dry-run` then run with `GRAPHCLERK_API_BASE_URL` |

**Manual demo checklist (draft for C3):**

1. `docker compose up -d --build` — API on **8010** (per README).  
2. `python scripts/load_phase6_demo.py` with correct **`GRAPHCLERK_API_BASE_URL`**.  
3. Open UI → **Artifacts** — confirm new artifact.  
4. **Graph** — confirm demo nodes/edge.  
5. **Semantic indexes** — confirm row; note **`vector_status`**.  
6. **Query playground** — submit question; expect **packet** + warnings; **evidence may be empty** if not indexed.  
7. **Retrieval logs** — confirm log row / packet snapshot.  
8. Confirm **no** `/answer` route.

---

## Recommended decision

**Phase 9 planning can start in parallel** with **C1 + C3 + C6** hardening slices — implementation of Phase **9** should still wait on charter/allowlist.

If the org requires **evidence-rich** demos for every stakeholder, schedule **C5(b)** (dev indexing recipe) **before** external Phase **9** demos — still not a code-architecture blocker for Phase **9** design work.

---

## Primary handoff summaries

### Project Manager Agent

1. **Mission recap:** Defined **two-tier** E2E (minimal vs rich) and a slice backlog **C0–C6**.  
2. **Scope touched:** This report only.  
3. **Drift / findings:** **No Severity A** engineering blockers; **expectation** risk on demo vs Qdrant.  
4. **Follow-ups:** **Y** — choose **C5** policy and schedule **C1/C3**.  
5. **Recommended next actions:** Approve **C0** commit of reports; open Phase **9** planning doc.

### Status Documentation Agent

1. **Mission recap:** No `docs/status/*` edits in this task.  
2. **Scope touched:** N/A.  
3. **Drift / findings:** Existing status already distinguishes partial Phase **5** and Phase **8** baseline.  
4. **Follow-ups:** **N** mandatory from this deliverable.  
5. **Recommended next actions:** After **C3**, optional one-line pointer in `PROJECT_STATUS` “Demo expectations” — separate approved slice.

### Audit Agent

1. **Mission recap:** Confirmed **no `/answer`**, **no** hidden inference in traced paths; demo honest about vectors.  
2. **Scope touched:** Read-only cross-check FileClerk + demo docs.  
3. **Drift / findings:** **Empty evidence** after loader is **documented**, not a defect.  
4. **Follow-ups:** **Y** — archive note on **PHASE_7** audit cross-phase text (low priority).  
5. **Recommended next actions:** Keep audits append-only; prefer **PHASE_STATUS** for “now.”

### Code Quality Agent (read-only)

1. **Mission recap:** FileClerk pipeline remains semantic-search-first → traversal.  
2. **Scope touched:** N/A edits.  
3. **Drift / findings:** Alternative traversal seeds would be **product change**, not hardening polish.  
4. **Follow-ups:** **N**.  
5. **Recommended next actions:** If **C5(c)** ever ships, treat as new phase slice with invariants review.

### Testing Agent

1. **Mission recap:** Proposed **C4** gated E2E; default suite unchanged.  
2. **Scope touched:** N/A execution this task.  
3. **Drift / findings:** **Tests not run** for report-only task.  
4. **Follow-ups:** **Y** when **C4** implemented.  
5. **Recommended next actions:** `pytest -q` after any new E2E test.

### Git Agent

1. **Mission recap:** **No** stage/commit per charter.  
2. **Scope touched:** Untracked report file pending user.  
3. **Drift / findings:** `git status` will list `docs/reports/*.md` until committed.  
4. **Follow-ups:** **Y** — user runs `git add docs/reports/…` when ready.  
5. **Recommended next actions:** Optional **C0** commit bundling inventory + this plan.

---

## Answers to charter questions (quick index)

1. **Minimal E2E demo:** Docker + API + **Phase 6** loader + graph wiring + **manual** retrieve + logs + UI (see checklist).  
2. **Can remain `pass_with_notes`:** Phases **3–8** partial items listed in **Deferred** — do not block minimal E2E honesty.  
3. **Frontend/UI updates:** **C1** typings + readable Phase **7** fields; **C2** deferred until **`graphclerk_model_pipeline`** exists on data.  
4. **Backend/API gaps:** None for *minimal* path; **rich** path needs indexing story (**C5**).  
5. **Vector indexing:** **Not** required for *minimal* coherent demo; **required** for semantic-routed evidence from demo SI.  
6. **Demo loader data sufficiency:** Creates artifact/EU/graph/SI; **does not** index vectors — see **5**.  
7. **Clean path:** Loader covers **1–4**; operator covers **5–7** manually; **8** satisfied by absence of `/answer`.  
8. **Tests:** Default pytest + optional **C4** integration chain.  
9. **Manual checklist:** **C3** deliverable (section above).  
10. **Blockers vs polish:** **A=0** blockers for minimal path; **B** items for clarity; **C** polish; **D** north-star.
