---
name: Phase 8 Specialized Model Pipeline
overview: Governed contracts, envelopes, adapters (NotConfigured first), validation, and optional seams for future specialized model helpers—no inference by default, no retrieval/evidence mutation, model output never treated as source evidence. Canonical plan; slice checkboxes below mirror execution truth; PM agent should reconcile todos with this file after each slice.
isProject: true
todos:
  - id: phase8-slice-8-0-entry-gate
    content: "Slice 8.0 — Entry gate + plan alignment (status/audit gates, pre–Phase 8 sweeps; no product code)."
    status: completed
  - id: phase8-slice-8a-contracts
    content: "Slice 8A — Boundary contracts (`model_pipeline_contracts` task/result types; no adapters, no retrieval/FileClerk imports)."
    status: completed
  - id: phase8-slice-8b-envelopes
    content: "Slice 8B — Request/response envelopes + `ModelPipelineError` (status/error semantics; no persistence, no adapters)."
    status: completed
  - id: phase8-slice-8c-not-configured
    content: "Slice 8C — NotConfigured adapter shell (protocol, explicit error, deterministic test adapter only; no real model)."
    status: completed
  - id: phase8-slice-8d-output-validation
    content: "Slice 8D — Model output validation service (typed outputs, reject prose/source-truth; deeper than top-level dict checks; no FileClerk wiring)."
    status: completed
  - id: phase8-slice-8e-candidate-seam
    content: "Slice 8E — Candidate-only integration seam (approval-gated; no EvidenceUnit / RetrievalPacket mutation; no ranking change)."
    status: completed
  - id: phase8-slice-8f-eval-fixtures
    content: "Slice 8F — Evaluation fixtures for model-helper outputs (deterministic; failure cases; no production inference)."
    status: completed
  - id: phase8-slice-8g-local-inference-design
    content: "Slice 8G — Optional local inference adapter design (Ollama/vLLM etc.); design-only unless deps explicitly approved."
    status: pending
  - id: phase8-slice-8h-docs-status
    content: "Slice 8H — Docs/status honesty (what Phase 8 is/is not; no overclaim of models or /answer)."
    status: pending
  - id: phase8-slice-8i-audit
    content: "Slice 8I — Phase 8 audit artifact under docs/audits/ after implementation slices warrant it."
    status: pending
  - id: phase8-pm-reconcile
    content: "PM — After each merged slice update this plan’s slice checklist + todo statuses; flag drift vs docs/status/README."
    status: pending
---

# Phase 8 — Specialized Model Pipeline (working plan)

**Plan id:** `1b9d495c`  
**Canonical path:** [`.cursor/plans/phase_8_specialized_model_pipeline_1b9d495c.plan.md`](phase_8_specialized_model_pipeline_1b9d495c.plan.md)  
**Phase contract (read-only reference):** [`docs/phases/graph_clerk_phase_8_specialized_model_pipeline.md`](../../docs/phases/graph_clerk_phase_8_specialized_model_pipeline.md)

This file is the **Cursor working plan** for Phase 8. It does **not** change phase governance; early slices intentionally **narrow** scope versus the full phase doc until contracts and validation exist.

**PM / tracking:** Use the YAML **todos** above (and the slice checklist further down) as the execution backlog. When a slice ships, set its todo `status` to `completed` and tick the matching **Slice progress** row; keep `phase8-pm-reconcile` in sync or mark it `completed` only when you intentionally end a PM pass (otherwise leave `pending` as a standing reminder).

---

## Phase purpose

Introduce a **governed, typed, testable boundary** for future **specialized model helpers** (classification, extraction, routing assistance only where outputs remain typed, bounded, traceable). Models assist **adapters and proposals**; they do **not** replace FileClerk, graph/evidence traceability, or `source_fidelity` semantics.

---

## Non‑negotiable invariants and rules

### Invariant: model output is not evidence

Anything produced by a model helper is **derived** or **candidate** metadata unless and until it is normalized through **existing** evidence contracts, ingestion/FileClerk boundaries, and **`source_fidelity`** semantics. Model output must **never** silently become source truth or substitute for selected `RetrievalPacket` evidence.

### Explicit rules (all slices)

