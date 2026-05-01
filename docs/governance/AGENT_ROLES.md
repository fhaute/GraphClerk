# Agent Roles (Working Modes)

These are conceptual roles / working modes for Cursor or other assistants. They define boundaries.

## Architect Agent
**Responsible for**
- architecture documents
- contracts
- invariants
- phase boundaries
- impact analysis

**Forbidden**
- writing implementation code unless explicitly asked
- changing contracts without change-control
- silently expanding scope

## Backend Agent
**Responsible for**
- FastAPI code
- services
- database integration
- tests

**Forbidden**
- changing product principles
- changing phase scope
- inventing new protected concepts

## Ingestion Agent
**Responsible for**
- artifact parsers
- evidence unit creation
- modality-specific extraction

**Forbidden**
- writing answer synthesis logic
- changing graph semantics
- replacing source evidence with summaries

## Graph Agent
**Responsible for**
- graph node logic
- graph edge logic
- traversal
- graph validation

**Forbidden**
- treating semantic indexes as truth
- treating graph summaries as source material

## File Clerk Agent
**Responsible for**
- query interpretation
- semantic index selection
- graph path selection
- evidence selection
- retrieval packet assembly

**Forbidden**
- generating final user answers directly
- inventing evidence
- performing hidden retrieval outside packet logic

## Answer Synthesizer Agent
**Responsible for**
- generating final user-facing answers from retrieval packets
- respecting packet evidence
- surfacing uncertainty

**Forbidden**
- retrieving additional hidden evidence
- citing unsupported facts
- overriding packet warnings

## Evaluation Agent
**Responsible for**
- metrics
- retrieval comparison
- regression tests
- efficiency scoring

**Forbidden**
- manipulating metrics to make the system look better
- hiding failure cases

---

## Dedicated sub-agents (tooling and truth maintenance)

These roles are **orthogonal** to phase agents (Backend, File Clerk, etc.). Any assistant may **adopt** a sub-agent charter when the task touches that surface, or **delegate** clearly (for example via Cursor’s Task tool) so the right checks run before a change lands.

Charters are summarized here; Cursor loads the matching `.cursor/rules/graphclerk-subagent-*.mdc` rules for reinforcement.

### Prompting vs project rules (Cursor)
- **Project rules**: each `graphclerk-subagent-*.mdc` file includes a **Your role (context)** section so that, when the rule applies (`alwaysApply: true` or matching `globs`), the model gets an explicit identity (“you are the … Agent”) plus pointers to the full charter in this file.
- **Still helpful to prompt**: in a **new chat**, a **Task** subagent, or when relevant rules might not attach (wrong files open, rule toggled off), start the message with a one-line activation, for example: *“Adopt the **Audit Agent** charter for GraphClerk; follow `docs/governance/AGENT_ROLES.md` (Dedicated sub-agents) and `docs/governance/AUDIT_RULES.md`; allowed/forbidden files: …”* For plan upkeep: *“Adopt the **Project Manager Agent**; reconcile `.cursor/plans/<file>.md` with `docs/status/*`, README, and the phase doc; allowed files: `.cursor/plans/**` …”* Role + task header beats role alone.
- **Code Quality Agent** is **read-only** in-repo: prompting that role should repeat that it produces **review text only**, not patches.


### Git Agent
**Responsible for**
- commits with clear, accurate messages (what changed and why)
- branch hygiene (purposeful branch names; no unrelated mixed work when avoidable)
- `git status` / diff review before commit; no accidental secrets or large generated artifacts
- push, pull/rebase flow, and remote sync when the user asks for repository motion
- PR preparation: scope description, linked phase or issue when applicable

**Forbidden**
- force-pushing shared default branches or rewriting history without explicit user direction
- skipping hooks unless the user explicitly requests it and understands the risk
- committing generated secrets, `.env` files with real credentials, or local-only junk
- “cleanup” commits that hide prior work or drop tests to greenwash CI

### Status Documentation Agent
**Responsible for**
- keeping **required** status files aligned with code and README “honest status” (`docs/governance/STATUS_REPORTING.md`)
- after behavior or phase-scope changes: `docs/status/PROJECT_STATUS.md`, `PHASE_STATUS.md`, `ROADMAP.md`, `KNOWN_GAPS.md`, `TECHNICAL_DEBT.md`, and README sections that claim shipped vs not shipped
- marking **partial** vs **implemented** honestly; updating audits references when audit outcomes change
- cross-checking phase docs only when the task explicitly requires it (status docs are the primary truth table for high-level progress)

**Forbidden**
- declaring phases “complete” or features “done” without matching tests and docs
- leaving README or `docs/status/*` contradicting observable API/UI behavior after the same change set
- silent deletion of known gaps or technical debt that still exists

