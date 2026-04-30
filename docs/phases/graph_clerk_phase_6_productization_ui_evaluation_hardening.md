# GraphClerk Phase 6 — Productization, UI, Evaluation, and Hardening

## Phase Dependency
This phase must only start after:

```text
Phase 0 — Governance Baseline
Phase 1 — Foundation and Core Architecture
Phase 2 — Text-First Ingestion and Evidence Units
Phase 3 — Semantic Index and Graph Layer
Phase 4 — File Clerk and Retrieval Packets
Phase 5 — Multimodal Ingestion
```

Phase 6 assumes:

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
- Multimodal ingestion works at a basic level
- Graph layer exists
- Semantic index search works
- File Clerk retrieval packets exist
- Context budget exists
- Retrieval logs exist
- Phase 5 tests pass
- Phase 5 audit is pass or pass_with_notes
```

Cursor must not implement this phase unless Phase 5 is complete and status docs confirm it.

---

## Purpose
Turn GraphClerk from a backend research system into a usable product/demo.

This phase makes the system visible, measurable, testable, and honest.

The goal is not just to show answers.

The goal is to show the retrieval trace:

```text
question
  → semantic index
  → graph path
  → evidence units
  → context budget
  → retrieval packet
  → optional answer
```

GraphClerk’s value is not only the final response.

Its value is that users can inspect how the evidence was selected.

---

## Core Objective
At the end of this phase, GraphClerk should have:

```text
- a usable web UI
- a query playground
- a retrieval packet viewer
- an artifact/evidence viewer
- a graph explorer
- a semantic index explorer
- a retrieval log viewer
- an evaluation/comparison dashboard
- public demo sample data
- improved README and onboarding docs
- hardened error handling
- release checklist
- final Phase 6 audit
```

This phase makes GraphClerk demo-ready and GitHub-ready.

---

## Product Principle Preserved In This Phase
GraphClerk should not hide the retrieval process.

The UI must make the core idea visible:

> Less junk to the LLM. Better evidence routing. Clearer traceability.

The user should be able to see:

```text
- why a semantic index was selected
- which graph nodes and edges were followed
- which evidence units were included
- which evidence units were pruned
- what warnings were raised
- what confidence level was assigned
- whether ambiguity existed
```

---

## Scope

### Included

```text
- Frontend application skeleton
- Query playground
- RetrievalPacket viewer
- Artifact viewer
- EvidenceUnit viewer
- SemanticIndex explorer
- Graph explorer
- RetrievalLog viewer
- Evaluation dashboard
- Naive RAG vs GraphClerk comparison mode
- Metrics display
- Sample demo corpus
- Improved installation docs
- Improved API docs
- Release readiness checklist
- hardening pass
- Phase 6 audit
```

### Excluded

```text
- Enterprise authentication
- Multi-tenant permissions
- Production-grade billing
- Full team workspace management
- Cloud deployment automation unless explicitly scoped
- Advanced graph editing UI unless explicitly scoped
- Perfect UX polish
- Production observability stack
```

---

## Non-Negotiable Rules For This Phase

```text
1. The UI must not hide retrieval traceability.
2. The UI must not imply unsupported product maturity.
3. Metrics must not be fake vanity numbers.
4. Evaluation results must be reproducible from sample data.
5. README must be honest about limitations.
6. Demo data must be clearly marked as demo data.
7. UI must consume backend contracts, not invent its own shapes.
8. No frontend-only fake retrieval packets.
9. No hidden mock data in production mode.
10. Errors must be visible to the user.
11. Status docs must be updated before phase completion.
12. Phase 6 audit must be created before phase completion.
```

---

# Core Product Flow

```text
User uploads or selects demo artifacts
  ↓
EvidenceUnits are available
  ↓
Graph and SemanticIndexes exist
  ↓
User asks a question
  ↓
GraphClerk creates RetrievalPacket
  ↓
UI shows semantic index route
  ↓
UI shows graph path
  ↓
UI shows evidence units
  ↓
UI shows context budget decisions
  ↓
Optional answer is shown
  ↓
