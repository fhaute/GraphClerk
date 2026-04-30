# GraphClerk Phase 4 — File Clerk and Retrieval Packets

## Phase Dependency
This phase must only start after:

```text
Phase 0 — Governance Baseline
Phase 1 — Foundation and Core Architecture
Phase 2 — Text-First Ingestion and Evidence Units
Phase 3 — Semantic Index and Graph Layer
```

Phase 4 assumes:

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
- GraphNode and GraphEdge models exist
- Evidence support links exist
- SemanticIndex model exists
- SemanticIndex embeddings/search work
- SemanticIndexes resolve to graph entry nodes
- Bounded graph traversal works
- Phase 3 tests pass
- Phase 3 audit is pass or pass_with_notes
```

Cursor must not implement this phase unless Phase 3 is complete and the status docs confirm it.

---

## Purpose
Build the File Clerk retrieval engine.

This is the core identity of GraphClerk.

The File Clerk does not answer the user directly.

It receives a user question and returns a structured RetrievalPacket containing:

```text
- interpreted intent
- selected semantic indexes
- graph paths
- source-backed evidence
- confidence
- ambiguity notes
- alternative interpretations
- context budget decisions
- warnings
- suggested answer mode
```

This phase turns GraphClerk from a meaning index into an actual evidence-routing layer.

Phase 4 also formalizes an optional RAG consumer mode. This does **not** change the core identity of GraphClerk. The core remains the File Clerk and the RetrievalPacket. The optional RAG consumer exists only to consume RetrievalPackets and produce packet-grounded answers.

GraphClerk can therefore be used in two modes:

```text
Mode 1 — Retrieval layer only
GraphClerk returns RetrievalPackets for another RAG app, LLM app, agent, or external consumer.

Mode 2 — Optional local RAG consumer
GraphClerk creates a RetrievalPacket and then uses a packet-bound AnswerSynthesizer to produce an answer.
```

The optional RAG consumer must never bypass the File Clerk.

---

## Core Objective
At the end of this phase, GraphClerk should be able to:

```text
- accept a user question
- interpret the likely retrieval intent
- search semantic indexes
- select primary semantic routes
- identify possible alternative interpretations
- resolve selected semantic indexes into graph entry nodes
- traverse the graph within limits
- collect source-backed evidence
- rank and prune evidence according to a context budget
- assemble a structured RetrievalPacket
- optionally synthesize an answer from the RetrievalPacket using a packet-bound LocalRAGConsumer / AnswerSynthesizer
- log retrieval decisions
- expose /retrieve and optional /answer endpoints
- test retrieval packet structure and behavior
- update status docs
- produce a Phase 4 audit
```

---

## Product Principle Preserved In This Phase
GraphClerk is not trying to create a fourth RAG category.

GraphClerk is a correction layer.

It combines useful parts of RAG, Agentic RAG, and CAG:

```text
From RAG:
- retrieval
- grounding
- external knowledge

From Agentic RAG:
- query interpretation
- decomposition
- evidence sufficiency checks