- **No** `POST /answer` / answer synthesis in GraphClerk retrieval or this pipeline unless a **future**, separately approved phase explicitly scopes it.
- **No** default LLM calls: core paths stay local‑first; any inference adapter is **opt‑in**, explicit, and off by default (NotConfigured / explicit errors).
- **No retrieval mutation:** no changes to how routes are chosen, evidence is ranked, packets are assembled, or `RetrievalPacket` evidence semantics.
- **No evidence mutation:** no rewriting, silent enrichment, or replacement of `EvidenceUnit` text or packet source evidence from model output.

---

## Entry conditions (planning / implementation gate)

- **Phase 5:** remains **partial** / audit **`pass_with_notes`** (multimodal honest partials; no OCR/ASR/caption/video completion claimed).
- **Phase 6:** **`pass_with_notes`** baseline accepted per `docs/status/*` and Phase 6 audit.
- **Phase 7:** baseline **implemented** / audit **`pass_with_notes`** on record; **Slice 7I** (deterministic context boosting) **deferred/cancelled** pending separate approval.
- **Pre‑Phase‑8:** structural verification report exists; follow‑up remediation referenced there; code cleanliness sweep shows **no Severity A** blockers; language metadata key duplication remediated (e.g. commit `a0b9e20` or equivalent).
- **Phase 8 / 9:** **`not_started`** for product implementation until each slice is explicitly approved and delivered.
- **Honesty:** status docs and README must not claim Phase 8 product features (registry, routing, inference) until implemented and tested.

---

## Non‑scope (Phase 8 kickoff and early slices)

- Model **training** or fine‑tuning.
- **Answer synthesis** or **`/answer`**.
- **Default** or hidden **LLM** dependencies or calls.
- Changing **`RetrievalPacket`** evidence semantics or selected evidence payloads.
- **FileClerk** bypass; graph/index **persistence** from raw model output.
- **Phase 9** IDE integration.
- **Frontend** work unless a later slice is explicitly scoped (not required for kickoff).

---

## Risks

| Risk | Mitigation |
|------|------------|
| Phase doc scope is **broad** (registry, UI, Ollama, etc.) vs early **contract‑only** work | Sequence **8A→8D** before integration; treat phase doc “components” as **later** slices unless approved. |
| Accidental **coupling** to `FileClerkService`, `retrieval_packet_builder`, or routes | **Forbidden imports** in early modules; code review + contract tests that only exercise boundaries. |
| Model JSON treated as **evidence** | Enforce **candidate/derived** labeling in schemas (8B); validation service (8D); no persistence without normalization (8E gated). |
| **Dependency creep** (Ollama, vLLM, etc.) | **8G** design‑only unless separately approved; **no** `pyproject` / requirements changes without approval. |

---

## Testing expectations

| When | Expectation |
|------|-------------|
| **This kickoff** (plan + optional status pointer only) | **No** `pytest` / frontend build required — **no** `backend/**` or `frontend/**` changes. |
| **Slice 8A** (future) | Add `backend/tests/test_phase8_model_pipeline_contracts.py`; run `python -m pytest` from `backend/`; keep integration tests env‑gated as today. |
| **Later slices** | Contract tests + failure cases per slice; no claiming “tested” in status without running the relevant suite. |

---

## Status‑doc expectations

- Keep **Phase 5** partial / **`pass_with_notes`**; **Phase 6** **`pass_with_notes`**; **Phase 7** **`pass_with_notes`**; **Phase 9** **`not_started`**.
- Keep **`POST /answer`** deferred; keep **OCR/ASR/caption/video** absent as today.
- **Phase 8** remains **`not_started`** for implementation until code lands; only add **traceability** (e.g. pointer to this plan) if useful.
- Do **not** mark Phase 8 “implemented” or claim registry/routing/inference until true.

---

## First implementation slice recommendation

**Slice 8A — Specialized model boundary contracts** only: typed roles/interfaces, no inference, no new dependencies, no retrieval or evidence paths touched. Await **explicit** task approval before editing `backend/**`.

---

## Slice checklist (8.0 — 8I)

