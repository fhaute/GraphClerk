# Phase 1–8 Full Completion Program

| Field | Value |
|-------|--------|
| **Document type** | Active planning program (not an audit; not a phase spec) |
| **Audience** | Maintainers, implementers, Audit / Status / PM sub-agents |
| **Phase 9** | **Not started** — this program is explicitly **pre–Phase 9** |
| **Relationship to audits** | Prior `pass_with_notes` audits remain **correct and authoritative** for what they accepted (**baseline**). This document targets **full intended product completion** for Phases **1–8** and does **not** erase, supersede, or imply that those audits were wrong. |

**Delegated work (Cursor Task, etc.):** Any **Dedicated sub-agent** must end its final message with a **Primary handoff** per [`docs/governance/AGENT_ROLES.md`](../governance/AGENT_ROLES.md) → *Dedicated sub-agents* → *Handoff to primary / parent* (mission recap, scope touched, drift/findings, follow-ups Y/N, recommended next actions).

---

## 1. Executive summary

GraphClerk has **audited baselines** for many phases (**`pass_with_notes`** in historical artifacts) that **correctly accepted** partial or contract-only delivery at audit time. That is **not** the same as **this program’s “full intended product completion”** for every phase, **nor** the same as **agreed-scope closure** where a later **full-completion** audit exists.

**Completion Program progress (current):** **Track C** (Phase **7**) and **Track D** (Phase **8**) are **complete** for their **agreed Phase 1–8 completion scopes**, with **`pass`** full-completion audits — [`PHASE_7_FULL_COMPLETION_AUDIT.md`](../audits/PHASE_7_FULL_COMPLETION_AUDIT.md) and [`PHASE_8_FULL_COMPLETION_AUDIT.md`](../audits/PHASE_8_FULL_COMPLETION_AUDIT.md). Baseline history remains in [`PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md) and [`PHASE_8_AUDIT.md`](../audits/PHASE_8_AUDIT.md) (**`pass_with_notes`**).

**The program is not globally closed:** **Phase 5** multimodal (**Track A**) remains the **largest implementation gap** versus long-form multimodal intent (OCR/ASR/image-audio EUs, etc.). **Track H** (single cross-cutting Phase **1–8** full-completion audit) is **not done**. **`POST /answer`** (**Track E**) remains a **product decision** (in vs outside final “full completion” scope) before any **unqualified** “Phase **1–8** fully done” claim.

This document remains the **active** completion program. It defines the work tracks, decisions, tests, docs, and final audit path toward a **coherent end-to-end product**:

**content ingestion → EvidenceUnits → graph / semantic index → vector-indexed retrieval → RetrievalPacket → retrieval logs → context intelligence → optional model-assisted metadata → optional packet-only answer synthesis → UI inspection → integration guide**

**Important:** **OCR, ASR, automatic semantic-index vector backfill, and `POST /answer`** are **not** implemented in the broad product sense of §3 **except** where explicitly documented (e.g. **manual** vector backfill — **Track B** **B1**; optional language/model paths behind env gates). **Phase 9 has not started.**

The **largest structural gap** for a “real” retrieval demo is still **vector population**: semantic search and FileClerk routes that depend on indexed vectors require `vector_status=indexed`; indexes often remain `pending` without a deliberate indexing step, which yields **valid but empty-evidence** packets. **Track B** remains central to that story.

---

## 2. Why current `pass_with_notes` baselines are not enough

| Area | What `pass_with_notes` accepted | Why it is not “full completion” |
|------|--------------------------------|--------------------------------|
| **Phase 5** ([`PHASE_5_AUDIT.md`](../audits/PHASE_5_AUDIT.md)) | Partial multimodal: PDF/PPTX text to EvidenceUnits; image/audio **validation shells**; no OCR/ASR/caption/video EUs | Intended multimodal scope still includes **EU-producing** image/audio paths, hardened extraction, and explicit policies for optional modalities |
| **Phase 3–4** ([`PROJECT_STATUS.md`](../status/PROJECT_STATUS.md), [`KNOWN_GAPS.md`](../status/KNOWN_GAPS.md)) | APIs, Qdrant service, `POST /retrieve`, honest `pending` indexes | **Rich retrieval** requires a **documented** path to **`indexed`** vectors; no silent “pending” confusion for operators |
| **Phase 7** ([`PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md)) | Recording-only `actor_context`, `language_context` from selected evidence metadata, enrichment no-op default | Full completion may require **production language policy**, aggregation persistence, UI clarity, and an explicit decision on **7I** boosting vs recording-only forever |
| **Phase 8** ([`PHASE_8_AUDIT.md`](../audits/PHASE_8_AUDIT.md)) | Contracts, validation, standalone projection, **8G design-only** | **D2**–**D4** registry/settings/Ollama/purpose contracts (**not** ingest-wired); **D2.5** selector design; **no** merge into ingestion/enrichment as shipped behavior |
| **`POST /answer`** | Correctly **deferred** | Full product may still **choose** packet-only `/answer` before Phase 9 (**Track E** decision) |

**Terminology:** **`pass_with_notes` did not err** — it **accepted the baseline** under documented notes. This program **extends** that baseline toward **full intended completion** without rewriting audit history.

---

## 3. Full completion definition for Phases 1–8

**“Full completion”** (for this program) means:

1. **End-to-end pipeline** is **demonstrable** following the integration guide: ingest → EUs → graph links → semantic index → **indexed** vectors where the guide promises semantic retrieval → **`POST /retrieve`** returns a **RetrievalPacket** with **honest** warnings and, on the **documented golden path**, **non-empty** evidence where the guide says so.
2. **Phase 5** meets the **intended** multimodal scope **agreed in this program** (which may explicitly **defer video** or other items **outside Phases 1–8** — but the deferral must be **written**, not implied).
3. **Phase 7** meets agreed policies: language detection / no-detector, aggregation persistence, `language_context` / `actor_context` behavior, and UI that **never implies context is evidence or personalization**.
4. **Phase 8** meets agreed “real pipeline” scope: optional env-gated adapters, validation before projection, merge rules, observability — still **Invariant-safe** (model output **not** evidence).
5. **Track E** resolved: implement **`/answer`** as a **separate** track or **in** full completion, with **packet-only** semantics if implemented.
6. **Track F + G** match shipped behavior; **Track H** closes with a **new** full-completion audit artifact and status terminology that distinguishes **baseline audited** vs **full completion** (per [`STATUS_REPORTING.md`](../governance/STATUS_REPORTING.md)).

**North-star / outside Phases 1–8 unless explicitly pulled in:** Phase **9** IDE integration, enterprise RBAC/SLA, full inference **fleet** UI, translation-as-product, hidden personalization, replacing or deleting historical audits.

---

## 4. Track A — Phase 5 full multimodal completion

| Attribute | Detail |
|-----------|--------|
| **Goal** | Normalize agreed modalities into **`EvidenceUnit`s** with correct **`source_fidelity`**, **location** metadata, explicit **failure semantics**, optional-deps policy, **tests**, and **UI visibility** aligned with [`docs/phases/graph_clerk_phase_5_multimodal_ingestion.md`](../phases/graph_clerk_phase_5_multimodal_ingestion.md) **intent** (see phase doc **Implementation status (current)** vs **Core Objective**). |
| **Current state** | PDF/PPTX: text extraction to EUs when optional extras installed (`extracted`). Image/audio: **validation only**; **no** EUs; **503** where documented. Video: **not supported** (**400**). Audited **`pass_with_notes`** — baseline accepted, not full multimodal completion. |
| **Missing work** | PDF/PPTX **hardening** (quality, edge cases, failure classes). **Image OCR**; **image captioning / visual summaries** (policy: EU vs metadata-only). **Audio ASR**. **EvidenceUnits** from image/audio where supported. **Optional video**: decision in or **explicitly deferred outside Phases 1–8**. **source_fidelity** rules for OCR/ASR/caption. **Locations**: PDF page; PPTX slide/region; image region/OCR box where possible; audio timestamp ranges; video frame/timestamp ranges **if** video in scope. Optional dependency matrix + CI strategy. |
| **Required design decisions** | Video in-scope vs deferred. First OCR engine (**requires dependency research** if not locked). First ASR engine (**requires dependency research**). Caption/summary as EU text vs `metadata_json` only. `source_fidelity` values per modality. Geometry/timestamp JSON shape. Optional extras vs required core. **400 vs 503 vs 500** matrix (client/config vs transient upstream). |
| **Proposed slices** | **A1** PDF hardening · **A2** PPTX hardening · **A3** OCR path + location · **A4** ASR path + timestamps · **A5** Caption/visual summary policy · **A6** Video decision + implementation or ADR deferral · **A7** HTTP error matrix + docs + UI panels |
| **Likely files** (future implementation) | `backend/app/services/multimodal_ingestion_service.py`, `backend/app/services/extraction/*`, `backend/app/api/routes/artifacts.py`, evidence/artifact schemas, `frontend/src/components/*` (evidence/artifact viewers). |
| **Forbidden files** | Do not edit **`docs/audits/*`** to rewrite old verdicts; do not edit **`docs/phases/*`** in this program’s doc-only slice (phase changes are separate change-control). Do not claim OCR/ASR/video complete in **status** until implemented + tested. |
| **Tests required** | Extend Phase 5 HTTP matrix; extractor unit tests; File Clerk + `POST /retrieve` with multimodal EUs; golden files for PDF/PPTX/OCR/ASR where feasible; optional gated integration for heavy deps. |
| **Docs required** | Status/README honest deltas; optional ADR for engine choice; integration guide updates (**Track F**). |
| **Risks** | Dependency license/ops burden; non-deterministic models if used for “extraction”; conflating caption text with **verbatim** evidence. |
| **Dependencies** | Track **B** not strictly blocking OCR, but **demo narrative** needs B for semantic evidence; Track **C** may consume language tags on new EU text. |
| **Acceptance criteria** | Phase doc **intent** satisfied **or** explicitly deferred in writing; audits updated via **new** audit pass when closing; no silent success with zero evidence; UI matches actual capabilities. |

