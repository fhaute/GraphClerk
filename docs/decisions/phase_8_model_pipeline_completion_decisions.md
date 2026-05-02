# Phase 8 — Model Pipeline Completion Decisions (Phase 1–8 Completion Program)

## Metadata / status

| Field | Value |
|-------|--------|
| **Completion program** | Phase 1–8 Completion Program — **Track D** (D1 decisions + **D2.5 design amendment**) |
| **Document type** | **Design / decision record only** — D1 + **D2.5** are **no implementation** slices |
| **Code changes** | **None** in D1/D2.5 — backend, frontend, scripts, dependencies unchanged |
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
- **Projection** — `ModelPipelineCandidateMetadataProjectionService` → **`metadata["graphclerk_model_pipeline"]`** on **`EvidenceUnitCandidate`** when callers attach it (same subtree shape as EU **`metadata_json`** at persistence).
- **Evaluation fixtures** — deterministic builders + tests.
- **Design** — Slice **8G** local inference narrative (**design-only** in working plan).
- **Audit / historical baseline** — **`PHASE_8_AUDIT.md`** remains **`pass_with_notes`** as recorded history. **Default** install: **no** production model HTTP; **`POST /answer`** remains Track **E**.
- **Completion program D6 (optional ingest wiring)** — when **`GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED=true`** with validated companion env, **`POST /artifacts`** may persist **`metadata_json["graphclerk_model_pipeline"]`** on **`EvidenceUnit`** rows after language enrichment — **metadata only**; **no** evidence / **`text`** / **`source_fidelity`** mutation.

This decision record captures **D1**/ **D2.5** design plus implementation notes **D4**–**D6**; remaining Phase 8 program gaps (**D7** UI/selector, **D8** audit, **`openai_compatible`**) stay explicit in **`KNOWN_GAPS.md`**.

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

**D2.5 note:** Interim env vars (including a single **`GRAPHCLERK_MODEL_PIPELINE_MODEL`**) are **not** the final product shape. **Per-purpose** mapping and contracts land in **D4**; **D3** should accept **explicit model context per call** where needed — see **D2.5 Amendment** (Option **B**).

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

## D2.5 Amendment — model purpose registry and frontend selector

### Status

| Field | Value |
|-------|--------|
| **Slice** | Completion Program — **Track D Slice D2.5** |
| **Nature** | **Design amendment only** — **no** backend, **no** frontend, **no** scripts, **no** persistence, **no** Ollama adapter in this slice |
| **Relationship to D2** | **Track D Slice D2** (settings + static adapter registry, default **`not_configured`**) **remains in force**. This amendment adds **product shape** for **per-purpose** model configuration and a **future** operator UI — **not implemented** until later slices. |

### Problem statement

Operators (including local **Ollama**) need to choose **which model** runs for **which GraphClerk task purpose**. Phase 8 must **not** assume a single permanent global model string as the final product shape.

### Truth (honesty — all still accurate after D2.5)

- **No** backend **model purpose registry** (per-role mapping, persisted or not) is **implemented** yet.
- **No** frontend **model selector** UI is **implemented** yet.
- **No** model HTTP calls on default install; **no** **Ollama** adapter shipped yet (pending **D3**).
- **No** **`POST /answer`**; **no** Phase **9**.
- Default adapter remains **`not_configured`**; **no** calls unless explicitly configured.
- **`routing_hint_generator`** stays **disabled** until **separately approved** (retrieval influence risk).
- **Model output remains metadata-only** under agreed projection rules; **model output is not evidence**.

### Terminology

| Term | Definition |
|------|------------|
| **Provider** | Inference transport family — e.g. **Ollama**, **OpenAI-compatible** / **vLLM**-style HTTP. |
| **Model** | Provider-specific model id — e.g. `llama3.1:8b`, `mistral:7b`, `qwen2.5:7b`. |
| **Purpose** | A **GraphClerk** pipeline role that may invoke the model pipeline — aligned with **`ModelPipelineRole`** where possible. |
| **Purpose mapping** | The binding of **provider**, **model**, **timeouts**, **enabled** flags, and related options **per purpose**. |
| **Selector UI** | **Future** frontend (or dev-only) surface to view/edit purpose mappings — **design-only** in D2.5. |

