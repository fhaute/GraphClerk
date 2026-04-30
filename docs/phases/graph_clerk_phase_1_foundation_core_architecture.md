# GraphClerk Phase 1 — Foundation and Core Architecture

## Phase Dependency
This phase must only start after **Phase 0 — Governance Baseline** is complete.

Phase 1 must follow:

```text
- PROJECT_PRINCIPLES.md
- CURSOR_RULES.md
- AGENT_ROLES.md
- ARCHITECTURAL_INVARIANTS.md
- CONTRACTS.md
- PHASE_PROTOCOL.md
- CHANGE_CONTROL.md
- TESTING_RULES.md
- CODING_STANDARDS.md
- DOCUMENTATION_STANDARDS.md
- STATUS_REPORTING.md
- AUDIT_RULES.md
```

Cursor must not implement this phase unless the governance baseline exists in the repository.

---

## Purpose
Build the first technical foundation of GraphClerk.

This phase creates the backend skeleton, database connection, vector store connection, project structure, test harness, and first implementation of the core persistence models.

This phase is still not about RAG intelligence.

It is about creating a stable technical spine that later phases can safely extend.

---

## Core Objective
At the end of this phase, GraphClerk should:

```text
- boot locally with Docker Compose
- expose a working FastAPI backend
- connect to PostgreSQL
- connect to Qdrant
- run Alembic migrations
- expose health/version endpoints
- contain the initial core database models
- include basic tests
- include phase status documentation
- include an audit file for Phase 1
```

---

## Product Principle Preserved In This Phase
GraphClerk is an evidence-routing layer for RAG systems.

Even though Phase 1 does not yet ingest or retrieve evidence, its architecture must already protect the later principle:

> Search meaning first, then retrieve evidence.

The core schema should prepare for:

```text
Artifact
EvidenceUnit
GraphNode
GraphEdge
SemanticIndex
RetrievalPacket
RetrievalLog
```

---

## Scope

### Included

```text
- Backend folder structure
- FastAPI application skeleton
- PostgreSQL service
- Qdrant service
- Docker Compose
- Environment configuration
- Logging setup
- SQLAlchemy setup
- Alembic setup
- Initial persistence models
- Initial Pydantic schemas where needed
- Basic service/repository structure
- Health endpoint
- Version endpoint
- Pytest setup
- Basic CI placeholder or local test command
- Phase 1 status update
- Phase 1 audit file
```

### Excluded

```text
- Real artifact ingestion
- Markdown parsing
- PDF parsing
- PowerPoint parsing
- Image/audio/video processing
- Embedding generation
- Semantic index search
- Graph traversal logic
- File Clerk logic
- Retrieval packet assembly
- LLM answer synthesis
- Frontend UI
```

---

## Non-Negotiable Rules For This Phase

```text
1. Do not implement future phase logic.
2. Do not create fake ingestion endpoints.
3. Do not create fake retrieval endpoints.
4. Do not use external LLMs.
5. Do not add dependencies without documenting why.
6. Do not mix SQLAlchemy models with Pydantic API schemas.
7. Do not put business logic inside route handlers.
8. Every public class/function must include a docstring.
9. Every public endpoint must have tests.
10. Every implemented model must have basic persistence tests.
11. Update status docs before phase completion.
12. Create a Phase 1 audit before phase completion.
```

---

## Recommended Tech Stack

### Backend

```text
Python 3.12+
FastAPI
Pydantic v2
SQLAlchemy 2.x
Alembic
Uvicorn
```

### Storage

```text
PostgreSQL
Qdrant
```

### Development

```text
Docker Compose
Pytest
httpx for API tests
Ruff or Black for formatting/linting
python-dotenv or Pydantic settings
```

### Optional Later, Not Required Now

```text
NetworkX
sentence-transformers
Ollama
Whisper
PyMuPDF
python-pptx
```

These should not be added in Phase 1 unless explicitly justified.

---

