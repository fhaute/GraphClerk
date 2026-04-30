---
name: Phase 4 File Clerk Plan
overview: "Phase 4 mandatory delivery: POST /retrieve returning structured, validated RetrievalPackets plus honest RetrievalLog persistence. Reuses Phase 3 semantic search and bounded traversal via thin services—no god-service FileClerk, no chunk-RAG bypass, no hidden retrieval. Optional POST /answer, LocalRAGConsumer, and AnswerSynthesizer are explicitly deferred until a separate Slice I draft is approved after /retrieve is complete."
todos:
  - id: p4-slice-protocol
    content: "For each slice A–H: publish pre-slice draft (name, files, responsibilities, contracts, errors, tests, acceptance, non-scope); no implementation until user approves that slice."
    status: completed
  - id: p4-schemas-contracts
    content: Slice A — RetrievalPacket Pydantic schemas + contract tests + retrieval-specific domain errors (required fields per phase doc).
    status: completed
  - id: p4-query-intent
    content: Slice B — Deterministic QueryIntentService + tests (controlled intent vocabulary).
    status: completed
  - id: p4-route-selection
    content: "Slice C — RouteSelectionService: invokes SemanticIndexSearchService internally, selects primary/alternatives + reasons; FileClerk does not call search directly."
    status: completed
  - id: p4-evidence-selection
    content: "Slice D — EvidenceSelectionService: EvidenceUnits only via graph support links on traversed nodes/edges + tests."
    status: completed
  - id: p4-context-budget
    content: "Slice E — ContextBudgetService: caps + visible pruning_reasons + tests."
    status: completed
  - id: p4-packet-builder
    content: "Slice F — RetrievalPacketBuilder: validate/assemble packet; no-match and low-evidence packets per locked rules + tests."
    status: completed
  - id: p4-retrieval-log-migration-fileclerk
    content: Slice G — Start with Alembic migration retrieval_log.retrieval_packet (nullable JSONB) + model; RetrievalLog write helper; FileClerkService orchestration only + persistence + tests (no /retrieve route yet).
    status: completed
  - id: p4-retrieve-endpoint
    content: Slice H — POST /retrieve + wire in main + HTTP mapping + integration-gated tests as needed.
    status: completed
  - id: p4-slice-i-deferred
    content: "Slice I (NOT in Phase 4) — Cancelled unless separately approved: POST /answer, LocalRAGConsumer, AnswerSynthesizer not implemented."
    status: cancelled
  - id: p4-docs-audit
    content: Slice J — README/status/ROADMAP + docs/audits/PHASE_4_AUDIT.md (+ optional PHASE_4 summary doc); document Slice I not implemented unless approved.
    status: completed
isProject: false
---

# Phase 4 — File Clerk and Retrieval Packets (plan)

Canonical specification: [docs/phases/graph_clerk_phase_4_file_clerk_retrieval_packets.md](docs/phases/graph_clerk_phase_4_file_clerk_retrieval_packets.md).

## Core rule (mandatory vs optional)

- **Mandatory (Phase 4 closure)**: `POST /retrieve` returns a **structured, valid `RetrievalPacket`** (JSON) for every request, including failure and empty-match cases, with explicit warnings and `answer_mode` as required by locked rules below.
- **Optional (not part of default Phase 4)**: `POST /answer`, `LocalRAGConsumer`, `AnswerSynthesizer` — **Slice I is not approved automatically**. After Slice H is done and tested, a **separate Slice I draft** must be written and **explicitly approved** before any `/answer` code lands.

## Hard boundary (non-negotiable)

- No multimodal ingestion
- No PDF/PPTX/media ingestion
- No automatic graph extraction
- No autonomous agent loops
- No cloud LLM requirement
- No production UI
- No chunk-RAG bypass around FileClerk
- No hidden retrieval inside answer synthesis (when Slice I exists, answer path is packet-only; until then, no answer path)

## Locked decisions

### 1. RetrievalLog persistence

- Add nullable **`retrieval_log.retrieval_packet`** column as **`JSONB`** via a **dedicated Alembic migration**.
- **Timing**: migration lands at the **start of the slice that first persists packets** (Slice G — see below), not before schemas/services are ready unless we split migration-only; preferred is **first commit of Slice G** = migration + model + write path.
- The JSONB snapshot is the **canonical logged RetrievalPacket**.
- Continue populating existing summary fields on `RetrievalLog` where useful for debugging/queries (`selected_indexes`, `graph_path`, `evidence_unit_ids`, `warnings`, etc.) without pretending they replace the full packet.

### 2. FileClerkService role (orchestration only, not a god service)

`FileClerkService` **orchestrates only**. It must remain a coordinator with injected collaborators.

**May call**

- `QueryIntentService`
- `RouteSelectionService` (this service **owns** invocation of `SemanticIndexSearchService` so FileClerk does not call search/vector/embeddings directly—keeps orchestration thin)
- `GraphTraversalService`
- `EvidenceSelectionService`
- `ContextBudgetService`
- `RetrievalPacketBuilder`
- RetrievalLog persistence (via a small dedicated helper/repository pattern—not ad-hoc SQL in FileClerk)

**Must not**

- Invent evidence or include EvidenceUnits not justified by graph support links on returned graph nodes/edges
- Mutate graph, artifacts, or semantic indexes
- Generate final user-facing prose (that is Slice I only, template/local-first, and deferred)
- Bypass `EvidenceSelectionService` to load evidence directly
- Perform hidden retrieval outside the documented pipeline (no direct Qdrant/Postgres evidence reads except through the listed services)

### 3. No semantic match behavior

