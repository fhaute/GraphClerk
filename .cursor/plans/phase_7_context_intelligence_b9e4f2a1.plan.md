---
name: Phase 7 Context Intelligence plan
overview: "Working plan for [docs/phases/graph_clerk_phase_7_context_intelligence.md](docs/phases/graph_clerk_phase_7_context_intelligence.md): language metadata + ActorContext as routing/interpretation metadata only — **not** evidence or translation product. Baseline slices **7A–7H** implemented; **7I** boosting deferred/cancelled; **7J** docs/status complete; **7K** audit complete (`docs/audits/PHASE_7_AUDIT.md`, pass_with_notes). Phase 8 / Phase 9 remain out of scope."
todos:
  - id: p7-slice-70
    content: "Slice 7.0 — Entry gate + plan alignment (Phase 6 pass_with_notes; Phase 5 partial; no backend code)."
    status: completed
  - id: p7-slice-7a
    content: "Slice 7A — EvidenceEnrichmentService shell: no-op enrichment; candidates unchanged; tests prove text/source_fidelity untouched."
    status: completed
  - id: p7-slice-7b
    content: "Slice 7B — Language metadata contract on EvidenceUnitCandidate (metadata_json path); no migration unless approved; no detection yet; no text modification."
    status: completed
  - id: p7-slice-7c
    content: "Slice 7C — LanguageDetectionService adapter shell (NotConfigured + deterministic/local test adapter); explicit unknown/low-confidence; no remote services; no translation."
    status: completed
  - id: p7-slice-7d
    content: "Slice 7D — Wire enrichment into text/Markdown + Phase 5 extractor persistence path after 7A–7C stable; preserve source_fidelity; regression tests Phase 2 + Phase 5 paths."
    status: completed
  - id: p7-slice-7e
    content: "Slice 7E — ArtifactLanguageAggregationService implemented (pure merge helper over EU metadata projections); Artifact.metadata_json persistence / ingestion wiring deferred."
    status: completed
  - id: p7-slice-7f
    content: "Slice 7F — RetrievalPacket.language_context optional section; backward-compatible; query/evidence languages only; no translation."
    status: completed
  - id: p7-slice-7g
    content: "Slice 7G — ActorContext schema for POST /retrieve (optional); absent = unchanged behavior; invalid = clear failure; no boosting; no persistence."
    status: completed
  - id: p7-slice-7h
    content: "Slice 7H — RetrievalPacket.actor_context recording (used false/true); influences recorded-only; tests prove ActorContext does not create evidence."
    status: completed
  - id: p7-slice-7i
    content: "Slice 7I — Deterministic context boosting: cancelled/deferred for Phase 7 baseline; separate approval + evaluation fixtures + audit criteria required (see plan § Slice 7I)."
    status: cancelled
  - id: p7-slice-7j
    content: "Slice 7J — Docs/status: language metadata vs translation; ActorContext vs evidence; no translation-engine or memory-agent claims."
    status: completed
  - id: p7-slice-7k
    content: "Slice 7K — Phase 7 audit: docs/audits/PHASE_7_AUDIT.md after implementation slices."
    status: completed
isProject: false
---

# Phase 7 — Context Intelligence: Language and Actor Context

**Reminder:** **Context can influence retrieval routes, but must never become evidence.**

Phase contract: [`docs/phases/graph_clerk_phase_7_context_intelligence.md`](../../docs/phases/graph_clerk_phase_7_context_intelligence.md).

---

## Phase purpose (from phase doc)

Add a controlled context-intelligence layer to GraphClerk.

Phase 7 is not about making GraphClerk a chatbot, a memory agent, or a translation engine.

It is about helping the File Clerk understand two things more explicitly:

```text
1. Language context
   - What language is the user asking in?
   - What language is the evidence in?
   - What language should downstream answers use?
   - Was a query translation or language bridge used?

2. Actor context
   - Who is asking?
   - What project, role, expertise level, or recent topic may disambiguate the request?
   - What answer language or explanation style is preferred?
   - What permissions or scope constraints apply?
```

