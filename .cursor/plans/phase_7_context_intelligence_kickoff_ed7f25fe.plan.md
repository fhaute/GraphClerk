---
name: Phase 7 context intelligence kickoff
overview: Open Phase 7 — Context Intelligence (Language and Actor Context) by creating a Cursor working plan, performing minimal honest status alignment, and proposing Slice 7A (no-op `EvidenceEnrichmentService` shell) as the first implementation slice. No backend code, no schema changes, no Phase 7 implementation work in this delivery.
todos:
  - id: p7-doc-gate
    content: "Slice 7.0 — Entry gate verification: confirm Phase 6 pass_with_notes, Phase 5 partial, /answer deferred, no OCR/ASR/caption/video claims; Phase 7 is correct next phase."
    status: completed
  - id: p7-create-plan
    content: Project Manager sub-agent creates .cursor/plans/phase_7_context_intelligence_<8hex>.plan.md with Slices 7.0–7K, purpose, non-scope, acceptance, risks, testing/status expectations, and the routing-not-evidence reminder.
    status: completed
  - id: p7-status-check
    content: Status Documentation sub-agent verifies whether any status doc edits are strictly required to honestly mark Phase 7 = not_started, planning underway; default is no edit.
    status: completed
  - id: p7-audit-readonly
    content: Audit sub-agent read-only review of the plan for phase boundary risks and overclaim; no audit artifact written.
    status: completed
  - id: p7-codequality-readonly
    content: Code Quality sub-agent read-only review of plan and any status edits for phase leakage, contract risk, and over-broad first slice.
    status: completed
  - id: p7-testing-report
    content: Testing sub-agent reports tests-not-run because planning/docs-only and cites the rule allowing this.
    status: completed
  - id: p7-git-commit
    content: "Git sub-agent stages only approved files (explicit per-file git add), verifies pre-existing governance modifications remain unstaged, commits 'docs: start phase 7 context intelligence planning'; no push without explicit approval."
    status: completed
  - id: p7-slice-7a-proposal
    content: Recommend Slice 7A (EvidenceEnrichmentService no-op shell) as the first implementation slice for a future, separately-approved prompt — do NOT implement in this task.
    status: completed
isProject: false
---

## Phase 7 — Context Intelligence (Language and Actor Context): kickoff plan

This task is **planning + minimal status alignment only**. No backend, frontend, schema, dependency, audit-artifact, or Phase 8/9 work will be performed. Sub-agent delegation will be used for execution; each delegated sub-agent must end its final message with a **Primary handoff report** per [docs/governance/AGENT_ROLES.md](docs/governance/AGENT_ROLES.md) → Dedicated sub-agents → Handoff to primary / parent.

### Entry-gate result (already verified, read-only)

- Phase 6 audit: [docs/audits/PHASE_6_AUDIT.md](docs/audits/PHASE_6_AUDIT.md) — **`pass_with_notes`** (2026-05-01).
- Phase 5: **partial / `pass_with_notes`** ([docs/audits/PHASE_5_AUDIT.md](docs/audits/PHASE_5_AUDIT.md)) — not marked complete.
- Phase 4 and earlier: implemented.
- `/answer`, OCR, ASR, captioning, video: **not started / deferred** — explicit in [docs/status/KNOWN_GAPS.md](docs/status/KNOWN_GAPS.md).
- Phase 8 / 9 phase docs exist but are not status-claimed — Phase 7 is correctly next.
- No prior Phase 7 plan exists under [.cursor/plans/](.cursor/plans/).

### Pre-existing unstaged drift (out of scope; will NOT be staged)

These files already had unstaged modifications before this task started and are explicitly off-limits for the Phase 7 commit:

- `M .cursor/rules/governance.md`
- `M docs/governance/AGENT_ROLES.md`
- `M docs/governance/CURSOR_RULES.md`
- `?? .cursor/rules/graphclerk-subagent-project-manager.mdc`

The Git sub-agent will use **explicit per-file `git add` only** — never `git add .` / `git add -A`.

### Files to be created or edited

Allowed for this task:

- **NEW** `.cursor/plans/phase_7_context_intelligence_<8hex>.plan.md` — Cursor working plan (front-matter + slice list, mirroring the `.plan.md` style of [.cursor/plans/phase_6_ui_plan_818a2a0a.plan.md](.cursor/plans/phase_6_ui_plan_818a2a0a.plan.md)).
- Possibly minimal pointers in [docs/status/PHASE_STATUS.md](docs/status/PHASE_STATUS.md), [docs/status/ROADMAP.md](docs/status/ROADMAP.md), and [docs/status/PROJECT_STATUS.md](docs/status/PROJECT_STATUS.md) marking Phase 7 as **`not_started`** with planning underway — only if needed; status docs currently make no Phase 7 claim, so a one-line addition each is the maximum.
- [docs/status/KNOWN_GAPS.md](docs/status/KNOWN_GAPS.md) and [docs/status/TECHNICAL_DEBT.md](docs/status/TECHNICAL_DEBT.md): no edits unless required to keep claims honest. Default: no edits.
- [README.md](README.md): no edits unless a strict honesty correction is required. Default: no edits.

Forbidden for this task (re-confirmed): everything under `backend/**`, `frontend/**`, `docker-compose.yml`, `backend/pyproject.toml`, `requirements*`, `docs/audits/**`, the Phase 8/9 phase docs, `.cursor/rules/**`, and any other `.cursor/plans/` files.

### Cursor plan content (`.cursor/plans/phase_7_context_intelligence_<8hex>.plan.md`)

Front-matter `todos` cover Slices 7.0 → 7K (`status: pending` for all except 7.0 which is `in_progress`). Body sections:

- **Phase purpose** — quote the [phase doc](docs/phases/graph_clerk_phase_7_context_intelligence.md) Purpose verbatim, then the key principle: *"Context can influence retrieval routes, but it must not become evidence."*
- **Entry conditions** — Phase 6 `pass_with_notes`, Phase 5 still partial, `/answer` deferred, no OCR/ASR/caption/video claimed, Phase 8 not started.
- **Non-scope (Phase 7)** — quote the phase-doc *Excluded* list and add: no `/answer`, no `LocalRAGConsumer`, no `AnswerSynthesizer`, no Phase 8 model pipeline, no UI work, no translation engine, no persisted actor memory, no LLM calls, no hidden retrieval outside FileClerk/RetrievalPacket, no protected-term renames, no silent fallbacks.
- **Slices** (each with: scope, allowed/forbidden file hints, acceptance, deferred items):
  - **Slice 7.0** — Entry gate + plan alignment (no backend code).
  - **Slice 7A** — `EvidenceEnrichmentService` shell (no-op pass-through).
  - **Slice 7B** — Language metadata contract on `EvidenceUnitCandidate` via `metadata_json` (no DB migration, no detection yet, no text modification).
  - **Slice 7C** — `LanguageDetectionAdapter` contract + `NotConfigured` / deterministic local test adapter; explicit unknown / low-confidence behavior; no remote services; no translation.
  - **Slice 7D** — Wire enrichment into existing Phase 2 text/Markdown and Phase 5 PDF/PPTX persistence path only after 7A–7C are stable; `text` and `source_fidelity` provably unchanged.
  - **Slice 7E** — Optional Artifact language aggregation into `metadata_json` (no first-class columns).
  - **Slice 7F** — Optional `RetrievalPacket.language_context` section (backward-compatible; records query/evidence languages; no translation).
  - **Slice 7G** — Optional `actor_context` request schema for `POST /retrieve`; `/retrieve` works unchanged when absent; invalid context fails clearly; no boosting; no persistence.
  - **Slice 7H** — `RetrievalPacket.actor_context` recording; `used=false` when absent; `used=true` when present; influences "recorded only; no route boost applied"; tests prove ActorContext does not create evidence.
  - **Slice 7I** — Optional deterministic context boosting — **explicitly deferred** until 7G/7H are stable; not in initial implementation unless separately approved.
  - **Slice 7J** — Docs/status update (language metadata vs translation; ActorContext vs evidence; no claim of translation engine or memory agent).
  - **Slice 7K** — Phase 7 audit: create `docs/audits/PHASE_7_AUDIT.md` after implementation slices.
- **Acceptance criteria** — copy the phase-doc *Acceptance Criteria* block verbatim.
- **Risks** — copy the phase-doc Risk 1–6 block.
- **Testing expectations** — pytest from `backend/` after each behavior-affecting slice; no test removal; integration tests only with documented env; per the Testing Agent charter ([.cursor/rules/graphclerk-subagent-testing.mdc](.cursor/rules/graphclerk-subagent-testing.mdc)).
- **Status-doc expectations** — Status Documentation sub-agent updates `docs/status/*` only when shipped behavior, contracts, phase scope, or honest "not implemented" claims change.
- **Reminder block** — bold, top-and-bottom: *Context can influence retrieval routes, but must never become evidence.*