If semantic search yields **no usable indexed semantic indexes** (empty list after search + route selection policy), `/retrieve` must still return a **valid** `RetrievalPacket` with:

- `warnings` includes a machine-readable entry such as **`no_semantic_index_match`** (exact string to be fixed in Slice F contract)
- `answer_mode`: **`not_enough_evidence`**
- `selected_indexes`, `graph_paths`, `evidence_units` (and related sections) empty **as appropriate**, still structurally valid

This is **not** an HTTP error unless the request itself is invalid.

### 4. Evidence source rule

Evidence in the packet must come **only** from **graph support links** (`GraphNodeEvidence`, `GraphEdgeEvidence`) attached to **graph nodes and edges present** in the traversal output. No free-text chunk search, no vector dump of arbitrary EvidenceUnits, no repository-wide EvidenceUnit scans.

### 5. Optional `/answer` (Slice I — deferred)

- **Not implemented** until a **separate Slice I plan** is drafted and **explicitly approved** after Slice H.
- If approved later:
  - `LocalRAGConsumer` consumes **RetrievalPackets only**
  - `AnswerSynthesizer` is **template / local-first** initially; **no LLM required**
  - No hidden semantic search, graph traversal, DB lookup, or Qdrant calls
  - Answer must respect `answer_mode` and `warnings` from the packet

### 6. Shared semantic search wiring

If extracting a shared factory from [`backend/app/api/routes/semantic_indexes.py`](backend/app/api/routes/semantic_indexes.py) (e.g. `_build_search_service`) for reuse by `RouteSelectionService` / FileClerk wiring:

- Must be **behavior-preserving** for existing `GET /semantic-indexes/search`
- Any change to search semantics requires an **explicitly scoped** follow-up + tests (default: **no behavior change**)

## Slice execution protocol (required)

For **each slice A through H** (and Slice J), **before any implementation**:

1. Publish a slice draft containing:
   - slice name
   - expected files to change
   - responsibilities
   - contracts / schemas
   - error behavior
   - required tests
   - acceptance criteria
   - explicit non-scope
2. **Wait for user approval** of that slice draft.
3. Only then implement the slice (proceed slice-by-slice).

Slice I follows the same protocol but only **after** Slice H is accepted/merged and a standalone Slice I draft is approved.

## Implementation slices (mandatory path: A → H, then J)

### Slice A — RetrievalPacket contracts + errors

- Pydantic models for `RetrievalPacket` and nested structures per phase doc required fields.
- Domain errors only as needed for slices A–H (avoid unused exception types).

### Slice B — QueryIntentService

- Deterministic/local-first intent classification (`explain`, `compare`, `locate`, `summarize`, `debug`, `recommend`, `unknown`) + confidence + notes.

### Slice C — RouteSelectionService

- Inputs: question + intent (optional) + **results from `SemanticIndexSearchService`** (internal to this service).
- Outputs: primary + alternative routes with `selection_reason`.
- Implements policy for alternatives (deterministic “closeness” rule documented in slice draft).

### Slice D — EvidenceSelectionService

- Inputs: traversal output (nodes/edges) + graph evidence link rows.
- Outputs: ordered, deduped evidence candidates with traceability to support links.

### Slice E — ContextBudgetService

- Enforces caps from phase doc defaults unless overridden by `/retrieve` options.
- Emits visible `pruning_reasons`.

### Slice F — RetrievalPacketBuilder

- Assembles final packet object; validates required fields.
- Implements **locked no-match** and low-evidence behaviors.

### Slice G — RetrievalLog migration + FileClerkService (no HTTP yet)

- **First deliverable in this slice**: Alembic migration adds `retrieval_log.retrieval_packet` JSONB nullable + SQLAlchemy model update.
- Implement `FileClerkService` orchestration + persistence write (canonical JSONB + summary fields).
- **Does not** add `POST /retrieve` yet (keeps API surface unchanged until Slice H).

**Process note (Phase 4 closure):** Slice G and Slice H were **delivered together** during implementation. This is a **process note only** and does **not** indicate missing functionality: migration `0004_phase4_retrieval_packet_log`, model, repository, `FileClerkService` persistence, and `POST /retrieve` are all present in the codebase.

### Slice H — `POST /retrieve`

- FastAPI route, request/response models, wiring to `FileClerkService`.
- HTTP mapping for true client/request failures only; “no semantic match” remains **200 + valid packet**.

### Slice J — Docs, status, Phase 4 audit

- Update README + `docs/status/*` + ROADMAP Phase 4 entry.
- Add `docs/audits/PHASE_4_AUDIT.md`.
- Explicitly state Slice I not implemented unless separately approved.

### Slice I — (deferred) Optional answer path

- **Tracker:** `p4-slice-i-deferred` is **`cancelled`** for Phase 4 closure (optional slice; explicit approval never sought for this repo state).
- **Not implemented:** `POST /answer`, `LocalRAGConsumer`, `AnswerSynthesizer` — do not treat as pending work for Phase 4.

## Phase-level acceptance criteria

- `POST /retrieve` always returns a JSON body validating as `RetrievalPacket` (including no-match case).
- Retrieval path uses semantic index search + bounded traversal + graph-linked evidence only.
- Context budget and pruning reasons are visible in the packet.
- `RetrievalLog.retrieval_packet` stores the canonical packet snapshot for successful persistence paths (and define behavior for persistence failures explicitly in slice drafts).
- No non-doc work for Slice I unless separately approved.

## Explicit non-scope (phase)

Same as phase doc hard exclusions: multimodal/media ingestion, automatic graph extraction, agent autonomy, cloud LLM requirement, production UI, chunk-RAG bypass, hidden retrieval.
