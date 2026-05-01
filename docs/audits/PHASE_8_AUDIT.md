# Phase 8 Audit — Specialized Model Pipeline (baseline)

**Date**: 2026-05-03  
**Result**: `pass_with_notes`

This audit accepts the **Phase 8 baseline** (Slices **8A–8H** implementation + documentation, **8G design-only**) as **honest, contract-aligned, and test-backed** at the repository boundary. It does **not** certify production specialized-model inference, a model registry, operator UI for pipeline runs, ingestion/enrichment merge of **`graphclerk_model_pipeline`**, or **`POST /answer`**. Phase **5** remains **partial** (`pass_with_notes`). Phase **6** and **7** remain **`pass_with_notes`** per their audit artifacts. Phase **9** remains **`not_started`**.

---

## Executive notes (non-negotiable honesty)

- **Model output is not evidence.** Pipeline modules produce typed envelopes and (when projected) **metadata-only** subtrees under **`graphclerk_model_pipeline`**; they do **not** create **`EvidenceUnit`** rows, mutate **`EvidenceUnitCandidate.text`**, override **`source_fidelity`**, or alter **`RetrievalPacket`** selected source evidence.
- **No production inference:** **`NotConfiguredModelPipelineAdapter`** is the real default semantics for “no adapter configured”; **`DeterministicTestModelPipelineAdapter`** is **tests-only** (documented). **No** Ollama/vLLM client, **no** HTTP inference adapter implementation, **no** new inference dependencies in **`pyproject.toml`** for this baseline (verified by audit scope: **no** Phase 8 requirement to change deps; status honesty confirms none claimed).
- **No `/answer`:** No answer synthesis, **`LocalRAGConsumer`**, or LLM calls introduced on ingestion/retrieval/FileClerk paths for Phase 8.
- **Slice 8G** remains **design-only** (working plan § Slice 8G); optional future **A/B** HTTP adapters are **not** implemented.

---

## Verification evidence

| Check | Command / artifact | Result |
|--------|---------------------|--------|
| Phase 8 targeted tests | `cd backend` → `python -m pytest tests/test_phase8_model_pipeline_contracts.py tests/test_phase8_model_pipeline_output_validation_service.py tests/test_phase8_model_pipeline_candidate_projection_service.py tests/test_phase8_model_pipeline_evaluation_fixtures.py -q` | **Pass** (exit 0) |
| Backend default suite | `cd backend` → `python -m pytest -q` | **Pass** (exit 0; skips as designed for gated tests) |
| Forbidden imports (spot) | `rg` on `model_pipeline_contracts.py`, `model_pipeline_output_validation_service.py`, `model_pipeline_candidate_projection_service.py` for `file_clerk`, `retrieval_packet`, `route_selection`, `evidence_selection` | **No matches** |

**Not executed in this audit run** (not required for Phase 8 scope): `npm run build` — Phase 8 did **not** change `frontend/**`.

---

## Scope

In scope: Slices **8A–8F** code, **8G** design (plan only), **8H** docs/status honesty, as reflected in:

- [`docs/phases/graph_clerk_phase_8_specialized_model_pipeline.md`](../phases/graph_clerk_phase_8_specialized_model_pipeline.md)
- [`.cursor/plans/phase_8_specialized_model_pipeline_1b9d495c.plan.md`](../../.cursor/plans/phase_8_specialized_model_pipeline_1b9d495c.plan.md)
- `docs/status/*`, `README.md` (honesty alignment)

Out of scope: Production HTTP inference adapter, registry, settings wiring, ingestion/enrichment integration, Phase **9**, **`/answer`**.

---

## Implementation summary (traceability)