## Suggested Repository Structure After Phase 1

```text
graphclerk/
  backend/
    app/
      api/
        __init__.py
        routes/
          __init__.py
          health.py
          version.py
      core/
        __init__.py
        config.py
        logging.py
      db/
        __init__.py
        base.py
        session.py
        migrations/
      models/
        __init__.py
        artifact.py
        evidence_unit.py
        graph_node.py
        graph_edge.py
        semantic_index.py
        retrieval_log.py
      schemas/
        __init__.py
        health.py
        version.py
        artifact.py
        evidence_unit.py
        graph.py
        semantic_index.py
        retrieval_packet.py
      services/
        __init__.py
        qdrant_service.py
      repositories/
        __init__.py
      main.py
    tests/
      __init__.py
      test_health.py
      test_version.py
      test_db_connection.py
      test_qdrant_connection.py
      test_models.py
    pyproject.toml
  docs/
    governance/
    phases/
      PHASE_1_FOUNDATION.md
    status/
      PROJECT_STATUS.md
      PHASE_STATUS.md
      KNOWN_GAPS.md
      TECHNICAL_DEBT.md
    audits/
      PHASE_1_AUDIT.md
  docker-compose.yml
  README.md
  .env.example
  .gitignore
```

This structure can be adjusted, but any significant change must be reflected in documentation.

---

# Core Models For Phase 1

Phase 1 creates the first persistence version of the core concepts.

These models do not need full business behavior yet.

They must exist cleanly and be migratable.

---

## Artifact Model

### Purpose
Represents an original source object.

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

### Suggested Fields

```text
id
filename
title
artifact_type
mime_type
storage_uri
checksum
metadata
created_at
updated_at
```

### Rules

```text
- Artifact represents source material.
- Artifact content must not be overwritten by derived summaries.
- Artifact does not contain retrieval logic.
```

---

## EvidenceUnit Model

### Purpose
Represents a usable evidence object extracted from an artifact.

Examples:

```text
paragraph
heading
slide title
OCR result
image caption
transcript segment
visual summary
```

### Suggested Fields

```text
id
artifact_id
modality
content_type
text
location
source_fidelity
confidence
metadata
created_at
updated_at
```

### Required Controlled Values

`source_fidelity` should support:

```text
verbatim
extracted
derived
computed
```

`modality` should prepare for:

```text
text
pdf
slide
image
audio
video
code
web
```

### Rules

```text
- EvidenceUnit must link to Artifact.
- EvidenceUnit must preserve source traceability.
- Phase 1 does not create real evidence units from files yet.
```

---

## GraphNode Model

### Purpose
Represents a node in the structured knowledge graph.

Possible node types:

```text
concept
claim
entity
artifact
source
technique
problem
decision
metric
modality
```

### Suggested Fields

```text
id
node_type
label
summary
metadata
created_at
updated_at
```

### Rules

```text
- GraphNode does not replace source evidence.
- Claim-like nodes should later require support.
- Phase 1 only defines persistence shape.
```

---

## GraphEdge Model

### Purpose
Represents a typed relation between graph nodes.

Possible relation types:

```text
supports
explains
improves
causes
reduces
contradicts
depends_on
part_of
related_to
mentions
represents
has_source
```

### Suggested Fields

```text
id
from_node_id
to_node_id
relation_type
summary
confidence
metadata
created_at
updated_at
```

### Rules

```text
- GraphEdge connects two valid GraphNodes.
- GraphEdge relation_type should be controlled.
- GraphEdge does not perform traversal by itself.
```

---

## SemanticIndex Model

### Purpose
Represents a searchable meaning entry point into the graph.

A SemanticIndex is not truth.

It is an access path.

### Suggested Fields

```text
id
meaning
summary
embedding_text
entry_node_ids or separate link table
metadata
created_at
updated_at
```

### Rules

```text
- SemanticIndex must later resolve to graph nodes.
- SemanticIndex must not replace graph truth.
- Phase 1 does not need real embeddings yet.
```