Evaluation metrics are logged
```

---

# Frontend Stack

Recommended stack:

```text
React
Vite
TypeScript
Tailwind CSS
React Router optional
TanStack Query optional
React Flow optional for graph visualization
```

Keep the UI clean and functional.

Avoid overdesigning the first version.

The first UI should show the architecture clearly, not win design awards.

---

# Frontend Folder Structure

Suggested:

```text
frontend/
  src/
    api/
      client.ts
      artifacts.ts
      evidence.ts
      graph.ts
      semanticIndexes.ts
      retrieval.ts
      evaluation.ts
    components/
      layout/
      query/
      packets/
      graph/
      artifacts/
      evidence/
      evaluation/
    pages/
      DashboardPage.tsx
      QueryPlaygroundPage.tsx
      ArtifactsPage.tsx
      EvidencePage.tsx
      GraphPage.tsx
      SemanticIndexesPage.tsx
      RetrievalLogsPage.tsx
      EvaluationPage.tsx
    types/
      artifact.ts
      evidence.ts
      graph.ts
      semanticIndex.ts
      retrievalPacket.ts
      evaluation.ts
    main.tsx
  package.json
  vite.config.ts
```

---

# Main UI Pages

## 1. Dashboard Page

Purpose:

```text
Give a quick overview of the local GraphClerk instance.
```

Should show:

```text
- total artifacts
- total evidence units
- total graph nodes
- total graph edges
- total semantic indexes
- recent retrievals
- current system status
```

---

## 2. Query Playground

Purpose:

```text
The main demo page.
```

User can:

```text
- enter a question
- choose retrieval options
- call /retrieve
- optionally call /answer
```

Should show:

```text
- interpreted intent
- selected semantic indexes
- graph paths
- evidence units
- alternative interpretations
- context budget
- warnings
- confidence
- final answer if available
```

This is the most important page.

---

## 3. RetrievalPacket Viewer

Purpose:

```text
Inspect the full structured packet.
```

Should show both:

```text
- readable UI view
- raw JSON view
```

Readable sections:

```text
Intent
Selected indexes
Graph paths
Evidence
Alternatives
Context budget
Warnings
Confidence
Answer mode
```

---

## 4. Artifact Viewer

Purpose:

```text
Inspect uploaded/imported artifacts.
```

Should show:

```text
- artifact metadata
- filename
- artifact_type
- checksum
- ingestion status
- evidence unit count
- source location if available
```

---

## 5. EvidenceUnit Viewer

Purpose:

```text
Inspect evidence units from all modalities.
```

Should show:

```text
- artifact source
- modality
- content_type
- source_fidelity
- text/summary
- location metadata
- confidence
```

The user should be able to filter by:

```text
artifact
modality
content_type
source_fidelity
```

---

## 6. SemanticIndex Explorer

Purpose:

```text
Inspect meaning entry points.
```

Should show:

```text
- meaning
- summary
- embedding_text
- entry graph nodes
- search score when searched
```

Should support:

```text
- search indexes by query
- click index to view entry nodes
```

---

## 7. Graph Explorer

Purpose:

```text
Inspect graph nodes, edges, and evidence support.
```

Simple version:

```text
- list nodes
- list edges
- show node neighborhood
- show evidence support
```

Better version:

```text
- graph visualization using React Flow
- click node to inspect evidence
- click edge to inspect relation/support
```

Do not overbuild graph visualization in the first pass.

Traceability matters more than beauty.

---

## 8. Retrieval Logs Viewer

Purpose:

```text
Inspect past retrieval runs.
```

Should show:

```text
- question
- interpreted intent
- selected indexes
- evidence count
- confidence
- warnings
- latency
- created_at
```

Should allow opening a previous RetrievalPacket.

---

## 9. Evaluation Dashboard

Purpose:

```text
Prove that GraphClerk improves evidence routing compared to naive RAG.
```

Should show:

```text
- token estimate
- evidence unit count
- graph path count
- selected index count
- warnings
- confidence
- latency
- naive retrieval comparison
```

---

# Evaluation System

Phase 6 should add a simple evaluation layer.

Do not start with complex academic metrics.

Start with useful operational metrics.

## Required Metrics

```text
retrieval_latency_ms
semantic_index_count_selected
graph_nodes_visited
graph_edges_visited
evidence_units_considered
evidence_units_selected
evidence_units_pruned
estimated_context_tokens
warnings_count
packet_confidence
answer_mode
```

## Comparison Mode

GraphClerk should compare:

```text
Naive retrieval:
query → top evidence units/chunks by vector/text search