The goal is to improve retrieval orientation while preserving GraphClerk’s core evidence discipline.

The key principle is:

> Context can influence retrieval routes, but it must not become evidence.

---

## Entry conditions

- Phase 6 audit **`pass_with_notes`** ([`docs/audits/PHASE_6_AUDIT.md`](../../docs/audits/PHASE_6_AUDIT.md)).
- Phase 5 remains **partial** / **`pass_with_notes`** — not claimed complete.
- **`POST /answer`** deferred; no `LocalRAGConsumer` / `AnswerSynthesizer` in scope for Phase 7 kickoff or early slices.
- OCR / ASR / captioning / video not claimed implemented (Phase 5 honesty preserved).
- Phase 8 (specialized model pipeline) and Phase 9 (IDE integration): phase docs may exist; **no implementation started** — do not implement Phase 8/9 work inside Phase 7.

---

## Non-scope (exclusions + explicit guardrails)

From phase doc — **Excluded unless explicitly reopened:**

```text
- full translation engine
- silent query translation
- translated evidence stored as source truth
- translated evidence marked verbatim
- LLM-based profile summarization
- automatic persistent user memory
- automatic actor profile updates
- complex authorization system
- enterprise identity management
- sensitive personal data expansion
- cross-tenant actor context
- answer synthesis changes unless packet-bound
- hidden retrieval outside FileClerk
- UI personalization beyond displaying packet fields
```

Additionally for sequencing and honesty:

- No **`/answer`**, **`LocalRAGConsumer`**, or **`AnswerSynthesizer`** work in Phase 7 unless a future slice explicitly scopes packet-bound synthesis only (still separate from retrieval).
- No Phase 8 model-pipeline work.
- No hidden retrieval outside **FileClerk** / **RetrievalPacket** boundaries.
- No silent fallbacks; failures explicit.
- Do not rename protected GraphClerk terms ([`docs/governance/CHANGE_CONTROL.md`](../../docs/governance/CHANGE_CONTROL.md)).
- **Query translation** is **not** part of the first implementation slices (see Slice 7F notes).
- **No LLM calls** in core context enrichment unless explicitly scoped later.
- **No persisted actor memory** in early slices.

---

## Slices (7.0–7K)

### Slice 7.0 — Entry gate + plan alignment

- Verify Phase 6 **`pass_with_notes`**, Phase 5 partial, `/answer` deferred, multimodal limits honest.
- Set Phase 7 as next active **implementation** phase in status docs when planning completes.
- **No backend code.**

### Slice 7A — EvidenceEnrichmentService shell

- No-op enrichment pipeline; candidates pass through unchanged.
- **Allowed (typical):** `backend/app/services/evidence_enrichment_service.py`, `backend/tests/test_phase7_evidence_enrichment_service.py`, `backend/app/services/__init__.py` only if needed.
- **Forbidden:** `backend/app/api/**`, `retrieval_packet.py`, retrieve request schemas, `file_clerk_service.py`, `multimodal_ingestion_service.py` (unless a later slice explicitly requires), frontend, migrations, language-detection deps.
- Tests prove **text** and **source_fidelity** are not modified.

### Slice 7B — Language metadata contract

- **EvidenceUnitCandidate** may carry language fields via **`metadata_json`** (or equivalent) — **no DB migration** unless separately approved.
- No language detection yet; **no text modification.**

### Slice 7C — LanguageDetectionService adapter shell

- **LanguageDetectionAdapter** contract; **NotConfigured** or deterministic/local test adapter.
- Explicit unknown / low-confidence behavior; **no remote services**; **no translation.**

### Slice 7D — Evidence enrichment integration

- Wire enrichment into **text/Markdown** and existing **extractor → candidate persistence** paths only after **7A–7C** are stable.
- Preserve **text** / **source_fidelity**; regression coverage for Phase 2 + Phase 5 paths.

### Slice 7E — Artifact language aggregation

- Aggregate detected languages into **Artifact** `metadata_json` if scoped.
- **No** first-class DB columns unless separately approved.
- **Implementation (service-only):** `ArtifactLanguageAggregationService` in `backend/app/services/artifact_language_aggregation_service.py` returns a **new** metadata dict with `graphclerk_language_aggregation`; callers persist separately — **not** wired into ingestion in this slice.

