# GraphClerk Phase 7 — Context Intelligence: Language and Actor Context

## Phase Dependency
This phase must only start after:

```text
Phase 0 — Governance Baseline
Phase 1 — Foundation and Core Architecture
Phase 2 — Text-First Ingestion and Evidence Units
Phase 3 — Semantic Index and Graph Layer
Phase 4 — File Clerk and Retrieval Packets
Phase 5 — Multimodal Ingestion
Phase 6 — Productization, UI, Evaluation, and Hardening
```

Phase 7 assumes:

```text
- Governance docs exist
- Cursor rules exist
- coding standards exist
- documentation standards exist
- status reporting exists
- audit rules exist
- FastAPI backend exists
- PostgreSQL works
- Qdrant works
- Artifact and EvidenceUnit models exist
- Text/Markdown ingestion works
- Multimodal ingestion works at the documented Phase 5 level
- Graph layer exists
- Semantic index search works
- File Clerk retrieval packets exist
- Context budget exists
- Retrieval logs exist
- Phase 6 UI/productization layer exists
- Phase 6 tests pass
- Phase 6 audit is pass or pass_with_notes
```

Cursor must not implement this phase unless Phase 6 is complete and status docs confirm it.

---

## Implementation status (current)

**Slices 7A–7H are implemented** in the backend with targeted tests; **Slice 7J** (docs/status honesty alignment per the Phase 7 working plan) and **Slice 7K** (audit) are complete — [`docs/audits/PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md) records **`pass_with_notes`** (2026-05-02). Remaining items are **explicit audit notes** (e.g. no production detector-by-default, no translation, **Slice 7I** boosting deferred), not unconditional “green” closure.

### Shipped baseline (honest)

- **`EvidenceEnrichmentService`** no-op shell (pass-through; preserves **`text`** / **`source_fidelity`**).
- **Language metadata contract** on **`EvidenceUnitCandidate`** / persistence via **`metadata_json`** (no mandatory migration for Phase 7 baseline).
- **`LanguageDetectionService`** adapter shell (**NotConfigured** / deterministic test adapters); **not** wired as automatic production detection on ingest by default.
- **Enrichment seam** wired into **text/Markdown** and **multimodal** candidate persistence paths using the **no-op** default enrichment.
- **`ArtifactLanguageAggregationService`** as a **pure** merge helper over evidence metadata projections (callers persist separately; ingestion artifact aggregation wiring remains deferred).
- **`RetrievalPacket.language_context`** derived from **selected evidence `metadata_json` only** (no detection / translation in packet assembly for this slice).
- **Optional `actor_context`** on **`POST /retrieve`** (`RetrieveRequest`) validated by API/schema.
- **`RetrievalPacket.actor_context`** (**`PacketActorContextRecording`**) — **`used`** / **`recorded_context`** / explicit **`influence`**; **no** route or evidence boost from ActorContext in this baseline.

### Explicitly not implemented (baseline gaps; non-exhaustive)

- **Real** automatic language detection in ingestion by default; **translation**; **query translation**.
- **Language-based** or **actor-based** boosting / personalization of retrieval ranks or routes (**Slice 7I** boosting is **deferred / cancelled** pending separate approval — see working plan).
- **Persisted actor memory**; ActorContext-driven **access-control** changes; **LLM** calls for context; **Phase 7**-specific UI productization (see **`docs/status/TECHNICAL_DEBT.md`**).

### Retrieval influence vs recording

**North-star (design principle — future approved capability only; not the shipped Phase 7 baseline):**

> Context can influence retrieval routes, but it must not become evidence.

In the **current** codebase baseline, **`language_context`** and request **`actor_context`** are **recorded on `RetrievalPacket`** for traceability; they **do not** alter route selection, evidence selection/ranking, graph traversal, context budget, warnings, confidence, or answer mode. Any **future** approved routing influence must remain **explicit** on the packet, respect evidence grounding, and must **not** introduce hidden retrieval or bypass access control.

---

## Purpose

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

The key principle (**north-star for future approved routing influence — not a claim about today’s recording-only baseline**) is:

> Context can influence retrieval routes, but it must not become evidence.

---

## Product Principle Preserved In This Phase

GraphClerk remains a local-first, graph-guided evidence-routing layer for RAG systems.

Phase 7 must not break the separation between:

```text
Source truth        → Artifacts and EvidenceUnits
Structured meaning → GraphNodes, GraphEdges, SemanticIndexes
Retrieval routing  → FileClerk and RetrievalPackets
Context priors     → LanguageContext and ActorContext
Answer synthesis   → Optional downstream consumer only
```

Language context and actor context are **routing and interpretation metadata**.

They are not source truth.

Bad architecture:

```text
Actor profile says project has risk → treat as evidence that project has risk
Translated evidence text → mark as verbatim source
User preference → bypass access controls
Language guess → silently rewrite evidence
```

Allowed architecture:

```text
User question
  ↓
LanguageContext + ActorContext
  ↓
FileClerk route interpretation
  ↓
SemanticIndex search / graph traversal / evidence selection
  ↓
RetrievalPacket records context influence
  ↓
Downstream answer layer may use packet guidance
```

---

## Core Objective

At the end of this phase, GraphClerk should support context-aware retrieval metadata without compromising source fidelity.

The target end state for Phase 7 is:

```text
- EvidenceUnits can carry language metadata
- Artifacts can aggregate detected language metadata from EvidenceUnits
- a shared EvidenceEnrichmentService exists
- a LanguageDetectionService exists behind an explicit adapter boundary
- language detection failures are explicit or represented as warnings
- /retrieve can optionally accept ActorContext
- RetrievalPackets can record language_context and actor_context
- FileClerk can record visible context influence
- actor context can be passed as request context without being treated as evidence
- query translation / query variants are supported only if explicitly scoped and recorded
- actor context boosting is supported only if visible in the packet
- tests prove context does not alter source evidence or bypass authorization
- docs/status updates are honest
- Phase 7 audit exists
```

This phase makes GraphClerk better at understanding the **request situation** without weakening evidence traceability.

---

## Scope

### Included

```text
- EvidenceUnit language metadata
- optional Artifact language aggregation
- EvidenceEnrichmentService
- LanguageDetectionService and adapter contract
- optional local language detection adapter
- language metadata tests
- RetrievalPacket language_context schema
- optional ActorContext request schema for /retrieve
- RetrievalPacket actor_context schema
- FileClerk visibility for context influence
- deterministic / explicit context influence rules
- tests proving ActorContext is not evidence
- tests proving language enrichment does not modify source text
- status docs update
- Phase 7 audit
```

### Excluded unless explicitly reopened

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

---

## Non-Negotiable Rules For This Phase

```text
1. ActorContext is not evidence.
2. LanguageContext is not evidence.
3. User beliefs must not be treated as facts.
4. User preferences must not override source-backed evidence.
5. ActorContext must not bypass access control.
6. Query translation, if used, must be recorded in the RetrievalPacket.
7. Source evidence must never be silently translated and marked verbatim.
8. Translated evidence previews, if ever stored, must be marked derived and linked to the original EvidenceUnit.
9. Language detection must not modify EvidenceUnit text.
10. Low-confidence language detection must be explicit.
11. Actor-context influence must be visible in the RetrievalPacket.
12. Context boosting must be deterministic or explainable.
13. Sensitive actor data must not be echoed unnecessarily.
14. No hidden LLM calls are allowed in core context enrichment unless explicitly scoped.
15. Every public class/function must have a docstring.
16. Status docs must be updated before phase completion.
17. Phase 7 audit must be created before phase completion.
```

---

# Core Concepts

## LanguageContext

LanguageContext describes the language state of a retrieval request and its evidence.

It answers:

```text
- What language did the user ask in?
- What language should the answer use?
- What source languages are present in selected evidence?
- Were translated query variants used?
- Were language warnings raised?
```

LanguageContext does not translate evidence by itself.

It records language decisions and evidence language metadata.

---

## ActorContext

ActorContext describes who is asking and what context may help interpret the request.

It can include:

```text
- actor_id
- preferred_name
- role
- active_project
- current_phase
- recent_topics
- expertise_level
- preferred_answer_language
- known_languages
- retrieval preferences
- permissions scope reference
```

ActorContext is a routing prior, not a source of truth.

It may influence:

```text
- semantic route selection
- ambiguity handling
- preferred answer language
- explanation depth
- retrieval options
```

It must not:

```text
- create evidence
- override evidence
- bypass authorization
- silently alter the answer
- leak private profile details unnecessarily
```

---

## EvidenceEnrichmentService

EvidenceEnrichmentService is a shared enrichment pipeline applied after extraction and before EvidenceUnit persistence.

Recommended flow:

```text
Artifact uploaded
  ↓
Modality router
  ↓
Extractor
  ↓
EvidenceUnitCandidate(s)
  ↓
EvidenceEnrichmentService
      - language detection
      - future metadata enrichment
  ↓
EvidenceUnit persistence
```

Extractors should extract.

Enrichers should annotate.

Persistence should create final EvidenceUnits.

---

# Phase 7 Tracks

## Track 7A — Language Awareness

### Purpose

Make source language and request language explicit.

This track prepares GraphClerk for multilingual retrieval without implementing a full translation product.

### Included

```text
- LanguageDetectionService
- LanguageDetectionAdapter contract
- EvidenceUnitCandidate language fields
- EvidenceUnit language metadata
- optional Artifact language aggregation
- language detection warnings
- tests for source text preservation
```

### Deferred

```text
- automatic query translation
- multilingual semantic index boosting
- translated evidence previews
- answer-language routing beyond metadata
- full RetrievalPacket language_context unless explicitly scoped in a later slice
```

### Language metadata fields

EvidenceUnit-level fields may be stored directly or inside `metadata_json`, depending on migration scope:

```text
language: optional string
language_confidence: optional float
language_detection_method: optional string
language_warnings: optional list[string]
```

Artifact-level metadata may include:

```text
primary_language: optional string
detected_languages: optional list[string]
language_confidence: optional float
```

### Language detection rules

```text
- Empty text → language null or unknown.
- Very short text → unknown or low confidence.
- Detection failure → explicit warning or controlled failure.
- Detection must not modify text.
- No silent guessing.
```

### Source fidelity rules

```text
Original text from source artifact → preserve existing source_fidelity
PDF/PPTX extracted text → extracted, detected source language
OCR output → extracted, detected OCR text language
Audio transcript → extracted, detected transcript language
Machine translation of evidence → derived, linked to original EvidenceUnit
```

Important invariant:

> A translated evidence text is never verbatim source evidence.

---

## Track 7B — ActorContext / User Backstory

### Purpose

Allow `/retrieve` to receive request-level actor context so the File Clerk can record or later use it as an explicit routing prior.

### Included first

```text
- ActorContext request schema
- RetrievalPacket actor_context schema
- FileClerk records context presence and allowed influence metadata
- no automatic boosting in first slice
- no persisted ActorProfile in first slice
```

### Deferred

```text
- persisted actor profiles
- automatic actor memory updates
- LLM-generated profile summaries
- route boosting based on recent topics
- complex permission integration
- decay / memory retention logic
```

### ActorContext request object example

```json
{
  "actor_id": "actor_fred",
  "role": "technical_builder",
  "active_project": "GraphClerk",
  "current_phase": "Phase 7",
  "recent_topics": [
    "language detection",
    "ActorContext",
    "RetrievalPacket"
  ],
  "preferred_answer_language": "en",
  "expertise_level": "intermediate_technical",
  "permissions_scope": ["graphclerk_repo"]
}
```

### RetrievalPacket actor_context example

```json
{
  "actor_context": {
    "used": true,
    "actor_profile_id": "actor_fred",
    "influences": [
      {
        "signal": "active_project",
        "value": "GraphClerk",
        "effect": "recorded as request context; no route boost applied in this slice",
        "confidence": 1.0
      }
    ],
    "warnings": []
  }
}
```

If no context is used:

```json
{
  "actor_context": {
    "used": false,
    "actor_profile_id": null,
    "influences": [],
    "warnings": []
  }
}
```

---

# RetrievalPacket Extensions

Phase 7 may extend the RetrievalPacket contract through explicit change-control.

## language_context

Suggested structure:

```json
{
  "language_context": {
    "user_query_language": "fr",
    "answer_language": "fr",
    "evidence_languages": ["en"],
    "query_translation_used": false,
    "query_variants": [
      {
        "language": "fr",
        "text": "Quels sont les risques du projet ?",
        "role": "original_user_query"
      }
    ],
    "translation_warnings": []
  }
}
```

## actor_context

Suggested structure:

```json
{
  "actor_context": {
    "used": true,
    "actor_profile_id": "actor_fred",
    "influences": [
      {
        "signal": "recent_topic",
        "value": "language detection",
        "effect": "boosted language-awareness semantic routes",
        "confidence": 0.72
      }
    ],
    "warnings": []
  }
}
```

### Packet extension rules

```text
- Packet schema changes require contract tests.
- Context sections must be optional and backwards-compatible where possible.
- Context influence must be visible and machine-readable.
- No actor context value may be treated as EvidenceUnit text.
- No translated query may be confused with source evidence.
```

---

# Query Translation Rules

Query translation is **not** required in the first Phase 7 slice.

If implemented later, the rules are strict:

Allowed:

```text
User asks in French.
GraphClerk creates an English retrieval query variant.
GraphClerk searches semantic indexes using original + translated variants.
GraphClerk retrieves English evidence.
RetrievalPacket records original query and translated query variant.
Downstream answer layer answers in French if configured.
```

Forbidden:

```text
GraphClerk silently translates source evidence and marks it verbatim.
GraphClerk hides translated query variants.
GraphClerk treats translated evidence as source truth.
GraphClerk changes EvidenceUnit text in place.
```

---

# Relationship With Permissions

ActorContext may include a permission scope reference, but authorization must remain separate.

Do not mix:

```text
Retrieval preference
Access rights
Source truth
```

Recommended separation:

```text
ActorContext → helps interpretation and routing
AuthorizationContext → decides what evidence can be retrieved
EvidenceUnits → source-backed facts
RetrievalPacket → records selected evidence and context influences
```

If evidence is excluded due to access rules, RetrievalPacket may record a non-disclosing warning:

```text
restricted_evidence_excluded
```

It must not reveal unauthorized document details.

---

# API Surface

## /retrieve extension

Phase 7 may extend `POST /retrieve` input with optional context objects.

Example:

```json
{
  "question": "What are the risks here?",
  "options": {
    "max_evidence_units": 8,
    "include_alternatives": true
  },
  "actor_context": {
    "actor_id": "actor_fred",
    "active_project": "GraphClerk",
    "recent_topics": ["language detection", "multimodal ingestion"],
    "preferred_answer_language": "en"
  }
}
```

### API rules

```text
- actor_context is optional.
- language hints are optional.
- absence of context must not break retrieval.
- invalid context must fail clearly.
- context must not bypass evidence selection or authorization.
```

---

# Data Model Strategy

## Minimal first implementation

Prefer metadata fields first.

Possible approach:

```text
EvidenceUnit.metadata_json.language
EvidenceUnit.metadata_json.language_confidence
EvidenceUnit.metadata_json.language_detection_method
Artifact.metadata_json.primary_language
Artifact.metadata_json.detected_languages
```

This avoids premature schema churn while still proving the enrichment flow.

If language becomes a stable query dimension later, promote fields to first-class columns through a migration.

## ActorContext persistence

Do not persist complex ActorContext in the first slice.

Start with request-supplied context and RetrievalLog / RetrievalPacket visibility.

Persisted profiles can come later:

```text
actor_profile
actor_project_context
actor_topic_memory
actor_language_preferences
actor_retrieval_preferences
```

or an event-backed memory model if governance requires stronger auditability.

---

# Services To Implement

## LanguageDetectionService

Responsible for:

```text
- detecting likely language of text-bearing candidates
- returning language, confidence, method, warnings
- handling short/empty/ambiguous text explicitly
```

Forbidden:

```text
- changing candidate text
- translating evidence
- creating retrieval query variants
- calling remote services unless explicitly scoped
```

## LanguageDetectionAdapter

Responsible for:

```text
- wrapping a concrete language detection implementation
- exposing a stable detect(text) contract
- failing explicitly when not configured
```

## EvidenceEnrichmentService

Responsible for:

```text
- applying enrichment steps to EvidenceUnitCandidates
- preserving original candidate text
- attaching metadata/warnings
- returning enriched candidates
```

Forbidden:

```text
- creating EvidenceUnits directly unless already part of existing persistence path
- mutating Artifacts
- performing retrieval
```

## ActorContextService

Responsible for:

```text
- validating ActorContext request objects
- normalizing optional fields
- producing context influence records
- redacting or excluding unsafe fields from packet output if needed
```

Forbidden:

```text
- treating actor context as evidence
- bypassing authorization
- persisting memory without explicit scope
```

## ContextInfluenceService

Optional later service responsible for:

```text
- applying deterministic retrieval boosts from ActorContext
- recording every boost reason
- ensuring boosts are visible in RetrievalPacket
```

This should not be implemented in the first ActorContext slice unless explicitly approved.

---

# Error Handling Requirements

Errors must be explicit.

Possible errors:

```text
LanguageDetectionUnavailableError
LanguageDetectionError
InvalidLanguageCodeError
InvalidActorContextError
ActorContextTooLargeError
ContextInfluenceError
QueryTranslationUnavailableError
QueryTranslationError
```

Rules:

```text
- Missing language detector should not crash ingestion unless strict mode is enabled.
- Failed detection should attach warning or fail according to configured policy.
- Invalid actor context should return a clear validation error.
- Actor context that exceeds configured limits should fail clearly.
- Query translation failures must be represented in language_context warnings if translation is optional.
```

---

# Required Tests

## Language metadata tests

```text
test_evidence_unit_candidate_can_carry_language_metadata
test_language_detection_does_not_modify_candidate_text
test_empty_text_language_is_null_or_unknown
test_short_text_language_has_low_confidence
test_language_detection_failure_adds_warning_or_fails_explicitly
test_artifact_detected_languages_aggregate_from_evidence_units
test_mixed_language_artifact_can_report_multiple_languages
```

## Source fidelity tests

```text
test_translated_evidence_preview_cannot_be_marked_verbatim
test_language_metadata_does_not_change_source_fidelity
test_pdf_pptx_language_metadata_keeps_extracted_fidelity
```

## RetrievalPacket language context tests

```text
test_retrieval_packet_can_include_language_context
test_language_context_records_query_language
test_language_context_records_evidence_languages
test_query_translation_variant_is_recorded_when_used
test_language_context_absent_or_empty_when_not_used
```

## ActorContext contract tests

```text
test_actor_context_schema_accepts_minimal_context
test_actor_context_not_required_for_retrieve
test_actor_context_rejects_invalid_language_code
test_actor_context_rejects_oversized_recent_topics
test_actor_context_is_not_treated_as_evidence
```

## ActorContext packet tests

```text
test_retrieval_packet_records_actor_context_not_used
test_retrieval_packet_records_actor_context_used_without_boosting
test_actor_context_influence_is_visible_when_applied
test_actor_context_sensitive_fields_are_not_echoed_unnecessarily
```

## Routing / safety tests

```text
test_active_project_boost_does_not_create_evidence
test_recent_topic_boost_does_not_override_source_evidence
test_actor_context_does_not_bypass_authorization
test_context_influence_records_reason_and_confidence
test_no_actor_context_preserves_phase_4_retrieve_behavior
```

---

# Documentation Requirements

Phase 7 must create or update:

```text
docs/phases/graph_clerk_phase_7_context_intelligence.md
docs/status/PROJECT_STATUS.md
docs/status/PHASE_STATUS.md
docs/status/KNOWN_GAPS.md
docs/status/TECHNICAL_DEBT.md
docs/audits/PHASE_7_AUDIT.md
README.md
```

Optional but recommended:

```text
docs/adr/ADR-0010-language-context-strategy.md
docs/adr/ADR-0011-actor-context-strategy.md
docs/contracts/RETRIEVAL_PACKET_CONTEXT_EXTENSIONS.md
```

## README must say

```text
Implemented:
- Language metadata on EvidenceUnits if implemented
- ActorContext in RetrievalPackets if implemented
- visible context influence if implemented

Limitations:
- GraphClerk is not a translation engine
- ActorContext is not evidence
- ActorContext does not bypass access control
- query translation is optional/deferred unless implemented
- persisted user memory is not implemented unless explicitly added
```

Do not claim GraphClerk understands the user like an autonomous memory agent.

Do not claim translated evidence is source truth.

---

# Phase 7 Audit Requirements

Create:

```text
docs/audits/PHASE_7_AUDIT.md
```

Audit must answer:

```text
- Does language metadata preserve source text?
- Are translated query variants recorded if used?
- Is translated evidence prevented from being marked verbatim?
- Does ActorContext remain separate from EvidenceUnits?
- Is ActorContext visible as routing influence, not source truth?
- Does ActorContext avoid bypassing authorization?
- Are sensitive actor fields handled safely?
- Are context influence reasons recorded?
- Did any hidden LLM/translation/memory behavior appear?
- Do README/status docs overclaim personalization or translation?
- Are tests sufficient for context boundaries?
```

Allowed audit result:

```text
pass
pass_with_notes
needs_fix
blocked
```

Phase 7 is not complete if audit result is `needs_fix` or `blocked`.

---

# Implementation Tasks

## Task 1 — Add Phase 7 planning and status docs *(historical kickoff — superseded)*

Original kickoff text asked to add Phase 7 to the roadmap as **`not_started`**. **Today:** Phase 7 **baseline is implemented** with audit **`pass_with_notes`** ([`docs/audits/PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md), 2026-05-02); `docs/status/*` and the roadmap reflect delivery — **do not** regress Phase 7 to **`not_started`**.

