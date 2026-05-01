# GraphClerk Phase 9 — IDE and AI Client Integration / Developer Evidence Orchestration

## Status

Draft / proposed

---

## Phase Dependency

This phase should only start after:

```text
Phase 0 — Governance Baseline
Phase 1 — Foundation and Core Architecture
Phase 2 — Text-First Ingestion and Evidence Units
Phase 3 — Semantic Index and Graph Layer
Phase 4 — File Clerk and Retrieval Packets
Phase 5 — Multimodal Ingestion
Phase 6 — Productization, UI, Evaluation, and Hardening
Phase 7 — Context Intelligence: Language and Actor Context
Phase 8 — Specialized Model Pipeline and Model Governance
```

Phase 9 assumes:

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
- Multimodal ingestion works at the documented Phase 5 level
- Graph layer exists
- Semantic index search works
- FileClerk retrieval packets exist
- Context budget exists
- Retrieval logs exist
- Phase 6 UI/productization layer exists
- Phase 7 context-intelligence layer exists where implemented
- Phase 8 model registry / model governance exists where implemented
- RetrievalPackets remain the core output of FileClerk
- GraphClerk does not require answer synthesis to be useful
```

Cursor or any coding agent must not implement Phase 9 unless Phase 8 is complete and status docs confirm it, unless this phase is explicitly reopened earlier as a parallel developer-tooling track.

---

## Purpose

Phase 9 turns GraphClerk into a developer-facing evidence clerk that can be used inside IDEs, AI coding environments, and AI reasoning clients.

The first practical target is Cursor, but the architectural boundary is broader: GraphClerk should expose itself as a client-agnostic MCP-based evidence/context server. Claude Desktop and Claude Code should be treated as first-class integration targets alongside Cursor.

The broader goal is to expose GraphClerk as a tool that coding agents and AI reasoning clients can call before modifying or reasoning about a repository, so they can retrieve traceable project context, phase constraints, contracts, protected concepts, known gaps, and architectural rules.

GraphClerk should not become an autonomous coding agent.

GraphClerk should remain the evidence-routing layer that tells a coding assistant or reasoning client:

```text
- what evidence is relevant
- which files or docs support it
- what phase constraints apply
- which contracts must not be broken
- which known gaps or technical debt matter
- what warnings or ambiguity exist
```

The key principle is:

> AI clients should receive structured evidence and constraints before they reason over or edit a project.

---

## Product Principle Preserved In This Phase

GraphClerk remains a local-first, graph-guided evidence-routing layer for RAG systems.

Phase 9 extends that principle into developer tooling.

The integration must not turn GraphClerk into a direct code generator, autonomous IDE agent, or hidden retrieval shortcut.

Allowed architecture:

```text
Cursor / IDE task
  ↓
GraphClerk MCP server or IDE adapter
  ↓
FileClerk retrieval
  ↓
RetrievalPacket
  ↓
IDE receives project-grounded evidence and constraints
  ↓
Coding agent plans or edits using visible context
```

Forbidden architecture:

```text
Cursor / IDE task
  ↓
GraphClerk scans repo directly
  ↓
GraphClerk generates code edits
  ↓