#### Slice 7E — Design notes (artifact aggregation, design-only)

**Recommended option:** **D — minimal sequencing (“A now, wire later”)** — ship **`ArtifactLanguageAggregationService`** (+ focused unit tests) as a **pure, DB-free** function over evidence-level language projections **before** coupling ingestion. **Do not choose C** (ingestion wiring) in the same slice as first implementation: default enrichment is still no-op and persisted **`EvidenceUnit.metadata_json`** rarely carries **`language`** today, so transactional aggregation would mostly emit empty/warning shapes and blur ownership with caller-supplied artifact metadata. **B** (defer all code) is weaker than **A** because the aggregation contract and tests stabilize **`metadata_json`** merge rules early.

**Rationale (PM / sequencing):** Avoid silent “aggregation” that looks authoritative while EU language fields are absent; avoid overwriting **`Artifact.metadata_json`** keys supplied at **`create_from_bytes`**. A standalone service proves merge semantics and numeric summaries without API or migration churn; ingestion wiring becomes a **follow-up** slice once enrichment reliably sets EU language metadata (or explicitly-approved manual metadata paths exist).

**1 — Aggregation output shape (proposal)** — Store under a **single namespaced sub-key** on **`artifact.metadata_json`** (sibling keys preserved), e.g. **`graphclerk_language_aggregation`** (avoids collision with user **`language_context`** / retrieval naming):

```json
{
  "graphclerk_language_aggregation": {
    "version": 1,
    "source": "evidence_unit_metadata_json",
    "languages": [
      {
        "language": "en",
        "evidence_unit_count": 4,
        "average_confidence": 0.91,
        "min_confidence": 0.8,
        "max_confidence": 0.95
      }
    ],
    "primary_language": "en",
    "distinct_language_count": 1,
    "evidence_units_without_language_metadata_count": 0,
    "warnings": []
  }
}
```

**2 — Unknown / null language entries:** Prefer **counts, not fake ISO rows**: bucket only EUs where **`metadata_json.language`** is a **non-null string**. Track **`evidence_units_without_language_metadata_count`** separately (covers missing key, **`language: null`**, or empty-string policy if later tightened). Optionally include **`warnings`** such as **`partial_evidence_language_metadata`** when that count &gt; 0. Do **not** infer language from absence.

**3 — Low-confidence representation:** Carry **per-language** **`min_confidence`**, **`max_confidence`**, **`average_confidence`** from EU **`language_confidence`** when present; when confidence absent for some units in a bucket, document rule explicitly (**e.g.** exclude from average denominator or treat as **null** contribution — choose one in implementation; no guessing). Add **`warnings`** like **`low_average_confidence`** only if product wants a threshold **without** inventing new detection.

**4 — Transaction vs recompute:** **Phase 1 implementation:** pure **`aggregate_for_evidence_metadata(rows: list[dict[str, Any]]) -> dict[str, Any]`** (or equivalent) — **no DB inside service**. Callers may invoke **after** EU persistence in the **same transaction** once wired, passing **`metadata_json`** snapshots read from created rows—**separate approval** for wiring. Optional future: **`recompute_artifact_language_metadata(session, artifact_id)`** batch job—out of scope for minimal 7E.

**5 — Avoid overwriting user artifact metadata:** **Never replace** entire **`metadata_json`**. **Deep-merge only** the **`graphclerk_language_aggregation`** key (replace subtree wholesale when recomputing that subtree). Preserve **`title`**, **`pages`**, or any user-supplied keys from ingest request metadata.

**6 — Traceability:** **`source": "evidence_unit_metadata_json"`** + **`version`**. **v1** omit per-EU IDs in aggregate to limit packet size and PII surface; if IDs are needed later, add **`evidence_unit_ids_by_language`** behind an explicit flag/version bump—not default.

