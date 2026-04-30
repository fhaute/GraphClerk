# GraphClerk Phase 0 — Governance Baseline

## Purpose
Create the project control layer before any technical implementation begins.

This phase exists to prevent AI-assisted development drift. Before repository structure, database schema, ingestion logic, APIs, vector stores, or UI are implemented, GraphClerk needs explicit rules, contracts, boundaries, and working agreements for Cursor or any coding agent.

The goal is simple:

> Move fast, but inside hard architectural guardrails.

---

## Core Objective
At the end of this phase, the project should have:

```text
- Git initialized
- A minimal repository root
- Governance documents committed
- Protected concepts named
- Cursor rules written
- Agent roles defined
- Architectural invariants documented
- Contract rules established
- Phase execution protocol defined
- Testing rules defined
- Coding standards defined
- Documentation standards defined
- Status reporting rules defined
- Audit rules defined
- Change-control process created
```

This phase should happen before the technical repo structure is fully settled.

---

## Why This Phase Exists
Cursor can move extremely fast. That speed is useful, but dangerous without constraints.

Without this phase, Cursor may:

```text
- rename foundational concepts
- mix architectural layers together
- create hidden shortcuts
- add unrequested abstractions
- change schemas silently
- implement future phases too early
- hide errors behind fallbacks
- create fake completeness
- make the project look done while breaking the architecture
```

Phase 0 turns Cursor from a wandering assistant into a constrained implementation worker.

---

## Core Product Principle
GraphClerk is not just another RAG chatbot.

It is an evidence-routing layer for RAG systems.

Core positioning:

> GraphClerk turns messy multimodal knowledge into structured evidence packets for LLMs.

The system should combine useful parts of RAG, Agentic RAG, and CAG without becoming uncontrolled, expensive, or context-heavy.

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

GraphClerk's correction:
- retrieve meaning first
- follow graph paths
- return structured evidence packets
- send less junk to the LLM
```

GraphClerk may include an optional packet-bound RAG consumer, but this must remain separate from the core retrieval layer.

```text
GraphClerk Core:
Artifact → EvidenceUnit → Graph → SemanticIndex → RetrievalPacket

Optional LocalRAGConsumer:
RetrievalPacket → AnswerSynthesizer → Answer
```

The optional consumer must never bypass FileClerk, RetrievalPackets, graph traversal rules, or evidence traceability.

---

## Phase Scope

### Included

```text
- Initialize Git
- Create initial repo root
- Create governance docs
- Define Cursor rules
- Define agent roles
- Define non-negotiable contracts
- Define architectural invariants
- Define phase execution protocol
- Define change-control rules
- Define coding standards
- Define docstring standards
- Define code documentation rules
- Define status document rules
- Define audit rules
- Define documentation rules
- Define testing rules
- Make first commit
```

### Excluded

```text
- FastAPI implementation
- Database implementation
- Qdrant or vector store implementation
- API endpoints
- Artifact ingestion
- Evidence unit extraction
- Graph traversal
- Semantic index search
- File Clerk logic
- LLM integration
- UI
```

---

## Initial Repository State
The initial repo should be minimal.

Suggested structure:

```text
graphclerk/
  docs/
    governance/
      PROJECT_PRINCIPLES.md
      CURSOR_RULES.md
      AGENT_ROLES.md
      ARCHITECTURAL_INVARIANTS.md
      CONTRACTS.md
      PHASE_PROTOCOL.md
      CHANGE_CONTROL.md
      TESTING_RULES.md
      CODING_STANDARDS.md
      DOCUMENTATION_STANDARDS.md
      STATUS_REPORTING.md
      AUDIT_RULES.md
  README.md
  .gitignore
```

Only after these governance documents exist should Phase 1 define the full technical structure.

---

## Git Initialization

### Tasks

```text
1. Create project folder.
2. Initialize Git.
3. Add .gitignore.
4. Add initial README.md.
5. Add docs/governance folder.
6. Add governance documents.
7. Make first commit.
```

### Suggested First Commit Message

```text
chore: initialize GraphClerk governance baseline
```

---

# Governance Document 1 — PROJECT_PRINCIPLES.md

## Purpose
Define what GraphClerk is, what it is not, and which principles guide every phase.

## Required Content

```text
# GraphClerk Project Principles

