# GraphClerk Governance Guardrails

Before making changes, read:
- `docs/governance/PROJECT_PRINCIPLES.md`
- `docs/governance/CURSOR_RULES.md`
- `docs/governance/ARCHITECTURAL_INVARIANTS.md`
- `docs/governance/CHANGE_CONTROL.md`

## Non-negotiables
- Do not rename protected terms: Artifact, EvidenceUnit, GraphNode, GraphEdge, SemanticIndex, FileClerk, RetrievalPacket, SourceFidelity, ModelAdapter, IngestionPipeline, ContextBudget.
- Do not implement future phases early.
- Do not mix retrieval and answer synthesis (retrieval returns packets; synthesis generates prose).
- No silent fallbacks: failures must be explicit.

## Prompt contract
Every implementation request must include: phase, task name, allowed/forbidden files, expected output, tests, acceptance criteria, and required docs updates.