Archived kickoff acceptance:

```text
- Phase 7 doc exists
- roadmap mentions Phase 7 after Phase 6
```

Current baseline truth:

```text
- Slices 7A–7H shipped; 7J (docs/status honesty) and 7K (audit) complete per plan/status
- audit pass_with_notes on record; boosting (7I) deferred/cancelled pending separate approval
```

## Task 2 — Add EvidenceEnrichmentService shell

Create enrichment pipeline with no-op behavior first.

Acceptance:

```text
- existing ingestion still works
- candidates pass through unchanged
- tests prove text is not modified
```

## Task 3 — Add language metadata contract

Add candidate metadata fields or metadata_json mapping for language.

Acceptance:

```text
- language metadata can be carried
- source text is unchanged
- source_fidelity is unchanged
```

## Task 4 — Add LanguageDetectionService

Add adapter-based local language detection.

Acceptance:

```text
- detector returns language/confidence/method
- short/empty text handled explicitly
- failure behavior tested
```

## Task 5 — Add Artifact language aggregation

Aggregate languages from EvidenceUnits into Artifact metadata.

Acceptance:

```text
- single-language artifact reports primary language
- mixed-language artifact reports multiple languages
- evidence-level language remains more precise
```

## Task 6 — Add RetrievalPacket language_context