No packet, no evidence, no trace
```

GraphClerk should help Cursor reason inside guardrails.

It should not become the worker that silently changes the repository.

---

## Core Objective

At the end of this phase, GraphClerk should have:

```text
- an MCP server exposing GraphClerk developer tools
- Cursor-compatible configuration and install instructions
- scoped project/repository context retrieval
- tools for retrieving phase-aware development context
- tools for contract and protected-term lookup
- tools for known-gap and technical-debt lookup
- optional diff-audit support
- optional phase-guard checks before coding
- Cursor rules and command templates
- developer-oriented RetrievalPacket summaries
- traceability from IDE responses back to source artifacts and evidence units
- tests for MCP tool contracts
- tests proving tools do not bypass FileClerk
- documentation for Cursor setup and future IDE adapters
- Phase 9 audit
```

The practical goal is to make GraphClerk usable as a repository-aware evidence clerk from inside Cursor.

---

## Scope

### Included

```text
- MCP server for GraphClerk
- MCP tool schemas and contracts
- Cursor installation documentation
- recommended `.cursor/rules` templates
- command templates for common GraphClerk workflows
- project/repo scope configuration
- developer context retrieval tool
- phase guard tool
- contract lookup tool
- known-gap lookup tool
- technical-debt lookup tool
- optional diff audit tool
- optional file explanation tool
- optional architecture constraint lookup
- RetrievalPacket-to-developer-context adapter
- MCP request/response validation
- trace logging for IDE tool calls
- tests for MCP tools
- docs/status updates
- Phase 9 audit
```

### Excluded

```text
- GraphClerk directly editing source code
- autonomous coding loops
- hidden repo-wide scanning outside configured scope
- direct vector/chunk search bypassing FileClerk
- direct answer synthesis unless explicitly packet-bound
- replacing Cursor rules with GraphClerk logic
- replacing human code review
- marketplace publishing before local MCP integration is stable
- enterprise IDE policy management
- hosted SaaS plugin infrastructure
- multi-tenant team workspaces unless separately scoped
- automatic persistent developer memory unless governed by Phase 7 rules
```

---

## Non-Negotiable Rules

```text
1. IDE integration must not bypass FileClerk.
2. MCP tools must return RetrievalPackets or bounded structures derived from RetrievalPackets.
3. GraphClerk must not perform direct vector/chunk retrieval for IDE tools unless it is part of the documented FileClerk route.
4. GraphClerk must not directly edit files.
5. GraphClerk must not apply patches.
6. GraphClerk must not commit code.
7. GraphClerk must not run arbitrary shell commands from IDE requests unless a separate governed tool-execution phase approves it.
8. Cursor may use GraphClerk evidence, but GraphClerk remains the evidence clerk.
9. Phase, governance, contract, and known-gap constraints must be visible before coding when relevant.
10. MCP tool output must expose warnings and uncertainty.
11. MCP tool output must include source traceability where available.
12. No frontend-only or IDE-only fake RetrievalPackets.
13. No hidden repo-wide scanning outside configured project scope.
14. No marketplace package may overclaim maturity.
15. Diff audit is advisory unless explicitly configured as blocking.
16. Every public class/function must have docstrings.
17. Tests must cover MCP contracts and failure behavior.
18. Status docs must be updated before phase completion.
19. Phase 9 audit must be created before phase completion.
```

---

## Core Use Cases

### Use Case 1 — Retrieve context before coding

A coding agent asks:

```text
What constraints apply before modifying the retrieval packet UI?
```

GraphClerk returns:

```text
- relevant phase rules
- backend/frontend contract constraints
- known limitations
- relevant evidence units
- warnings
- confidence
```

### Use Case 2 — Phase guard

A coding agent proposes:

```text
Add answer synthesis to the Phase 6 UI.
```

GraphClerk checks current status and returns:

```text
- warning or block recommendation
- reason: POST /answer is not implemented
- reason: LocalRAGConsumer is deferred
- reason: UI must not imply unsupported answer synthesis
```

### Use Case 3 — Contract lookup

A coding agent asks:

```text
What fields must a RetrievalPacket include?
```

GraphClerk returns the contract-backed fields and source references.

### Use Case 4 — Protected concept lookup

A coding agent asks:

```text
Can I rename EvidenceUnit to SourceChunk?
```

GraphClerk returns governance warnings and change-control requirements.

### Use Case 5 — Diff audit

A coding agent submits a patch or file list.

GraphClerk checks:

```text
- forbidden files touched
- phase boundary violations
- contract changes without tests
- docs/status not updated
- future-phase leakage
- known-gap mismatch
```

GraphClerk returns advisory findings.

---

## Integration Targets

### Client-agnostic boundary — MCP

The real Phase 9 product boundary is the GraphClerk MCP server. Cursor, Claude, and future tools should be clients of that boundary rather than separate backends.

The preferred architecture is:

```text
GraphClerk MCP Server
  ├── Cursor client profile
  ├── Claude Desktop client profile
  ├── Claude Code client profile
  ├── VS Code / Windsurf profiles later
  └── CI / PR bot profiles later