GraphClerk retrieval:
query → SemanticIndex → graph path → evidence packet
```

If naive vector search over EvidenceUnits is not yet available, a simplified baseline can be:

```text
keyword search over EvidenceUnits
```

But this limitation must be documented.

## Evaluation Output

Example:

```json
{
  "question": "How do I reduce hallucination in RAG?",
  "naive": {
    "evidence_units_selected": 8,
    "estimated_context_tokens": 3200,
    "warnings": []
  },
  "graphclerk": {
    "semantic_indexes_selected": 2,
    "graph_paths": 3,
    "evidence_units_selected": 4,
    "estimated_context_tokens": 1200,
    "warnings": ["ambiguous_query"]
  }
}
```

---

# Demo Corpus

Phase 6 should include a small demo corpus.

Suggested corpus:

```text
1 Markdown architecture note
1 PDF article or report
1 PowerPoint pitch deck
1 architecture diagram image
1 short audio transcript or audio file
optional 1 short video clip
```

The corpus should demonstrate:

```text
- text evidence
- PDF evidence
- slide evidence
- image evidence
- audio evidence
- graph support
- semantic indexes
- retrieval packet trace
```

Demo data must be clearly marked.

No copyrighted/private content should be committed unless allowed.

---

# API Hardening

Phase 6 should review API behavior.

Hardening checks:

```text
- consistent error response shape
- validation errors are clear
- no stack traces leaked to normal users
- unsupported operations fail explicitly
- pagination exists for list endpoints if needed
- large payload handling is documented
- CORS configured for local frontend
```

---

# Backend Contract Stability

The frontend must consume backend contracts.

If backend schemas need changes, update:

```text
- CONTRACTS.md
- API docs
- tests
- frontend types
- change-control notes
```

Do not let the frontend create alternative unofficial packet shapes.

---

# Installation and Onboarding

The README should support a new developer.

Required sections:

```text
- What GraphClerk is
- What problem it solves
- What it does not do yet
- Quickstart
- Docker Compose setup
- Backend commands
- Frontend commands
- Running tests
- Loading demo data
- Asking first query
- Viewing retrieval trace
- Architecture overview
- Phase status
```

Quickstart target:

```text
git clone
cp .env.example .env
docker compose up
load demo data
open frontend
ask a demo question
```

---

# Release Readiness Checklist

Create:

```text
docs/release/RELEASE_CHECKLIST.md
```

Checklist:

```text
- tests pass
- Docker setup works
- README quickstart works
- demo data loads
- /health works
- /retrieve works
- UI query playground works
- status docs are honest
- known gaps listed
- security/dependency audit completed
- Phase 6 audit completed
```

---

# Security and Dependency Review

Phase 6 should include a lightweight dependency/security review.

Required:

```text
- list backend dependencies
- list frontend dependencies
- document why major dependencies exist
- check for obvious vulnerable packages if tooling available
- document unresolved security gaps
```

Possible tools:

```text
pip-audit optional
npm audit optional
```

Do not block the whole phase on perfect security tooling, but record what was checked.

---

# Error Handling and UX Rules

UI should show errors clearly.

Examples:

```text
Qdrant unavailable
PostgreSQL unavailable
no semantic indexes found
no graph path found
no evidence support found
extractor unavailable
retrieval packet invalid
```

Do not show blank pages for backend failures.

Do not hide warnings from RetrievalPackets.

---

# Required Tests

## Backend Tests

```text
test_retrieve_endpoint_still_works_with_demo_data
test_retrieval_logs_list_endpoint_if_added
test_evaluation_comparison_endpoint_if_added
test_error_response_shape
test_demo_data_loader
```

## Frontend Tests / Smoke Tests

Depending on tooling:

```text
test_query_playground_renders
test_packet_viewer_renders_required_sections
test_artifact_page_renders
test_evidence_page_renders
test_semantic_index_page_renders
test_graph_page_renders
test_evaluation_page_renders
```

If automated frontend tests are too heavy in first pass, document manual smoke tests.

## Manual Smoke Tests

```text
- Start Docker Compose
- Open frontend
- Load demo data
- Ask demo question
- Inspect selected semantic indexes
- Inspect graph path
- Inspect evidence units
- Inspect context budget
- Inspect optional answer
- Open retrieval log
```

---

# Documentation Requirements

Phase 6 must create or update:

```text
docs/phases/PHASE_6_PRODUCTIZATION_UI_EVALUATION.md
docs/status/PROJECT_STATUS.md
docs/status/PHASE_STATUS.md
docs/status/KNOWN_GAPS.md
docs/status/TECHNICAL_DEBT.md
docs/audits/PHASE_6_AUDIT.md
docs/release/RELEASE_CHECKLIST.md
README.md
```

Optional but recommended:

```text
docs/demo/DEMO_CORPUS.md
docs/evaluation/EVALUATION_METHOD.md
docs/api/API_OVERVIEW.md
```

---

# README Must Say

```text
Implemented:
- Text/Markdown ingestion
- Basic multimodal ingestion
- EvidenceUnit model
- Graph nodes and graph edges
- Semantic indexes
- Meaning-first semantic index search
- Bounded graph traversal
- File Clerk retrieval packets
- Context budget pruning
- Retrieval trace UI
- Basic evaluation comparison