Extend packet schema through change-control.

Acceptance:

```text
- packet can include language_context
- absence of language_context remains valid if intended
- tests cover evidence language list and query language
```

## Task 7 — Add ActorContext schema to /retrieve

Allow optional ActorContext on retrieval requests.

Acceptance:

```text
- /retrieve works without actor_context
- /retrieve accepts minimal actor_context
- invalid actor_context fails clearly
```

## Task 8 — Record ActorContext in RetrievalPacket

Record context presence and allowed influence metadata.

Acceptance:

```text
- actor_context.used=false when absent
- actor_context.used=true when present
- no retrieval boosting yet unless explicitly scoped
- tests prove no evidence is created from actor context
```

## Task 9 — Optional deterministic context boosting

Apply limited route boosts from ActorContext.

Acceptance:

```text
- boosts are deterministic
- boosts are visible in packet
- boosts cannot create evidence
- boosts cannot bypass authorization
```

This task should not be implemented until Tasks 7–8 are stable.

## Task 10 — Update docs and status

Update README, status docs, known gaps, and technical debt.

Acceptance:

```text
- docs distinguish language metadata from translation
- docs distinguish actor context from evidence
- limitations are clear
```

## Task 11 — Add Phase 7 audit

Create audit file.

Acceptance:

```text
- audit result is pass or pass_with_notes
```

