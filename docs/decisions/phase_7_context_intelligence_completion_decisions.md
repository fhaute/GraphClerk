# Phase 7 — Context Intelligence: Full Completion Decision Record

**Not a claim of shipped full completion** — this file records **decisions and deferrals** for Track **C2+** implementation. The audited **baseline** remains `pass_with_notes`; production detection, boosting, and translation are **not** implemented unless a future slice says so.

| Field | Value |
|-------|--------|
| **Track / slice** | **Track C — Slice C1** (Phase 1–8 Completion Program) |
| **Document type** | Design / **decision record only** — no backend, frontend, or script behavior changes |
| **Phase 9** | **Not started** — this record is explicitly **pre–Phase 9** |
| **Audit baseline** | [`docs/audits/PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md) remains **valid baseline history** (`pass_with_notes`, 2026-05-02). This document does **not** replace, rewrite, or supersede that audit. |
| **Target** | **Full intended Phase 7 completion** per [`docs/phases/graph_clerk_phase_7_context_intelligence.md`](../phases/graph_clerk_phase_7_context_intelligence.md) *Core Objective* vs what the audited **baseline** already shipped |
| **Status** | **Decisions recorded** — implementation is **out of scope** for this slice |
| **Date** | 2026-05-01 |

---

## 1. Current Phase 7 baseline (implemented + audited)

The following is the **honest shipped baseline** (Slices **7A–7H**, **7J**, **7K**); see [`PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md) and [`KNOWN_GAPS.md`](../status/KNOWN_GAPS.md).

| Area | State |
|------|--------|
| **Language metadata** | Canonical optional keys on `EvidenceUnitCandidate.metadata`: `language`, `language_confidence`, `language_detection_method`, `language_warnings` — validated by `validate_optional_language_metadata` in [`backend/app/schemas/evidence_unit_candidate.py`](../../backend/app/schemas/evidence_unit_candidate.py); persisted on evidence via `metadata_json` where callers supply metadata. |
| **Language detection** | [`LanguageDetectionService`](../../backend/app/services/language_detection_service.py) + adapter protocol; **`NotConfiguredLanguageDetectionAdapter`** (explicit unavailable); **`DeterministicTestLanguageDetectionAdapter`** (tests / deterministic rules only). **No** production third-party detector wired as default. |
| **Enrichment** | [`EvidenceEnrichmentService`](../../backend/app/services/evidence_enrichment_service.py) — **identity / no-op** default; seam invoked from text and multimodal ingestion **before** candidate persistence. |
| **Artifact language aggregation** | [`ArtifactLanguageAggregationService`](../../backend/app/services/artifact_language_aggregation_service.py) — **pure helper**; emits `graphclerk_language_aggregation` subtree for merge into artifact metadata; **no** automatic persistence from ingestion in baseline. |
| **`language_context`** | [`RetrievalPacketBuilder`](../../backend/app/services/retrieval_packet_builder.py) derives **`RetrievalPacket.language_context`** from **selected evidence** metadata projections only — **no** `LanguageDetectionService` in packet assembly; **not** translation. |
| **`actor_context` (request)** | Optional on **`POST /retrieve`** per [`RetrieveRequest`](../../backend/app/schemas/retrieval.py) / [`ActorContext`](../../backend/app/schemas/retrieval.py). |
| **`actor_context` (packet)** | [`PacketActorContextRecording`](../../backend/app/schemas/retrieval_packet.py) on `RetrievalPacket` with explicit **`influence`** (e.g. `recorded_only_no_route_boost_applied`). |
| **Retrieval influence** | **`actor_context` does not influence** route selection, evidence ranking, graph traversal, context budget, warnings, confidence, or `answer_mode` in baseline ([`FileClerkService.retrieve`](../../backend/app/services/file_clerk_service.py) passes context for **packet assembly after** orchestration). |
| **Not in baseline** | Production language-ID-by-default; **translation** / query translation; **Slice 7I** deterministic boosting; **automatic** artifact aggregation **persistence** wiring. |

---

## 2. Why the baseline is not “full Phase 7 completion”

The **audit** correctly accepted **`pass_with_notes`**: contracts, tests, and explicit non-goals match the **narrow** delivery.

**Full intended Phase 7** (phase doc *Core Objective*) still implies **policy and wiring choices** that the baseline **deliberately deferred**:

- Whether GraphClerk will ship a **production-capable** language detector behind the adapter boundary, or keep **`NotConfigured`** as the long-term product story for Phases 1–8.
- **Where** detection runs if approved (ingest vs retrieve vs both), and how that interacts with **`language_context`** usefulness.
- Whether **`graphclerk_language_aggregation`** is **persisted** on `Artifact.metadata_json` automatically or remains a **manual / operator** merge.
- Whether **`actor_context`** stays **recording-only** through “full completion” or gains **deterministic, auditable** retrieval influence (**7I**).
- Whether **translation** or **query translation** enters scope before Phase 9.
- **UI and onboarding** truth: operators must not confuse **context** with **evidence**, or believe **actor_context** changes ranks when it does not.

This ADR records **recommended** directions so implementation slices (**C2+**) can proceed without inventing product behavior in code.

---

## 3. Decision summary

| # | Topic | Recommended choice | Notes |
|---|--------|-------------------|--------|
| 1 | Production language detection | **Path B** (lightweight local adapter) **after** **requires dependency research**; until research closes, **effective policy A** — keep **`NotConfigured`** as shipped default | Do **not** pick a library in this document |
| 2 | Wiring location | **A** — ingestion **enrichment** path for persisted EU `metadata_json` when detector is approved | Optional narrow **retrieve-time** use remains a future option, not default |
| 3 | Aggregation persistence | **A** once evidence language metadata is reliably populated; **B** until then | Avoid stale aggregation over empty metadata |
| 4 | `language_context` after detection | **Unchanged contract** — derived from **selected evidence metadata**; not evidence; not translation; **no hidden ranking** unless boosting explicitly approved + implemented | More useful once metadata exists |
| 5 | `actor_context` policy | **A** — **recording-only** for full Phase 7 completion unless Fred **explicitly** approves boosting | Avoid hidden personalization |
| 6 | Deterministic boosting (7I) | **A** — **defer / cancel for Phase 1–8** by default; **B** only after explicit approval + spec’d rules + tests | **B** is **not** chosen here |
| 7 | Translation / query translation | **A** or **B** — **defer product translation** outside 1–8; allow **metadata-only** language tags without translation | No query rewrite as “evidence” |
| 8 | UI / operator visibility | Labeled **context** panels; show persisted language + aggregation when present; **warn** that `actor_context` does **not** affect retrieval in baseline | No translation / personalization claims |
| 9 | Docs / onboarding | Update pipeline, troubleshooting, examples (if request shapes change), status/gaps in **same delivery** as behavior | See § Decision 9 |

---

## 4. Decision 1 — Production language detection

| Option | Description |
|--------|-------------|
| **A** | Keep **`NotConfigured`** as the **Phase 1–8** story; defer any production detector **outside** the completion program |
| **B** | Add a **lightweight local** detector adapter (e.g. small on-process library) behind explicit config; default remains **not configured** until env enables |
| **C** | Remote / LLM-based language detection |
| **D** | **`DeterministicTestLanguageDetectionAdapter`** only (no real detector) |

**Recommended choice:** **B**, **conditional on dependency research** — evaluate Python ecosystem options (license, wheel availability, accuracy/latency, **no silent network** unless explicitly scoped). **If research blocks or rejects all candidates**, adopt **A** as an **explicit written policy**: “Phase 7 full completion = metadata contract + optional manual tags + `NotConfigured` default,” not silent guessing.

**Rationale:** B preserves **local-first**, explicit failure semantics, and aligns with existing adapter patterns (`NotConfigured` / opt-in). C increases operational and provenance risk for a **routing** signal. D is unsuitable as production truth.

**Consequences:** New optional dependency **or** explicit no-dep path; settings knob; tests for adapter + invalid outputs; docs for operators.

**Implementation slices:** **C2** (research + ADR addendum), **C3** (adapter + config).

**Tests required:** Unit tests for adapter; invalid `LanguageDetectionResult` rejection; config rejects bad combinations (mirror semantic-search embedding guards where appropriate).

**Docs required:** `TESTING_RULES.md` / operator env when implemented; onboarding troubleshooting for “detector unavailable.”

**Open sub-decision:** **Requires dependency research** — **does not block C1**; blocks **C3** until closed.

---

## 5. Decision 2 — Language detection wiring location

| Option | Description |
|--------|-------------|
| **A** | **Ingestion enrichment seam** — detector output merged into **candidate `metadata`** before EU persistence |
| **B** | **Retrieval-time** — run detector only on **selected** evidence text |
| **C** | **Both** A and B |
| **D** | **Manual / operator** enrichment only (no automatic detector) |

