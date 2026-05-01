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

## Dedicated sub-agents (Cursor)
For **git**, **status documentation**, **project management / plan alignment** (`.cursor/plans/`), **testing**, **Docker**, **audits**, and **code quality** (read-only review and documented findings) work, follow the charters in `docs/governance/AGENT_ROLES.md` (**Dedicated sub-agents**) and the matching Cursor rules under `.cursor/rules/graphclerk-subagent-*.mdc`. Those rules include a **Your role (context)** block; for Task agents or chats where rules may not attach, explicitly prompt with the same role line—see **Prompting vs project rules** in `AGENT_ROLES.md` under **Dedicated sub-agents**.

**Delegated runs:** When work is **delegated** (for example Cursor **Task**) or the user asks for a report back, every **Dedicated sub-agent** must end its final message with a **Primary handoff** to the parent. Format: **Handoff to primary / parent** in `docs/governance/AGENT_ROLES.md` (**Dedicated sub-agents**).

**Minimum expectations**
- **Git Agent**: review diffs and `git status` before commit; no secrets; accurate commit messages.
- **Status Documentation Agent**: any change that alters **shipped behavior**, **API contracts**, **phase scope**, or **honest “not implemented”** claims must update `docs/status/*` and README as needed in the **same** change set (or explicitly leave a TODO only if the user forbids doc edits).
- **Project Manager Agent**: **planning and sequencing** for **`.cursor/plans/*`**—reconcile milestones and **current slice** with `docs/status/*`, README, and phase docs; **does not** implement **backend/** or **frontend/** product code unless explicitly scoped; surface blockers and **avoid premature Phase 8 / Phase 9** work in plans when phase truth does not support it; flag when status docs need a separate pass.
- **Testing Agent**: run or extend tests appropriate to the change; do not remove tests to pass.
- **Docker Agent**: after Compose/Dockerfile edits, validate the documented quickstart path when feasible.
- **Audit Agent**: when closing a phase, preparing a release, or changing major schema/deps, run the checklist in `docs/governance/AUDIT_RULES.md`; record outcomes under `docs/audits/` with an explicit result and honest notes; sync status docs when the audit result changes scope claims.
- **Code Quality Agent**: **read-only**—assess modules against `CODING_STANDARDS.md` / `DOCUMENTATION_STANDARDS.md` / invariants; output structured findings and refactor **ideas**; **do not** modify source, tests, or config while in this role (implementation is a separate, explicitly scoped task).

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