From CAG:
- context pruning
- context budgeting
- pinning important facts
```

GraphClerk's correction:

```text
- retrieve meaning first
- follow graph paths
- return structured evidence packets
- send less junk to the LLM
```

The File Clerk is the component that enforces this.

The optional RAG consumer is not a shortcut around GraphClerk. It is a consumer of GraphClerk output.

Bad architecture:

```text
question → vector chunks → LLM answer
```

Allowed architecture:

```text
question → FileClerk → RetrievalPacket → LocalRAGConsumer / AnswerSynthesizer → answer
```

---

## Scope

### Included

```text
- FileClerkService
- RetrievalPacket schema and persistence/logging shape
- Query intent classification using deterministic/local-first logic
- Semantic index selection orchestration
- Entry node resolution orchestration
- Graph traversal orchestration
- Evidence collection from graph support links
- Evidence ranking/pruning
- ContextBudget manager
- Ambiguity and alternative interpretation representation
- Retrieval warnings
- RetrievalLog updates
- /retrieve endpoint
- optional /answer endpoint using RetrievalPacket only
- optional LocalRAGConsumer boundary
- AnswerSynthesizer boundary
- tests for retrieval packets
- tests for context budget behavior
- tests for ambiguity handling
- status docs update
- Phase 4 audit
```

### Excluded

```text
- Multimodal ingestion
- PDF ingestion
- PowerPoint ingestion
- image/audio/video ingestion
- automatic graph extraction
- autonomous agent loops
- free-roaming tool use
- cloud LLM requirement
- advanced UI
- production-grade evaluation dashboard
- direct chunk-based RAG bypass around the File Clerk
```

---

## Non-Negotiable Rules For This Phase

```text
1. The File Clerk must return structured data, not final prose.
2. The File Clerk must not invent evidence.
3. The File Clerk must not create graph nodes or edges during retrieval.
4. The File Clerk must not mutate source artifacts.
5. The File Clerk must not perform hidden retrieval outside documented steps.
6. Answer synthesis, if implemented, must consume only the RetrievalPacket.
7. The optional LocalRAGConsumer must consume RetrievalPackets only.
8. The optional LocalRAGConsumer must not bypass the File Clerk.
9. The AnswerSynthesizer must not perform hidden semantic search or graph traversal.
10. The AnswerSynthesizer must not query Qdrant, Postgres, files, or repositories directly.
11. Context budget pruning must be explicit and visible in the packet.
12. Ambiguity must be represented instead of hidden.
13. Retrieval failures must be explicit.
14. No external LLM dependency is required.
15. Every public class/function must have a docstring.
16. Every public endpoint must have tests.
17. Retrieval packets must have schema/contract tests.
18. Status docs must be updated before phase completion.
19. Phase 4 audit must be created before phase completion.
```

---

# Core Flow

## Core retrieval flow

```text
User question
  ↓
FileClerkService
  ↓
Query intent interpretation
  ↓
SemanticIndex search
  ↓
Primary route selection
  ↓
Alternative route detection
  ↓
Entry GraphNode resolution
  ↓
Bounded graph traversal
  ↓
Evidence collection
  ↓
Evidence ranking and pruning
  ↓
RetrievalPacket assembly
```

## Optional RAG consumer flow

```text
User question
  ↓
FileClerkService
  ↓
RetrievalPacket
  ↓
LocalRAGConsumer
  ↓
AnswerSynthesizer
  ↓
Packet-grounded answer
```

The optional RAG consumer starts only after a RetrievalPacket exists. It does not perform its own retrieval.

---

# File Clerk Responsibility

The File Clerk is the evidence-routing brain.

It answers this question:

> Given this user question, what structured evidence packet should the LLM receive?

It does not answer:

> What should the final user-facing response say?

That belongs to the AnswerSynthesizer.

The File Clerk is the mandatory core of Phase 4. The optional LocalRAGConsumer is downstream of the File Clerk and must not replace it.

---

# Optional RAG Consumer Boundary

GraphClerk may include an optional RAG consumer, but this consumer is not the core product boundary.

```text
GraphClerk Core:
Artifact → EvidenceUnit → Graph → SemanticIndex → RetrievalPacket