### Slice 7A proposal (do NOT implement yet — for the next prompt)

Allowed likely files:

- `backend/app/services/evidence_enrichment_service.py` (new)
- `backend/tests/test_phase7_evidence_enrichment_service.py` (new)
- `backend/app/services/__init__.py` only if needed for export

Forbidden for Slice 7A (re-stated to prevent leakage): `backend/app/api/**`, `backend/app/schemas/retrieval_packet.py`, retrieve request schemas, `backend/app/services/file_clerk_service.py`, `backend/app/services/multimodal_ingestion_service.py`, `frontend/**`, `docs/status/**`, migrations, `pyproject.toml`, any language-detection dependency.

Acceptance for Slice 7A:

- `EvidenceEnrichmentService` class exists with a documented `enrich(candidates) -> candidates` (or equivalent) pass-through method.
- Accepts candidate-like objects and returns them unchanged (text and `source_fidelity` byte-identical).
- No DB access, no LLM calls, no language detection, no translation, no ActorContext, no `EvidenceUnit` creation.
- Unit tests prove pass-through semantics (text unchanged, source_fidelity unchanged, count preserved, ordering preserved).
- Existing backend test suite still passes (`python -m pytest -q` from `backend/`).

### Sub-agent delegation plan (for execution)

Each sub-agent must end with a **Primary handoff report** (Mission recap → files touched → drift / blockers → next actions). Order:

1. **Status Documentation sub-agent** — verify Phase 7 entry conditions in README/status/roadmap/known gaps; report whether any status edits are strictly required to honestly reflect Phase 7 = `not_started, planning`. If none required, say so.
2. **Project Manager sub-agent** — confirm Phase 7 is correct next phase (not Phase 8/9), confirm Slice 7A is a sufficiently small first slice, identify any blockers; create the `.cursor/plans/phase_7_context_intelligence_<8hex>.plan.md` per the structure above.
3. **Audit sub-agent** — read-only Phase 7 boundary review of the plan: no claim of implementation, no overclaim, no Phase 8/9 leakage, no /answer claim, ActorContext / LanguageContext separation respected. Output findings only; **no** audit artifact written this task.
4. **Code Quality sub-agent** — read-only review of the plan and any status edits: phase leakage, contract risk, over-broad first slice. Output findings only; **no** patches.
5. **Testing sub-agent** — report "tests not run because planning/docs-only"; cite the Testing Agent rule that backend tests are required only for behavior-affecting backend changes ([.cursor/rules/graphclerk-subagent-testing.mdc](.cursor/rules/graphclerk-subagent-testing.mdc)).
6. **Git sub-agent** — explicit per-file `git add` of approved files only; verify pre-existing modified governance files are NOT staged; commit `docs: start phase 7 context intelligence planning`. **No push** unless the user explicitly approves it after the commit lands.

### Final report (to be produced after execution)

- Entry-gate result (already verified above).
- Project Manager recommendation (start with Slice 7A only).
- Files changed (just the plan file; status doc edits only if strictly required).
- Whether status docs changed (likely **no**).
- Whether a Phase 7 plan was created (yes — new file).
- Recommended first implementation slice (Slice 7A — `EvidenceEnrichmentService` shell).
- Tests run or not run (not run — planning/docs-only).
- Commit hash if committed.
- Final `git status --short` — must still show the four pre-existing unstaged governance items untouched.
- Brief summary of each sub-agent's Primary handoff report.

### Non-negotiables explicitly carried forward

ActorContext is not evidence. LanguageContext is metadata/routing context, not source truth. User beliefs are not facts. User preferences cannot override source-backed evidence. ActorContext does not bypass access control. Language detection cannot modify EvidenceUnit text. No silent translation. Query translation is **not** in the first slice. No persisted actor memory in the first slice. No LLM calls. No `/answer` / `LocalRAGConsumer` / `AnswerSynthesizer` work. No Phase 8 model pipeline work. No hidden retrieval outside FileClerk / RetrievalPacket boundaries. No silent fallbacks. No protected-term renames. No edits outside the requested scope. No staging of unrelated files.