| Slice | Name | Notes |
|-------|------|--------|
| **8.0** | Entry gate + plan alignment | Verify Phase 7 `pass_with_notes`, pre‑Phase‑8 sweeps, no Severity A cleanliness blockers; publish this plan; **no** backend code. |
| **8A** | Specialized model boundary contracts | Typed model roles/interfaces only; **no** real model calls; **no** inference; **no** dependency adds; **no** retrieval behavior changes. |
| **8B** | ModelTask schema / envelopes | Typed input/output contracts; status/error semantics; explicit **derived** / **candidate** labeling; **no** persistence unless separately approved. |
| **8C** | NotConfigured model adapter shell | Adapter protocol; NotConfigured raises **explicit** error; deterministic **test** adapter only; **no** real model. |
| **8D** | Model output validation service | Validates typed outputs; rejects unbounded prose where structured output is required; rejects source‑truth claims; **no** FileClerk integration yet. |
| **8E** | Candidate‑only integration seam | **Approval‑gated:** helpers may produce **candidate metadata only**; **no** `EvidenceUnit` text mutation; **no** `RetrievalPacket` source evidence mutation; **no** route/evidence ranking change. **Slice 8E (projection-only):** `ModelPipelineCandidateMetadataProjectionService` landed — validated envelope → `graphclerk_model_pipeline` subtree only; **no** ingestion/enrichment wiring yet. |
| **8F** | Evaluation fixtures | Deterministic fixtures + failure cases; **no** production inference. **Implemented:** `backend/tests/fixtures/phase8_model_pipeline_cases.py` + `backend/tests/test_phase8_model_pipeline_evaluation_fixtures.py`. |
| **8G** | Optional local inference adapter design | Design only (Ollama/vLLM/etc.); **no** dependency add without approval. |
| **8H** | Docs/status update | Document what Phase 8 **is / is not**; no claim of model implementation or answer synthesis until true. |
| **8I** | Phase 8 audit | After implementation slices; artifact under `docs/audits/` per project audit rules. |

### Slice progress (planning tracker)

- [x] **8.0** — Entry gate + plan alignment (working plan created; kickoff docs‑only).
- [x] **8A** — Boundary contracts (`backend/app/services/model_pipeline_contracts.py` + `backend/tests/test_phase8_model_pipeline_contracts.py`; contracts only, no adapters).
- [x] **8B** — Request/response envelopes (`ModelPipelineRequestEnvelope`, `ModelPipelineResponseEnvelope`, `ModelPipelineError`; status/error semantics; no adapters).
- [x] **8C** — Adapter shell (`ModelPipelineAdapter`, `NotConfiguredModelPipelineAdapter`, `DeterministicTestModelPipelineAdapter` tests-only; no registry, no real inference).
- [x] **8D** — Output validation service (`model_pipeline_output_validation_service.py`; deep recursive checks; reports only, no mutation).
- [x] **8E** — Candidate seam (**projection-only Option A** — `model_pipeline_candidate_projection_service.py` + tests; merge into candidates / enrichment deferred per § Slice 8E).
- [x] **8F** — Evaluation fixtures (`tests/fixtures/phase8_model_pipeline_cases.py`, `test_phase8_model_pipeline_evaluation_fixtures.py`; no adapter execution in fixtures).
- [ ] **8G** — Local inference design only.
- [ ] **8H** — Docs/status alignment post‑implementation.
- [ ] **8I** — Phase 8 audit.

---

## Slice 8E — Design notes (candidate-only integration seam)

**Status:** Design notes below remain canonical for enrichment/ingestion wiring. **Implementation (2026‑05‑01):** pure **`ModelPipelineCandidateMetadataProjectionService`** (`backend/app/services/model_pipeline_candidate_projection_service.py`) + `backend/tests/test_phase8_model_pipeline_candidate_projection_service.py` — projection metadata subtree only; **no** FileClerk, ingestion, enrichment, API, DB, or adapter calls inside projection. Optional merge paths (**B/C**) remain **not implemented**.

### PM recommendation — option letter

| Choice | Verdict |
|--------|---------|
| **A** — Pure projection service: validated pipeline output → namespaced **`graphclerk_model_pipeline`** metadata blob **only**; **no** ingestion wiring in the same slice | **Preferred first implementation** |
| **B** — Thin `EvidenceEnrichmentService` path that merges **only** a pre-built projection (still **no** adapter calls inside enrichment) | **After A + after 8F** |
| **C** — Direct merge in `TextIngestionService` / `MultimodalIngestionService` | **Avoid first** — coupling + persistence pressure |
| **D** — Defer all **8E** until **8F** | **Partial only:** defer **merge into candidates / enrichment** until **after 8F**; pure **A** may still ship earlier **without** ingestion touch |
| **E** — Other minimal (e.g. explicit `ProjectionOk` / `ProjectionRejected` ADT) | Same boundary as **A** |