GraphClerk is a local-first, graph-guided evidence-routing layer for RAG systems.

It does not try to replace RAG frameworks, vector databases, or LLMs.
It improves the layer between user intent and LLM context.

Core principle:
Search meaning first, then retrieve evidence.
```

## Core Principles

```text
1. GraphClerk retrieves meaning first, then evidence.
2. Original source artifacts are never overwritten.
3. Evidence units preserve traceability to original artifacts.
4. Semantic indexes are access paths, not source truth.
5. The graph organizes source-backed meaning.
6. The File Clerk returns structured retrieval packets, not vague prose.
7. LLMs synthesize answers from packets; they do not create truth.
8. Local-first ingestion is preferred.
9. Multimodal content must normalize into evidence units.
10. Every major behavior must be testable.
11. Context should be pruned before reaching the LLM.
12. Retrieval should expose confidence, ambiguity, and source support.
13. Optional answer generation must consume RetrievalPackets only and must not perform hidden retrieval.
```

## Non-Goals

```text
- GraphClerk is not a full autonomous agent framework.
- GraphClerk is not a chatbot by itself.
- GraphClerk is not a vector database.
- GraphClerk is not a document storage system only.
- GraphClerk is not EBES.
- GraphClerk does not replace original source material with summaries.
- GraphClerk core is not a direct chunk-to-LLM RAG shortcut.
- Optional answer generation must remain packet-bound and traceable.
```

---

# Governance Document 2 — CURSOR_RULES.md

## Purpose
Define strict operating rules for Cursor and any coding assistant.

## Core Rules

```text
1. Do not modify files outside the requested scope.
2. Do not rename protected concepts without explicit approval.
3. Do not introduce new architecture without updating governance docs.
4. Do not implement future phases early.
5. Do not replace source truth with summaries.
6. Do not hide errors behind silent fallbacks.
7. Do not change public schemas without updating contracts and tests.
8. Do not add dependencies without explaining why.
9. Do not remove tests to make implementation pass.
10. Do not create fake completeness.
11. Do not mix ingestion, retrieval, graph, and answer synthesis layers.
12. Do not generate final answers inside retrieval services.
13. Do not make LLM calls required for core local-first ingestion unless explicitly scoped.
14. Do not implement a direct RAG bypass that answers from chunks, vectors, files, or hidden database reads instead of RetrievalPackets.
```

## Cursor Prompt Requirements
Every Cursor implementation prompt should specify:

```text
- phase number
- task name
- files allowed to change
- files forbidden to change
- expected output
- required tests
- acceptance criteria
- documentation updates required
```

## Example Cursor Task Header

```text
Phase: 1 — Foundation
Task: Add FastAPI health endpoint
Allowed files:
- backend/app/main.py
- backend/tests/test_health.py
Forbidden files:
- docs/governance/*
- database models
- retrieval services
Expected result:
- GET /health returns {"status": "ok"}
Tests:
- test_health_endpoint
```

---

# Governance Document 3 — AGENT_ROLES.md

## Purpose
Define conceptual development agents and their boundaries.

These are not necessarily autonomous agents. They are working modes for Cursor or other AI assistants.

## Architect Agent
Responsible for:

```text
- architecture documents
- contracts
- invariants
- phase boundaries
- impact analysis
```

Forbidden:

```text
- writing implementation code unless explicitly asked
- changing contracts without change-control
- silently expanding scope
```

## Backend Agent
Responsible for:

```text
- FastAPI code
- services
- database integration
- tests
```

Forbidden:

```text
- changing product principles
- changing phase scope
- inventing new protected concepts
```

## Ingestion Agent
Responsible for:

```text
- artifact parsers
- evidence unit creation
- modality-specific extraction
```

Forbidden:

```text
- writing answer synthesis logic
- changing graph semantics
- replacing source evidence with summaries
```

## Graph Agent
Responsible for:

```text
- graph node logic
- graph edge logic
- traversal
- graph validation
```

Forbidden:

```text
- treating semantic indexes as truth
- treating graph summaries as source material
```

## File Clerk Agent
Responsible for:

```text
- query interpretation
- semantic index selection
- graph path selection
- evidence selection
- retrieval packet assembly
```

Forbidden:

```text
- generating final user answers directly
- inventing evidence
- performing hidden retrieval outside packet logic
```

## Answer Synthesizer Agent
Responsible for:

```text
- generating final user-facing answers from retrieval packets
- respecting packet evidence
- surfacing uncertainty
```

Forbidden:

```text
- retrieving additional hidden evidence
- citing unsupported facts
- overriding packet warnings
```

## LocalRAGConsumer Agent
Responsible for:

```text
- optional packet-grounded answer flow
- consuming RetrievalPackets
- invoking an AnswerSynthesizer only from packet content
- returning final answers with traceability to packet evidence
```

Forbidden:

```text
- bypassing FileClerk
- performing hidden semantic search, graph traversal, vector search, file lookup, or database evidence lookup
- answering without a RetrievalPacket
- hiding packet warnings or uncertainty
```

## Evaluation Agent
Responsible for:

```text
- metrics
- retrieval comparison
- regression tests
- efficiency scoring
```

Forbidden:

```text
- manipulating metrics to make the system look better
- hiding failure cases
```

---

# Governance Document 4 — ARCHITECTURAL_INVARIANTS.md

## Purpose
Document the rules that should not be broken.

## Invariant 1 — Source artifacts are immutable
Original artifact content must not be overwritten by derived summaries, extracted claims, embeddings, or graph structures.

## Invariant 2 — Evidence units are traceable
Every EvidenceUnit must link back to an Artifact and, when possible, to a specific source location.

## Invariant 3 — Semantic indexes are not truth
SemanticIndex records are searchable access paths into the graph. They are not the source of truth.

## Invariant 4 — Graph claims require support
Claim-like GraphNodes and meaningful GraphEdges should link to supporting EvidenceUnits whenever possible.

## Invariant 5 — File Clerk returns structured data
The retrieval layer returns RetrievalPackets, not unstructured answer prose.

## Invariant 6 — Answer synthesis is separate from retrieval
The answer generator consumes RetrievalPackets. It must not perform hidden retrieval.

## Invariant 7 — Multimodal content becomes evidence units
PDFs, slides, images, audio, and video must normalize into EvidenceUnits.

## Invariant 8 — No silent fallbacks
If a parser, model, vector store, graph operation, or retrieval step fails, the system must expose the failure clearly.

## Invariant 9 — Local-first ingestion
External LLMs are optional adapters, not required core dependencies.

## Invariant 10 — Phase boundaries matter
A phase must not implement future phase scope unless the phase docs are updated first.

## Invariant 11 — Context budget must be explicit
Retrieval packets should manage evidence size intentionally. Context bloat is a failure mode.

## Invariant 12 — Ambiguity should be represented
When user intent is ambiguous, RetrievalPackets should include alternatives instead of pretending certainty.

## Invariant 13 — Optional RAG consumes packets only
If GraphClerk includes an optional RAG consumer or answer endpoint, it must consume RetrievalPackets only. It must not perform hidden retrieval, vector search, graph traversal, file lookup, database evidence lookup, or direct chunk-to-LLM answering.

---

# Governance Document 5 — CONTRACTS.md

## Purpose
Define stable interfaces and data promises.

Contracts should start high-level in Phase 0 and become stricter during implementation.

## Protected Contracts

```text
Artifact Contract
EvidenceUnit Contract
GraphNode Contract
GraphEdge Contract
SemanticIndex Contract
RetrievalPacket Contract
FileClerk Contract
LocalRAGConsumer Contract
ModelAdapter Contract
IngestionPipeline Contract
```

## Contract Format
Each contract should define:

```text
- purpose
- required fields
- optional fields
- forbidden behavior
- lifecycle
- validation rules
- example JSON
- test expectations
```

## Artifact Contract Summary
An Artifact represents original source material.

Examples:

```text
Markdown file
PDF
PowerPoint
image
audio
video
web page
```

Artifact must preserve reference to original content.

## EvidenceUnit Contract Summary
An EvidenceUnit is a source-backed piece of usable evidence extracted from an Artifact.

It must include:

```text
artifact_id
modality
content_type
text or representation
location metadata when available
source_fidelity
confidence
```

## SourceFidelity Values

```text
verbatim
extracted
derived
computed
```

## SemanticIndex Contract Summary
A SemanticIndex is a searchable meaning entry point.

It must point to graph nodes.

It must not replace graph truth or source evidence.

## RetrievalPacket Contract Summary
A RetrievalPacket is the structured object returned by the File Clerk.

It should include:

```text
question
interpreted_intent
selected_indexes
graph_paths
evidence_units
claims
alternative_interpretations
confidence
warnings
context_budget
answer_mode
```

## LocalRAGConsumer Contract Summary
A LocalRAGConsumer is an optional component that produces packet-grounded answers.

It must consume a RetrievalPacket and must not perform hidden retrieval.

Forbidden behavior:

```text
- direct vector/chunk search
- hidden graph traversal
- hidden file or database evidence lookup
- answering without a RetrievalPacket
- ignoring packet warnings, ambiguity, confidence, or answer_mode
```

---

# Governance Document 6 — PHASE_PROTOCOL.md

## Purpose
Define how phases are executed and completed.

## Each Phase Must Include

```text
- purpose
- scope
- non-scope
- components
- allowed files
- expected deliverables
- acceptance criteria
- required tests
- completion definition
```

## Phase Completion Rule
A phase is not complete because code exists.

A phase is complete only when:

```text
- code exists
- tests pass
- docs are updated
- acceptance criteria are satisfied
- no future phase was silently implemented
```

## Implementation Rule
Each implementation task must be small enough to review.

Bad:

```text
Build the whole ingestion system.
```

Good:

```text
Implement Artifact model and migration only.
```

---

# Governance Document 7 — CHANGE_CONTROL.md

## Purpose
Prevent accidental changes to foundational concepts.

## Protected Terms

```text
Artifact
EvidenceUnit
GraphNode
GraphEdge
SemanticIndex
FileClerk
RetrievalPacket
LocalRAGConsumer
SourceFidelity
ModelAdapter
IngestionPipeline
ContextBudget
```

## Change Requirements
Any change to protected terms requires:

```text
1. Written reason
2. Impact analysis
3. Contract update
4. Migration or update plan
5. Tests updated
6. Explicit approval
```

## Forbidden Silent Changes

```text
- Renaming core models without migration notes
- Changing JSON output shape without contract update
- Changing source_fidelity values without tests
- Changing retrieval packet schema silently
- Moving responsibilities between layers without docs
```

---

# Governance Document 8 — TESTING_RULES.md

## Purpose
Define testing expectations from the beginning.

## Minimum Rules

```text
1. Every service gets unit tests.
2. Every public endpoint gets API tests.
3. Every schema contract gets validation tests.
4. Ingestion must test source preservation.
5. Retrieval must test packet structure.
6. Graph traversal must test limits and edge filtering.
7. Model outputs must be validated before persistence.
8. No test may be removed just to make implementation pass.
9. Regressions must receive regression tests.
10. Multimodal extractors must test traceability to artifacts.
```

## Future Test Categories

```text
contract tests
unit tests
API tests
ingestion tests
retrieval tests
graph traversal tests
vector search tests
evaluation tests
UI smoke tests
```

---

# Governance Document 9 — CODING_STANDARDS.md

## Purpose
Define mandatory coding standards for every implementation phase.

These standards are not optional style preferences. They are part of the project contract.

## Core Rules

```text
1. Code must be readable before clever.
2. Every public function, class, service, and model must have a docstring.
3. Every non-trivial private function should have a docstring or explanatory comment.
4. Complex logic must be broken into small, testable functions.
5. No hidden side effects.
6. No silent exception swallowing.
7. No broad except blocks without explicit error handling.
8. No business logic inside API route handlers when it belongs in services.
9. No database access from unrelated layers.
10. No hardcoded configuration values.
11. No unused dependencies.
12. No fake implementations unless explicitly marked as temporary and tracked.
```

## Python Standards

```text
- Use Python 3.12+.
- Use type hints everywhere practical.
- Use Pydantic models for external input/output schemas.
- Use SQLAlchemy models only for persistence, not API contracts.
- Use service classes or service functions for business logic.
- Keep route handlers thin.
- Prefer explicit errors over magic fallbacks.
- Use enums for controlled vocabularies such as source_fidelity, modality, relation_type, and answer_mode.
```

## Docstring Standard
Every public class/function/method should explain:

```text
- what it does
- expected inputs
- returned output
- important errors or failure modes
- architectural constraints if relevant
```

Example:

```python
async def create_evidence_unit(command: CreateEvidenceUnitCommand) -> EvidenceUnit:
    """Create a source-backed evidence unit for an artifact.

    The function preserves traceability to the original artifact and must not
    rewrite or summarize source content unless the resulting EvidenceUnit is
    explicitly marked as derived.

    Raises:
        ArtifactNotFoundError: If the referenced artifact does not exist.
        InvalidSourceFidelityError: If source_fidelity is unsupported.
    """
```

## Comments Standard
Comments should explain why, not repeat what the code says.

Bad:

```python
# increment i
i += 1
```

Good:

```python
# Keep traversal bounded so one dense graph region cannot explode the packet.
```

## Layering Rules

```text
API routes:
- request validation
- call service
- return response

Services:
- business logic
- orchestration
- validation

Repositories:
- database reads/writes

Models:
- persistence shape only

Schemas:
- external contracts

Adapters:
- external tools, models, OCR engines, vector stores
```

## Code Review Checklist
Every implementation slice should answer:

```text
- Is this within the requested phase?
- Are protected concepts respected?
- Are public functions documented?
- Are errors explicit?
- Are tests included?
- Is the code easy to remove or refactor if this slice fails?
```

---

# Governance Document 10 — DOCUMENTATION_STANDARDS.md

## Purpose
Define how documentation must be created and updated.

GraphClerk should be understandable from its documents, not only from its code.

## Required Documentation Types

```text
architecture docs
phase docs
contract docs
status docs
audit docs
API docs
model/adapter docs
decision records
```

## Documentation Rules

```text
1. Every phase must have a phase document.
2. Every protected contract must have a contract section.
3. Every major architectural decision must be recorded.
4. Every implemented phase must update its status document.
5. Every non-obvious module must have a README or module-level docstring.
6. Documentation must distinguish current behavior from planned behavior.
7. Documentation must not claim functionality that is not implemented and tested.
```

## Architecture Decision Records
Create ADRs for important decisions.

Suggested folder:

```text
docs/adr/
```

ADR format:

```text
# ADR-0001 — Decision title

## Status
Proposed | Accepted | Superseded

## Context
Why this decision exists.

## Decision
What we decided.

## Consequences
What this changes, improves, or limits.
```

## Required Early ADRs

```text
ADR-0001 — GraphClerk retrieves meaning before evidence
ADR-0002 — Semantic indexes are access paths, not truth
ADR-0003 — Local-first ingestion is the default
ADR-0004 — Evidence units are the multimodal normalization layer
ADR-0005 — Retrieval packets separate retrieval from answer synthesis
```

---

# Governance Document 11 — STATUS_REPORTING.md

## Purpose
Force honest project status tracking.

The project must always make clear what is done, partial, blocked, deferred, or unimplemented.

## Required Status Files

```text
docs/status/PROJECT_STATUS.md
docs/status/PHASE_STATUS.md
docs/status/KNOWN_GAPS.md
docs/status/TECHNICAL_DEBT.md
docs/status/ROADMAP.md
```

## Status Categories

```text
not_started
in_progress
implemented
tested
documented
blocked
deferred
failed
removed
```

## Status Rules

```text
1. A feature is not "done" until it is implemented, tested, and documented.
2. Partially working features must be marked partial.
3. Known gaps must be written down, not hidden.
4. Deferred work must have a reason.
5. Technical debt must be tracked when intentionally accepted.
6. Status docs must be updated at the end of every phase.
```

## Example Status Entry

```text
Feature: Markdown ingestion
Status: tested
Evidence:
- backend/tests/test_markdown_ingestion.py
- docs/phases/PHASE_2_TEXT_INGESTION.md
Notes:
- Tables inside Markdown are currently stored as table_text evidence units.
- No semantic table interpretation yet.
```

---

# Governance Document 12 — AUDIT_RULES.md

## Purpose
Create a habit of auditing architecture, code, tests, dependencies, and claims.

Audits prevent the project from quietly drifting away from its own contracts.

## Required Audit Types

```text
architecture audit
contract audit
test audit
dependency audit
security audit
retrieval quality audit
multimodal extraction audit
status honesty audit
```

## Audit Schedule

```text
- After every phase
- Before every public release
- Before major schema changes
- After major dependency changes
```

## Audit Questions

### Architecture Audit

```text
- Did this phase violate any architectural invariant?
- Did any layer take responsibility from another layer?
- Did any future phase get implemented silently?
```

### Contract Audit

```text
- Did schemas change?
- Were contracts updated?
- Were tests updated to reflect contract changes?
```

### Test Audit

```text
- Are critical paths tested?
- Were any tests removed or weakened?
- Are failure cases tested?
```

### Dependency Audit

```text
- Were dependencies added?
- Are they necessary?
- Are they documented?
- Are licenses acceptable?
```

### Status Honesty Audit

```text
- Does the README overclaim?
- Do status docs match actual behavior?
- Are partial features clearly marked?
```

## Audit Output
Each audit should produce a short file:

```text
docs/audits/YYYY-MM-DD_PHASE_X_AUDIT.md
```

Audit result values:

```text
pass
pass_with_notes
needs_fix
blocked
```

## Release Rule
No public release should happen without an audit marked either:

```text
pass
pass_with_notes
```

---

## Phase 0 Tasks

### Task 1 — Create project folder

```text
mkdir graphclerk
cd graphclerk
```

### Task 2 — Initialize Git

```text
git init
```

### Task 3 — Create minimal files

```text
README.md
.gitignore
docs/governance/
```

### Task 4 — Add governance documents

```text
docs/governance/PROJECT_PRINCIPLES.md
docs/governance/CURSOR_RULES.md
docs/governance/AGENT_ROLES.md
docs/governance/ARCHITECTURAL_INVARIANTS.md
docs/governance/CONTRACTS.md
docs/governance/PHASE_PROTOCOL.md
docs/governance/CHANGE_CONTROL.md
docs/governance/TESTING_RULES.md
docs/governance/CODING_STANDARDS.md
docs/governance/DOCUMENTATION_STANDARDS.md
docs/governance/STATUS_REPORTING.md
docs/governance/AUDIT_RULES.md
```

### Task 5 — First commit

```text
git add .
git commit -m "chore: initialize GraphClerk governance baseline"
```

---

## Deliverables
At the end of this phase:

```text
- Git repository initialized
- README exists
- .gitignore exists
- governance docs exist
- protected terms are named
- Cursor rules are documented
- agent roles are documented
- architectural invariants are documented
- contracts are documented
- phase protocol is documented
- change-control is documented
- testing rules are documented
- coding standards are documented
- documentation standards are documented
- status reporting rules are documented
- audit rules are documented
- first commit exists
```

---

## Acceptance Criteria

```text
Given a fresh project,
when Cursor is asked to implement Phase 1,
then it has explicit governance rules to follow.

Given a protected concept is mentioned,
then its name and role are defined in governance docs.

Given an implementation changes a contract,
then the change-control process defines what must be updated.

Given code is implemented,
then docstrings, tests, documentation, and status updates are required according to governance rules.

Given a phase is completed,
then an audit must be produced or explicitly deferred with a written reason.

Given a phase starts,
then its scope and completion rules are already defined.

Given the repository history is inspected,
then the first commit establishes the governance baseline before implementation code.
```

---

## Risks

### Risk 1 — Too much bureaucracy
Governance should constrain architecture, not slow down every small code change.

### Risk 2 — Vague contracts
Contracts must become specific enough for Cursor to follow.

### Risk 3 — Rules ignored during implementation
Every Cursor prompt should reference the relevant governance documents.

### Risk 4 — Premature repo structure lock-in
Phase 0 initializes Git and governance, but does not freeze the full technical structure yet.

### Risk 5 — Governance without enforcement
Rules only matter if prompts, tests, reviews, and commits follow them.

---

## Suggested Duration

```text
Fast mode: 0.5 day
Clean mode: 1 day
```

---

## Phase Completion Definition
Phase 0 is complete when the project has a committed governance baseline that Cursor and future agents must follow before any technical implementation begins.

The baseline must include coding standards, docstring rules, documentation rules, testing rules, status tracking, and audit requirements.

No backend code is required.

No database code is required.

No AI code is required.

The output of this phase is control.