**7 — No EU language metadata:** Emit subtree with **`languages": []`**, **`primary_language": null`**, **`distinct_language_count": 0`**, **`warnings": ["no_evidence_language_metadata"]`** **or** omit **`graphclerk_language_aggregation`** entirely—pick one policy in implementation (**explicit-empty subtree** preferred for honesty vs silent omission).

**8 — Wire now?** **No for first merge** — implement **service + tests** only (**A**). Re-evaluate wiring (**C-like**) once enrichment populates EU language fields routinely (**after** detection-backed enrichment is approved and scoped).

**9 — Tests required:** Empty EU list; all EUs missing language keys; mixed **`language`** codes; mixed confidence / missing confidence; multiple langs → **`primary_language`** tie-break rule (**document**: e.g. highest **count**, then highest **average_confidence**); merge preserves unrelated artifact metadata keys; **never** mutates EU text/**`source_fidelity`** (service receives dicts only).

**10 — Allowed files (when implemented):** Likely **`backend/app/services/artifact_language_aggregation_service.py`**, **`backend/tests/test_phase7_artifact_language_aggregation_service.py`**. **Forbidden until separately scoped:** **`backend/app/api/**`**, retrieval schemas, **`Artifact` model columns**, migrations. **Wiring** touchpoints (**`text_ingestion_service.py`**, **`multimodal_ingestion_service.py`**, **`artifact_service.py`**) require **explicit follow-up approval**.

### Slice 7F — RetrievalPacket `language_context`

- Optional packet section; **backward-compatible**.
- Records query language / evidence languages when available; **no translation** in early slices.

### Slice 7G — ActorContext schema for `/retrieve`

- Optional request object; **`POST /retrieve`** unchanged when absent.
- Invalid context fails clearly (**400**/validation), not silent fallback.
- **No boosting**, **no persistence.**

### Slice 7H — RetrievalPacket `actor_context` recording

- `actor_context.used=false` when absent; `used=true` when present.
- Influence records: **recorded only; no route boost applied** until Slice 7I is approved.
- Tests prove **ActorContext does not create EvidenceUnits** or substitute for evidence.

### Slice 7I — Optional deterministic context boosting

**Status: deferred / cancelled for the current Phase 7 baseline** (no implementation in-tree now). **7G** and **7H** are complete: **ActorContext** is accepted on requests and recorded on **`RetrievalPacket`** with explicit **`influence`** metadata, but it **must not** affect retrieval until boosting is re-approved.

**Why not implement boosting in Phase 7 now**

- **ActorContext** is wired for transparency only; using it to rerank routes or evidence without **evaluation fixtures**, **deterministic rules**, and **audit criteria** risks silent overrides of evidence-grounded behavior.
- Any future boosting work requires **separate approval** and must:
  - ship **evaluation fixtures** (reproducible inputs/expected boundaries);
  - **prove** ActorContext cannot override evidence or bypass **source grounding**;
  - **record influence** on **`RetrievalPacket`** (no hidden retrieval);
  - **not** bypass **access control**;
  - **not** personalize or trigger **hidden retrieval** paths.

**Slice 7J** (**docs/status**) is **complete** for the Phase 7 baseline honesty pass; **Slice 7K** — audit artifact **`docs/audits/PHASE_7_AUDIT.md`** filed (**`pass_with_notes`**, 2026-05-02).

### Slice 7J — Docs / status update

**Done for baseline:** README, `docs/status/*` (incl. `PROJECT_STATUS`, `PHASE_STATUS`, `ROADMAP`, `KNOWN_GAPS`, `TECHNICAL_DEBT`), and phase doc **Implementation status (current)** aligned — Phase **7** baseline implemented; **`PHASE_7_AUDIT.md`** (**`pass_with_notes`**); **7I** boosting deferred/cancelled.

- Distinguish **language metadata** from **translation**.
- Distinguish **ActorContext** from **evidence**.
- Do not claim GraphClerk is a translation engine or autonomous memory agent.

### Slice 7K — Phase 7 audit

**Complete:** [`docs/audits/PHASE_7_AUDIT.md`](../../docs/audits/PHASE_7_AUDIT.md) — result **`pass_with_notes`** (2026-05-02); status docs + README aligned. **`pass`** was not claimed due to explicit deferred detector/translation/boosting/UI debt.