**Recommended choice:** **A** when a production detector is approved — language metadata should **travel with `EvidenceUnit`s** and remain stable for audits and aggregation.

**Rationale:** Retrieval-time-only recomputation (**B**) duplicates work, complicates reproducibility, and risks divergence from stored metadata. **C** is justified only if a future product needs **query-language** detection separate from evidence language (not chosen here). **D** remains valid under Decision **1A**.

**Consequences:** Ingestion latency and failure handling must be explicit (warnings vs hard fail — specify in C4 implementation, not here).

**Implementation slices:** **C4** — wire detector into **`EvidenceEnrichmentService`** (or parallel path) **without** mutating `text` / `source_fidelity`.

**Tests required:** Enrichment wiring integration tests; prove **no** `text` mutation.

**Docs required:** Pipeline guide — where language tags appear in the lifecycle.

---

## 6. Decision 3 — Artifact language aggregation persistence

| Option | Description |
|--------|-------------|
| **A** | Persist **`graphclerk_language_aggregation`** into **`Artifact.metadata_json`** after evidence creation / enrichment (idempotent merge) |
| **B** | Keep **pure helper only**; callers/operators merge manually |
| **C** | **Recompute on demand** at read time only |

**Recommended choice:** **A** **if** Decision **1** + **2** produce reliable per-EU language metadata; otherwise **B** until detector wiring exists (avoid misleading aggregation over mostly-null languages).

**Rationale:** Artifact-level summaries are **operator UX** and cross-EU analytics; persistence avoids N+1 recompute. **C** can hide staleness unless invalidation is defined.

**Consequences:** Need hooks post-evidence commit (or batch repair job); staleness if EUs change after aggregation — document refresh policy.

**Implementation slices:** **C5** — ingestion or post-ingest job calling `ArtifactLanguageAggregationService` + repository update.

**Tests required:** Persistence tests; warnings when no language metadata; no mutation of EU text.

**Docs required:** Architecture / pipeline — artifact metadata subtree.

---

## 7. Decision 4 — `language_context` after production detection

**Definition (unchanged by detector wiring on evidence):**

- **`language_context`** remains **derived from selected evidence `metadata_json`** (and existing builder rules).
- It is **not** evidence and **not** translation.
- It should become **more informative** once evidence carries real `language` / confidence / method fields.
- It must **not** introduce a **hidden ranking effect** unless **Decision 6** is explicitly approved and implemented with visible packet semantics.

**Rationale:** Keeps a single source of truth (stored EU metadata) and preserves auditability.

**Implementation slices:** **C6** — extend packet tests with **realistic** persisted metadata fixtures (no LLM).

**Tests required:** `test_phase7_retrieval_packet_language_context` extensions; property: builder does not call remote detectors.

---

## 8. Decision 5 — `actor_context` policy

| Option | Description |
|--------|-------------|
| **A** | **Recording-only** for Phase 7 “full completion” |
| **B** | **Deterministic boost** with strict, tested rules (**7I**) |
| **C** | Use **`actor_context`** only for **explanation / copy**, never retrieval |

**Recommended choice:** **A** for **full Phase 7 completion** under this program unless Fred **explicitly** approves **B**. **C** is compatible with **A** (UI copy) and does not require backend ranking changes.

**Rationale:** Actor-based retrieval influence can read as **hidden personalization**, weaken evidence grounding, and complicate security story (must never bypass access control).

**Consequences:** UI must remain honest: **no** “personalized retrieval” claims.

**Implementation slices:** Default path — none for ranking. If Fred approves **B** later: **C-boost-1** (separate slice) with explicit `influence` literals and evaluation fixtures.

**Tests required:** Regression: **`actor_context` no-influence** on routes/ranks; schema tests unchanged.

**Docs required:** Troubleshooting + playground copy — recording-only.

---

## 9. Decision 6 — Deterministic boosting (Slice 7I)

| Option | Description |
|--------|-------------|
| **A** | **Defer / cancel 7I** for Phase 1–8 program |
| **B** | Implement only with **evaluation fixtures** and **explainable** packet influence fields |
| **C** | Leave as **future research** without closure |

**Recommended choice:** **A** (default program outcome). **B** is **not** selected in this record — if Fred approves later, a **separate** slice **C-boost-1** must name **exactly** what ranking fields may change and how audits prove **no evidence injection** and **no AC bypass**.

**Rationale:** Matches current **`KNOWN_GAPS`** / audit posture; avoids shipping subtle rank deltas without a harness.

