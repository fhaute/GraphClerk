# Documentation Standards

GraphClerk should be understandable from its documents, not only from its code.

## Required documentation types
- architecture docs
- phase docs
- contract docs
- status docs
- audit docs
- API docs
- model/adapter docs
- decision records

## Documentation rules
1. Every phase must have a phase document.
2. Every protected contract must have a contract section.
3. Every major architectural decision must be recorded.
4. Every implemented phase must update its status document.
5. Every non-obvious module must have a README or module-level docstring.
6. Documentation must distinguish current behavior from planned behavior.
7. Documentation must not claim functionality that is not implemented and tested.

## In-code documentation standard (module docstrings)
When a module is a "code page" that developers read to understand system
behavior (especially API routes, services, and adapters), it MUST include a
module-level docstring that answers:
- purpose and phase scope
- key invariants/constraints (e.g., transaction ownership, ordering guarantees)
- boundary conventions (e.g., UUIDs as strings at HTTP boundary)
- error semantics (what becomes 400 vs 404; what remains framework-level 422)

Minimum required content for API route modules (`backend/app/api/routes/*.py`):
- endpoints provided by the module (high level)
- pagination conventions (`limit`/`offset`) when applicable
- which layer owns transaction boundaries (route vs service)
- explicit error mapping (400/404) and what remains a 422 from invalid inputs

Minimum required content for service/repository modules:
- phase scope
- side effects and ownership (commit/rollback responsibility, disk/network IO)
  when relevant

## Architecture decision records (ADRs)
Folder: `docs/adr/`

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

## Required early ADRs
- ADR-0001 — GraphClerk retrieves meaning before evidence
- ADR-0002 — Semantic indexes are access paths, not truth
- ADR-0003 — Local-first ingestion is the default
- ADR-0004 — Evidence units are the multimodal normalization layer
- ADR-0005 — Retrieval packets separate retrieval from answer synthesis