---

## 5. Track B — Semantic index / vector backfill completion

| Attribute | Detail |
|-----------|--------|
| **Goal** | Make **`vector_status=indexed`** achievable, observable, and **honest**: indexing job and/or **manual dev command**, automatic upsert policy (if approved), **integration tests**, **demo path** with **non-empty** evidence when following the guide, explicit **Qdrant failure** → `failed`, no silent **`pending`** confusion. |
| **Current state** | `SemanticIndex.vector_status`: `pending | indexed | failed`. Qdrant upsert/search services exist. **Semantic index creation does not auto-populate vectors** ([`PROJECT_STATUS.md`](../status/PROJECT_STATUS.md), [`KNOWN_GAPS.md`](../status/KNOWN_GAPS.md)). **`GET /semantic-indexes/search`** returns **indexed** only. **Automatic vector backfill is not implemented today.** |
| **Missing work** | Policy for when vectors are built; backfill/job orchestration; operator visibility; embedding production path decision; transition rules **`pending` → `indexed` | `failed`**; minimal indexed demo recipe; reduce “valid empty packet” surprise via docs + behavior. |
| **Required design decisions** | Auto-enqueue on SI create vs **manual-first** vs operator-triggered only. Sync vs async job. How Qdrant errors surface (API, status field, logs). Whether **embedding adapter** choice blocks automation (**requires dependency research** for vendor/model). |
| **Proposed slices** | **B1** (shipped) Manual backfill + tests with stubbed search · **B2** (implemented) Test-safe semantic search embedding wiring — see below · **B3** Status API/UI surfacing for `vector_status` / indexing errors · **B4** Auto policy (if approved) + idempotency · **B5** (implemented) Full-stack integration: ingest → index → retrieve (no FileClerk / factory monkeypatch) — [`test_phase1_8_track_b_full_stack_retrieve.py`](../../backend/tests/test_phase1_8_track_b_full_stack_retrieve.py) |
| **Likely files** | `backend/app/services/semantic_index_service.py`, `backend/app/api/routes/semantic_indexes.py`, embedding services, `scripts/*` **if** user later allows scripts for CLI, repositories, tests under `backend/tests/`. |
| **Forbidden files** | For **this** docs-only delivery: no backend/scripts edits here. Implementation must not set `indexed` without successful Qdrant truth. |
| **Tests required** | Unit + gated Qdrant integration; FileClerk retrieve with indexed SI; failure path sets `failed` explicitly. |
| **Docs required** | Track **F** onboarding: “run vector indexing”; README/status when behavior ships. |
| **Risks** | CI without Qdrant; embedding dimension mismatches; long-running jobs without visibility. |
| **Dependencies** | Production or dev embedding endpoint decision; may parallel **Track F** skeleton. |
| **Acceptance criteria** | Operator can follow doc and reach **`indexed`** or see explicit **`failed`**; demo path can show **non-empty** semantic evidence; no undocumented `pending` limbo. |

### Track B — Slice B1 (implemented)

- **Service:** `SemanticIndexVectorIndexingService` in [`backend/app/services/semantic_index_service.py`](../../backend/app/services/semantic_index_service.py) — embeds non-empty `embedding_text`, upserts to Qdrant via `VectorIndexService`, sets `vector_status` to **`indexed`** on success or **`failed`** on empty text / embedding / vector errors; records diagnostics under `metadata_json.graphclerk_vector_indexing`; skips already **`indexed`** unless `force=True`; retries **`failed`** rows from `index_all_pending`.
- **Operator CLI:** [`scripts/backfill_semantic_indexes.py`](../../scripts/backfill_semantic_indexes.py) — `--semantic-index-id` or `--all-pending` (dev embeddings: `DeterministicFakeEmbeddingAdapter`, not production semantics).
- **Tests:** [`backend/tests/test_phase1_8_track_b_indexed_retrieval.py`](../../backend/tests/test_phase1_8_track_b_indexed_retrieval.py) (requires DB-backed `db_ready` when `RUN_INTEGRATION_TESTS=1` + `DATABASE_URL`).
- **Not in B1:** automatic indexing on `POST /semantic-indexes` create; background job system; production embedding adapter in the API default factory.

### Track B — Slice B5 (implemented)

- **Test:** [`backend/tests/test_phase1_8_track_b_full_stack_retrieve.py`](../../backend/tests/test_phase1_8_track_b_full_stack_retrieve.py) — `create_app` + httpx ASGI transport; creates artifact, evidence, graph node + link, semantic index (`embedding_text` aligned with retrieve `question` for deterministic vectors); runs **`SemanticIndexVectorIndexingService`** in-process (same adapter/dimension as B1/B2); asserts `vector_status=indexed` and **`POST /retrieve`** returns a packet with matching `evidence_unit_id` / `artifact_id`. **No** monkeypatch of FileClerk or `build_semantic_index_search_service`.
- **Gate:** env vars documented in [`TESTING_RULES.md`](../governance/TESTING_RULES.md) (*Track B Slice B5*); test skips when unset (default CI).
- **B5.1 (2026-05-01):** Gated integration run **passed** against local Compose Postgres + Qdrant after clearing a **stale** `semantic_indexes` collection whose vector size did not match dim **8**; evidence in [`RELEASE_CHECKLIST.md`](../release/RELEASE_CHECKLIST.md) (*Track B Slice B5.1*). Not a claim about production embedding or auto-indexing.
- **B5.2:** Operator/docs follow-up — Qdrant **dimension mismatch** failure mode and **dev-only** collection reset are documented in [`TESTING_RULES.md`](../governance/TESTING_RULES.md), [`PHASE_6_DEMO_CORPUS.md`](../demo/PHASE_6_DEMO_CORPUS.md), and [`RELEASE_CHECKLIST.md`](../release/RELEASE_CHECKLIST.md).

### Track B — Slice B2 (implemented): guarded deterministic semantic search embeddings

**Outcome:** Settings field **`GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER`** (`not_configured` \| `deterministic_fake`, default `not_configured`) with Pydantic validation: **`deterministic_fake`** requires **`RUN_INTEGRATION_TESTS=1`** and is **rejected** when **`APP_ENV=prod`**. [`build_semantic_index_search_service`](../../backend/app/services/semantic_index_search_factory.py) wires **`DeterministicFakeEmbeddingAdapter`** (dim 8, same as B1 backfill) only when that mode is active. Documented in [`TESTING_RULES.md`](../../docs/governance/TESTING_RULES.md). **B5** (gated httpx full-stack ingest → vector index → `POST /retrieve` without FileClerk or factory monkeypatch) is **implemented** in [`test_phase1_8_track_b_full_stack_retrieve.py`](../../backend/tests/test_phase1_8_track_b_full_stack_retrieve.py); see [`TESTING_RULES.md`](../governance/TESTING_RULES.md) *Track B Slice B5*.

**Problem (post-B1):** [`scripts/backfill_semantic_indexes.py`](../../scripts/backfill_semantic_indexes.py) and `SemanticIndexVectorIndexingService` use **`DeterministicFakeEmbeddingAdapter`** against Qdrant, but [`build_semantic_index_search_service`](../../backend/app/services/semantic_index_search_factory.py) always wires **`NotConfiguredEmbeddingAdapter`** ([`semantic_index_search_factory.py`](../../backend/app/services/semantic_index_search_factory.py) L29–31). Query vectors for search therefore cannot match backfilled vectors in a **single** process unless tests monkeypatch the factory (allowed today) or the app gains a **guarded** alternate embedding path for search only.

**Goal of B2:** smallest change so a **gated** integration test can run **ingest → backfill → `GET /semantic-indexes/search` → `POST /retrieve` → non-empty evidence** using real Qdrant + real FileClerk route selection **without monkeypatching `FileClerkService` or route internals**. (Monkeypatching only the **factory module** remains a smaller alternative — see Option B — but does not meet a strict “zero patch” bar.)

#### Design options evaluated