**Smallest safe slice:** **A** (pure module + tests), **no** enrichment/ingestion edits until **8F** fixtures exist.

### Sub-agent summaries (this design pass)

- **PM:** Sequence **8F before E2 wiring**; split **E1** projection vs **E2** optional enrichment merge if scope creeps.
- **Code quality:** All Phase 8 writes under **`metadata_json["graphclerk_model_pipeline"]`**; **`proposed`** subtree only for model-suggested fields; projection imports **no** FileClerk/retrieval.
- **Audit:** Namespace + **`validation.ok`** + **no** `text` / `source_fidelity` mutation prevents treating model JSON as evidence; document honest limits in **8H**.
- **Testing:** Golden fixtures from **8F**; clone candidates and assert **`text`/`source_fidelity` unchanged**; **`validation.ok` false** → **no** merge; unavailable adapter → **no** metadata by default.
- **Git:** Plan file only unless implementation follows.

### Design Q&A (required)

1. **Seam:** **`ModelPipelineCandidateMetadataProjection`** service (name TBD): validated envelope + report → **`dict | None`** for the **`graphclerk_model_pipeline`** subtree only.
2. **Inputs:** Success **`ModelPipelineResponseEnvelope`** + **`ModelPipelineOutputValidationReport.ok`** + **`model_pipeline_request_id`**; optionally extracted **`ModelPipelineResult`**.
3. **Outputs:** **Metadata only** — mergeable nested dict; **never** mutates candidate evidence fields.
4. **New candidates:** **Out of scope** for minimal **8E**; defer unless separately approved.
5. **Future `source_fidelity` if new candidates ever allowed:** **`derived`** / **`computed`** only; never **`verbatim`** for model body text.
6. **Traceability:** Include **`schema_version`**, **`model_pipeline_request_id`**, **`role`**, **`output_kind`**, **`status`**, **`provenance.source`**, **`validation`** (`ok` + compact **`issues`**), **`proposed`**.
7. **`ModelPipelineOutputValidationService`:** Runs **before** projection; projection **refuses** if **`ok`** is false.
8. **Validation fails:** **No merge**; **no** silent attach (quarantine/logging **deferred**).
9. **Adapter unavailable:** **No** candidate metadata by default (matches **NotConfigured** behavior).
10. **8E vs 8F:** **8F before any enrichment/ingestion wiring**; **pure A** may precede **8F** if it stays **off** ingestion paths.
11. **Enrichment vs standalone:** **Standalone A first**; optional enrichment hook (**B**) only after **8F**, default remains **no-op** in production.
12. **Allowed files (future impl, illustrative):** `backend/app/services/model_pipeline_candidate_projection_service.py`, `backend/tests/test_phase8_model_pipeline_candidate_projection*.py`; later optionally **`evidence_enrichment_service.py`** for thin merge. **Forbidden until approved:** `text_ingestion_service.py`, `multimodal_ingestion_service.py`, FileClerk/retrieval/route/evidence selection, API, DB, adapters in enrichment default path.
13. **Tests:** Projection golden JSON; reject paths; immutability on cloned candidates; import boundaries.
14. **Deferred:** Orchestrator calling adapters; new EU candidates from models; UI; quarantine store.

### Canonical metadata shape (`metadata_json`)

```json
{
  "graphclerk_model_pipeline": {
    "schema_version": "phase8.v1",
    "model_pipeline_request_id": "...",
    "role": "evidence_candidate_enricher",
    "output_kind": "candidate_metadata",
    "status": "success",
    "provenance": { "source": "deterministic_test" },
    "validation": { "ok": true, "issues": [] },
    "proposed": { "labels": [], "hints": [] }
  }
}
```

---

## Slice 8A — acceptance criteria (when implemented)

- Contracts exist for future **specialized model roles** (typed, bounded).
- Contracts **do not** call models or perform I/O.
- Contracts **do not** persist data.
- Contracts **do not** mutate evidence or `RetrievalPacket` contents.
- Contracts **do not** touch retrieval / FileClerk / route or evidence selection services.
- Tests prove modules are importable and enforce **basic** validation contracts.
- Full backend **`python -m pytest`** passes after 8A code lands.