```

### Primary development target — Cursor

Cursor is the first practical IDE integration target because it directly supports AI-assisted coding workflows.

Phase 9 should provide:

```text
- MCP server configuration for Cursor
- example `.cursor/rules`
- example command prompts
- local setup guide
- dogfooding workflow for the GraphClerk repo itself
```

### First-class AI client targets — Claude Desktop and Claude Code

Claude Desktop and Claude Code should be treated as first-class Phase 9 targets, not distant future examples.

Phase 9 should provide:

```text
- MCP server configuration for Claude Desktop
- MCP server configuration for Claude Code where applicable
- Claude-friendly context packet formatting
- setup notes for local GraphClerk backend usage
- safety notes around tool permissions and project scope
```

Claude use cases differ slightly from Cursor:

```text
Cursor:
- evidence and constraints before code edits
- phase guard before implementation
- diff audit after proposed changes

Claude Desktop:
- project/repo reasoning over traceable evidence
- architecture exploration
- contract and known-gap lookup

Claude Code:
- coding-agent guardrails
- evidence retrieval before edits
- advisory diff audit and phase checks
```

### Future targets

The architecture should avoid client-specific assumptions where possible.

Future adapters may include:

```text
- VS Code
- Windsurf
- Codex-style CLI agents
- GitHub pull request review bots
- local CI advisory checks
```

Cursor is the first implementation target, but MCP is the durable integration boundary.

---

# Phase 9 Tracks

## Track 9A — MCP Server Foundation

### Purpose

Expose GraphClerk through a Model Context Protocol server so IDEs and coding agents can call GraphClerk tools.

### Included

```text
- MCP server package/module
- tool registration
- input/output schemas
- configuration loading
- connection to GraphClerk backend API or internal service layer
- explicit error handling
- local development startup command
- tests for tool registration and schemas
```

### Deferred

```text
- hosted MCP server deployment
- authentication for team usage
- marketplace packaging
- remote multi-user mode
```

---

## Track 9B — Developer Context Retrieval Tool

### Purpose

Provide the main IDE-facing retrieval tool.

Suggested tool name:

```text
graphclerk.retrieve_context
```

Input example:

```json
{
  "question": "What constraints apply before editing the retrieval packet UI?",
  "scope": {
    "project": "GraphClerk",
    "phase": "Phase 6",
    "paths": ["frontend/src"]
  },
  "options": {
    "include_raw_packet": false,
    "include_evidence": true,
    "max_evidence_units": 8
  }
}
```

Output should include:

```text
- summary
- relevant constraints
- selected indexes
- graph paths
- evidence references
- warnings
- confidence
- raw RetrievalPacket optionally
```

Rules:

```text
- Must use FileClerk / RetrievalPacket path.
- Must not perform hidden direct search.
- Must expose warnings.
- Must preserve source traceability.
```

---

## Track 9C — Phase Guard Tool

### Purpose

Help Cursor identify whether a planned task fits the current phase and project status.

Suggested tool name:

```text
graphclerk.phase_guard
```

Input example:

```json
{
  "phase": "Phase 6",
  "task": "Add answer synthesis panel to the UI",
  "files": ["frontend/src/components/AnswerPanel.tsx"]
}
```

Output example:

```json
{
  "status": "warn",
  "reasons": [
    "POST /answer is not implemented",
    "LocalRAGConsumer is deferred",
    "Phase 6 UI must not imply unsupported answer synthesis"
  ],
  "recommended_action": "Do not implement an answer panel unless it clearly shows unsupported/deferred state or a separate approved backend plan exists.",
  "evidence_refs": []
}
```

Possible statuses:

```text
allow
warn
blocked_by_current_status
requires_change_control
insufficient_context
```

Rules:

```text
- Advisory by default.
- Must cite or reference source-backed project status where available.
- Must not modify files.
- Must not approve work that contradicts explicit phase docs.
```

---

## Track 9D — Contract and Governance Lookup Tools

### Purpose

Expose project contracts and governance constraints to IDE agents.

Suggested tools:

```text
graphclerk.contract_lookup
graphclerk.protected_term_lookup
graphclerk.governance_lookup
```

Example questions:

```text
- What is the RetrievalPacket contract?
- Can I rename SemanticIndex?
- What are the rules for source fidelity?
- What must happen before changing a protected term?
```

Output should include:

```text
- relevant contract section
- forbidden behavior
- required tests/docs if changed
- change-control requirements
- source references
```

Rules:

```text
- Must distinguish governance rules from implementation status.
- Must surface change-control requirements.
- Must not infer permission to change protected concepts.
```

---

## Track 9E — Known Gap and Technical Debt Tools

### Purpose

Allow Cursor to ask what is currently missing or risky before implementing a task.

Suggested tools:

```text
graphclerk.known_gap_lookup
graphclerk.technical_debt_lookup
```

Example questions:

```text
- Is OCR implemented?
- Is POST /answer available?
- Is SemanticIndex auto-indexing implemented?
- Are frontend tests available?
```

Output should include:

```text
- status
- affected phase
- known limitation
- suggested caution
- source references
```

Rules:

```text
- Must not convert planned features into implemented claims.
- Must distinguish partial, implemented, deferred, and not_started.
```

---

## Track 9F — Diff Audit Tool

### Purpose

Allow Cursor or a developer to ask GraphClerk to review a proposed diff for architectural drift.

Suggested tool name:

```text
graphclerk.audit_diff
```

Input example:

```json
{
  "phase": "Phase 6",
  "changed_files": [
    "frontend/src/components/AnswerPanel.tsx",
    "backend/app/services/file_clerk_service.py"
  ],
  "diff_summary": "Adds an answer panel and modifies FileClerk output."
}
```

Output should include:

```text
- advisory verdict
- possible phase violations
- possible contract changes
- missing tests
- missing docs/status updates
- hidden future-phase risk
- recommended next action
```

Possible verdicts:

```text
pass
pass_with_notes
needs_review
likely_phase_violation
requires_change_control
insufficient_context
```

Rules:

```text
- Must be advisory unless configured otherwise.
- Must not replace tests.
- Must not replace human review.
- Must not claim a diff is safe without enough evidence.
```

---

## Track 9G — Client Profiles: Cursor, Claude Desktop, and Claude Code

### Purpose

Provide ready-to-use client profiles that make GraphClerk easy to use from Cursor, Claude Desktop, and Claude Code without creating separate product logic for each client.

Cursor deliverables:

```text
.cursor/rules/graphclerk-core.md
.cursor/rules/graphclerk-phase-discipline.md
.cursor/rules/graphclerk-no-bypass.md
.cursor/commands/graphclerk-context.md
.cursor/commands/graphclerk-before-coding.md
.cursor/commands/graphclerk-audit-diff.md
```

Claude deliverables:

```text
docs/integrations/CLAUDE_DESKTOP_MCP_SETUP.md
docs/integrations/CLAUDE_CODE_MCP_SETUP.md
docs/integrations/CLAUDE_CONTEXT_PACKET_GUIDE.md
examples/claude/graphclerk_mcp_config.example.json
```

Rule themes:

```text
- Ask GraphClerk for context before architectural changes.
- Do not bypass RetrievalPackets.
- Respect phase boundaries.
- Do not modify protected concepts without change-control.
- Do not overclaim implemented features.
- Update tests and status docs when contracts change.
```

Commands and client prompts should be templates, not magic hidden behavior.

Client profiles may adapt formatting for each environment, but they must not change GraphClerk's core evidence-routing behavior.

---

## Track 9H — Packaging: Cursor Marketplace and Claude MCP Extension

### Purpose

Prepare GraphClerk for client packaging after local MCP integration is stable. This includes Cursor Marketplace packaging and Claude-compatible MCP extension packaging where appropriate.

Included later:

```text
- package metadata
- install instructions
- screenshots or demo flow
- Cursor Marketplace description
- Claude MCP extension / package notes
- topic/category choices
- versioning policy
- security notes
- limitation notes
```

Rules:

```text
- Marketplace package must not overclaim production maturity.
- Claude extension/package must not overclaim production maturity.
- It must clearly say GraphClerk is an evidence-routing layer.
- It must clearly say which features require a running GraphClerk backend.
- It must clearly say which features are advisory.
```

Marketplace or extension packaging should not happen before the MCP tools are locally tested against the GraphClerk repository from at least Cursor and one Claude client.

---

# MCP Tool Contract Principles

Every MCP tool should define:

```text
- purpose
- input schema
- output schema
- allowed behavior
- forbidden behavior
- error behavior
- traceability fields
- tests
```

Tool output should be structured and machine-readable.

Avoid vague prose-only responses.

Suggested common output fields:

```json
{
  "tool": "graphclerk.retrieve_context",
  "status": "ok",
  "summary": "...",
  "findings": [],
  "warnings": [],
  "confidence": 0.0,
  "evidence_refs": [],
  "packet_id": null,
  "raw_packet": null
}
```

---

# Developer Context Adapter and Client Context Profiles

Phase 9 may introduce a `DeveloperContextAdapter` that converts a full RetrievalPacket into compact client-friendly structures.

The adapter should support client profiles such as:

```text
cursor
claude_desktop
claude_code
generic_mcp
```

The profile may change formatting, density, and ordering, but must not change evidence meaning or hide warnings.

Purpose:

```text
- preserve packet traceability
- reduce context bloat for coding agents and AI reasoning clients
- expose constraints clearly
- keep raw packet available when requested
```

Forbidden:

```text
- removing warnings
- hiding ambiguity
- inventing evidence
- rewriting evidence as unsupported claims
- treating summaries as source truth
```

Suggested output sections:

```text
- task_orientation
- relevant_phase_constraints
- relevant_contracts
- protected_terms
- known_gaps
- technical_debt
- suggested_files_to_inspect
- evidence_summary
- warnings
- raw_packet_reference
```

---

# Project Scope Configuration

Phase 9 should support explicit scope configuration.

Example:

```json
{
  "project_name": "GraphClerk",
  "repo_root": ".",
  "allowed_paths": [
    "docs/",
    "backend/app/",
    "backend/tests/",
    "frontend/src/"
  ],
  "forbidden_paths": [
    ".env",
    "data/secrets/",
    "node_modules/",
    ".venv/"
  ],
  "default_phase": "Phase 9",
  "backend_url": "http://localhost:8010"
}
```

Rules:

```text
- Scope must be explicit.
- Secrets must be excluded by default.
- Large generated folders must be excluded by default.
- IDE tools must not silently scan outside allowed paths.
```

---

# MCP Security and Safety Requirements

Phase 9 expands GraphClerk into IDE and AI-client environments, so MCP security must be explicit and first-class.

Minimum requirements:

```text
- no arbitrary command execution
- no secret file reading by default
- no automatic file modification
- no automatic commits
- no hidden outbound network calls beyond configured GraphClerk backend and model providers
- clear local-only default mode
- explicit configuration for remote backend usage
- clear error when backend is unavailable
- client-specific setup docs must explain what tools are exposed
- client-specific setup docs must explain how to disable tools
```

MCP tools should fail closed when scope is invalid.

Claude Desktop, Claude Code, Cursor, and future clients must all use the same safety defaults unless a stricter client profile is configured.

---

# Relationship With Phase 7 Context Intelligence

Phase 9 may use ActorContext to describe the developer or coding session.

Allowed:

```text
- active_project = GraphClerk
- current_phase = Phase 9
- expertise_level = developer
- preferred_answer_language
- recent_topics as routing metadata
```

Forbidden:

```text
- treating developer preference as source evidence
- using ActorContext to bypass repository scope
- persisting developer memory without explicit Phase 7-compatible governance
```

ActorContext remains a routing prior, not evidence.

---

# Relationship With Phase 8 Model Governance

Phase 9 may use Phase 8 model routing if model-assisted summarization, diff interpretation, or contract extraction is introduced.

Rules:

```text
- model use must be role-bound
- model output must be validated
- model traces must record model id and role
- model output must not become source truth
- model-generated findings must remain advisory unless validated against source-backed evidence
```

Phase 9 must not introduce hidden model calls outside the Phase 8 governance structure.

---

# API / Service Components

Recommended components:

```text
McpServer
McpToolRegistry
DeveloperContextService
DeveloperContextAdapter
PhaseGuardService
ContractLookupService
KnownGapLookupService
TechnicalDebtLookupService
DiffAuditService
CursorConfigService
ClaudeConfigService
IdeTraceService
ScopeValidationService
```

Adapters:

```text
CursorMcpAdapter
ClaudeDesktopMcpAdapter
ClaudeCodeMcpAdapter
GenericMcpAdapter
GraphClerkBackendApiClient
LocalGraphClerkServiceAdapter optional
```

Schemas:

```text
DeveloperContextRequest
DeveloperContextResponse
PhaseGuardRequest
PhaseGuardResponse
ContractLookupRequest
ContractLookupResponse
KnownGapLookupRequest
KnownGapLookupResponse
DiffAuditRequest
DiffAuditResponse
IdeToolTrace
ProjectScopeConfig
```

---

# Error Handling Requirements

Errors must be explicit.

Possible errors:

```text
GraphClerkBackendUnavailableError
InvalidMcpToolInputError
ProjectScopeInvalidError
ProjectScopeViolationError
RetrievalPacketUnavailableError
DeveloperContextBuildError
PhaseGuardEvaluationError
ContractLookupError
KnownGapLookupError
DiffAuditInputTooLargeError
UnsupportedIdeAdapterError
CursorConfigError
ClaudeConfigError
UnsupportedClientProfileError
```

Rules:

```text
- Backend unavailable must not be reported as no evidence.
- Scope violations must fail clearly.
- Invalid MCP input must return validation errors.
- Diff audit must handle oversized diffs by asking for smaller input or using summaries.
- Tool failures must not produce fake successful findings.
```

---

# Required Tests

## MCP foundation tests

```text
test_mcp_server_registers_graphclerk_tools
test_mcp_tool_schemas_are_valid
test_mcp_tool_rejects_invalid_input
test_mcp_backend_unavailable_fails_clearly
test_mcp_tool_output_has_status_and_warnings
test_mcp_tool_supports_cursor_client_profile
test_mcp_tool_supports_claude_desktop_client_profile
test_mcp_tool_supports_claude_code_client_profile
```

## Retrieve context tests

```text
test_retrieve_context_uses_fileclerk_path
test_retrieve_context_returns_developer_context
test_retrieve_context_can_include_raw_packet
test_retrieve_context_preserves_packet_warnings
test_retrieve_context_preserves_evidence_refs
test_retrieve_context_respects_scope_config
```

## Phase guard tests

```text
test_phase_guard_allows_in_scope_task
test_phase_guard_warns_on_deferred_answer_synthesis
test_phase_guard_warns_on_phase6_ui_overclaim
test_phase_guard_requires_change_control_for_protected_term_change
test_phase_guard_returns_insufficient_context_when_status_missing
```

## Contract/governance tests

```text
test_contract_lookup_returns_retrieval_packet_contract
test_protected_term_lookup_detects_evidence_unit
test_governance_lookup_returns_change_control_requirements
test_contract_lookup_does_not_invent_missing_contracts
```

## Known gap / technical debt tests

```text
test_known_gap_lookup_reports_post_answer_not_implemented
test_known_gap_lookup_reports_ocr_not_implemented
test_known_gap_lookup_distinguishes_partial_from_complete
test_technical_debt_lookup_reports_frontend_tests_missing
```

## Diff audit tests

```text
test_diff_audit_warns_when_forbidden_files_touched
test_diff_audit_warns_when_contract_changes_without_tests
test_diff_audit_warns_when_docs_status_not_updated
test_diff_audit_is_advisory_by_default
test_diff_audit_handles_oversized_diff_explicitly
```

## Security / scope tests

```text
test_scope_config_excludes_env_files
test_scope_config_excludes_node_modules
test_tool_rejects_paths_outside_repo_scope
test_tool_does_not_execute_shell_commands
test_tool_does_not_modify_files
```

---

# Documentation Requirements

Phase 9 must create or update:

```text
docs/phases/PHASE_9_IDE_INTEGRATION_DEVELOPER_EVIDENCE_ORCHESTRATION.md
docs/status/PROJECT_STATUS.md
docs/status/PHASE_STATUS.md
docs/status/KNOWN_GAPS.md
docs/status/TECHNICAL_DEBT.md
docs/audits/PHASE_9_AUDIT.md
docs/integrations/CURSOR_MCP_SETUP.md
docs/integrations/CLAUDE_DESKTOP_MCP_SETUP.md
docs/integrations/CLAUDE_CODE_MCP_SETUP.md
docs/integrations/IDE_TOOL_CONTRACTS.md
docs/integrations/DEVELOPER_CONTEXT_ADAPTER.md
docs/integrations/DIFF_AUDIT.md
```

Optional:

```text
docs/adr/ADR-000X-cursor-mcp-integration.md
docs/adr/ADR-000X-developer-context-packets.md
docs/marketplace/CURSOR_MARKETPLACE_NOTES.md
docs/marketplace/CLAUDE_MCP_EXTENSION_NOTES.md
.cursor/rules/graphclerk-core.md
.cursor/rules/graphclerk-phase-discipline.md
.cursor/rules/graphclerk-no-bypass.md
```

---

# README Must Say

```text
Implemented:
- MCP server for IDE integration if implemented
- Cursor setup instructions if implemented
- developer context retrieval tools if implemented
- phase guard tools if implemented
- contract / known-gap lookup tools if implemented
- advisory diff audit if implemented