| Option | Scope | Production risk | Hidden fallback risk | Operator clarity | Integration usefulness | No-silent-fallback alignment | Config impact |
|--------|-------|-----------------|----------------------|------------------|-------------------------|------------------------------|---------------|
| **A — Test-only env / settings flag** | Small–medium: `Settings` + branch in `build_semantic_index_search_service` | **Low** if `deterministic_fake` is **rejected** in `APP_ENV=prod` (validator) and ideally only when `RUN_INTEGRATION_TESTS=1` or explicit dev flag | **Low** if default remains `not_configured` and mis-set env **fails closed** in prod | Document in `TESTING_RULES.md` + demo doc; operators use real embeddings in prod | **High** — true `create_app()` + httpx, no factory monkeypatch | **Good** — explicit mode; no silent switch to fake | Adds typed field(s) + validation |
| **B — DI / monkeypatch factory in tests only** | **Smallest** — no `config.py` change; pytest replaces `build_semantic_index_search_service` | **None** in prod | **None** | N/A (test-only) | **High** with patch; **not** “zero patch” | **Good** | None |
| **C — Dedicated test app factory helper** | Medium: new test helper or `create_app(..., overrides=)` | Low if test-only entrypoint | Low | Test docs only | **High** if wired once; may still patch or inject | **Good** | Depends on shape |
| **D — Production embedding first** | Large; blocks on vendor research | N/A | N/A | N/A | High eventually; **out of scope** for B2 | N/A | Large |
| **E — Leave monkeypatch-only** | Zero | None | None | Confusing for “E2E” claims | Medium | **Good** | None |

**Chosen approach for implementation (B2):** **Option A (narrow, validated)** as the **primary** path for a **documented, zero–factory-monkeypatch** full-stack test, **plus** retain **Option B** as an explicitly supported **smaller** pattern in `TESTING_RULES.md` (factory monkeypatch is **not** FileClerk internals — acceptable for unit/API tests that already use it).

- **Rationale:** A guarded settings branch keeps **one** construction site ([`semantic_index_search_factory.py`](../../backend/app/services/semantic_index_search_factory.py)); Pydantic can **forbid** deterministic mode in `prod` and optionally require `RUN_INTEGRATION_TESTS=1` even in `test` to avoid accidental local misuse. Aligns with **no silent fallback**: default stays **`NotConfigured`**; deterministic is **opt-in** and **loud** (log line at startup when enabled).
- **Why not D alone:** B2 explicitly **does not** select a production embedding provider.
- **Why not E alone:** Fails the stated goal of full-stack retrieve **without** relying on patch discipline for “real E2E” narrative; E remains valid for **narrow** tests.

#### Answers (design questions)

1. **Smallest safe design for gated deterministic end-to-end:** Add a **single** settings-controlled branch in `build_semantic_index_search_service` to use `DeterministicFakeEmbeddingAdapter` + same `expected_dimension` (8) as today’s vector stack, **guarded** so `prod` cannot enable it; OR use **Option B** (factory monkeypatch) if the project accepts that as “full-stack enough.”
2. **Config vs test factory vs DI:** **Primary:** `config.py` + factory (A). **Alternative:** test-only patch of `build_semantic_index_search_service` (B). **Avoid** large `create_app` DI (C) unless A/B prove insufficient.
3. **Accidental production fake:** `app_env == "prod"` → **reject** deterministic at settings parse; optional: deterministic only if `RUN_INTEGRATION_TESTS=1`; startup log: `semantic_search_embedding_mode=deterministic_fake (integration test only)`.
4. **Interaction with B1 script:** Script stays **standalone** (imports adapter directly). **Same** `DeterministicFakeEmbeddingAdapter` + dimension **8** when app is in test deterministic mode so backfill vectors and query embeddings use **identical** math — required for Qdrant cosine search to match. Document shared constant (dimension + adapter class) in one place in implementation slice.
5. **Share adapter with B1 script?** **Behaviorally yes** (same algorithm + dimension); **code path** can stay duplicated in script vs factory **or** a tiny shared helper module later — implementation choice, not blocking.
6. **Files implementation would likely touch:** [`backend/app/core/config.py`](../../backend/app/core/config.py), [`backend/app/services/semantic_index_search_factory.py`](../../backend/app/services/semantic_index_search_factory.py), possibly [`backend/app/main.py`](../../backend/app/main.py) only if startup logging is added there (prefer factory log). Tests: [`backend/tests/test_phase1_8_track_b_indexed_retrieval.py`](../../backend/tests/test_phase1_8_track_b_indexed_retrieval.py) or new `test_phase1_8_track_b_fullstack_integration.py`; [`docs/governance/TESTING_RULES.md`](../../docs/governance/TESTING_RULES.md). Optional: `.env.example` line (docs-only env name).
7. **Tests to add:** Gated `RUN_INTEGRATION_TESTS=1` + `DATABASE_URL` + `QDRANT_URL`: create artifact/evidence/node link + SI with `embedding_text`, run **`SemanticIndexVectorIndexingService`** (or script subprocess — heavier), **unset** monkeypatch, set env for deterministic search mode, `create_app()` + `httpx` `POST /retrieve`, assert non-empty `evidence_units`. Separate test: **prod settings** reject deterministic mode (unit test with `pydantic.ValidationError` or equivalent).
8. **Status/docs:** Update [`docs/status/KNOWN_GAPS.md`](../status/KNOWN_GAPS.md) / [`PROJECT_STATUS.md`](../status/PROJECT_STATUS.md) **only when behavior ships** — not for this design-only pass. Update [`TESTING_RULES.md`](../../docs/governance/TESTING_RULES.md) in the **implementation** slice.
9. **C4 full-stack vs next slice:** Treat **true** ingest→Qdrant→search→retrieve **without** factory monkeypatch as **B2** (or **B2+B5** if split: B2 = wiring, B5 = long integration test). **C4** in the completion program referred to UI context — do not conflate; use **B5** label above for integration.
10. **Deferred:** Production embedding adapter for **default** `prod` search; automatic indexing on create; UI surfacing (**B3**); optional **B**-only policy if team decides env-based A is unnecessary.

#### Implementation record (B2 shipped)

| Item | Detail |
|------|--------|
| **Config** | [`backend/app/core/config.py`](../../backend/app/core/config.py) — `semantic_search_embedding_adapter` + `@model_validator` |
| **Factory** | [`backend/app/services/semantic_index_search_factory.py`](../../backend/app/services/semantic_index_search_factory.py) |
| **Tests** | [`backend/tests/test_config.py`](../../backend/tests/test_config.py), [`backend/tests/test_phase1_8_track_b_indexed_retrieval.py`](../../backend/tests/test_phase1_8_track_b_indexed_retrieval.py) |
| **B5 (implemented)** | Gated httpx test: ingest → `SemanticIndexVectorIndexingService` → `POST /retrieve` with **no** `build_semantic_index_search_service` / FileClerk monkeypatch — [`test_phase1_8_track_b_full_stack_retrieve.py`](../../backend/tests/test_phase1_8_track_b_full_stack_retrieve.py). |

---

## 6. Track C — Phase 7 full context intelligence completion

| Attribute | Detail |
|-----------|--------|
| **Goal** | Close **policy and wiring** for language + actor context per [`docs/phases/graph_clerk_phase_7_context_intelligence.md`](../phases/graph_clerk_phase_7_context_intelligence.md): optional **Lingua** detection behind explicit env + optional extra; **`POST /artifacts`** product wiring (**Track C8**); **artifact language aggregation** persistence; **`language_context`** from selected EU **`metadata_json`** only; **`actor_context`** recording-only (**no** boost); translation deferred outside **1–8**; UI + onboarding; **Track C9** = **final Phase 7 full-completion audit** (program-wide closure still aligns with **Track H** / [`STATUS_REPORTING.md`](../governance/STATUS_REPORTING.md)). |
| **Current state** | **Track C** (**C1–C9**) **complete** for agreed Phase 7 Phase 1–8 completion scope — **[`docs/audits/PHASE_7_FULL_COMPLETION_AUDIT.md`](../audits/PHASE_7_FULL_COMPLETION_AUDIT.md)** (**`pass`**, **Track C Slice C9**). **`POST /artifacts`** **`build_evidence_enrichment_service`**: **`not_configured`** (default) vs **`lingua`** + optional extra (**503** fail loud). **`language_context`** (**selected** EU metadata); **`actor_context`** **recording only**. Baseline history: [`PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md) (**`pass_with_notes`**). **Slice 7I** boosting **not** implemented (out of scope). |
| **Missing work** | Optional **translation** / **7I** boosting only after explicit approval + separate tracks; anti-AC-bypass proofs if boosting ever ships. |
| **Required design decisions** | **7I** forever deferred vs approved with fixtures. Translation in Phase 7 scope or **explicitly outside 1–8**. |
| **Proposed slices** | **C1** ✅ · **C2** ✅ · **C3** ✅ optional **Lingua** adapter + settings + tests ([`TESTING_RULES.md`](../governance/TESTING_RULES.md)) — [`phase_7_language_detector_dependency_decision.md`](../decisions/phase_7_language_detector_dependency_decision.md) addendum · **C4** ✅ enrichment accepts injected detector · **C5** ✅ artifact aggregation persistence · **C6** ✅ packet/context tests · **C7** ✅ UI/operator visibility · **C8** ✅ **`POST /artifacts`** product wiring for **`lingua`** when configured · **C9** ✅ Final Phase 7 full-completion audit ([`PHASE_7_FULL_COMPLETION_AUDIT.md`](../audits/PHASE_7_FULL_COMPLETION_AUDIT.md)) · optional **C-boost-1** / **C-translation-1** only after explicit approval (**outside** agreed Track C closure) |
| **Likely files** | `evidence_enrichment_service.py`, `language_detection_service.py`, `artifact_language_aggregation_service.py`, `text_ingestion_service.py`, `multimodal_ingestion_service.py`, `retrieval_packet_builder.py`, `file_clerk_service.py` (if boosting), schemas, `frontend/src/types/retrievalPacket.ts`, `QueryPlayground.tsx`, etc. |
| **Forbidden files** | Do not use **context** to **hide** retrieval or bypass access control; do not edit historical audits to remove **7I** deferral notes—append new outcomes. |
| **Tests required** | Extend `test_phase7_*`; ranking/evidence-order tests if boosting; property tests that actor cannot inject evidence. |
| **Docs required** | Onboarding: how to set `actor_context` / read `language_context`; failure modes. |
| **Risks** | Personalization perception; secret retrieval; flaky remote detectors. |
| **Dependencies** | **Track A** (language tags on OCR/ASR text) optional; align with **Track D** metadata merge boundaries. |
| **Acceptance criteria** | Decisions documented; behavior matches docs; UI does not imply personalization-as-evidence; audit-ready. |

### Track C — Slice C1 (completed): Phase 7 context intelligence completion decisions

- **Outcome:** Design-only **decision record** created — **[`docs/decisions/phase_7_context_intelligence_completion_decisions.md`](../decisions/phase_7_context_intelligence_completion_decisions.md)**. **No** backend, frontend, or script changes in this slice. **Phase 9** has **not** started. Prior [`PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md) remains **baseline history**.
- **Purpose:** Decide or explicitly defer production detector policy, wiring location, aggregation persistence, `language_context` / `actor_context` policy, deterministic boosting, translation scope, and UI/docs implications **before** implementation slices **C2+**.
- **Recommended next Track C slice (superseded by C2 completion):** ~~**C2**~~ — see **Track C — Slice C2** below.