**Tests required (if B ever approved):** Rank ordering fixtures; “actor cannot inject evidence”; packet `influence` audit trail.

---

## 10. Decision 7 — Translation / query translation

| Option | Description |
|--------|-------------|
| **A** | **Defer** translation / query translation **outside Phases 1–8** |
| **B** | **Language-aware metadata only** — tags, warnings; **no** translated evidence text |
| **C** | **Query translation** before retrieval |
| **D** | **Answer** translation (downstream) |

**Recommended choice:** **A** or **B** — prefer **A** for product “translation,” **B** is already consistent with metadata keys without claiming a translation engine.

**Rationale:** Translation creates **correctness and provenance** risk; belongs after retrieval spine and language tagging are stable; **`/answer`** remains out of scope here.

**Consequences:** No `language_context` field may imply “we translated your query.”

**Implementation slices:** If ever approved: **C-translation-1** (separate, post–Fred sign-off).

**Tests required:** N/A for deferral; contract tests if a future API adds `query_translation_applied` flags.

**Docs required:** Explicit “GraphClerk does not translate” in onboarding until scope changes.

---

## 11. Decision 8 — UI / operator visibility

**When behavior matches this program’s recommendations:**

| Surface | Operator should see |
|---------|---------------------|
| **Evidence / artifact** | Language metadata keys when persisted; **`graphclerk_language_aggregation`** when persisted |
| **Packet** | `language_context` aggregates; **`actor_context`** recording + **`influence`** |
| **Warnings / copy** | Clear statement that **`actor_context` does not change retrieval** in baseline / approved policy |
| **Must not** | Imply **translation**, **personalized evidence selection**, or that **context overrides provenance** |

**Implementation slice:** **C7** (frontend) — only if backend persistence or labels warrant new panels; **`npm run build`** when touched.

---

## 12. Decision 9 — Docs / onboarding updates (post-implementation)

After **C2–C6** (and **C7** if needed), update in the **same delivery** as behavior:

| Doc | Update |
|-----|--------|
| [`GRAPHCLERK_PIPELINE_GUIDE.md`](../onboarding/GRAPHCLERK_PIPELINE_GUIDE.md) | Lifecycle: where language metadata is set; how `language_context` is derived |
| [`TROUBLESHOOTING_AND_OPERATIONS.md`](../onboarding/TROUBLESHOOTING_AND_OPERATIONS.md) | Detector unavailable, empty aggregation, “actor does not boost” |
| [`EXAMPLES_COOKBOOK.md`](../onboarding/EXAMPLES_COOKBOOK.md) | Only if **`POST /retrieve`** examples gain new optional fields worth showing |
| [`KNOWN_GAPS.md`](../status/KNOWN_GAPS.md), [`TECHNICAL_DEBT.md`](../status/TECHNICAL_DEBT.md), [`PROJECT_STATUS.md`](../status/PROJECT_STATUS.md) | Honest deltas per [`STATUS_REPORTING.md`](../governance/STATUS_REPORTING.md) |

---

## 13. Implementation slice proposal (Track C after C1)

| Slice | Content |
|-------|---------|
| **C1** | **This decision record** (complete) |
| **C2** | Production language detector **dependency research / decision** |
| **C3** | Detector adapter implementation behind **`NotConfigured`** default |
| **C4** | Ingestion **enrichment wiring** for language metadata |
| **C5** | **Artifact** language aggregation **persistence** |
| **C6** | Packet / **`language_context`** tests with **realistic persisted** metadata |
| **C7** | **UI / operator visibility** (if needed) |
| **C8** | **Final Phase 7 full-completion audit** (under Audit Agent charter; **new** artifact) |
| **C-boost-1** | **Only** if Fred explicitly approves deterministic boosting |
| **C-translation-1** | **Only** if Fred explicitly approves translation scope |

**Recommended next slice:** **C2**.

---

## 14. Acceptance criteria (full Phase 7 completion for this program)

1. **No hidden context influence** unless explicitly approved, **packet-visible**, and **tested**.
2. **Language metadata persists** where this ADR commits (EU + optional artifact aggregation).
3. **`language_context`** reflects **selected evidence metadata**; not labeled as translation.
4. **`actor_context` policy** is **explicit** in code, tests, and UI copy.
5. **Docs and UI tell the truth** — no overclaim of detector, boosting, or translation.
6. **Tests pass** for agreed scope.
7. **Final audit** (**C8**) can report **`pass`** or **`pass_with_notes`** with an explicit **“outside Phases 1–8”** table — not **`pass_with_notes`** hiding missing intended scope.