---

## RetrievalLog Model

### Purpose
Stores retrieval traces for future debugging and evaluation.

### Suggested Fields

```text
id
question
selected_indexes
graph_path
evidence_unit_ids
confidence
warnings
latency_ms
token_estimate
created_at
```

### Rules

```text
- RetrievalLog supports observability.
- Phase 1 only creates model shape.
- No retrieval behavior is implemented yet.
```

---

# Configuration Requirements

Create a typed configuration layer.

Required variables:

```text
APP_NAME
APP_ENV
LOG_LEVEL
DATABASE_URL
QDRANT_URL
QDRANT_API_KEY optional
```

`.env.example` should include safe example values.

No secrets should be committed.

---

# API Endpoints For Phase 1

Only infrastructure endpoints should exist.

## Health Endpoint

```text
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

Optional additional checks:

```text
database: ok
qdrant: ok
```

## Version Endpoint

```text
GET /version
```

Expected response:

```json
{
  "name": "GraphClerk",
  "version": "0.1.0",
  "phase": "phase_1_foundation"
}
```

---

# Required Tests

Minimum tests for Phase 1:

```text
test_health_endpoint
test_version_endpoint
test_database_connection
test_qdrant_connection
test_artifact_model_creation
test_evidence_unit_model_creation
test_graph_node_model_creation
test_graph_edge_model_creation
test_semantic_index_model_creation
test_retrieval_log_model_creation
```

Additional useful tests:

```text
test_config_loads_from_environment
test_missing_required_config_fails_clearly
test_graph_edge_requires_valid_nodes
test_evidence_unit_requires_artifact
```

---

# Documentation Requirements

Phase 1 must create or update:

```text
docs/phases/PHASE_1_FOUNDATION.md
docs/status/PROJECT_STATUS.md
docs/status/PHASE_STATUS.md
docs/status/KNOWN_GAPS.md
docs/status/TECHNICAL_DEBT.md
docs/audits/PHASE_1_AUDIT.md
README.md
.env.example
```

## Status Update Rules

`PROJECT_STATUS.md` should clearly say:

```text
Current phase: Phase 1 — Foundation
Implemented:
- FastAPI skeleton
- PostgreSQL connection
- Qdrant connection
- initial core models

