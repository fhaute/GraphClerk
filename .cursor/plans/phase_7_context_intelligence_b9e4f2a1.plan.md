---
name: Phase 7 Context Intelligence plan
overview: "Working plan for [docs/phases/graph_clerk_phase_7_context_intelligence.md](docs/phases/graph_clerk_phase_7_context_intelligence.md): language metadata + ActorContext as routing/interpretation metadata only — **not** evidence or translation product. First coding slice: **7A** (`EvidenceEnrichmentService` no-op pass-through). Phase 8 model pipeline and Phase 9 IDE integration remain out of scope."
todos:
  - id: p7-slice-70
    content: "Slice 7.0 — Entry gate + plan alignment (Phase 6 pass_with_notes; Phase 5 partial; no backend code)."
    status: in_progress
  - id: p7-slice-7a
    content: "Slice 7A — EvidenceEnrichmentService shell: no-op enrichment; candidates unchanged; tests prove text/source_fidelity untouched."
    status: pending
  - id: p7-slice-7b
    content: "Slice 7B — Language metadata contract on EvidenceUnitCandidate (metadata_json path); no migration unless approved; no detection yet; no text modification."
    status: pending
  - id: p7-slice-7c
    content: "Slice 7C — LanguageDetectionService adapter shell (NotConfigured + deterministic/local test adapter); explicit unknown/low-confidence; no remote services; no translation."
    status: pending
  - id: p7-slice-7d
    content: "Slice 7D — Wire enrichment into text/Markdown + Phase 5 extractor persistence path after 7A–7C stable; preserve source_fidelity; regression tests Phase 2 + Phase 5 paths."
    status: pending
  - id: p7-slice-7e
    content: "Slice 7E — Artifact language aggregation into metadata_json if scoped; no first-class DB columns unless approved."
    status: pending
  - id: p7-slice-7f
    content: "Slice 7F — RetrievalPacket.language_context optional section; backward-compatible; query/evidence languages only; no translation."
    status: pending
  - id: p7-slice-7g
    content: "Slice 7G — ActorContext schema for POST /retrieve (optional); absent = unchanged behavior; invalid = clear failure; no boosting; no persistence."
    status: pending
  - id: p7-slice-7h
    content: "Slice 7H — RetrievalPacket.actor_context recording (used false/true); influences recorded-only; tests prove ActorContext does not create evidence."
    status: pending
  - id: p7-slice-7i
    content: "Slice 7I — Optional deterministic context boosting — DEFERRED until 7G/7H stable; separate approval required."
    status: pending
  - id: p7-slice-7j
    content: "Slice 7J — Docs/status: language metadata vs translation; ActorContext vs evidence; no translation-engine or memory-agent claims."
    status: pending
  - id: p7-slice-7k
    content: "Slice 7K — Phase 7 audit: docs/audits/PHASE_7_AUDIT.md after implementation slices."
    status: pending
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

- **Deferred** until **7G/7H** are stable; requires separate approval.
- Must remain visible in packet; must not bypass authorization; must not invent evidence.

### Slice 7J — Docs / status update

- Distinguish **language metadata** from **translation**.
- Distinguish **ActorContext** from **evidence**.
- Do not claim GraphClerk is a translation engine or autonomous memory agent.

### Slice 7K — Phase 7 audit

- Create **`docs/audits/PHASE_7_AUDIT.md`** after implementation slices land.
- Target outcome: **`pass`** or **`pass_with_notes`** per [`docs/governance/AUDIT_RULES.md`](../../docs/governance/AUDIT_RULES.md).

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