---

# Cursor Prompt Template For Phase 7 Tasks

Every Cursor prompt for this phase should begin with:

```text
You are working on GraphClerk Phase 7 — Context Intelligence: Language and Actor Context.
You must follow docs/governance/*.
ActorContext is a routing prior, not evidence.
LanguageContext is metadata and routing context, not source truth.
Do not silently translate evidence.
Do not bypass FileClerk, RetrievalPackets, or access-control boundaries.
Only modify the files listed below.
Add or update tests as specified.
Add docstrings to public classes/functions.
Update status docs only if this task requires it.
```

Then specify:

```text
Allowed files:
Forbidden files:
Task:
Acceptance criteria:
Required tests:
Documentation updates:
```

---

# Deliverables

At the end of Phase 7:

```text
- EvidenceEnrichmentService
- LanguageDetectionService
- language metadata on EvidenceUnits
- optional Artifact language aggregation
- RetrievalPacket language_context if scoped
- ActorContext request schema if scoped
- RetrievalPacket actor_context if scoped
- visible context influence records
- tests proving context does not become evidence
- tests proving language handling preserves source fidelity
- documentation/status updates
- Phase 7 audit
```

---

# Acceptance Criteria

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

# Known Non-Features After Phase 7

Depending on final slice scope, GraphClerk may still not support:

```text
- full translation engine
- persisted actor profiles
- automatic memory updates
- complex permission system
- LLM-generated user summaries
- multilingual semantic index boosting
- translated evidence previews
- answer-language routing
- cross-tenant actor context
```

These are acceptable if documented.

---

# Risks

## Risk 1 — ActorContext becomes fake evidence

If user profile data is treated as source truth, GraphClerk’s evidence model breaks.

Mitigation:

```text
- tests proving actor context does not create EvidenceUnits
- packet influence records separated from evidence_units
- audit checks
```

## Risk 2 — Language handling silently changes evidence

If evidence text is translated or rewritten without fidelity changes, source traceability breaks.

Mitigation:

```text
- language detection does not modify text
- translated evidence must be derived
- tests for source preservation
```

## Risk 3 — Query translation hides retrieval changes

Translated query variants can improve recall but reduce transparency if hidden.

Mitigation:

```text
- record query variants in language_context
- warnings for failed/low-confidence translation
```

## Risk 4 — Sensitive actor data leaks

Actor profiles can contain private context.

Mitigation:

```text
- minimal request-supplied context first
- no persisted memory in first slice
- redaction rules
- avoid echoing sensitive fields unnecessarily
```

## Risk 5 — Context boosting bypasses authorization

A strong actor prior could accidentally retrieve unauthorized evidence if mixed with permissions.