| Slice | Primary paths |
|-------|----------------|
| **8A–8C** | `backend/app/services/model_pipeline_contracts.py`; tests `backend/tests/test_phase8_model_pipeline_contracts.py` |
| **8D** | `backend/app/services/model_pipeline_output_validation_service.py`; tests `backend/tests/test_phase8_model_pipeline_output_validation_service.py` |
| **8E** | `backend/app/services/model_pipeline_candidate_projection_service.py`; tests `backend/tests/test_phase8_model_pipeline_candidate_projection_service.py` |
| **8F** | `backend/tests/fixtures/phase8_model_pipeline_cases.py`; tests `backend/tests/test_phase8_model_pipeline_evaluation_fixtures.py` |
| **8G** | Design in `.cursor/plans/phase_8_specialized_model_pipeline_1b9d495c.plan.md` § Slice 8G only |
| **8H** | `docs/status/*`, `README.md`, phase doc **Implementation status** |

---

## Detailed checklist (required audit checks)

### 1. Slice 8A — contracts

| Check | Verdict | Notes |
|--------|---------|--------|
| Typed roles / input / output / status contracts exist | **Pass** | `ModelPipelineRole`, `ModelPipelineInputKind`, `ModelOutputKind`, `ModelPipelineStatus`, `ModelPipelineTask`, `ModelPipelineResult` in `model_pipeline_contracts.py`. |
| No model calls | **Pass** | Contracts are pure types + validation; no inference I/O. |
| No FileClerk / retrieval imports | **Pass** | Spot grep: no matches in pipeline service modules listed above. |
| Truth-claim bans (top-level / contracted paths) | **Pass** | `_forbid_truth_claims_top_level` on task/result/request metadata/trace/error details; deeper scan in 8D. |

### 2. Slice 8B — envelopes

| Check | Verdict | Notes |
|--------|---------|--------|
| Request/response envelopes exist | **Pass** | `ModelPipelineRequestEnvelope`, `ModelPipelineResponseEnvelope`, `ModelPipelineError`. |
| Success vs failure semantics explicit | **Pass** | `ModelPipelineResponseEnvelope._validate_success_vs_failure_shape`; tests in contracts suite. |
| No partial results on non-success | **Pass** | Non-success requires `result=None`, non-`None` error (8B rules). |
| Error `details` truth-claim bans | **Pass** | `ModelPipelineError._forbid_truth_in_details`. |

### 3. Slice 8C — adapter shell

| Check | Verdict | Notes |
|--------|---------|--------|
| `ModelPipelineAdapter` protocol exists | **Pass** | Protocol + `run` signature. |
| **NotConfigured** returns **unavailable**, not success | **Pass** | `NotConfiguredModelPipelineAdapter.run` → `status=unavailable`, explicit error; tests. |
| Deterministic adapter **test-only** | **Pass** | Docstring: “**Tests-only** adapter”; not production registry default. |
| No real model adapter | **Pass** | No Ollama/vLLM/transformers implementation in repo for pipeline. |

### 4. Slice 8D — output validation

| Check | Verdict | Notes |
|--------|---------|--------|
| Recursive truth / prose checks | **Pass** | `_truth_and_prose_scan`; nested `is_evidence`, `source_fidelity: verbatim`, prose-like keys where restricted. |
| Reports, not exceptions (normal path) | **Pass** | `ModelPipelineOutputValidationReport`; service returns report. |
| No input mutation | **Pass** | Docstring + implementation pattern (issues collected). |
| No FileClerk / retrieval wiring | **Pass** | Imports limited to contracts; grep clean. |

### 5. Slice 8E — projection

| Check | Verdict | Notes |
|--------|---------|--------|
| Namespaced subtree **`graphclerk_model_pipeline`** only | **Pass** | `GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY`; single top-level key in output dict. |
| **`proposed`** isolates payload | **Pass** | `result.payload` deep-copied under `proposed`. |
| Validation failure → `None` | **Pass** | `if not validation.ok: return None`. |
| Non-success / error slot → `None` | **Pass** | Guards on status, `result`, `error`. |
| No candidate creation / no persistence | **Pass** | Pure function-style service; no DB/API/FileClerk imports. |