Optional RAG Consumer:
RetrievalPacket → AnswerSynthesizer → Answer
```

The optional RAG consumer exists to make GraphClerk easier to demo and easier to use locally. It must still prove the value of RetrievalPackets rather than bypassing them.

## LocalRAGConsumer rules

```text
- It may accept a question only if it internally calls FileClerkService first.
- It may accept a RetrievalPacket directly.
- It must generate answers only from the RetrievalPacket.
- It must respect answer_mode, warnings, confidence, and ambiguity fields.
- It must not perform hidden retrieval.
- It must not query SemanticIndexSearchService, GraphTraversalService, EvidenceUnitRepository, Qdrant, Postgres, files, or external tools directly.
```

Allowed:

```text
question → FileClerkService → RetrievalPacket → LocalRAGConsumer → AnswerSynthesizer → answer
```

Forbidden:

```text
question → direct vector/chunk search → LLM answer
```

---

# RetrievalPacket Contract

A RetrievalPacket is the main output of Phase 4.

Suggested structure:

```json
{
  "packet_type": "retrieval_packet",
  "question": "How do I reduce hallucination in RAG?",
  "interpreted_intent": {
    "intent_type": "explain",
    "confidence": 0.78,
    "notes": []
  },
  "selected_indexes": [
    {
      "semantic_index_id": "idx_reduce_rag_hallucination",
      "meaning": "Ways to reduce hallucination in RAG systems",
      "score": 0.91,
      "selection_reason": "Best semantic match for hallucination reduction."
    }
  ],
  "graph_paths": [
    {
      "start_node_id": "node_hallucination",
      "nodes": ["node_hallucination", "node_grounding", "node_reranking"],
      "edges": ["edge_reranking_improves_grounding"],
      "depth": 1
    }
  ],
  "evidence_units": [
    {
      "evidence_unit_id": "ev_001",
      "artifact_id": "artifact_001",
      "modality": "text",
      "content_type": "paragraph",
      "source_fidelity": "verbatim",
      "text": "Reranking improves retrieval precision before generation.",
      "location": {
        "section_path": ["Retrieval", "Reranking"],
        "line_start": 42,
        "line_end": 44
      },
      "selection_reason": "Supports edge_reranking_improves_grounding.",
      "confidence": 0.86
    }
  ],
  "alternative_interpretations": [
    {
      "if_user_meant": "reduce token cost instead of hallucination",
      "suggested_semantic_indexes": ["idx_reduce_rag_cost"],
      "reason": "The question could also refer to efficiency rather than accuracy."
    }
  ],
  "context_budget": {
    "max_evidence_units": 8,
    "selected_evidence_units": 3,
    "pruned_evidence_units": 5,
    "pruning_reasons": [
      "duplicate_support",
      "lower_confidence",
      "weaker_source_fidelity"
    ]
  },
  "warnings": [],
  "confidence": 0.79,
  "answer_mode": "answer_with_evidence"
}
```

---

# RetrievalPacket Required Fields

```text
packet_type
question
interpreted_intent
selected_indexes
graph_paths
evidence_units
alternative_interpretations
context_budget
warnings
confidence
answer_mode
```

---

# Intent Types

Start with a small controlled set:

```text
explain
compare
locate
summarize
debug
recommend
unknown
```

Intent classification can be deterministic at first.

Example heuristics:

```text
"what is" / "explain" → explain
"compare" / "vs" / "difference" → compare
"where" / "which file" / "find" → locate
"summarize" → summarize
"why does this fail" / "debug" → debug
"should I" / "what do you recommend" → recommend
```

Later, a local model can improve this.

---

# Answer Modes

Suggested controlled values:

```text
answer_with_evidence
answer_with_caveats
ask_clarification
not_enough_evidence
conflicting_evidence
unsupported
```

The File Clerk suggests the answer mode.

The AnswerSynthesizer must respect it.

---

# Ambiguity Handling

The File Clerk should not pretend every question has one meaning.

When query intent or semantic index search suggests multiple plausible meanings, the packet should include alternatives.

Example:

```json
{
  "alternative_interpretations": [
    {
      "if_user_meant": "latency efficiency",
      "suggested_semantic_indexes": ["idx_reduce_latency"],
      "reason": "The phrase 'make it faster' could refer to runtime latency."
    },
    {
      "if_user_meant": "token cost efficiency",
      "suggested_semantic_indexes": ["idx_reduce_token_cost"],
      "reason": "The phrase 'efficient' could refer to cost."
    }
  ]
}
```

Ambiguity should affect confidence.

---

# ContextBudget Manager

The ContextBudget manager prevents context bloat.

It decides which evidence units survive into the packet.

It should consider:

```text
semantic index score
graph proximity
source_fidelity
support confidence
duplicate evidence
modality priority later
recency later
max evidence units
max estimated tokens
```

For Phase 4, keep it simple.

Recommended defaults:

```text
max_evidence_units = 8
max_graph_paths = 3
max_selected_indexes = 3
max_tokens_estimate = 3000 optional
```

Pruning reasons should be visible:

```text
duplicate_support
lower_confidence
outside_graph_depth
exceeds_context_budget
weaker_source_fidelity
```

---

# Evidence Selection Rules

Evidence should be selected from graph support links.

Preferred evidence order:

```text
1. verbatim source_fidelity
2. extracted source_fidelity
3. derived source_fidelity
4. computed source_fidelity
```

When multiple EvidenceUnits support the same graph edge/node, prefer:

```text
- higher confidence
- more direct graph support
- less duplicated content
- shorter but sufficient evidence
```

The File Clerk should not include huge evidence blocks if a smaller source-backed unit is sufficient.

---

# Confidence Rules

Phase 4 confidence can be simple but explicit.

Possible inputs:

```text
semantic index score
intent confidence
evidence support confidence
graph path availability
number of direct evidence units
ambiguity penalty
warning penalty
```

Example simple formula:

```text
packet_confidence = average(
  semantic_index_score,
  intent_confidence,
  evidence_support_confidence
) - ambiguity_penalty - warning_penalty
```

The exact formula should be documented if implemented.

---

# Retrieval Warnings

Possible warnings:

```text
no_semantic_index_match
semantic_index_has_no_entry_nodes
no_graph_path_found
no_evidence_support_found
ambiguous_query
context_budget_pruned_many_items
low_confidence
vector_index_unavailable
```

Warnings should be machine-readable.

---

# RetrievalLog Updates

Phase 4 should start logging retrieval decisions.

A RetrievalLog should include:

```text
question
interpreted_intent
selected_indexes
graph_paths
evidence_unit_ids
alternative_interpretations_count
warnings
confidence
latency_ms
context_budget_summary
created_at
```

Retrieval logs are for observability and future evaluation.

They are not source truth.

---

# Optional LocalRAGConsumer and AnswerSynthesizer

Phase 4 may include a basic LocalRAGConsumer and AnswerSynthesizer, but they must be strictly separated from retrieval.

The LocalRAGConsumer is the optional RAG mode. It consumes a RetrievalPacket and asks an AnswerSynthesizer to produce a final response.

The AnswerSynthesizer consumes a RetrievalPacket and produces a final response.

It must not:

```text
- perform semantic search
- traverse the graph
- retrieve hidden evidence
- query Qdrant
- query Postgres
- read files
- call repositories
- invent citations
- ignore packet warnings
- ignore answer_mode
```

## Local-First Rule
No external LLM should be required.

Possible implementations:

```text
- template-based answer synthesizer for early tests
- local Ollama-compatible model adapter later
- OpenAI-compatible adapter as optional, disabled by default
```

For Phase 4, a template-based synthesizer may be enough.

This avoids cost and keeps behavior testable.

## Packet-bound answer behavior

If the packet says `answer_mode = not_enough_evidence`, the answer must not present a confident unsupported answer.

If the packet contains warnings or alternative interpretations, the answer must either surface them or follow the packet's suggested mode.

The answer layer is allowed to format, summarize, and explain the packet. It is not allowed to expand the evidence set.

---

# API Endpoints For Phase 4

## Retrieve packet

```text
POST /retrieve
```

Input:

```json
{
  "question": "How do I reduce hallucination in RAG?",
  "options": {
    "max_evidence_units": 8,
    "max_graph_depth": 1,
    "include_alternatives": true
  }
}
```

Output:

```text
RetrievalPacket
```

## Optional answer endpoint

```text
POST /answer
```

Input:

```json
{
  "question": "How do I reduce hallucination in RAG?",
  "options": {
    "max_evidence_units": 8
  }
}
```

Flow:

```text
question → FileClerkService → RetrievalPacket → LocalRAGConsumer → AnswerSynthesizer → final response
```

The response should include the packet ID or retrieval log ID for traceability.

---

# Services To Implement

## FileClerkService
Responsible for:

```text
- orchestrating retrieval
- calling QueryIntentService
- calling SemanticIndexService
- calling GraphTraversalService
- calling EvidenceSelectionService
- calling ContextBudgetService
- assembling RetrievalPacket
- writing RetrievalLog
```

Forbidden:

```text
- generating final prose answers
- creating graph nodes/edges
- mutating source artifacts
- hidden retrieval outside the documented flow
```

## QueryIntentService
Responsible for:

```text
- classifying user query intent
- estimating confidence
- detecting simple ambiguity
```

## RouteSelectionService
Responsible for:

```text
- selecting primary semantic indexes
- selecting alternative semantic indexes
- explaining selection reasons
```

## EvidenceSelectionService
Responsible for:

```text
- collecting EvidenceUnits from graph support links
- ranking evidence
- removing duplicates
- preserving source fidelity rules
```

## ContextBudgetService
Responsible for:

```text
- enforcing max evidence units
- enforcing token estimate if implemented
- recording pruning reasons
```

## RetrievalPacketBuilder
Responsible for:

```text
- building a valid RetrievalPacket schema
- validating required fields
- ensuring machine-readable warnings
```

## LocalRAGConsumer Optional
Responsible for:

```text
- consuming RetrievalPackets
- coordinating packet-bound answer generation
- exposing optional local RAG behavior without bypassing FileClerk
- respecting answer_mode, warnings, ambiguity, and confidence
```

Forbidden:

```text
- direct semantic search
- direct graph traversal
- direct vector search
- repository/database/file access
- evidence expansion outside the packet
```

## AnswerSynthesizer Optional
Responsible for:

```text
- producing final text from RetrievalPacket only
```

Forbidden:

```text
- additional retrieval
- graph traversal
- hidden source lookup outside packet
```

---

# Error Handling Requirements

Errors must be explicit.

Examples:

```text
RetrievalPacketBuildError
QueryIntentError
NoSemanticIndexMatchError optional
SemanticIndexResolutionError
GraphTraversalError
EvidenceSelectionError
ContextBudgetError
AnswerSynthesisError
```

Empty retrieval may be a valid packet if represented clearly with warnings and `answer_mode = not_enough_evidence`.

---

# Required Tests

Minimum tests:

```text
test_retrieve_endpoint_returns_retrieval_packet
test_retrieval_packet_required_fields
test_query_intent_explain
test_query_intent_compare
test_query_intent_locate
test_semantic_index_selection_used_in_packet
test_graph_paths_included_in_packet
test_evidence_units_included_from_graph_support
test_context_budget_limits_evidence_units
test_context_budget_records_pruning_reasons
test_ambiguity_adds_alternative_interpretations
test_low_evidence_sets_not_enough_evidence_mode
test_retrieval_warnings_are_machine_readable
test_retrieval_log_created
test_answer_synthesizer_uses_packet_only_if_implemented
test_local_rag_consumer_does_not_bypass_file_clerk_if_implemented
```

Optional tests:

```text
test_duplicate_evidence_pruned
test_verbatim_evidence_preferred_over_derived
test_confidence_decreases_with_ambiguity
test_no_semantic_index_match_returns_packet_with_warning
test_answer_endpoint_returns_trace_id_if_implemented
```

---

# Documentation Requirements

Phase 4 must create or update:

```text
docs/phases/PHASE_4_FILE_CLERK_RETRIEVAL_PACKETS.md
docs/status/PROJECT_STATUS.md
docs/status/PHASE_STATUS.md
docs/status/KNOWN_GAPS.md
docs/status/TECHNICAL_DEBT.md
docs/audits/PHASE_4_AUDIT.md
README.md
```

## README Must Say

```text
Implemented:
- Text/Markdown ingestion
- Graph nodes and graph edges
- Semantic indexes
- Meaning-first semantic index search
- Bounded graph traversal
- File Clerk retrieval packets
- Context budget pruning
- Retrieval logs