Mitigation:

```text
- keep AuthorizationContext separate
- test that actor context cannot bypass evidence access rules
```

## Risk 6 — Scope creep into personalization agent

ActorContext can turn into an autonomous memory assistant if uncontrolled.

Mitigation:

```text
- Phase 7 starts with request context only
- persistent memory deferred
- no automatic profile updates without approval
```

---

# Suggested Duration

```text
Fast mode: 1–2 weeks
Clean mode: 3–6 weeks
```

A fast version should prioritize:

```text
- EvidenceEnrichmentService shell
- language metadata contract
- local language detection adapter
- ActorContext request schema
- RetrievalPacket context sections
- tests and audit
```

---

# Phase Completion Definition

**Baseline closure (shipped and audited in this repository):** Phase 7 **baseline** is satisfied when GraphClerk represents language and actor **routing/interpretation metadata** explicitly (including on `EvidenceUnitCandidate` / `metadata_json` and on `RetrievalPacket`), preserves source fidelity, records **`language_context`** and request **`actor_context`** on packets **without** using them to alter route selection, evidence selection/ranking, traversal, budget, warnings, confidence, or answer mode — as verified by tests and [`docs/audits/PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md) (**`pass_with_notes`**). **Slice 7I** (deterministic context boosting) is **deferred / cancelled** pending **separate approval** and must not be assumed from baseline closure. This baseline does **not** require empirical proof that context **improves** retrieval ranks or routes; it requires **honest recording and traceability**, not behavioral uplift.

**Product / north-star (not required for baseline closure):** Future work might seek context that **influences** retrieval under explicit packet-visible rules; that is **out of scope** for the audited **`pass_with_notes`** baseline above.

The **delivered** output is **controlled context metadata and recording**, not a personalization, translation, or boosting product.