### Track C — Slice C2 (completed): language detector dependency research

- **Outcome:** Research-only decision — **[`docs/decisions/phase_7_language_detector_dependency_decision.md`](../decisions/phase_7_language_detector_dependency_decision.md)**. **No** dependency added; **no** `pyproject.toml` / backend / frontend / script changes. **Phase 9** not started. Phase **7** audit baseline unchanged.
- **Recommendation:** First production-capable adapter target **`lingua-language-detector`** (optional extra; default remains **`NotConfigured`**); documented alternates **`cld3-py`**, **`py3langid`** / **`fast-langdetect`**.
- **Recommended next Track C slice (superseded by C3):** ~~**C3**~~ — see **Track C — Slice C3** below.

### Track C — Slice C3 (completed): optional Lingua language detection adapter

- **Outcome:** Optional **`language-detector`** extra (`lingua-language-detector>=2.2.0`); **`GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER`** / `language_detection_adapter` (`not_configured` \| `lingua`, default **`not_configured`**); **`LinguaLanguageDetectionAdapter`**, **`build_language_detection_adapter`**, **`build_language_detection_service`**; tests + [`TESTING_RULES.md`](../governance/TESTING_RULES.md). **No** ingestion, retrieval, aggregation, translation, or actor-boost changes. **Phase 9** not started.
- **Recommended next Track C slice (superseded by C4):** ~~**C4**~~ — see **Track C — Slice C4** below.

### Track C — Slice C4 (implemented): optional language metadata in enrichment before EU persistence

- **Outcome:** `EvidenceEnrichmentService` accepts optional injected `LanguageDetectionService`; when present, `enrich` merges canonical language keys onto **new** `EvidenceUnitCandidate` instances (`dataclasses.replace`), preserves caller-supplied non-empty `language` and conservative skip when other language keys exist without `language`, records stable `language_warnings` on unavailable/failure paths, and never mutates `text` / `source_fidelity`. Default `EvidenceEnrichmentService()` remains a **no-op**. *(Slice C4 did **not** enable Lingua from routes by itself — **Track C8** wires **`POST /artifacts`** when **`GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER=lingua`**.)*
- **Tests:** [`backend/tests/test_phase7_evidence_enrichment_service.py`](../../backend/tests/test_phase7_evidence_enrichment_service.py), [`backend/tests/test_phase7_evidence_enrichment_integration.py`](../../backend/tests/test_phase7_evidence_enrichment_integration.py).
- **Recommended next Track C slice (superseded by C5):** ~~**C5**~~ — see **Track C — Slice C5** below.

### Track C — Slice C5 (implemented): artifact language aggregation persistence

- **Outcome:** After `EvidenceUnitService.create_from_candidates`, text and multimodal ingestion call `apply_language_aggregation_to_artifact`, which merges **`graphclerk_language_aggregation`** from each created EU’s **`metadata_json`** (honest absence when no language keys) and assigns the merged dict to **`Artifact.metadata_json`**, preserving unrelated keys and replacing only the aggregation subtree. **No** migrations, **no** retrieval changes.
- **Tests:** [`backend/tests/test_phase7_artifact_language_aggregation_persistence.py`](../../backend/tests/test_phase7_artifact_language_aggregation_persistence.py), extensions in [`test_phase2_ingestion.py`](../../backend/tests/test_phase2_ingestion.py), [`test_phase5_artifact_ingest_routing.py`](../../backend/tests/test_phase5_artifact_ingest_routing.py), [`test_phase7_evidence_enrichment_integration.py`](../../backend/tests/test_phase7_evidence_enrichment_integration.py).
- **Recommended next Track C slice (superseded by C6):** ~~**C6**~~ — see **Track C — Slice C6** below.

### Track C — Slice C6 (implemented): packet / context tests with persisted metadata

- **Outcome:** **Tests only** — no production code changes required. Coverage proves `RetrievalPacket.language_context` is derived from **selected** evidence `metadata_json` (same aggregation rules as artifact subtree, but builder passes `artifact_metadata=None`), honest absence when metadata lacks `language`, independence from nested `graphclerk_language_aggregation` blobs on EU rows, coexistence with **recording-only** `actor_context`, ingestion→EU→`EvidenceCandidate`→packet flow when enrichment is injected (DB-backed), and gated Track B retrieve responses expose `language_context` with `source=selected_evidence_metadata` (default API ingest path still without injected detection).
- **Tests:** [`backend/tests/test_phase7_retrieval_packet_language_context.py`](../../backend/tests/test_phase7_retrieval_packet_language_context.py), [`test_phase7_retrieval_packet_actor_context.py`](../../backend/tests/test_phase7_retrieval_packet_actor_context.py), [`test_phase7_artifact_language_aggregation_persistence.py`](../../backend/tests/test_phase7_artifact_language_aggregation_persistence.py), [`test_phase4_packet_builder.py`](../../backend/tests/test_phase4_packet_builder.py), [`test_phase1_8_track_b_full_stack_retrieve.py`](../../backend/tests/test_phase1_8_track_b_full_stack_retrieve.py), [`test_phase1_8_track_b_indexed_retrieval.py`](../../backend/tests/test_phase1_8_track_b_indexed_retrieval.py).
- **Recommended next Track C slice (superseded by C7):** ~~**C7**~~ — see **Track C — Slice C7** below.

### Track C — Slice C7 (implemented): UI / operator visibility (language)

- **Outcome:** **Artifacts & evidence** shows a readable **Language aggregation** block when **`metadata_json.graphclerk_language_aggregation`** exists (primary language, counts, warnings, languages table); raw **metadata** JSON unchanged. **RetrievalPacket** panel clarifies **selected evidence** `metadata_json` vs **artifact** aggregation subtree; **Query Playground** copy reflected **default** ingest at time of **C7**. Onboarding: pipeline, troubleshooting, minimal guide, examples cookbook aligned with **packet `language_context` ≠ artifact aggregation**; packet builder does **not** read artifact aggregation for `language_context`.
- **Scope:** Frontend + docs only; **no** backend / retrieval / API behavior changes.
- **Recommended next Track C slice (superseded by C8):** ~~**C8**~~ — see **Track C — Slice C8** below.

### Track C — Slice C8 (implemented): product wiring for configured language detection

- **Outcome:** **`POST /artifacts`** builds **`EvidenceEnrichmentService`** via **`build_evidence_enrichment_service(settings)`** before opening a DB session: **`not_configured`** → default no-op enrichment; **`lingua`** → **`build_language_detection_service`** injected (**503** / **`LanguageDetectionUnavailableError`** if Lingua cannot be constructed — **no** downgrade). Same enrichment instance is passed to **`TextIngestionService`** and **`MultimodalIngestionService`**. Per-candidate detection failures remain **C4** semantics (**warnings**, ingestion continues; **`text`** / **`source_fidelity`** unchanged). **`graphclerk_language_aggregation`** (**C5**) and **`language_context`** (**selected** EU metadata) unchanged in meaning.
- **Tests:** [`backend/tests/test_phase7_language_detection_product_wiring.py`](../../backend/tests/test_phase7_language_detection_product_wiring.py).
- **Recommended next Track C slice (superseded by C9):** ~~**C9**~~ — see **Track C — Slice C9** below.