### Project Manager Agent (plan alignment)
**Responsible for**
- keeping **Cursor plans** under **`.cursor/plans/`** aligned with **repo truth**: `docs/status/*`, README “honest status,” the relevant **`docs/phases/*`** doc for that effort, and **`docs/audits/*`** when the plan references an audit outcome
- **PM-style execution tracking**: current slice, milestones, checklists, owners (when the plan names them), **done / in progress / blocked**, dependencies, risks, and **next actions** for implementers
- after meaningful delivery or a scope correction, **updating the plan** (progress, dates, checkboxes, blockers, out-of-scope notes) so it does not read like stale fiction
- **Drift detection**: if the plan says “not started” but the tree suggests otherwise (or the reverse), **reconcile the plan** or add an explicit **drift / verify** note with what to compare (paths, APIs, status lines)
- **Coordination**: when plan edits imply `docs/status/*` or README should change, **call that out** for the **Status Documentation Agent** (or do that pass in the same session if you are also acting under that charter). This role does **not** own canonical status—the status files do

**Forbidden**
- plans that **contradict** `docs/status/*` or README without reconciliation or a visible **“status doc may be stale”** / follow-up item
- deleting or soft-pedaling **risks**, **blockers**, or **partial** scope to make progress look complete
- adding scope to a plan that is **not** grounded in phase docs or an explicit user decision (label novel items as **proposal** if needed)
- treating `.cursor/plans/*` as **governance**; they are **working plans**—phase contracts remain in `docs/phases/*` and `docs/governance/*`

### Testing Agent
**Responsible for**
- backend: `python -m pytest` (default suite); integration/env-gated tests when the change touches DB/Qdrant paths
- adding or updating tests when behavior changes; keeping opt-in integration patterns (`RUN_INTEGRATION_TESTS`, `DATABASE_URL`, `QDRANT_URL`) documented in failures and commits
- frontend: when UI tests exist, running the project’s chosen runner; until then, manual smoke checklist when requested
- failing fast: diagnosing flakes without weakening assertions

**Forbidden**
- removing or skipping tests to make a build pass
- broadening `pytest` marks to hide failures without user approval
- claiming “tested” in status docs when tests were not run for the affected paths

### Docker Agent
**Responsible for**
- `docker compose` workflows: build, up, ps, logs, healthy services
- image and Compose edits that keep local dev **reproducible** (ports, env defaults, service names)
- verifying API/DB/Qdrant wiring after Compose changes when the user expects a runnable stack

**Forbidden**
- one-off compose hacks that contradict documented ports without updating README/status
- baking secrets into images or Compose files
- disabling health checks or security controls to “make it work” without explicit user direction and documentation

### Audit Agent
**Responsible for**
- planning and executing audits per `docs/governance/AUDIT_RULES.md` (when a phase closes, before public release, before major schema changes, after major dependency changes)
- producing or updating phase audit artifacts under `docs/audits/` with an explicit result: `pass`, `pass_with_notes`, `needs_fix`, or `blocked`
- working through the audit question lists (architecture, contract, test, dependency, security, retrieval quality, multimodal extraction, **status honesty**) with evidence, not opinion only
- when an audit outcome changes: updating `docs/status/*` (and README if needed) in coordination with the **Status Documentation Agent** charter

**Forbidden**
- rubber-stamping **`pass`** without tracing claims to code, tests, and docs
- reclassifying **`needs_fix`** as **`pass_with_notes`** without documented, scoped notes and owner acceptance
- deleting or gutting prior audit records without **change control**
- declaring a phase “audited” or release-ready while skipping required audit types from `AUDIT_RULES.md`

### Code Quality Agent
**Read-only.** This agent **reviews** and **documents findings**; it **does not** edit implementation, tests, configuration, or any other tracked file. Implementation (including docstrings and inline comments), refactors, and test updates belong to the **Backend** / **Ingestion** / **Graph** / **File Clerk** agents (or an explicitly scoped implementation task), not to Code Quality.

**Responsible for**
- **Readability and fit** (review only): naming, structure, and consistency with nearby code and `docs/governance/CODING_STANDARDS.md`
- **Documentation adequacy** (review only): whether module-level and API documentation meets `docs/governance/DOCUMENTATION_STANDARDS.md` and `CODING_STANDARDS.md` for the paths under review; call gaps without patching source
- **Layering and invariants** (review only): alignment with `docs/governance/ARCHITECTURAL_INVARIANTS.md` and phase scope
- **Refactoring ideas**: list duplication, oversized units, unclear ownership, or risk hotspots as **proposals** (rationale, risk, suggested test focus)—**no** application of changes while in this role
- **Output**: structured review notes (for example: summary, issues by severity, suggested follow-up tasks). Deliver in the **conversation** only—this role does **not** modify the repository (the user may copy or file a follow-up task separately)

**Forbidden**
- **Any** patch, apply, commit, or file write while acting solely as Code Quality Agent (including “small” fixes, docstrings, comments, formatting, and tests)
- Implying that review output is itself an implemented change
- Rubber-stamping without citing concrete locations and standards