Optional if implemented:
- Basic LocalRAGConsumer / answer synthesis from RetrievalPackets only

Not implemented yet:
- Multimodal ingestion
- automatic graph extraction
- advanced evaluation dashboard
- UI
```

Do not claim production-grade answer quality.

Do not claim autonomous agent behavior.

---

# Status Document Requirements

`PROJECT_STATUS.md` should update the current state.

Example:

```text
Current phase: Phase 4 — File Clerk and Retrieval Packets

Implemented:
- Query intent classification
- Semantic route selection
- RetrievalPacket assembly
- Context budget pruning
- Retrieval logs

Not implemented:
- Multimodal ingestion
- automatic graph extraction
- full evaluation dashboard
- UI
```

`KNOWN_GAPS.md` should include:

```text
- Query intent classification is simple/deterministic.
- Alternative interpretation detection is basic.
- Context budget uses simple ranking rules.
- LocalRAGConsumer / answer synthesis, if present, is packet-bound and basic.
- No multimodal ingestion yet.
```

`TECHNICAL_DEBT.md` should include any accepted shortcuts.

---

# Phase 4 Audit Requirements

Create:

```text
docs/audits/PHASE_4_AUDIT.md
```

Audit must answer:

```text
- Does the File Clerk return structured RetrievalPackets?
- Does the File Clerk avoid generating final prose answers directly?
- Does the File Clerk avoid inventing evidence?
- Does answer synthesis, if implemented, consume only the packet?
- Does the optional LocalRAGConsumer avoid bypassing the File Clerk?
- Are context budget decisions visible?
- Are ambiguity and alternatives represented?
- Are retrieval warnings machine-readable?
- Were any multimodal or automatic graph extraction features implemented early?
- Are all endpoints tested?
- Are known gaps listed?
- Does the README overclaim?
```

Allowed audit result:

```text
pass
pass_with_notes
needs_fix
blocked
```

Phase 4 is not complete if audit result is `needs_fix` or `blocked`.

---

# Implementation Tasks

## Task 1 — Define RetrievalPacket schemas
Create request/response schemas and contract tests.

Acceptance:

```text
- RetrievalPacket required fields exist
- warnings are machine-readable
- answer_mode uses controlled values
- context_budget structure exists
```

## Task 2 — Implement QueryIntentService
Add deterministic/local-first intent classification.

Acceptance:

```text
- explain/compare/locate/summarize/debug/recommend/unknown are supported
- intent confidence is returned
- tests cover common intent patterns
```

## Task 3 — Implement route selection
Use SemanticIndex search results to select primary and alternative routes.

Acceptance:

```text
- top semantic indexes are selected
- selection reasons are included
- alternatives can be represented
```

## Task 4 — Implement evidence collection
Collect EvidenceUnits from graph node/edge support links.

Acceptance:

```text
- evidence comes from graph support links
- source_fidelity is preserved
- no invented evidence appears
```

## Task 5 — Implement ContextBudgetService
Prune evidence and graph paths according to budget.

Acceptance:

```text
- max_evidence_units is respected
- pruning reasons are recorded
- duplicate evidence can be removed
```

## Task 6 — Implement RetrievalPacketBuilder
Assemble and validate final packet.

Acceptance:

```text
- valid packet is returned
- low evidence produces appropriate warnings/mode
- ambiguity is represented
```

## Task 7 — Implement FileClerkService orchestration
Wire intent, semantic search, graph traversal, evidence selection, context budget, and packet builder.

Acceptance:

```text
- question produces RetrievalPacket end to end
- retrieval log is written
```

## Task 8 — Implement /retrieve endpoint
Expose RetrievalPacket generation.

Acceptance:

```text
- endpoint returns packet
- endpoint is tested
```

## Task 9 — Optional LocalRAGConsumer and AnswerSynthesizer
Implement packet-bound local RAG answer generation from RetrievalPackets only.

Acceptance:

```text
- LocalRAGConsumer consumes RetrievalPacket only
- AnswerSynthesizer consumes RetrievalPacket only
- no hidden retrieval occurs
- tests prove packet-bound behavior
- tests prove the optional RAG path does not bypass FileClerk
```

## Task 10 — Optional /answer endpoint
Expose LocalRAGConsumer / answer synthesis if Task 9 is implemented.

Acceptance:

```text
- response includes final answer and trace/log ID
- answer respects packet warnings
```

## Task 11 — Add required tests
Implement all required tests for Phase 4.

Acceptance:

```text
- pytest passes
- packet behavior is tested
- context budget behavior is tested
```

## Task 12 — Update docs and status
Update README, phase docs, status docs, known gaps, and technical debt.

Acceptance:

```text
- documentation matches actual behavior
- limitations are clear
```

## Task 13 — Add Phase 4 audit
Create the Phase 4 audit file.

Acceptance:

```text
- audit result is pass or pass_with_notes
```

---

# Cursor Prompt Template For Phase 4 Tasks

Every Cursor prompt for this phase should begin with:

```text
You are working on GraphClerk Phase 4 — File Clerk and Retrieval Packets.
You must follow docs/governance/*.
Do not implement multimodal ingestion, automatic graph extraction, autonomous agent loops, advanced UI, or cloud LLM requirements.
The File Clerk must return structured RetrievalPackets and must not invent evidence.
Answer synthesis and LocalRAGConsumer behavior, if implemented, must consume RetrievalPackets only and must not bypass FileClerk.
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
At the end of Phase 4:

```text
- RetrievalPacket schemas
- QueryIntentService
- route selection logic
- EvidenceSelectionService
- ContextBudgetService
- RetrievalPacketBuilder
- FileClerkService
- /retrieve endpoint
- RetrievalLog updates
- optional LocalRAGConsumer
- optional AnswerSynthesizer
- optional /answer endpoint
- required tests
- Phase 4 documentation
- Phase 4 status update
- Phase 4 audit
```

---

# Acceptance Criteria

```text
Given a user question,
when /retrieve is called,
then GraphClerk returns a structured RetrievalPacket.

Given a RetrievalPacket,
then it includes interpreted intent, selected semantic indexes, graph paths, evidence units, context budget, warnings, confidence, and answer mode.

Given ambiguous semantic matches,
then the packet includes alternative interpretations.

Given too many evidence units,
then the ContextBudgetService prunes evidence and records pruning reasons.

Given weak or missing evidence,
then the packet uses warnings and answer_mode to show low support.

Given answer synthesis is implemented,
then the synthesizer only uses the RetrievalPacket and performs no hidden retrieval.

Given LocalRAGConsumer is implemented,
then it either consumes an existing RetrievalPacket or calls FileClerkService first and performs no direct retrieval.

Given pytest is run,
then all Phase 4 tests pass.

Given docs are inspected,
then they do not claim multimodal ingestion, autonomous agents, automatic graph extraction, or production-grade answer quality.

Given the Phase 4 audit is inspected,
then the result is pass or pass_with_notes.
```

---

# Known Non-Features After Phase 4

After this phase, GraphClerk still cannot:

```text
- ingest PDFs
- ingest PowerPoints
- ingest images
- ingest audio
- ingest video
- automatically extract claims
- automatically build the graph
- provide advanced UI
- provide full evaluation dashboard
- run autonomous multi-step agents
```

This is intentional.

---

# Risks

## Risk 1 — File Clerk becomes an answer generator
If the File Clerk starts producing final prose directly, the architecture blurs.

Mitigation:

```text
- strict RetrievalPacket contract
- optional AnswerSynthesizer kept separate
- audit checks
```

## Risk 2 — Hidden retrieval inside answer synthesis
If answer generation performs additional retrieval, packet traceability breaks.

Mitigation:

```text
- tests prove packet-only synthesis
- no retriever dependencies inside AnswerSynthesizer
```

## Risk 3 — Optional RAG consumer bypasses File Clerk
If the optional RAG consumer performs direct vector search or repository lookup, GraphClerk becomes another hidden chunk-RAG system.

Mitigation:

```text
- LocalRAGConsumer must consume RetrievalPackets only
- tests prove no retriever/repository dependencies inside LocalRAGConsumer
- /answer must call /retrieve/FileClerk path first
```

## Risk 4 — Context budget becomes invisible
If pruning happens silently, users cannot trust the packet.

Mitigation:

```text
- visible context_budget section
- pruning reasons required
```

## Risk 5 — Ambiguity is ignored
If ambiguity is hidden, the answer may look more certain than the evidence supports.

Mitigation:

```text
- alternative_interpretations field
- ambiguity warning
- confidence penalty
```

## Risk 6 — Packet bloat
The packet can become as noisy as chunk dumping.

Mitigation:

```text
- max evidence units
- max graph paths
- deduplication
- source fidelity priority
```

---

# Suggested Duration

```text
Fast mode: 3–5 days
Clean mode: 1–2 weeks
```

---

# Phase Completion Definition
Phase 4 is complete when GraphClerk can receive a user question, route it through semantic indexes and graph paths, collect source-backed evidence, prune context, represent ambiguity, and return a structured RetrievalPacket with tested behavior and honest documentation.

The output of this phase is the File Clerk.

