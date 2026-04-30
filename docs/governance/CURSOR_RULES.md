# Cursor Rules (Hard Guardrails)

These rules apply to Cursor and any coding assistant working in this repository.

## Core rules
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

## Required task header in prompts
Every implementation prompt must specify:
- phase number
- task name
- files allowed to change
- files forbidden to change
- expected output
- required tests
- acceptance criteria
- documentation updates required

## Example task header
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