Limitations:
- Not production-grade authentication
- Not enterprise permissioning
- Multimodal extraction quality depends on local extractors
- Graph and semantic indexes may still require manual/semi-manual setup
- Evaluation dashboard is basic
- Video understanding is limited unless explicitly implemented
```

---

# Status Document Requirements

`PROJECT_STATUS.md` should update the current state.

Example:

```text
Current phase: Phase 6 — Productization, UI, Evaluation, and Hardening

Implemented:
- UI query playground
- RetrievalPacket viewer
- Artifact/Evidence explorer
- SemanticIndex explorer
- Graph explorer
- retrieval logs
- basic evaluation dashboard
- demo corpus

Known limitations:
- no enterprise auth
- basic evaluation metrics
- limited video understanding
- extraction quality varies by modality
```

`KNOWN_GAPS.md` should include:

```text
- Authentication is not implemented or is local/dev only.
- Evaluation metrics are operational, not academic benchmark-grade.
- UI graph visualization is basic.
- Multimodal extraction is basic and extractor-dependent.
- No production deployment hardening yet.
```

`TECHNICAL_DEBT.md` should include accepted shortcuts.

---

# Phase 6 Audit Requirements

Create:

```text
docs/audits/PHASE_6_AUDIT.md
```

Audit must answer:

```text
- Does the UI show retrieval traceability?
- Does the UI consume backend contracts correctly?
- Are any fake frontend-only packets used?
- Are evaluation metrics honest and reproducible?
- Does README overclaim maturity?
- Does demo data load correctly?
- Are known gaps listed?
- Do tests or smoke tests cover the main user flow?
- Does the release checklist exist?
- Were dependency/security checks performed or explicitly deferred?
```

Allowed audit result:

```text
pass
pass_with_notes
needs_fix
blocked
```

Phase 6 is not complete if audit result is `needs_fix` or `blocked`.

---

# Implementation Tasks

## Task 1 — Create frontend skeleton
Set up React/Vite/TypeScript/Tailwind.

Acceptance:

```text
- frontend starts locally
- frontend can call backend health endpoint
- basic layout exists
```

## Task 2 — Add API client and shared types
Create frontend API client and TypeScript types matching backend contracts.

Acceptance:

```text
- frontend types match backend packet/artifact/evidence contracts
- no fake packet shapes
```

## Task 3 — Build Query Playground
Implement the main query UI.

Acceptance:

```text
- user can submit question
- /retrieve is called
- packet sections render
```

## Task 4 — Build RetrievalPacket Viewer
Create readable and raw JSON packet views.

Acceptance:

```text
- intent, indexes, graph paths, evidence, context budget, warnings, confidence render
```

## Task 5 — Build Artifact and Evidence viewers
Create pages for artifacts and evidence units.

Acceptance:

```text
- artifacts can be listed
- evidence can be filtered by artifact/modality/source_fidelity
```

## Task 6 — Build SemanticIndex Explorer
Create page for semantic indexes.

Acceptance:

```text
- indexes can be listed/searched
- entry nodes are visible
```

## Task 7 — Build Graph Explorer
Create basic graph inspection page.

Acceptance:

```text
- graph nodes and edges can be inspected
- node neighborhood can be viewed
- evidence support is visible
```

## Task 8 — Build RetrievalLog Viewer
Create page for retrieval logs.

Acceptance:

```text
- logs can be listed
- previous packet/log details can be inspected
```

## Task 9 — Build Evaluation Dashboard
Create simple comparison dashboard.

Acceptance:

```text
- GraphClerk metrics display
- naive baseline comparison displays if implemented
- limitations are documented
```

## Task 10 — Add demo corpus and loader
Create sample data and loader.

Acceptance:

```text
- demo data loads reproducibly
- demo query produces meaningful packet
```

## Task 11 — API hardening pass
Review error responses and endpoint behavior.

Acceptance:

```text
- error response shape is consistent
- unsupported operations fail clearly
- UI displays backend errors
```

## Task 12 — Documentation and onboarding
Update README and docs.

Acceptance:

```text
- quickstart works
- limitations are clear
- demo instructions exist
```

## Task 13 — Release checklist and audit
Create release checklist and Phase 6 audit.

Acceptance:

```text
- release checklist exists
- audit result is pass or pass_with_notes
```

---

# Cursor Prompt Template For Phase 6 Tasks

Every Cursor prompt for this phase should begin with:

```text
You are working on GraphClerk Phase 6 — Productization, UI, Evaluation, and Hardening.
You must follow docs/governance/*.
The UI must show retrieval traceability and must not fake backend data.
Do not add enterprise auth, billing, multi-tenant permissions, or unsupported maturity claims.
Only modify the files listed below.
Add or update tests/smoke tests as specified.
Add docstrings/comments where required by coding standards.
Update status docs only if this task requires it.
```

Then specify:

```text
Allowed files:
Forbidden files:
Task:
Acceptance criteria:
Required tests or smoke tests:
Documentation updates:
```

---

# Deliverables
At the end of Phase 6:

```text
- Frontend skeleton
- Query Playground
- RetrievalPacket Viewer
- Artifact Viewer
- EvidenceUnit Viewer
- SemanticIndex Explorer
- Graph Explorer
- RetrievalLog Viewer
- Evaluation Dashboard
- Demo corpus
- Demo loader
- API hardening pass
- README quickstart
- Release checklist
- Phase 6 documentation
- Phase 6 status update
- Phase 6 audit
```

---

# Acceptance Criteria

```text
Given a fresh clone,
when setup instructions are followed,
then the system starts locally.

Given demo data is loaded,
when a demo question is asked,
then the Query Playground shows a RetrievalPacket.

Given a RetrievalPacket is displayed,
then semantic indexes, graph paths, evidence units, context budget, warnings, confidence, and answer mode are visible.

Given evidence units are displayed,
then artifact, modality, content_type, source_fidelity, and location metadata are visible.

Given the Graph Explorer is used,
then nodes, edges, and evidence support can be inspected.

Given the Evaluation Dashboard is used,
then operational metrics are visible and honestly labeled.

Given backend errors occur,
then the UI displays clear error messages.

Given docs are inspected,
then README and status docs are honest about limitations.

Given the Phase 6 audit is inspected,
then the result is pass or pass_with_notes.
```

---

# Known Non-Features After Phase 6

After this phase, GraphClerk may still not support:

```text
- enterprise authentication
- multi-tenant permissions
- billing
- production observability
- full deployment automation
- perfect multimodal extraction
- full automatic graph construction
- advanced benchmark-grade evaluation
```

This is acceptable for a public alpha/demo.

---

# Risks

## Risk 1 — Pretty UI hides weak traceability
A nice-looking answer box is not enough.

Mitigation:

```text
- prioritize retrieval trace views
- make packet inspection central
```

## Risk 2 — Fake evaluation metrics
Bad metrics can make the project look dishonest.

Mitigation:

```text
- use simple operational metrics
- label limitations clearly
- make comparisons reproducible
```

## Risk 3 — Frontend invents data shapes
If the frontend does not follow backend contracts, the system splits.

Mitigation:

```text
- shared types or generated types
- backend contract tests
- frontend API client discipline
```

## Risk 4 — Overclaiming release maturity
A public demo is not an enterprise product.

Mitigation:

```text
- README honesty
- status docs
- known gaps
- audit
```

## Risk 5 — Setup friction
If users cannot run it quickly, the GitHub project loses momentum.

Mitigation:

```text
- Docker Compose
- demo data
- quickstart
- smoke tests
```

---

# Suggested Duration

```text
Fast mode: 1–2 weeks
Clean mode: 3–6 weeks
```

A fast version should prioritize:

```text
Query Playground
RetrievalPacket Viewer
Artifact/Evidence Viewer
basic Graph Explorer
basic Evaluation Dashboard
demo corpus
README quickstart
```

---

# Phase Completion Definition
Phase 6 is complete when GraphClerk can be run locally by a new developer, demo data can be loaded, a user can ask a question through the UI, the system shows the retrieval trace clearly, evaluation metrics are visible, documentation is honest, and the final phase audit passes.

The output of this phase is a public alpha/demo-ready GraphClerk.