### Track C — Slice C9 (completed): Final Phase 7 full-completion audit

- **Outcome:** New audit artifact **[`docs/audits/PHASE_7_FULL_COMPLETION_AUDIT.md`](../audits/PHASE_7_FULL_COMPLETION_AUDIT.md)** — result **`pass`** (2026-05-01). **`PHASE_7_AUDIT.md`** **not** edited (baseline history). Status docs (`PROJECT_STATUS`, `PHASE_STATUS`, `ROADMAP`, `KNOWN_GAPS`, `TECHNICAL_DEBT`), **`README.md`**, **`QueryPlayground.tsx`** (tiny copy), and this program updated. **No** backend/retrieval behavior change in **C9**.
- **Recommended next program track:** **Track D** closed (**D8** **`pass`**); proceed per **Track E–H** / phase roadmap when approved — **Track C**/**D** closures apply to **agreed Phase 1–8 scope** only.

**Track C** is **complete** — **C1** through **C9** are closed for the **agreed Phase 1–8 completion scope** (optional **translation / boosting** tracks remain **explicitly outside** unless reopened).

---

## 7. Track D — Phase 8 real model pipeline completion

| Attribute | Detail |
|-----------|--------|
| **Goal** | Optional **production-capable** inference path behind **explicit configuration**: **Ollama HTTP** and/or **OpenAI-compatible (e.g. vLLM)** adapter, **adapter registry**, **settings/env**, timeouts and error semantics, **mocked HTTP tests**, **`NotConfigured`** default unchanged when unset, **validation before projection**, **merge policy** for `graphclerk_model_pipeline` metadata, **ingestion/enrichment merge rules**, **no model output as evidence**, **observability**. Align with [`docs/phases/graph_clerk_phase_8_specialized_model_pipeline.md`](../phases/graph_clerk_phase_8_specialized_model_pipeline.md) **north-star** only where explicitly in scope; respect **Implementation status (current)** honesty. |
| **Current state** | **Track D complete** for agreed Phase 1–8 scope — **[`PHASE_8_FULL_COMPLETION_AUDIT.md`](../audits/PHASE_8_FULL_COMPLETION_AUDIT.md)** (**`pass`**, **D8**, **2026-05-02**). **D2**–**D7b** delivered (registry, Ollama adapter, purpose registry, enrichment orchestration, optional ingest merge, **D7a/D7b** UI/API). **Baseline history:** [`PHASE_8_AUDIT.md`](../audits/PHASE_8_AUDIT.md). Decisions: **[`phase_8_model_pipeline_completion_decisions.md`](../decisions/phase_8_model_pipeline_completion_decisions.md)**. |
| **Missing work (outside agreed Track D closure)** | Optional **D7c** writable selector / persistence / **auth**; optional **D3b** **`openai_compatible`** adapter — **not** required for Phase 8 agreed-scope **`pass`**. |
| **Required design decisions** | **D1** closed — see decision doc. **D2.5** amendment — [`phase_8_model_pipeline_completion_decisions.md`](../decisions/phase_8_model_pipeline_completion_decisions.md) § *D2.5 Amendment* — per-purpose model mapping + future selector UI (**design only**); **Option B** for D3 vs D4 (adapter proves HTTP; purpose contracts in **D4** before merge). |
| **Proposed slices** | **D1** ✅ · **D2** ✅ · **D2.5** ✅ · **D3** ✅ · **D4** ✅ · **D5** ✅ · **D6** ✅ · **D7a** ✅ · **D7b** ✅ · **D8** ✅ full-completion audit · **D7c** / **D3b** **future / optional** |
| **Likely files** | `model_pipeline_contracts.py`, new adapter modules, `model_pipeline_output_validation_service.py`, `model_pipeline_candidate_projection_service.py`, `evidence_enrichment_service.py`, `core/config.py`, tests. |
| **Forbidden files** | Model modules must **not** import FileClerk/retrieval (existing invariant); do not mutate `EvidenceUnit.text` / `source_fidelity` from model pipeline. |
| **Tests required** | HTTP mocking; timeout tests; merge tests; “no evidence from model” regression tests. |
| **Docs required** | Operator guide for env flags; security notes for outbound HTTP. |
| **Risks** | Accidental default-on LLM calls; prompt injection from media; dependency sprawl. |
| **Dependencies** | **Track A** metadata needs stable shapes; **Track C** enrichment ordering. |
| **Acceptance criteria** | Default install has **no** network model calls; when enabled, full validate→project→merge path tested; status docs honest. |

### Track D — Slice D1 (completed): Phase 8 model pipeline completion decisions

- **Outcome:** **[`docs/decisions/phase_8_model_pipeline_completion_decisions.md`](../decisions/phase_8_model_pipeline_completion_decisions.md)** — design-only record for **full Phase 8 completion** path (first adapter **Ollama**, static registry, settings/env, timeouts/errors, **`evidence_candidate_enricher`** first, validate-before-projection, metadata-only merge, preferred **`ModelPipelineMetadataEnrichmentService`** boundary, observability, **`/answer`** = Track **E**, security). **No** backend/frontend/scripts/deps changed. **Phase 9** not started. **[`PHASE_8_AUDIT.md`](../audits/PHASE_8_AUDIT.md)** unchanged (baseline history).

### Track D — Slice D2 (completed): model pipeline settings + static registry

- **Outcome:** [`backend/app/core/config.py`](../../backend/app/core/config.py) — `GRAPHCLERK_MODEL_PIPELINE_*` settings (default adapter **`not_configured`**; timeout **`0 < seconds <= 300`**; **`deterministic_test`** only when **`RUN_INTEGRATION_TESTS=1`** and **`APP_ENV` ≠ `prod`**). [`backend/app/services/model_pipeline_registry.py`](../../backend/app/services/model_pipeline_registry.py) — `build_model_pipeline_adapter(settings)` returns **`NotConfiguredModelPipelineAdapter`** for **`not_configured`**; **`ollama`** / **`openai_compatible`** raise **`ModelPipelineAdapterNotImplementedError`** (**`model_pipeline_adapter_not_implemented`**); **`deterministic_test`** requires injected **`deterministic_test_factory`** (no silent product path). **No** HTTP, **no** ingestion wiring, **no** new dependencies. Tests: [`test_phase8_model_pipeline_registry.py`](../../backend/tests/test_phase8_model_pipeline_registry.py), [`test_config.py`](../../backend/tests/test_config.py). Documented in [`TESTING_RULES.md`](../governance/TESTING_RULES.md).

### Track D — Slice D2.5 (completed): model purpose registry + frontend selector — design amendment

- **Outcome:** **[`docs/decisions/phase_8_model_pipeline_completion_decisions.md`](../decisions/phase_8_model_pipeline_completion_decisions.md)** — § **D2.5 Amendment**: terminology (**provider**, **model**, **purpose**, **purpose mapping**, **selector UI**); purpose keys aligned with **`ModelPipelineRole`**; rollout policy (**`evidence_candidate_enricher`** first; **`routing_hint_generator`** disabled until approved); illustrative future JSON config (**not implemented**); **Option B** — **D3** Ollama adapter with explicit per-call model context; **D4** purpose registry/contracts **before** ingestion merge; future admin API names (**not implemented**); persistence evaluation + **Fred** question on writable UI before auth; revised slice plan (**D7a** / **D7b** read-only vs **D7c** writable). **No** code, **no** frontend, **no** persistence (**D2.5** design slice only).

### Track D — Slice D3 (completed): Ollama HTTP adapter + mocked tests

- **Outcome:** [`backend/app/services/model_pipeline_ollama_adapter.py`](../../backend/app/services/model_pipeline_ollama_adapter.py) — **`OllamaModelPipelineAdapter`**, **`POST /api/generate`**, stdlib **`urllib`**, **`format: json`**, error codes (**`model_pipeline_ollama_unavailable`**, **`model_pipeline_ollama_http_error`**, **`model_pipeline_invalid_json`**, **`model_pipeline_schema_mismatch`**). Adapter registry builds Ollama adapter when **`BASE_URL`** + **`MODEL`** set; **`model_pipeline_ollama_misconfigured`** if missing. **No** ingestion wiring, **no** new dependencies. Tests: [`test_phase8_model_pipeline_ollama_adapter.py`](../../backend/tests/test_phase8_model_pipeline_ollama_adapter.py), updated registry tests.

### Track D — Slice D4 (completed): backend purpose registry / config contracts

- **Outcome:** [`backend/app/services/model_pipeline_purpose_registry.py`](../../backend/app/services/model_pipeline_purpose_registry.py) — **`ModelPipelinePurposeRegistry`**, **`ModelPipelinePurposeConfig`**, **`ModelPipelinePurposeResolution`**, **`resolve_model_pipeline_purpose`**, **`build_default_model_pipeline_purpose_registry(settings)`** (all purposes **disabled** unless **D6** env enables **`evidence_candidate_enricher`**). Phase 1–8 policy: **only** **`evidence_candidate_enricher`** may be **`enabled`** with **`adapter=ollama`**; **`routing_hint_generator`** / **`artifact_classifier`** / **`extraction_helper`** enabled → **`ModelPipelinePurposePolicyError`**. Default enricher **`output_kind`** template: **`derived_metadata`**. **No** HTTP, **no** adapter instances inside this module. Tests: [`test_phase8_model_pipeline_purpose_registry.py`](../../backend/tests/test_phase8_model_pipeline_purpose_registry.py).

### Track D — Slice D5 (completed): model metadata enrichment orchestration

- **Outcome:** [`backend/app/services/model_pipeline_metadata_enrichment_service.py`](../../backend/app/services/model_pipeline_metadata_enrichment_service.py) — **`ModelPipelineMetadataEnrichmentService`** takes injected **`ModelPipelineAdapter`**, **`ModelPipelineOutputValidationService`**, **`ModelPipelineCandidateMetadataProjectionService`**. **`enrich_candidates`** accepts **`ModelPipelinePurposeResolution`**; **`disabled`** → passthrough (no adapter calls); enabled → per-candidate **`ModelPipelineRequestEnvelope`** with deterministic **`request_id`** (`{prefix}-{index}`), **`adapter.run` → `validate_response` → `project`**, merge **only** **`metadata["graphclerk_model_pipeline"]`** into replacement **`EvidenceUnitCandidate`** instances (**no** **`text`** / **`source_fidelity`** mutation; input list and original **`metadata`** dicts untouched). **`ModelPipelineMetadataEnrichmentResult`** carries counts + **`warnings`**. Tests: [`test_phase8_model_pipeline_metadata_enrichment_service.py`](../../backend/tests/test_phase8_model_pipeline_metadata_enrichment_service.py) (fake adapters; **no** network).

### Track D — Slice D6 (completed): ingest merge (`evidence_candidate_enricher` env — Option A)

- **Outcome:** [`backend/app/core/config.py`](../../backend/app/core/config.py) — **`GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_*`** (default **off**; enabled requires **`GRAPHCLERK_MODEL_PIPELINE_ADAPTER=ollama`**, **`GRAPHCLERK_MODEL_PIPELINE_BASE_URL`**, non-empty **`GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL`**). [`artifacts.py`](../../backend/app/api/routes/artifacts.py) — **`build_evidence_enricher_model_pipeline_adapter`**, **`build_evidence_enrichment_service`** composes **`ModelPipelineMetadataEnrichmentService`** when enabled. [`evidence_enrichment_service.py`](../../backend/app/services/evidence_enrichment_service.py) — language enrichment **then** model metadata enrichment; runtime model failure does **not** block ingest. Tests: [`test_phase8_model_pipeline_ingestion_wiring.py`](../../backend/tests/test_phase8_model_pipeline_ingestion_wiring.py), [`test_config.py`](../../backend/tests/test_config.py).

### Track D — Slice D7a (completed): read-only model pipeline operator visibility

- **Outcome:** [`frontend/src/components/ArtifactsExplorer.tsx`](../../frontend/src/components/ArtifactsExplorer.tsx) — Phase **8** operator panel (env + EU vs artifact distinction); expanded evidence detail shows **`metadata_json` (raw)** and a readable **`graphclerk_model_pipeline`** subtree **when** the JSON response includes **`metadata_json`** (current **`GET /evidence-units/{id}`** schema may omit it). Introductory copy in [`frontend/src/components/EvaluationDashboard.tsx`](../../frontend/src/components/EvaluationDashboard.tsx). Docs: onboarding + [`TESTING_RULES.md`](../governance/TESTING_RULES.md), [`KNOWN_GAPS.md`](../status/KNOWN_GAPS.md), decision doc **D7a** note. **No** writable selector.

### Track D — Slice D7b (completed): read-only model pipeline configuration API + UI

- **Outcome:** [`backend/app/api/routes/model_pipeline.py`](../../backend/app/api/routes/model_pipeline.py) — **`GET /model-pipeline/config`** (read-only; **no** secrets; **no** raw base URL; **no** model HTTP). [`backend/app/schemas/model_pipeline_config.py`](../../backend/app/schemas/model_pipeline_config.py) — response builder from **`Settings`** + purpose registry. [`backend/tests/test_phase8_model_pipeline_config_api.py`](../../backend/tests/test_phase8_model_pipeline_config_api.py). [`frontend/src/api/modelPipeline.ts`](../../frontend/src/api/modelPipeline.ts), [`frontend/src/types/modelPipeline.ts`](../../frontend/src/types/modelPipeline.ts); **Evaluation dashboard** config table. Docs: [`TESTING_RULES.md`](../governance/TESTING_RULES.md), [`KNOWN_GAPS.md`](../status/KNOWN_GAPS.md), onboarding pointers, decision doc **D7b** note. **No** **`POST`/`PUT`/`PATCH`** config, **no** persistence, **no** auth.

### Track D — Slice D8 (completed): Phase 8 full-completion audit

- **Outcome:** **[`docs/audits/PHASE_8_FULL_COMPLETION_AUDIT.md`](../audits/PHASE_8_FULL_COMPLETION_AUDIT.md)** — audit result **`pass`** (**2026-05-02**). **`PHASE_8_AUDIT.md`** **not** edited (baseline history). Status alignment: **`PROJECT_STATUS`**, **`PHASE_STATUS`**, **`ROADMAP`**, **`KNOWN_GAPS`**, **`TECHNICAL_DEBT`**, this program, **`README.md`**, **`docs/api/API_OVERVIEW.md`**, onboarding/decision pointers as listed in the audit artifact. **No** backend/frontend behavior change in **D8**.

**Track D** is **complete** for the **agreed Phase 1–8 completion scope** — **D1** through **D8** (incl. **D2.5**) closed. **D7c** / **D3b** remain **optional future** tracks unless reopened.

---

## 8. Track E — `/answer` packet-only synthesis

| Attribute | Detail |
|-----------|--------|
| **Goal** | If approved: **`POST /answer`** (or equivalent) that consumes **only** a **`RetrievalPacket`** (and explicit config such as style), produces a **deterministic answer envelope**, **citations** from packet evidence, **no unsupported claims**, **no DB/FileClerk bypass**, clear behavior when **no evidence**, tests, optional UI viewer. |
| **Current state** | **`POST /answer` is not implemented**; deferred in README and status. |
| **Missing work** | Product decision **in vs outside** “full Phase 1–8 completion”; API design; synthesizer service; citation schema; guardrails against hidden retrieve; tests with stub LLM. |
| **Required design decisions** | Belongs before Phase 9? Answer format; citation reference shape; empty packet UX; whether UI viewer is required or deferred. |
| **Proposed slices** | **E0** Decision + ADR · **E1** Service skeleton + packet-only guard · **E2** LLM adapter (env-gated) · **E3** Citations + tests · **E4** Optional UI |
| **Likely files** | New route module, service, schemas, tests; optional frontend tab. |
| **Forbidden files** | Synthesizer must **not** call `FileClerkService` / DB for “more evidence” ([`ARCHITECTURAL_INVARIANTS.md`](../governance/ARCHITECTURAL_INVARIANTS.md) Invariant 6). |
| **Tests required** | Contract tests: reject requests with only a query id that could fetch hidden evidence; prove packet-only input. |
| **Docs required** | Security + RAG integration pattern (“GraphClerk retrieves; your LLM answers elsewhere” vs built-in `/answer`). |
| **Risks** | Users confuse `/answer` with retrieval; prompt injection via packet text. |
| **Dependencies** | **Track B** for meaningful citations on golden path; **Track C/D** for optional context fields in packet. |
| **Acceptance criteria** | Packet-only invariant enforced in code + tests; honest empty-evidence behavior. |

---

## 9. Track F — Onboarding / integration guide

| Attribute | Detail |
|-----------|--------|
| **Goal** | Single **“GraphClerk in your pipeline / RAG stack”** story: ingest → graph → semantic index → **index vectors** → retrieve → logs → context fields → optional model metadata → optional `/answer`; **Docker** quickstart pointers; **production** considerations; **curl** and **Python** examples; **architecture** diagram; **failure-mode** guide. |
| **Current state** | README, `docs/api/API_OVERVIEW.md`, demo corpus doc, release checklist — plus **`docs/onboarding/`** **Track F (F1–F5)** complete: entry, pipeline guide, minimal feed, architecture, troubleshooting, **examples cookbook** ([`README.md`](../onboarding/README.md), [`GRAPHCLERK_PIPELINE_GUIDE.md`](../onboarding/GRAPHCLERK_PIPELINE_GUIDE.md), [`FEED_CONTENT_MINIMAL_GUIDE.md`](../onboarding/FEED_CONTENT_MINIMAL_GUIDE.md), [`GRAPHCLERK_ARCHITECTURE.md`](../onboarding/GRAPHCLERK_ARCHITECTURE.md), [`TROUBLESHOOTING_AND_OPERATIONS.md`](../onboarding/TROUBLESHOOTING_AND_OPERATIONS.md), [`EXAMPLES_COOKBOOK.md`](../onboarding/EXAMPLES_COOKBOOK.md)). **Onboarding documentation baseline** for Phases **1–8** is delivered; **production deployment** deep-dives, **OCR/ASR/video** operator guides, and **`/answer`** docs remain **future** program/status work — not claimed here. |
| **Missing work** | Keep onboarding **honest** vs code (Status Agent drift checks); optional future slices **outside** F1–F5 (e.g. production runbook, multipart cookbook) if later approved. |
| **Required design decisions** | Doc location naming; how much lives in README vs dedicated guides; diagram tooling (Mermaid vs static). |
| **Proposed slices** | **F1–F5** (**implemented**) — skeleton, minimal feed, architecture + Mermaid, troubleshooting + Qdrant ops, examples cookbook |
| **Likely files** | New files under `docs/onboarding/` or `docs/integration/` only (docs). |
| **Forbidden files** | Do not overclaim features still partial. |
| **Tests required** | None for prose; optional CI link-check later. |
| **Docs required** | This track *is* docs. |
| **Risks** | Docs drift from code; mitigate by Status Agent updates per slice. |
| **Dependencies** | Parallel with **B1** for accurate indexing story. |
| **Acceptance criteria** | New contributor can run golden path + understand failures without reading source. **F1–F5** onboarding doc set satisfies the **Track F** documentation baseline for Phases **1–8** (not production SRE completeness). |

### Track F — Slice F1 (implemented): onboarding skeleton

- **Entry:** [`docs/onboarding/README.md`](../onboarding/README.md) — what GraphClerk is / is not, start-here flow, links to API overview, demo corpus, release checklist, testing rules, completion program; **Phase 9 not started**; **Track F F1–F5** complete.
- **Pipeline guide:** [`docs/onboarding/GRAPHCLERK_PIPELINE_GUIDE.md`](../onboarding/GRAPHCLERK_PIPELINE_GUIDE.md) — audience, at-a-glance flow, core concepts (**Artifact** … **`graphclerk_model_pipeline`**), explicit non-features, **10-step** baseline flow, minimal vs rich, manual backfill pointers + Qdrant dimension doc links, UI map, failure modes (short table + link to **F4**), integration patterns, security/honesty rules; links to **F3** architecture, **F4** troubleshooting, **F5** examples cookbook.
- **Discovery:** root [`README.md`](../../README.md) points integrators at `docs/onboarding/README.md` (short pointer).

### Track F — Slice F2 (implemented): minimal feed-content guide

- **Guide:** [`docs/onboarding/FEED_CONTENT_MINIMAL_GUIDE.md`](../onboarding/FEED_CONTENT_MINIMAL_GUIDE.md) — **PowerShell / `Invoke-RestMethod`** templates for **Steps 1–11** (stack → text artifact → evidence → graph node → evidence link → semantic index → **`scripts/backfill_semantic_indexes.py`** → **`POST /retrieve`** → retrieval logs → UI). Field names aligned to route schemas; examples labeled **template** (not executed in-doc). States **`POST /answer`** absent, no auto-vector backfill, **8-d** deterministic backfill, **minimal vs rich** retrieve expectations, **`not_configured`** vs optional **`deterministic_fake`** for query embeddings.
- **Cross-links:** onboarding `README` + pipeline guide point here; root `README` may mention this file beside the onboarding index.

### Track F — Slice F3 (implemented): architecture overview + pipeline narrative

- **Doc:** [`docs/onboarding/GRAPHCLERK_ARCHITECTURE.md`](../onboarding/GRAPHCLERK_ARCHITECTURE.md) — legend **`[current]`** / **`[manual/operator]`** / **`[future / not implemented]`**; **Mermaid** component + data-flow diagrams; Postgres vs Qdrant; API and UI surface tables; manual operator steps with links; optional/future branches without promises; explicit **non-claims** list; relates to pipeline + minimal feed guides.
- **Pipeline guide** links to this file at “pipeline at a glance” and replaces the old “architecture diagram” stub with a pointer to **F3**.

### Track F — Slice F4 (implemented): troubleshooting and operations

- **Doc:** [`docs/onboarding/TROUBLESHOOTING_AND_OPERATIONS.md`](../onboarding/TROUBLESHOOTING_AND_OPERATIONS.md) — quick triage table; **expected vs bug**; environment checklist (Docker ports, env vars, when to unset `GRAPHCLERK_*`); **Qdrant** vs Postgres; dev-only collection reset guidance (**no** casual production deletes); semantic index lifecycle; backfill failures; File Clerk / retrieve symptoms; **retrieval log** expectations; **HTTP** guide (400/404/409/422/500/502/503 + frontend connectivity); modality honesty; **`deterministic_fake`** guards; **runbooks**; **what not to do**; links. **Does not** claim auto-index, **`/answer`**, OCR/ASR/video, production inference, Phase **9**, or guaranteed logs.

### Track F — Slice F5 (implemented): examples cookbook

- **Doc:** [`docs/onboarding/EXAMPLES_COOKBOOK.md`](../onboarding/EXAMPLES_COOKBOOK.md) — **PowerShell** (`Invoke-RestMethod`, `ConvertTo-Json` **-Depth** for `entry_node_ids`), **curl**, **Python** `urllib.request` + optional `requests` note; Example set **D** backfill CLI; **E** retrieve + logs; **VERIFIED LOCALLY** for **`GET /health`** and **`GET /version`** only (`http://localhost:8010` in slice); all other HTTP paths **TEMPLATE — NOT EXECUTED IN THIS SLICE**; minimal vs rich table; cleanup links; no invented request bodies (schemas: `ArtifactCreateInlineRequest`, graph create/link, `SemanticIndexCreateRequest`, `RetrieveRequest`).

### Track F — documentation baseline (F1–F5)

For Phases **1–8** program purposes, **Track F** onboarding deliverables (**F1** skeleton, **F2** minimal feed, **F3** architecture, **F4** troubleshooting, **F5** examples cookbook) are **implemented**. This is **documentation baseline completeness**, **not** “production enterprise runbooks,” “OCR/ASR/video operator manuals,” or **`POST /answer`** documentation — those remain explicitly **out of scope** or **future** elsewhere in the program.

---

## 10. Track G — UI / observability completion

| Attribute | Detail |
|-----------|--------|
| **Goal** | UI reflects **truthful** product state: multimodal EUs and OCR/ASR/caption metadata; **`vector_status`** and indexing/backfill status (when built); **Phase 7** `language_context` / `actor_context` clearly labeled as **context**; **Phase 8** model metadata + validation issues; retrieval logs; optional answer viewer; frontend **build + tests** when harness lands. |
| **Current state** | Phase **6** UI **`pass_with_notes`**; much detail visible via **raw JSON**; frontend types may **lag** backend packet fields. |
| **Missing work** | Typed packet models; readable sections; multimodal-specific viewers; indexing state; optional Playwright/Vitest. |
| **Required design decisions** | Progressive disclosure vs new tabs; when to add E2E cost in CI. |
| **Proposed slices** | **G1** Packet types sync · **G2** Context panels + honest copy · **G3** Multimodal EU display · **G4** Vector/indexing status · **G5** Phase 8 metadata surfaces · **G6** Test harness |
| **Likely files** | `frontend/src/types/retrievalPacket.ts`, components, API clients. |
| **Forbidden files** | No “answer quality” metrics disguised as ground truth; no claim OCR/ASR exists until **Track A** ships. |
| **Tests required** | `npm run build`; later Vitest/Playwright per policy. |
| **Docs required** | UI screenshots in onboarding optional; evaluation tab copy per `docs/evaluation/EVALUATION_METHOD.md`. |
| **Risks** | UX implies hidden personalization. |
| **Dependencies** | Lands incrementally with **A, B, C, D, E**. |
| **Acceptance criteria** | UI matches backend; build passes; no overclaim. |

---

## 11. Track H — Final Phase 1–8 completion audit

| Attribute | Detail |
|-----------|--------|
| **Goal** | New **audit artifact** (filename per [`AUDIT_RULES.md`](../governance/AUDIT_RULES.md)) recording **full completion** evidence across architecture, contract, test, dependency, security, retrieval quality, multimodal, status honesty — without deleting prior audits. |
| **Current state** | Per-phase audits **`pass_with_notes`** for baselines; **no** single “Phase 1–8 full completion” audit yet. |
| **Missing work** | Checklist; command transcripts; demo recording or script; explicit list of **deferred outside 1–8** items. |
| **Required design decisions** | `pass` vs `pass_with_notes` for full program (recommend: **`pass_with_notes`** if any intentional deferrals remain, with explicit **outside 1–8** table). |
| **Proposed slices** | **H1** Checklist draft · **H2** Evidence collection · **H3** Audit write + status sync |
| **Likely files** | **`docs/audits/*`** — only when executing this track under **Audit Agent** charter (forbidden in *this* doc-only commit). |
| **Forbidden files** | Do not erase or rewrite old audit verdicts. |
| **Tests required** | Full backend suite; integration where claimed; `npm run build` if UI in scope; documented manual demo. |
| **Docs required** | `docs/status/*` + README terminology: **baseline** vs **full completion**. |
| **Risks** | Premature `pass`. |
| **Dependencies** | All chosen tracks complete or explicitly deferred. |
| **Acceptance criteria** | Audit references tests and docs; status honesty updated; deferrals explicit. |

---

## 12. Recommended implementation order

1. **Track B** — Unblocks **non-empty semantic evidence** on the documented path; reduces false “GraphClerk broken” reports.  
2. **Track F** (onboarding docs; **F1–F5** shipped) **in parallel** — Pipeline overview, minimal feed, architecture, troubleshooting, and examples cookbook while B lands.  
3. **Track C** (decisions + policy early) — Avoid rework on language metadata when **Track A** adds OCR/ASR text.  
4. **Track A** — Largest modality surface; benefits from B demo path and C policy.  
5. **Track D** — After EU/candidate metadata shapes stabilize.  
6. **Track E** — Only after **B** yields reliable packets and guardrails are clear (**C/D** as needed).  
7. **Track G** — Incrementally per backend feature slices.  
8. **Track H** — Last.

**Adjustment:** Insert **B0** “embedding provider decision” if **B** is blocked on production embeddings (**requires dependency research**).

---

## 13. First slice recommendation

**Track B — Slice B1:** **Documented minimal indexed demo path** + **operator manual backfill** (CLI or API sequence) proving `pending → indexed | failed` with **explicit** Qdrant errors, plus automated coverage (integration or high-fidelity mock) that **`POST /retrieve`** returns **non-empty** evidence when the semantic index is **indexed** and the question matches.

**Track B Slice B5 (shipped):** gated httpx test `test_phase1_8_track_b_full_stack_retrieve.py` — run when `RUN_INTEGRATION_TESTS=1`, `DATABASE_URL`, `QDRANT_URL`, `GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER=deterministic_fake`, and `APP_ENV` ≠ `prod` are set (details in [`TESTING_RULES.md`](../governance/TESTING_RULES.md)).

---

## 14. What not to do yet

- Do **not** implement **Phase 9** or claim it started.  
- Do **not** treat **`pass_with_notes`** as “wrong” — it **accepted the baseline**.  
- Do **not** add **silent fallbacks** (see repository `.cursor/rules/governance.md`).  
- Do **not** claim **OCR, ASR, video, production inference, `/answer`, or vector backfill** exist before they ship.  
- Do **not** delete or rewrite historical **audit** artifacts to match aspirations.

---

## 15. Open decisions

Use **DECIDE** (product owner), **RESEARCH** (spike/docs), **DEFER** (explicitly outside Phases 1–8).

| # | Topic | Track | Tag |
|---|--------|-------|-----|
| 1 | Video fully in Phase 5 vs deferred outside 1–8 | A | DECIDE |
| 2 | First OCR engine (Tesseract, Paddle, cloud, …) | A | RESEARCH |
| 3 | First ASR engine (whisper.cpp, cloud, …) | A | RESEARCH |
| 4 | Visual summaries as EUs vs metadata-only | A | DECIDE |
| 5 | `source_fidelity` for OCR/ASR/caption | A | DECIDE |
| 6 | Image region / audio timestamp / video frame representation | A | DECIDE |
| 7 | Optional dependency policy (extras vs core) | A | DECIDE |
| 8 | HTTP 400 vs 503 vs 500 matrix for extraction failures | A | DECIDE |
| 9 | Auto-enqueue vector indexing on SI create | B | DECIDE |
| 10 | Manual backfill before automation | B | DECIDE |
| 11 | Sync vs async vs operator-triggered indexing | B | DECIDE |
| 12 | Qdrant failure representation to clients/operators | B | DECIDE |
| 13 | Production embedding provider | B | RESEARCH |
| 14 | Production language detection vs explicit no-detector | C | DECIDE |
| 15 | Where detection runs (ingest / enrich / retrieve) | C | DECIDE |
| 16 | Persist artifact language aggregation automatically | C | DECIDE |
| 17 | `actor_context` recording-only forever vs deterministic boosting (7I) | C | DECIDE |
| 18 | Translation / query translation in Phase 7 vs DEFER | C | DECIDE |
| 19 | UI patterns that avoid “context = evidence” | C/G | DECIDE |
| 20 | Ollama first vs vLLM/OpenAI-compatible first | D | RESEARCH |
| 21 | Env-only enablement for adapters (recommended yes) | D | DECIDE |
| 22 | Safest first model **role** | D | DECIDE |
| 23 | Merge metadata before vs after validation | D | DECIDE |
| 24 | Model outputs may create candidates? (recommend: no new evidence text) | D | DECIDE |
| 25 | Include `/answer` in “full 1–8” vs separate track | E | DECIDE |
| 26 | Answer envelope + citation schema | E | DECIDE |
| 27 | Onboarding doc structure and diagram format | F | DECIDE |

---

## 16. Risks

- **Scope creep** (video, translation, 7I, registry UI).  
- **Dependency research** lag blocking A/B/D.  
- **CI truth gap** (Alembic chain, Qdrant integration) per [`TECHNICAL_DEBT.md`](../status/TECHNICAL_DEBT.md).  
- **UI/type drift** causing false confidence.  
- **Security**: outbound HTTP for models/OCR/ASR cloud providers.  
- **Operator confusion** between `pending` and broken retrieval.

---

## 17. Testing strategy

- **Backend default:** `cd backend && python -m pytest` (Testing Agent charter).  
- **Integration:** `RUN_INTEGRATION_TESTS=1` + `DATABASE_URL` / `QDRANT_URL` per [`TESTING_RULES.md`](../governance/TESTING_RULES.md) when touching DB/Qdrant paths.  
- **Track-specific:** Phase 5 HTTP matrix; Phase 7 non-boost / boost tests; Phase 8 HTTP mocks; FileClerk retrieve golden paths after **B**.  
- **Frontend:** `npm run build`; add Vitest/Playwright when **Track G** approves harness.  
- **Manual:** Docker quickstart + demo checklist (documented in **Track F**).  
- **Honesty:** Do not mark status **`tested`** without running relevant suites ([`STATUS_REPORTING.md`](../governance/STATUS_REPORTING.md)).

---

## 18. Documentation / onboarding strategy

- **Track F** is the **living** integration spine; README links into it.  
- Each implementation slice updates **`docs/status/*`** and README **in the same delivery** when behavior or contracts change (**Status Documentation Agent**).  
- Use **STATUS_REPORTING** categories; distinguish **partial** until **Track H** closes.  
- **Project Manager Agent** keeps **`.cursor/plans/*`** working plans aligned with this program (see `.cursor/rules/graphclerk-subagent-project-manager.mdc`).

---

## 19. Final audit strategy

- Execute under **Audit Agent** + [`AUDIT_RULES.md`](../governance/AUDIT_RULES.md): architecture, contract, test, dependency, security, retrieval quality, multimodal extraction, status honesty.  
- Produce a **new** audit file (do not replace `PHASE_5_AUDIT` etc.).  
- Tie each **pass** claim to **commands, paths, and doc sections**.  
- If anything remains intentionally incomplete, classify as **`pass_with_notes`** with an **“Outside Phases 1–8”** table.  
- Update **`docs/status/PHASE_STATUS.md`** to introduce terminology such as **“full completion (program)”** vs **“baseline audited”** — only after evidence exists.

---

## Appendix — Sub-agent routing (implementation phase)

| Work type | Sub-agent | Primary handoff |
|-----------|-----------|-----------------|
| Tests | Testing | Required |
| Status/README | Status Documentation | Required when behavior/claims change |
| New audit artifact | Audit | Required |
| `.cursor/plans` milestones | Project Manager | Required |
| Readiness review | Code Quality | Required (read-only findings) |
| Commits/push | Git | Required |

---

## References (read-only pointers)

- Governance: [`PROJECT_PRINCIPLES.md`](../governance/PROJECT_PRINCIPLES.md), [`ARCHITECTURAL_INVARIANTS.md`](../governance/ARCHITECTURAL_INVARIANTS.md), [`CURSOR_RULES.md`](../governance/CURSOR_RULES.md), [`AGENT_ROLES.md`](../governance/AGENT_ROLES.md), [`STATUS_REPORTING.md`](../governance/STATUS_REPORTING.md), [`AUDIT_RULES.md`](../governance/AUDIT_RULES.md)  
- Status: [`PROJECT_STATUS.md`](../status/PROJECT_STATUS.md), [`PHASE_STATUS.md`](../status/PHASE_STATUS.md), [`ROADMAP.md`](../status/ROADMAP.md), [`KNOWN_GAPS.md`](../status/KNOWN_GAPS.md), [`TECHNICAL_DEBT.md`](../status/TECHNICAL_DEBT.md)  
- Baseline audits: [`PHASE_5_AUDIT.md`](../audits/PHASE_5_AUDIT.md) … [`PHASE_8_AUDIT.md`](../audits/PHASE_8_AUDIT.md)  
- Phase contracts: [`graph_clerk_phase_5_multimodal_ingestion.md`](../phases/graph_clerk_phase_5_multimodal_ingestion.md), [`graph_clerk_phase_7_context_intelligence.md`](../phases/graph_clerk_phase_7_context_intelligence.md), [`graph_clerk_phase_8_specialized_model_pipeline.md`](../phases/graph_clerk_phase_8_specialized_model_pipeline.md)
