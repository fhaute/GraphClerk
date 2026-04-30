# Phase Protocol

## Each phase must include
- purpose
- scope
- non-scope
- components
- allowed files
- expected deliverables
- acceptance criteria
- required tests
- completion definition

## Phase completion rule
A phase is not complete because code exists.

A phase is complete only when:
- code exists
- tests pass
- docs are updated
- acceptance criteria are satisfied
- no future phase was silently implemented

## Implementation rule
Each implementation task must be small enough to review.

Bad:
```text
Build the whole ingestion system.
```

Good:
```text
Implement Artifact model and migration only.
```

