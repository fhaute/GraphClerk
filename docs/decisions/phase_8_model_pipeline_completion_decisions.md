# Phase 8 — Model Pipeline Completion Decisions (Phase 1–8 Completion Program)

## Metadata / status

| Field | Value |
|-------|--------|
| **Completion program** | Phase 1–8 Completion Program — **Track D Slice D1** |
| **Document type** | **Design / decision record only** — no implementation in this slice |
| **Code changes** | **None** — backend, frontend, scripts, dependencies unchanged |
| **Phase 9** | **Not started** |
| **Prior audit** | [`docs/audits/PHASE_8_AUDIT.md`](../audits/PHASE_8_AUDIT.md) remains **valid baseline history** (`pass_with_notes`, 2026-05-03); **not edited** by D1 |
| **Target** | Decisions for **full intended Phase 8 completion** (real HTTP adapter path, registry/settings, merge into ingestion behind config) **before** implementation slices **D2+** |
| **Parent context** | Phase doc north-star: [`docs/phases/graph_clerk_phase_8_specialized_model_pipeline.md`](../phases/graph_clerk_phase_8_specialized_model_pipeline.md) (**do not edit** in D1) |

---

## Current Phase 8 baseline (shipped honesty)

The repository **already** contains (per **`PHASE_8_AUDIT.md`** and code):

- **Contracts** — `ModelPipelineRole`, `ModelPipelineTask` / `ModelPipelineResult`, request/response envelopes (`model_pipeline_contracts.py`).
- **Adapters** — `ModelPipelineAdapter` protocol; **`NotConfiguredModelPipelineAdapter`** (explicit unavailable semantics); **`DeterministicTestModelPipelineAdapter`** (**tests-only**).
- **Output validation** — `ModelPipelineOutputValidationService` (semantic bounds, no FileClerk/retrieval).
- **Projection** — `ModelPipelineCandidateMetadataProjectionService` → **`metadata_json["graphclerk_model_pipeline"]`** only.
- **Evaluation fixtures** — deterministic builders + tests.
- **Design** — Slice **8G** local inference narrative (**design-only** in working plan).
- **Audit / status** — baseline **`pass_with_notes`**; **no** production HTTP client, **no** registry, **no** real outbound model calls on default paths, **no** ingestion/enrichment merge of model metadata, **no** **`POST /answer`**.

This decision record **does not** claim any of the missing items are implemented.

---

## Why the baseline is not “full completion”

Full Phase 8 completion for the **agreed Phase 1–8 program** (see **Acceptance criteria** below) requires:

- A **real**, **explicitly configured** HTTP inference adapter (at least one).
- **Settings + static registry** wiring with **`not_configured`** default preserved.
- **Timeout and structured error** semantics covered by tests.
- **Validate → project → (optional) merge** path with **no evidence mutation**.
- **Operator observability** and **honest docs/status** through a **full-completion** audit when implementation is done.

The **baseline** deliberately stopped at contracts, validation, projection, and fixtures.

---

## Decision summary

| # | Topic | Decision |
|---|--------|----------|
| 1 | First real adapter | **Ollama HTTP first** → then **OpenAI-compatible** (vLLM-style) second |
| 2 | Registry | **Static registry** mapping adapter keys → builders (**B**) |
| 3 | Settings | Env-based contract; default **`not_configured`**; **fail loud** if selected adapter misconfigured |
| 4 | Timeouts / errors | Distinct **`unavailable`** (retryable infra) vs **`error`** (contract/HTTP/body); explicit error codes for JSON/schema failures |
| 5 | First role | **`evidence_candidate_enricher`** only, **metadata-only** |
| 6 | Validation | **Always validate before projection**; failed validation → **no** projection/merge |
| 7 | Merge | Existing projection service; **only** `graphclerk_model_pipeline` subtree; **never** `text` / `source_fidelity` / new EU from model text |
| 8 | Ingestion boundary | **Separate orchestration service** (preferred **B**) after language enrichment; ordering fixed (see §8) |
| 9 | Observability | Metadata visible where EU/artifact UI exists; structured logs; docs for env; **no hidden calls** |
| 10 | `/answer` | **Track E only** — not Track D |
| 11 | Security | Untrusted content in / untrusted metadata out; validate; no AC changes; no retrieval expansion by model by default |

---

## Decision 1 — First real adapter target

**Options considered**