**Allowed files (8A task scope, typical):** `backend/app/services/model_pipeline_contracts.py`, `backend/tests/test_phase8_model_pipeline_contracts.py`. **Avoid** `backend/app/services/errors.py` unless a narrowly scoped pipeline error type is unavoidable. **Forbidden:** `backend/app/api/**`, `backend/app/models/**`, `backend/app/db/**`, `backend/app/repositories/**`, migrations, `file_clerk_service.py`, `retrieval_packet_builder.py`, `route_selection_service.py`, `evidence_selection_service.py`, `text_ingestion_service.py`, `multimodal_ingestion_service.py`, `frontend/**`, `pyproject.toml`, `requirements*`, `.cursor/rules/**`.

---

## High‑level flow (reference)

```mermaid
flowchart LR
  subgraph gate [Slice8_0]
    V[VerifyPhase7AndSweeps]
  end
  subgraph contracts [Slice8A_to_8D]
    A[TypedRolesContracts]
    B[ModelTaskEnvelopes]
    C[NotConfiguredShell]
    D[OutputValidation]
  end
  subgraph seam [Slice8E_onward]
    E[CandidateSeamIfApproved]
  end
  gate --> A --> B --> C --> D --> E
```

---

## Sub‑agent Primary handoffs (this kickoff)

Summaries per `docs/governance/AGENT_ROLES.md` → **Dedicated sub‑agents** → **Handoff to primary / parent**.

### Project Manager Agent

1. **Mission recap:** Deliver Phase 8 working plan + optional status trace; sequence slices 8.0–8I; block premature inference/training.
2. **Scope touched:** `.cursor/plans/phase_8_specialized_model_pipeline_1b9d495c.plan.md`; optional `docs/status/PHASE_STATUS.md`.
3. **Drift / findings:** Entry gate satisfied per `docs/status/*`, Phase 7 audit, pre‑Phase‑8 reports; Phase 8 product code still **`not_started`**.
4. **Follow‑ups:** **Y** — user approves **Slice 8A** implementation task with file allowlist.
5. **Recommended next actions:** Implement **8A** only after explicit approval; run pytest for that slice.

### Status Documentation Agent

1. **Mission recap:** Preserve honesty; add plan pointer only for traceability.
2. **Scope touched:** `PHASE_STATUS.md` (if edited).
3. **Drift / findings:** Phase 5–7 and `/answer`/OCR honesty unchanged; Phase 8 remains **`not_started`** for implementation.
4. **Follow‑ups:** **N** unless implementation changes shipped behavior.
5. **Recommended next actions:** After future slices, update `PROJECT_STATUS` / `ROADMAP` if scope claims change.

### Audit Agent

1. **Mission recap:** Prevent overclaiming Phase 8 or Phase 9.
2. **Scope touched:** Plan + status diff (read).
3. **Drift / findings:** No Phase 8 product implementation claimed; 8I audit deferred until implementation exists.
4. **Follow‑ups:** **N** for kickoff.
5. **Recommended next actions:** Run Phase 8 audit checklist when closing **8I**.

### Code Quality Agent (read‑only)

1. **Mission recap:** Guardrail for future 8A purity.
2. **Scope touched:** N/A code in kickoff.
3. **Drift / findings:** Future `model_pipeline_contracts.py` must stay free of retrieval/FileClerk imports.
4. **Follow‑ups:** **Y** at 8A review.
5. **Recommended next actions:** Single contracts module; expand only with envelopes (8B).

### Testing Agent

1. **Mission recap:** Tests for kickoff vs 8A.
2. **Scope touched:** None executed (docs/plan only).
3. **Drift / findings:** Kickoff requires **no** test run.
4. **Follow‑ups:** **Y** when `backend/**` changes for 8A+.
5. **Recommended next actions:** Default `pytest` after 8A.

### Git Agent

1. **Mission recap:** Stage only allowed paths; commit; push `master`.
2. **Scope touched:** Plan file ± `PHASE_STATUS.md`.
3. **Drift / findings:** Do not stage `backend/**`, `frontend/**`, caches, or forbidden paths.
4. **Follow‑ups:** **N** after successful push unless remote rejects.
5. **Recommended next actions:** Verify `git status` clean except intentional untracked.