### Purpose keys (initial set)

Aligned with existing contract roles:

| Purpose key | Notes |
|-------------|--------|
| **`evidence_candidate_enricher`** | **First** purpose to enable for product rollout — metadata on **existing** candidates; aligns with **Decision 5**. |
| **`artifact_classifier`** | **Later** — may follow **evidence** enrichment after patterns stabilize. |
| **`extraction_helper`** | **Not** first wave — may require **multimodal/vision** paths and extra deps; enable only when approved. |
| **`routing_hint_generator`** | **Must remain disabled** until **separate approval** — can influence **retrieval** perception and routing. |

### Recommended future configuration shape (illustrative — **not implemented**)

The following JSON is a **strawman** for **documentation and D4 contracts**; **do not** treat it as shipped behavior or a locked schema until **D4** defines types and validation.

```json
{
  "provider": "ollama",
  "base_url": "http://localhost:11434",
  "purposes": {
    "evidence_candidate_enricher": {
      "enabled": true,
      "model": "llama3.1:8b",
      "timeout_seconds": 30
    },
    "artifact_classifier": {
      "enabled": false,
      "model": null
    },
    "extraction_helper": {
      "enabled": false,
      "model": null
    },
    "routing_hint_generator": {
      "enabled": false,
      "model": null
    }
  }
}
```

**Open:** whether **provider** / **base_url** are global with **per-purpose model overrides**, or fully nested per purpose — **D4** should fix this without breaking **Invariant-safe** metadata-only semantics.

### D3 vs purpose registry — option analysis (**recommended: B**)

| Option | Meaning |
|--------|---------|
| **A** | Keep a single **`GRAPHCLERK_MODEL_PIPELINE_MODEL`** for the **first** Ollama adapter; add purpose registry in **D4**. |
| **B** (**recommended**) | **D3** implements the **Ollama HTTP** adapter with an **explicit model (and related params) supplied per call / request context** — not as the eternal product surface. **Product wiring** and **purpose mapping** land in **D4** (contracts + config resolution) **before** ingestion merge (**D6**). **Do not** let **D3**’s minimal env/settings become the **final** product shape by omission. |
| **C** | Introduce full purpose mapping in **D3** immediately. |

**Decision (D2.5):** Adopt **B**. **D3** proves HTTP + mocks + envelope integration; **D4** introduces **backend purpose registry / config contracts** so Fred-style “different model per purpose” is first-class before merge work.

### Future frontend selector UI (design-only)

**Likely placement**

- Prefer a dedicated **Admin → Model pipeline** (or **Settings → Model pipeline**) area **when** an admin shell exists; **or**
- Interim exposure via **Evaluation Dashboard** or similar **if** no admin area exists yet — still **read-only** or **dev-only** until persistence and auth are safe.

**Selector rows (conceptual)**

| Column / control | Purpose |
|------------------|---------|
| **Purpose** | Human-readable label + stable purpose key |
| **Enabled** | Toggle — default **off**; **`routing_hint_generator`** gated by policy/approval |
| **Provider** | e.g. Ollama / OpenAI-compatible |
| **Model** | Name or dropdown |
| **Timeout** | Per-purpose override where supported |
| **Status / last validation** | Last successful config validation or adapter health (future) |

**Model discovery**

- **Future** backend may call Ollama **`/api/tags`** (or equivalent) to populate dropdowns.
- **Until then**, **manual model name entry** is acceptable.

**Warnings (always visible in UI copy when implemented)**

- Model output is **metadata**, **not evidence**.
- **`POST /answer`** is **out of scope** for this UI (Track **E**).
- **Routing hints** default **off** until separately approved.
- **Outbound / local** inference runs **only** for **enabled** purposes with explicit config.

### Future backend API (design-only — **not implemented**)

Proposed **operator/admin** HTTP surface (names may change):