| Option | Assessment |
|--------|------------|
| **A. Ollama HTTP first** | **Preferred** — local-first, aligns with GraphClerk posture, simpler operator story for single-host dev |
| **B. vLLM / OpenAI-compatible HTTP first** | **Second wave** — common in serving stacks; same envelope patterns as A after registry exists |
| **C. Both in first wave** | **Rejected for D2–D4** — too broad; doubles HTTP edge cases before contracts are proven |
| **D. NotConfigured only through Phase 1–8** | **Rejected** — does not satisfy **full Phase 8 completion** goal of the Completion Program |
| **E. In-process transformers / llama.cpp** | **Rejected for first wave** — heavy operational + dependency burden in core repo |

**Decision:** **A first, then B.**  
Implement **Ollama HTTP** adapter + mocked tests first; add **OpenAI-compatible** adapter after registry/settings patterns stabilize (e.g. **D3b** / **D4b**-style follow-on slice).

---

## Decision 2 — Adapter registry shape

**Options considered**

| Option | Assessment |
|--------|------------|
| **A. Settings-selected factory only** | Too implicit; harder to test matrix of adapters |
| **B. Explicit static registry** | **Chosen** — small map **key → builder**; easy to test; no magic |
| **C. Dynamic plugin discovery** | **Out of scope** for Phase 1–8 |
| **D. Per-task routing registry** | **Deferred** — unnecessary until multiple adapters run concurrently |

**Decision:** **B — static registry**, e.g. keys:

- `not_configured` (default)
- `deterministic_test` (tests-only registration; not for production paths)
- `ollama`
- `openai_compatible`

---

## Decision 3 — Settings / environment contract

**Proposed settings (names subject to implementation slice; semantics fixed here)**

| Variable | Purpose |
|----------|---------|
| `GRAPHCLERK_MODEL_PIPELINE_ADAPTER` | `not_configured` \| `ollama` \| `openai_compatible` (default **`not_configured`**) |
| `GRAPHCLERK_MODEL_PIPELINE_BASE_URL` | HTTP base URL for chosen adapter (e.g. `http://localhost:11434` for Ollama) |
| `GRAPHCLERK_MODEL_PIPELINE_MODEL` | Model id / name for the provider |
| `GRAPHCLERK_MODEL_PIPELINE_TIMEOUT_SECONDS` | Client-side timeout (required bounds TBD in implementation; must be explicit) |
| `GRAPHCLERK_MODEL_PIPELINE_API_KEY` | Optional — OpenAI-compatible gateways or proxied local services |

**Avoid** a redundant `GRAPHCLERK_MODEL_PIPELINE_ENABLED` if **`adapter=not_configured`** is the single default-off switch.

**Fail loud:** If **`adapter` ≠ `not_configured`** and required URL/model/timeout cannot be parsed or are inconsistent, **startup or first-use failure** (implementation choice: prefer **fail at adapter build** time with clear error — **no** silent downgrade to `NotConfigured`).

---

## Decision 4 — Timeout and error semantics

**Categories**

| Situation | `ModelPipelineStatus` | `ModelPipelineError` / notes |
|-----------|----------------------|------------------------------|
| DNS / connection refused / TLS handshake failure | **`unavailable`** | `retryable=true` where applicable; code e.g. `model_pipeline_connection_failed` |
| Request **timeout** (client) | **`unavailable`** | `retryable=true`; code `model_pipeline_timeout` |
| HTTP **non-2xx** | **`error`** | `retryable=false` unless policy explicitly maps 429/503 (implementation may treat limited cases as `unavailable` + retryable — document in implementation) |
| **Invalid JSON** body | **`error`** | `retryable=false`; code **`model_pipeline_invalid_json`** |
| JSON parses but **schema / envelope mismatch** | **`error`** | code **`model_pipeline_schema_mismatch`** |
| Model output **fails `ModelPipelineOutputValidationService`** | Treat adapter response as **failed downstream use**: **no projection**, **no merge**; envelope may still be `success` from raw HTTP perspective — implementation must normalize to **`error`** or a dedicated validation-failed path **before** projection (preferred: **`error`** + `model_pipeline_validation_failed`) |

**Rule:** **Projection and merge never run** unless validation passes.

---

## Decision 5 — Model task roles allowed for first implementation

**Roles in contracts:** `artifact_classifier`, `evidence_candidate_enricher`, `routing_hint_generator`, `extraction_helper`.

**Decision:** First product slice enables **`evidence_candidate_enricher`** **only**, **metadata-only** outputs, on **existing** candidates. **No** new candidate creation from model-generated body text in Track D.

