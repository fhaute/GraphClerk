# GraphClerk Governance Guardrails

Before making changes, read:
- `docs/governance/PROJECT_PRINCIPLES.md`
- `docs/governance/CURSOR_RULES.md` (includes **Dedicated sub-agents**)
- `docs/governance/ARCHITECTURAL_INVARIANTS.md`
- `docs/governance/CHANGE_CONTROL.md`
- `docs/governance/AGENT_ROLES.md` (phase agents + **Dedicated sub-agents**: Git, Status docs, Project manager [plan alignment], Testing, Docker, Audits, Code quality [read-only review])

Sub-agent Cursor rules (same charters, file-targeted where applicable):
- `.cursor/rules/graphclerk-subagent-git.mdc`
- `.cursor/rules/graphclerk-subagent-status.mdc`
- `.cursor/rules/graphclerk-subagent-project-manager.mdc`
- `.cursor/rules/graphclerk-subagent-testing.mdc`
- `.cursor/rules/graphclerk-subagent-docker.mdc`
- `.cursor/rules/graphclerk-subagent-audits.mdc`
- `.cursor/rules/graphclerk-subagent-code-quality.mdc`

## Non-negotiables
- Do not rename protected terms: Artifact, EvidenceUnit, GraphNode, GraphEdge, SemanticIndex, FileClerk, RetrievalPacket, SourceFidelity, ModelAdapter, IngestionPipeline, ContextBudget.
- Do not implement future phases early.
- Do not mix retrieval and answer synthesis (retrieval returns packets; synthesis generates prose).
- No silent fallbacks: failures must be explicit.

## Prompt contract
Every implementation request must include: phase, task name, allowed/forbidden files, expected output, tests, acceptance criteria, and required docs updates.