| Method | Path (example) | Role |
|--------|------------------|------|
| `GET` | `/model-pipeline/config` | Read effective config (purposes, provider, flags) |
| `PUT` | `/model-pipeline/config` | Replace or patch config (**dangerous** without guards) |
| `GET` | `/model-pipeline/providers/ollama/models` | Proxy/discover models (e.g. `/api/tags`) |
| `POST` | `/model-pipeline/test` | Dry-run / health check for a purpose or provider |

**Auth / safety**

- Endpoints should be **admin/operator-only** once **auth** exists.
- **Until auth exists:** avoid **writable** **`PUT`** in exposed deployments, or restrict to **dev/local** guards (e.g. **`APP_ENV`**, bind address, feature flag) — **implementation choice in D4/D7**.

### Persistence — evaluation (**Track D immediate path**)

| Option | Assessment |
|--------|------------|
| **A. Env-only** | Fits **Phase 1–8** early slices; limited for multi-purpose mapping size/ergonomics. |
| **B. Local config file** | Good for single-host **Ollama**; needs path + reload semantics. |
| **C. DB-backed settings** | Strong for multi-user admin later; migration + ACL. |
| **D. UI writes → backend** | Requires **B** or **C** (or hybrid) and **auth**. |

**Recommendation (D2.5):** **D3/D4** may remain **env- or file-assisted** while **contracts** define the **canonical purpose mapping shape**. **Selector UI** stays **design-only** or **read-only / dev-only** until a **safe persistence layer** and **auth** story exist.

**Question for Fred:** Is a **writable** UI selector **required** before **auth** and **config persistence** exist? If **yes**, scope **D7b** and persistence (**B/C**) earlier; if **no**, ship **read-only** or **env-only** documentation first.

### Revised Track D slice plan (supersedes prior numeric table below)

| Slice | Content |
|-------|---------|
| **D2** | ✅ Settings + static registry (**implemented**). |
| **D2.5** | ✅ **This amendment** — purpose registry + selector **design** (no code). |
| **D3** | **Ollama HTTP** adapter + **mocked** tests; **no** ingestion wiring; per-call explicit model path (**Option B**); adapter-level timeout/error tests may ship here or immediately after. |
| **D4** | **Backend model purpose registry / config contracts** (types, validation, resolution); may subsume or extend env; HTTP edge-case tests as needed. |
| **D5** | **`ModelPipelineMetadataEnrichmentService`** (name TBD) — adapter → validate → project; **no** ingestion wiring yet. |
| **D6** | Ingestion merge behind **explicit per-purpose** config. |
| **D7** | Frontend / operator **visibility** for model pipeline config and metadata. |
| **D8** | Phase 8 **full-completion audit**. |
| **D3b / D4b** (optional) | **OpenAI-compatible** adapter after Ollama path proves patterns. |

**D7 split (if persistence + admin surface lag):**

- **D7a** — read-only visibility (env-backed or **GET** config).
- **D7b** — writable selector after persistence + **auth** (or approved dev-only writes).

### `/answer` / Track E

Unchanged: **`POST /answer`** remains **Track E**, **outside** Track **D**.

---

## D4 implementation note (backend purpose registry — shipped)

**Track D Slice D4** adds [`backend/app/services/model_pipeline_purpose_registry.py`](../../backend/app/services/model_pipeline_purpose_registry.py): **`ModelPipelinePurposeRegistry`**, **`resolve_model_pipeline_purpose`**, and Phase 1–8 **policy** (only **`evidence_candidate_enricher`** may be **`enabled`** with **`adapter=ollama`**; **`routing_hint_generator`** / **`artifact_classifier`** / **`extraction_helper`** cannot be enabled without **`model_pipeline_purpose_policy_blocked`**). Default enricher template uses **`derived_metadata`**. **No** persistence, **no** **`build_model_pipeline_adapter`** calls, **no** HTTP — **D5/D6** combine resolution with the adapter registry and ingestion.

---

## D5 implementation note (metadata enrichment orchestration — shipped)