**Rationale:** Lowest retrieval-influence risk vs `routing_hint_generator`; aligns with “metadata on existing candidates only” Completion Program language.

**Deferred:** `routing_hint_generator` (could affect routing perception), `artifact_classifier`, `extraction_helper` until separate approval + tests.

---

## Decision 6 — Validation-before-projection rule

**Affirmed:**

1. Adapter returns raw HTTP outcome → parse into typed envelope **or** structured **`ModelPipelineError`**.
2. **`ModelPipelineOutputValidationService`** runs on any path that could lead to projection.
3. **Projection** (`ModelPipelineCandidateMetadataProjectionService`) runs **only after** validation **success**.
4. **Failed validation** → **no** merge; EU/candidate **`text`** and **`source_fidelity`** unchanged.
5. **Model output never becomes evidence** — no **`is_evidence=true`**, no forcing **`source_fidelity=verbatim`** from model modules (existing validation boundaries reinforced in implementation/tests).

---

## Decision 7 — Candidate metadata projection and merge policy

**Decision:**

- Reuse **`ModelPipelineCandidateMetadataProjectionService`**.
- Write **only** under **`metadata_json["graphclerk_model_pipeline"]`** (existing contract).
- **Preserve** unrelated candidate metadata keys.
- **Never** write **`candidate.text`** or **`source_fidelity`** from model pipeline code paths.
- **Never** create **`EvidenceUnit`** rows from model free text in Track D.
- On **`unavailable`**, **`error`**, or validation failure → **no metadata merge** by default (honest no-op for enrichment step).

---

## Decision 8 — Ingestion / enrichment integration boundary

**Options**

| Option | Assessment |
|--------|------------|
| **A. Inside `EvidenceEnrichmentService`** | Possible but risks mixing Phase 7 language logic with Phase 8 HTTP |
| **B. Separate orchestration service** | **Preferred** — e.g. `ModelPipelineMetadataEnrichmentService` (name TBD) called from ingestion orchestration |
| **C. Ingestion calls adapter directly** | **Rejected** — duplicates validation/projection ordering |
| **D. Offline-only** | **Rejected** for full completion |

**Decision:** **B (preferred).** Ingestion pipeline **orchestration** order (conceptual):

1. Parse / extract → candidates  
2. **Language detection** enrichment (Phase 7)  
3. **Model pipeline metadata** step (Phase 8) — call adapter → validate → project onto candidate metadata  
4. **`EvidenceUnitService.create_from_candidates`**  
5. Artifact-level aggregation (Phase 7 language aggregation, etc.)

**D1 does not implement** this wiring — only fixes the boundary for later slices.

---

## Decision 9 — Observability / operator visibility

**Decision:**

- **`graphclerk_model_pipeline`** subtree visible on **EvidenceUnit** / artifact surfaces where JSON/metadata is already shown (extend minimally in later slice — **D7**).
- **Structured logs** for adapter key, timeout, and **non-sensitive** error codes (no raw prompts/secrets).
- **Operator docs** list env vars, default-off behavior, and **503/behavior** when adapter misconfigured (if surfaced via HTTP).
- **Tests** prove **default `not_configured`** → **no network** model calls.

---

## Decision 10 — `/answer` separation

**Decision:**

- **`POST /answer`** is **Track E**, **not** Track D.
- Track D **metadata enrichment** must **not** be framed or implemented as answer synthesis.
- Track E may **reuse** HTTP adapter **types** only via **explicit** future design — not assumed in D slices.
- **No** answer route in Track D implementation slices.

---

## Decision 11 — Security / prompt-injection boundary

**Decision (non-negotiable for implementation):**

- Model inputs include **untrusted** artifact/candidate text → treat model output as **untrusted metadata**.
- **Validate before projection** always.
- **No evidence creation** from model text; **no source truth** claims in projected subtrees (existing contract forbids top-level truth claims in task/result fields — preserve).
- **No access-control** changes from model pipeline.
- **No retrieval expansion** or FileClerk mutation driven by model output **by default**.
- **Outbound HTTP** only when adapter is **explicitly** selected and configured — **no** accidental calls in default install.

---

## Implementation slice proposal (Track D after D1)

