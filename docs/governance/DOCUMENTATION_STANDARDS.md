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