**Track D Slice D5** adds [`backend/app/services/model_pipeline_metadata_enrichment_service.py`](../../backend/app/services/model_pipeline_metadata_enrichment_service.py): **`ModelPipelineMetadataEnrichmentService`** with DI-only dependencies (adapter, **`ModelPipelineOutputValidationService`**, **`ModelPipelineCandidateMetadataProjectionService`**). **`enrich_candidates`** uses **`ModelPipelinePurposeResolution`**; **`disabled`** → no adapter/validation/projection; enabled → stable **`request_id`**, **`validate_response` before `project`**, merge **only** the **`graphclerk_model_pipeline`** subtree into **`EvidenceUnitCandidate.metadata`** via **`dataclasses.replace`**. **`ModelPipelineMetadataEnrichmentResult`** reports **`attempted_count` / `projected_count` / `skipped_count` / `failed_count` / `warnings`** for integration (**D6**). **No** global settings reads inside the service; **no** ingestion / enrichment / FileClerk / retrieval imports.

---

## D6 implementation note (ingest merge — Option A env — shipped)

**Track D Slice D6** wires **`ModelPipelineMetadataEnrichmentService`** into **`POST /artifacts`** via **[`build_evidence_enrichment_service`](../../backend/app/api/routes/artifacts.py)** when **`GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED=true`**. **[`Settings`](../../backend/app/core/config.py)** validates: **`GRAPHCLERK_MODEL_PIPELINE_ADAPTER=ollama`**, non-empty **`GRAPHCLERK_MODEL_PIPELINE_BASE_URL`**, non-empty **`GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL`**, optional purpose timeout in **`(0, 300]`**. **[`EvidenceEnrichmentService`](../../backend/app/services/evidence_enrichment_service.py)** applies language enrichment **then** model enrichment (same order for text and multimodal). **[`build_evidence_enricher_model_pipeline_adapter`](../../backend/app/api/routes/artifacts.py)** constructs **`OllamaModelPipelineAdapter`** with **purpose** model + resolved timeout (tests monkeypatch this hook). Runtime **`NotConfigured`** / validation failure paths leave candidates without **`graphclerk_model_pipeline`** but **do not** fail ingestion. **No** **`/answer`**, **no** retrieval/FileClerk changes, **no** **`openai_compatible`** adapter.

---

## Implementation slice proposal (Track D — historical reference)

The **authoritative** slice order is the **D2.5 “Revised Track D slice plan”** table above. The following **older** table is **superseded** for numbering after **D2.5**:

| Slice | Content (superseded labels) |
|-------|----------------------------|
| **D2** | Settings model + **static registry** + **`NotConfigured`** default preserved; unit tests — **done** |
| *(prior D3–D7)* | See revised plan: **D3** Ollama; **D4** purpose contracts; **D5** enrichment orchestration; **D6** ingest merge; **D7** UI/ops; **D8** audit |

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
- Whether **429/503** from server map to **`unavailable`** + retryable vs hard **`error`** (finalize in D3/D4 adapter work).
- **APP_ENV=prod** guardrails for `deterministic_test` adapter (mirror embedding/language patterns).
- UI depth for Phase 8 (**raw JSON** vs small summary panel) — **D7**.
- **Fred (D2.5):** Is a **writable** UI selector **required** before **auth** and **config persistence** exist? (See **D2.5** persistence section.)
- **D4:** Global **provider/base_url** vs fully **per-purpose** nesting in the canonical config schema.

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

**D2** through **D6** are shipped as documented in implementation notes above (**D6** = **`GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_*`** ingest wiring + **`EvidenceEnrichmentService`** ordering). **Next:** **D7** visibility / selector, **D8** full-completion audit — **no** **`/answer`** in Track **D**; **Phase 9** not started.

---

## Primary handoff (Audit / Project Manager → parent)

1. **Delivered:** **`phase_8_model_pipeline_completion_decisions.md`** — Track **D1** decisions + **D2.5** amendment; implementation notes through **D6** (ingest merge behind explicit enricher env).
2. **Next:** **D7** UI/ops; **D8** audit.
3. **Truth:** Optional ingest merge exists behind **`GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED`**; **`openai_compatible`** / selector UI / **`/answer`** / Phase **9** not claimed as fully shipped product surfaces beyond this doc’s scope.