### 6. Slice 8F — fixtures

| Check | Verdict | Notes |
|--------|---------|--------|
| Deterministic typed fixtures | **Pass** | `phase8_model_pipeline_cases.py` builders + frozen dataclasses. |
| Positive and negative cases | **Pass** | Evaluation fixture tests cover success + invalid paths + unavailable-shaped envelope. |
| No model calls | **Pass** | Fixtures construct typed objects only. |
| No adapter execution in fixtures | **Pass** | Unavailable case mirrors NotConfigured **shape** without calling adapter (per fixture design); tests assert semantics. |

### 7. Slice 8G — local inference design

| Check | Verdict | Notes |
|--------|---------|--------|
| Design-only | **Pass** | No new adapter module implementing HTTP inference in `backend/app/**` for 8G. |
| **NotConfigured** remains default narrative | **Pass** | Plan § 8G: option **E** until approval. |
| Ollama/vLLM only as future optional targets | **Pass** | Plan recommends **A/B** when/if approved; **C/D** deferred. |
| No dependencies added for inference | **Pass** | Phase 8 baseline did not add Ollama/vLLM deps (honesty + no impl). |

### 8. Slice 8H — docs/status

| Check | Verdict | Notes |
|--------|---------|--------|
| Baseline documented honestly | **Pass** | `docs/status/*` distinguish baseline vs north-star; this audit confirms consistency. |
| No production inference claim | **Pass** | Status docs state **no** real adapter / **no** wiring. |
| No `/answer` claim | **Pass** | Explicit deferral maintained. |
| Phase **9** `not_started` | **Pass** | `PHASE_STATUS.md` unchanged for Phase 9. |

### 9. Non-features (confirmed)

| Non-feature | Verdict |
|-------------|---------|
| Real Ollama/vLLM adapter | **Confirmed absent** |
| Model registry | **Confirmed absent** |
| Model settings/config wiring for pipeline | **Confirmed absent** |
| Model calls in app code (pipeline product path) | **Confirmed absent** for Phase 8 scope — pipeline is library-style services + tests only; no API route wires them by default |
| Model-output ingestion/enrichment wiring | **Confirmed absent** |
| DB/API/frontend changes **for Phase 8 slices** | **Confirmed** — Phase 8 slices did not add routes/UI for pipeline (existing app unchanged for pipeline feature surface) |
| **`RetrievalPacket`** source evidence mutation via pipeline | **Confirmed absent** |
| **`EvidenceUnit`** mutation via pipeline | **Confirmed absent** |
| **`source_fidelity`** override via pipeline | **Confirmed absent** |
| Answer synthesis | **Confirmed absent** |

---

## Explicit notes / limitations (`pass_with_notes`)

- **North-star vs baseline:** The phase doc’s broader objectives (registry, routing fleet, drift tooling, UI, etc.) remain **largely future**; only the **contract → validation → standalone projection → fixtures** baseline is audited here.
- **Integration:** Callers may invoke services in tests only today; **no** first-class product entrypoint or UI for Phase 8 pipeline runs.
- **Future adapter slice:** If HTTP adapters land, require mocked HTTP tests, timeouts, and continued **validation-before-projection** discipline per plan § 8G.

---

## Final decision

**`pass_with_notes`** — Phase **8 baseline** is **accepted** as implemented and documented. Remaining items are **explicitly deferred** (production inference, registry, merge into ingestion/enrichment, UI, **`/answer`**) and do **not** block closure of this audit artifact.

---

## Next-phase readiness statement

- **Phase 9** remains **`not_started`** until explicitly kicked off; this audit does **not** start Phase **9**.
- A **future** slice may implement an optional HTTP adapter (**8G** narrative), registry, or enrichment merge **only** under separate approval and file allowlists.
- Recommended pre-flight for any inference work: extend tests per § 8G Q14 (mocked HTTP, import boundaries, validation gates).