Limitations:
- GraphClerk does not edit code directly
- GraphClerk does not replace code review
- GraphClerk does not run arbitrary shell commands
- GraphClerk tools are advisory unless explicitly configured otherwise
- Cursor integration requires a running GraphClerk backend unless packaged differently
- Claude integration requires a running GraphClerk backend unless packaged differently
- Marketplace / extension packaging may be deferred
```

Do not claim GraphClerk is an autonomous coding agent.

Do not claim GraphClerk guarantees correct code.

Do not claim GraphClerk can enforce repository policy unless blocking enforcement is explicitly implemented.

---

# Status Document Requirements

`PROJECT_STATUS.md` should update the current state.

Example:

```text
Current phase: Phase 9 — IDE Integration and Developer Evidence Orchestration

Implemented:
- MCP server foundation
- Cursor setup docs
- retrieve_context tool
- phase_guard tool
- contract lookup tool
- known gap lookup tool
- advisory diff audit

Known limitations:
- Cursor integration is local-first
- Claude integration is local-first
- Marketplace / extension packaging is not complete
- Diff audit is advisory
- GraphClerk does not edit code directly
```

`KNOWN_GAPS.md` should include:

```text
- Marketplace / extension packaging not completed if deferred
- IDE/client integration tested first with Cursor and Claude only
- Diff audit advisory only
- No automatic enforcement in CI unless separately implemented
- No direct code editing by GraphClerk
```

`TECHNICAL_DEBT.md` should include accepted shortcuts.

---

# Phase 9 Audit Requirements

Create:

```text
docs/audits/PHASE_9_AUDIT.md
```

Audit must answer:

```text
- Does IDE integration use FileClerk / RetrievalPackets?
- Do MCP tools avoid hidden vector/chunk retrieval bypasses?
- Does GraphClerk avoid editing code directly?
- Are scope boundaries enforced?
- Are secrets excluded by default?
- Are tool outputs structured and machine-readable?
- Are warnings and uncertainty preserved?
- Are source/evidence references preserved where available?
- Are phase guard findings grounded in status/phase docs?
- Are contract lookup tools grounded in governance/contracts?
- Is diff audit advisory unless explicitly configured otherwise?
- Are Cursor rules and setup docs honest?
- Are Claude setup docs honest?
- Does README overclaim Marketplace or autonomous coding maturity?
- Are tests present for MCP contracts and failure behavior?
- Are known gaps listed?
```

Allowed audit result:

```text
pass
pass_with_notes
needs_fix
blocked
```

Phase 9 is not complete if audit result is `needs_fix` or `blocked`.

---

# Implementation Tasks

## Task 1 — Define Phase 9 contracts and docs

Create the phase document and initial integration contracts.

Acceptance:

```text
- Phase 9 doc exists
- MCP tool contract doc exists
- developer context adapter doc exists
- status docs mention Phase 9 as draft/proposed
```

---

## Task 2 — Build MCP server foundation

Implement a minimal MCP server package/module.

Acceptance:

```text
- MCP server starts locally
- tool registry works
- health/status tool works
- invalid input fails clearly
- tests cover tool registration
```

---

## Task 3 — Implement `graphclerk.retrieve_context`

Expose the main developer context retrieval tool.

Acceptance:

```text
- tool accepts question + optional scope
- tool calls FileClerk / retrieve path
- tool returns developer context derived from RetrievalPacket
- warnings and evidence references are preserved
- raw packet can be included when requested
```

---

## Task 4 — Implement `graphclerk.phase_guard`

Add phase-aware task checking.

Acceptance:

```text
- tool accepts phase + task + files
- tool returns allow/warn/block-style status
- tool references phase/status evidence where available
- tool does not modify files
```

---

## Task 5 — Implement contract and governance lookup

Add contract/protected-term/governance lookup tools.

Acceptance:

```text
- RetrievalPacket contract can be found
- protected terms can be found
- change-control requirements are surfaced
- missing contracts do not produce invented answers
```

---

## Task 6 — Implement known-gap and technical-debt lookup

Expose current limitations to Cursor.

Acceptance:

```text
- known gaps can be queried
- technical debt can be queried
- partial vs complete status is preserved
- not_started and deferred features are not described as implemented
```

---

## Task 7 — Add project scope configuration

Implement scope validation for IDE requests.

Acceptance:

```text
- allowed paths and forbidden paths are configurable
- secrets are excluded by default
- out-of-scope paths fail clearly
- no silent repo-wide scanning occurs
```

---

## Task 8 — Implement advisory diff audit

Add a first diff-audit tool.

Acceptance:

```text
- changed files can be checked
- diff summaries can be checked
- forbidden paths trigger warnings
- possible contract changes trigger warnings
- missing tests/docs trigger warnings where detectable
- output is advisory by default
```

---

## Task 9 — Add Cursor and Claude client setup docs

Create Cursor-specific and Claude-specific usage instructions.

Acceptance:

```text
- Cursor MCP setup doc exists
- Claude Desktop MCP setup doc exists
- Claude Code MCP setup doc exists where applicable
- sample Cursor config exists
- sample Claude config exists
- recommended `.cursor/rules` exist
- command templates exist
- Claude context packet guide exists
- docs explain local backend requirement
```

---

## Task 10 — Phase 9 audit and status update

Finalize the phase slice.

Acceptance:

```text
- tests pass
- status docs updated
- known gaps updated
- technical debt updated
- README updated honestly
- Phase 9 audit created
- audit result is pass or pass_with_notes
```

---

# Completion Definition

Phase 9 is complete only when:

```text
- MCP server exists and starts locally
- Cursor setup is documented
- Claude Desktop / Claude Code setup is documented where scoped
- retrieve_context works through FileClerk / RetrievalPackets
- phase_guard works against documented phase/status context
- contract/governance lookup works
- known-gap/technical-debt lookup works
- project scope boundaries are enforced
- diff audit exists if scoped into completion
- tests pass
- docs/status files are updated
- README does not overclaim
- Phase 9 audit is pass or pass_with_notes
```

If Marketplace packaging is not completed, Phase 9 may still pass with notes if the local Cursor/MCP integration works and the limitation is documented.

---

# Suggested First Slice

The first practical slice should be small:

```text
Slice 9A — Local Cursor MCP MVP

- MCP server foundation
- graphclerk.retrieve_context
- GraphClerk backend API client
- DeveloperContextAdapter
- Cursor setup doc
- Claude setup doc
- basic scope config
- tests for tool schema and FileClerk usage
```

Do not start with Marketplace packaging.

Dogfood the MCP integration on the GraphClerk repository first, using Cursor and at least one Claude client before packaging.

---

# Suggested Naming

Preferred phase title:

```text
Phase 9 — IDE and AI Client Integration / Developer Evidence Orchestration
```

Alternative shorter title:

```text
Phase 9 — MCP Developer Tooling
```

Preferred product framing:

```text
GraphClerk MCP: evidence-grounded project context before AI tools reason over or edit your repo.
```