---

## 15. Testing strategy (for future implementation slices)

| Layer | Tests |
|-------|--------|
| **Detector adapter** | Valid / invalid outputs; `NotConfigured`; optional gate for prod rejecting test-only adapters |
| **Enrichment wiring** | Metadata merge; **no** `text` / `source_fidelity` mutation |
| **Persistence** | EU `metadata_json`; artifact `metadata_json` aggregation subtree |
| **Retrieval packet** | `language_context` with real metadata; **`actor_context` no-influence** regressions |
| **UI** | Optional **`npm run build`** when **C7** ships |
| **Out of scope for Phase 7** | Integration tests that require **real LLMs** or production OCR/ASR — **not** part of Phase 7 unless explicitly scoped |

---

## 16. Risks

| Risk | Mitigation |
|------|------------|
| **Hidden personalization** | Recording-only default; explicit `influence`; UI warnings |
| **Language guesses treated as evidence** | Metadata-only; never rewrite EU `text`; label confidence |
| **Translation corrupting evidence** | Defer translation; never store translated EU as `verbatim` without a new phase decision |
| **Context influencing access control** | **Non-goal** — no `actor_context` → permission mapping |
| **Ingestion performance** | Batch / cap text length; async enrichment only if later approved with ops design |
| **Dependency footprint** | Research phase; optional extra; CI story |
| **Multilingual edge cases** | Short-text warnings; null language allowed; aggregation warnings |
| **Stale artifact aggregation** | Document refresh / re-run policy when EUs change |

---

## 17. Non-goals (explicit)

- **No** OCR / ASR / video ingestion as part of this Track **C** slice set
- **No** production Phase **8** model pipeline as prerequisite for Phase 7 completion decisions here
- **No** **`POST /answer`** / answer synthesis
- **No** Phase **9**
- **No** access-control changes driven by `actor_context`
- **No** model-generated **evidence text**
- **No silent actor boosting**

---

## 18. Open questions (for Fred / future slices)

| # | Question | Blocks C1? | Notes |
|---|-----------|------------|--------|
| 1 | Which **local** detector library (if any) passes license, accuracy, and ops bars? | **Closed in Track C Slice C2** — see [`phase_7_language_detector_dependency_decision.md`](phase_7_language_detector_dependency_decision.md) (**recommended:** optional **`lingua-language-detector`**; **`NotConfigured`** remains default). | **—** |
| 2 | Enrichment failure policy: **warn vs fail ingest** when detector errors? | **No** | Decide in **C4** |
| 3 | Does Fred approve **7I** boosting **ever** for Phases 1–8? | **No** | Default **no** |
| 4 | Is **any** query-language detection required without EU metadata? | **No** | Optional future; not default |

---

## 19. Final recommendation

1. **C2 dependency research** is complete — [`phase_7_language_detector_dependency_decision.md`](phase_7_language_detector_dependency_decision.md) is the **gate** for **C3** before **C4–C5** land in code.
2. Keep **`NotConfigured`** as the **only** default until **B** is proven safe — equivalent to **Decision 1**’s “A until B.”
3. Wire detection to **ingestion enrichment** (**Decision 2A**) when ready.
4. Persist **artifact aggregation** (**Decision 3A**) once EU tags are meaningful.
5. Keep **`actor_context` recording-only** and **defer 7I** unless explicitly approved (**Decisions 5–6**).
6. **Defer translation** (**Decision 7A/B**).
7. Plan **C7** + doc updates so operators never confuse **context** with **evidence**.
8. Close with **C8** audit under **Audit Agent** rules.

---

## Addendum — Track C Slice C2 (language detector dependency research)

**Completed:** dependency research and primary recommendation recorded in **[`phase_7_language_detector_dependency_decision.md`](phase_7_language_detector_dependency_decision.md)** — **no** package added, **no** code changes. **Next:** **C3** adapter implementation behind config.

---

## References

- Phase contract: [`docs/phases/graph_clerk_phase_7_context_intelligence.md`](../phases/graph_clerk_phase_7_context_intelligence.md) (read-only; not edited by this slice)
- Baseline audit: [`docs/audits/PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md)
- Program: [`docs/plans/phase_1_8_completion_program.md`](../plans/phase_1_8_completion_program.md)
- Invariants: [`docs/governance/ARCHITECTURAL_INVARIANTS.md`](../governance/ARCHITECTURAL_INVARIANTS.md)