- Target rule reference: [`docs/governance/AUDIT_RULES.md`](../../docs/governance/AUDIT_RULES.md).

---

## Acceptance criteria (phase doc — verbatim)

```text
Given text-bearing EvidenceUnits,
when language enrichment runs,
then language metadata is attached without changing source text.

Given a mixed-language artifact,
when language aggregation runs,
then Artifact metadata can represent multiple detected languages.

Given a user query with language context,
when a RetrievalPacket is created,
then language_context records query language and evidence languages if scoped.

Given ActorContext is absent,
when /retrieve is called,
then Phase 4 retrieval behavior remains unchanged.

Given ActorContext is present,
when /retrieve is called,
then the packet records actor context use without treating actor fields as evidence.

Given ActorContext suggests a route,
then no evidence is created and no unauthorized evidence is retrieved.

Given query translation is used,
then translated query variants are recorded.

Given evidence is translated in a future slice,
then translated text is marked derived and linked to the original EvidenceUnit.

Given pytest is run,
then all Phase 7 tests pass.

Given docs are inspected,
then they do not claim GraphClerk is a translation engine, autonomous memory system, or user-profile truth engine.

Given the Phase 7 audit is inspected,
then the result is pass or pass_with_notes.
```

---

## Risks (phase doc — Risks 1–6)

### Risk 1 — ActorContext becomes fake evidence

If user profile data is treated as source truth, GraphClerk’s evidence model breaks.

Mitigation:

```text
- tests proving actor context does not create EvidenceUnits
- packet influence records separated from evidence_units
- audit checks
```

### Risk 2 — Language handling silently changes evidence

If evidence text is translated or rewritten without fidelity changes, source traceability breaks.

Mitigation:

```text
- language detection does not modify text
- translated evidence must be derived
- tests for source preservation
```

### Risk 3 — Query translation hides retrieval changes

Translated query variants can improve recall but reduce transparency if hidden.

Mitigation:

```text
- record query variants in language_context
- warnings for failed/low-confidence translation
```

### Risk 4 — Sensitive actor data leaks

Actor profiles can contain private context.

Mitigation:

```text
- minimal request-supplied context first
- no persisted memory in first slice
- redaction rules
- avoid echoing sensitive fields unnecessarily
```

### Risk 5 — Context boosting bypasses authorization

A strong actor prior could accidentally retrieve unauthorized evidence if mixed with permissions.

Mitigation:

```text
- keep AuthorizationContext separate
- test that actor context cannot bypass evidence access rules
```

### Risk 6 — Scope creep into personalization agent

ActorContext can turn into an autonomous memory assistant if uncontrolled.

Mitigation:

```text
- Phase 7 starts with request context only
- persistent memory deferred
- no automatic profile updates without approval
```

---

## Testing expectations

- After each behavior-affecting backend slice: run **`python -m pytest`** from **`backend/`** (Testing Agent charter).
- Do not remove or weaken tests to pass.
- Integration tests: only with documented env (`RUN_INTEGRATION_TESTS`, `DATABASE_URL`, `QDRANT_URL` as applicable).
- **RetrievalPacket** / request schema changes require contract tests before claiming completeness.

---

## Status-documentation expectations

- Update **`docs/status/*`** and README honest-status sections when **shipped behavior**, **public API contracts**, **phase scope**, or **honest “not implemented”** claims change (Status Documentation Agent).
- Do **not** mark Phase 7 **implemented** or individual slices **complete** until the work and tests exist.
- Keep Phase 5 **partial**; Phase 6 **`pass_with_notes`**; Phase 8 **not started**.

---

## Recommended first coding slice

**Slice 7A only** — `EvidenceEnrichmentService` no-op shell + unit tests proving pass-through and fidelity preservation. **Do not** wire into ingestion, add detection, or touch **`POST /retrieve`** in the same slice unless explicitly re-scoped.

---

**Reminder:** **Context can influence retrieval routes, but must never become evidence.**