| Slice | Content |
|-------|---------|
| **D2** | Settings model + **static registry** + **`NotConfigured`** default preserved; unit tests |
| **D3** | **Ollama HTTP** adapter + **mocked** HTTP tests |
| **D4** | Timeout, malformed JSON, schema mismatch, non-2xx tests; validation-blocks-projection tests |
| **D5** | **`ModelPipelineMetadataEnrichmentService`** (name TBD) — orchestrates adapter → validate → project; **no** ingestion route wiring yet |
| **D6** | Wire enrichment step into **text + multimodal** ingest behind explicit config only |
| **D7** | Operator docs + minimal UI/raw JSON visibility notes |
| **D8** | **Phase 8 full-completion audit** (new artifact when ready — **not** in D1) |
| **D3b / D4b** (optional) | **OpenAI-compatible** adapter + mocks **after** Ollama path proves registry |

*(Renumber if program table is updated — logical order matters more than numeric labels.)*

---

## Acceptance criteria (full Phase 8 completion — future)

- Default install: **no** model HTTP calls.
- With **`ollama`** (or agreed adapter) configured: full **typed envelope** path exercised in tests (mocked HTTP acceptable for CI).
- **Timeout / error** semantics covered by tests.
- **Validation** blocks unsafe or invalid output from affecting candidates.
- **Projection** writes **only** `graphclerk_model_pipeline` metadata.
- **Ingestion merge** works **only** when explicitly configured.
- **No** FileClerk / retrieval imports in model pipeline modules (invariant + AST/import guard in CI optional).
- **No** `/answer`.
- **Docs/status** honest; **full-completion audit** can record **`pass`** for agreed Phase 1–8 Phase 8 scope (separate from **`PHASE_8_AUDIT.md`** baseline).

---

## Testing strategy

- Unit tests: settings parse, registry dispatch, default **`not_configured`**.
- Mocked HTTP: Ollama-shaped responses; timeouts via mock transport.
- Malformed JSON / wrong schema → **`model_pipeline_invalid_json`** / **`model_pipeline_schema_mismatch`**.
- Validation failure → **no** projection / **no** merge.
- Enrichment merge tests (post-D6): only metadata subtree changes.
- **Optional** gated integration smoke with real local Ollama — **skip** by default in CI.

---

## Risks

- **Accidental default-on** model calls → mitigate with explicit adapter enum + tests.
- **Prompt injection** via corpus text → output treated as metadata only; validate; never evidence.
- **Output mistaken for evidence** → docs + invariant tests.
- **Network flakiness** → `unavailable` + retryable semantics; operators tune timeout.
- **Long timeouts** blocking ingest → configurable timeout; consider async/worker **outside** D scope unless approved later.
- **Privacy / outbound data** → operator controls BASE_URL; document data leaves boundary when adapter runs.
- **Confusion with `/answer`** → explicit Track E separation in docs.
- **Ingest performance** → model step adds latency; optional **disable** by default via **`not_configured`**.

---

## Open questions (non-blocking for D1)

- Exact **Ollama** HTTP path and request JSON shape (implementation reads vendor docs; pin in adapter module docstring).
- Whether **429/503** from server map to **`unavailable`** + retryable vs hard **`error`** (finalize in D4).
- **APP_ENV=prod** guardrails for `deterministic_test` adapter (mirror embedding/language patterns).
- UI depth for Phase 8 (**raw JSON** vs small summary panel) — **D7**.

---

## Non-goals

- **`POST /answer`** / answer synthesis (**Track E**).
- **Phase 9**.
- **OCR / ASR / video** completion.
- **Translation**; **actor_context boosting** / Phase **7I**.
- **FileClerk / retrieval ranking** influence from model metadata by default.
- **Model-generated evidence** or EU rows from model text.
- **In-process GPU** / **transformers** / **llama.cpp** in first implementation wave.
- **Dynamic plugin** loading for adapters.

---

## Final recommendation

Proceed with **Track D Slice D2** after this decision record: add **settings + static registry** keeping **`NotConfigured`** as the only default behavior, then **Ollama HTTP adapter** with **mocked** tests, then validation/error hardening, then **metadata-only enrichment service**, then **optional ingestion wiring** and **operator visibility**, closing with a **new full-completion audit** artifact when implementation matches **Acceptance criteria**.

---

## Primary handoff (Audit / Project Manager → parent)

1. **Delivered:** **`phase_8_model_pipeline_completion_decisions.md`** (Track **D1**) — implementation roadmap for Phase 8 **full completion**; **no code**.
2. **Next:** **D2** settings + registry; **no** audit edits; **Phase 9** not started.
3. **Truth:** **No** production adapter, registry, merge, or **`/answer`** is claimed as shipped.