Not implemented:
- ingestion
- semantic search
- graph traversal
- file clerk
- answer synthesis
- UI
```

No README should claim that GraphClerk can ingest, retrieve, or answer yet.

---

# Phase 1 Audit Requirements

Create:

```text
docs/audits/PHASE_1_AUDIT.md
```

Audit must answer:

```text
- Did Phase 1 violate any governance invariant?
- Were any future phases implemented early?
- Were all public classes/functions documented?
- Were all required tests added?
- Were dependencies documented?
- Does the README overclaim?
- Are known gaps listed?
```

Allowed audit result:

```text
pass
pass_with_notes
needs_fix
blocked
```

Phase 1 is not complete if audit result is `needs_fix` or `blocked`.

---

# Implementation Tasks

## Task 1 — Prepare backend folder structure
Create the backend folder structure and empty modules.

Acceptance:

```text
- backend/app exists
- backend/tests exists
- module imports work
```

## Task 2 — Add FastAPI app skeleton
Create `backend/app/main.py` and wire routes.

Acceptance:

```text
- app starts locally
- GET /health works
- GET /version works
```

## Task 3 — Add configuration layer
Create typed settings.

Acceptance:

```text
- settings load from environment
- .env.example exists
- missing required config fails clearly
```

## Task 4 — Add Docker Compose
Create Docker Compose with:

```text
api
postgres
qdrant
```

Acceptance:

```text
- docker compose up starts all required services
- api can reach postgres
- api can reach qdrant
```

## Task 5 — Add database session and Alembic
Set up SQLAlchemy and migrations.

Acceptance:

```text
- Alembic migration can be created
- migration can be applied
- tests can use database session
```

## Task 6 — Implement core persistence models
Create models for:

```text
Artifact
EvidenceUnit
GraphNode
GraphEdge
SemanticIndex
RetrievalLog
```

Acceptance:

```text
- migration creates tables
- model creation tests pass
- relationship constraints work where required
```

## Task 7 — Add Qdrant service
Create a minimal service that can verify Qdrant availability.

Acceptance:

```text
- service can ping or list collections
- qdrant connection test passes
```

## Task 8 — Add tests
Add required tests listed above.

Acceptance:

```text
- pytest passes locally
```

## Task 9 — Add status docs
Update all required status documents.

Acceptance:

```text
- current implementation is honestly represented
- non-implemented features are listed clearly
```

## Task 10 — Add Phase 1 audit
Create audit file and resolve issues if needed.

Acceptance:

```text
- audit exists
- result is pass or pass_with_notes
```

---

# Cursor Prompt Template For Phase 1 Tasks

Every Cursor prompt for this phase should begin with:

```text
You are working on GraphClerk Phase 1 — Foundation and Core Architecture.
You must follow docs/governance/*.
Do not implement ingestion, retrieval, graph traversal, semantic search, File Clerk logic, LLM answer synthesis, or UI.
Only modify the files listed below.
Add or update tests as specified.
Add docstrings to public classes/functions.
Update docs/status only if this task requires it.
```

Then specify:

```text
Allowed files:
Forbidden files:
Task:
Acceptance criteria:
Required tests:
```

---

# Deliverables
At the end of Phase 1:

```text
- FastAPI backend skeleton
- Docker Compose
- PostgreSQL connection
- Qdrant connection
- Alembic migrations
- Core persistence models
- Health endpoint
- Version endpoint
- Test suite
- Phase 1 documentation
- Phase 1 status update
- Phase 1 audit
```

---

# Acceptance Criteria

```text
Given a fresh clone,
when docker compose up is run,
then the API, PostgreSQL, and Qdrant start.

Given the backend is running,
when GET /health is called,
then the response is healthy.

Given the backend is running,
when GET /version is called,
then the response identifies GraphClerk and Phase 1.

Given migrations are applied,
then all Phase 1 core tables exist.

Given pytest is run,
then all Phase 1 tests pass.

Given docs are inspected,
then status documents do not claim unimplemented features.

Given the Phase 1 audit is inspected,
then the result is pass or pass_with_notes.
```

---

# Known Non-Features After Phase 1

After this phase, GraphClerk still cannot:

```text
- ingest documents
- create evidence units from files
- embed semantic indexes
- search meaning
- traverse the graph
- assemble retrieval packets
- answer questions
- process multimodal files
- show a UI
```

This is intentional.

---

# Risks

## Risk 1 — Implementing too much too early
The most likely failure is Cursor adding ingestion or retrieval prematurely.

Mitigation:

```text
- strict allowed files
- strict phase scope
- audit before completion
```

## Risk 2 — Bad schema foundations
Bad model names or unclear field purposes will hurt later phases.

Mitigation:

```text
- contracts checked before implementation
- models kept minimal and explicit
```

## Risk 3 — Hidden dependency creep
Early dependency bloat makes the system harder to run.

Mitigation:

```text
- dependency additions require documentation
- audit dependencies at end of phase
```

## Risk 4 — Fake completeness
The system may look like a RAG project because the models exist, but it does not do RAG yet.

Mitigation:

```text
- status docs must be honest
- README must not overclaim
```

---

# Suggested Duration

```text
Fast mode: 0.5–1 day
Clean mode: 1–2 days
```

---

# Phase Completion Definition
Phase 1 is complete when the technical foundation starts cleanly, tests pass, core models exist, status docs are honest, and the Phase 1 audit passes.

No ingestion or retrieval behavior is required in this phase.

The output of this phase is a clean technical skeleton.

