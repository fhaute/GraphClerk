# Audit Rules

Audits prevent the project from quietly drifting away from its own contracts.

## Ownership (Audit Agent)
Executing audits to this standard, writing/updating artifacts under `docs/audits/`, and keeping outcomes consistent with `docs/status/*` when claims change is the responsibility of the **Audit Agent** charter (`docs/governance/AGENT_ROLES.md` → **Dedicated sub-agents** → **Audit Agent**).

## Required audit types
- architecture audit
- contract audit
- test audit
- dependency audit
- security audit
- retrieval quality audit
- multimodal extraction audit
- status honesty audit

## Audit schedule
- After every phase
- Before every public release
- Before major schema changes
- After major dependency changes

## Audit questions
### Architecture audit
- Did this phase violate any architectural invariant?
- Did any layer take responsibility from another layer?
- Did any future phase get implemented silently?

### Contract audit
- Did schemas change?
- Were contracts updated?
- Were tests updated to reflect contract changes?

### Test audit
- Are critical paths tested?
- Were any tests removed or weakened?
- Are failure cases tested?

### Dependency audit
- Were dependencies added?
- Are they necessary?
- Are they documented?
- Are licenses acceptable?

### Status honesty audit
- Does the README overclaim?
- Do status docs match actual behavior?
- Are partial features clearly marked?

## Audit output
Each audit should produce a short file:
`docs/audits/YYYY-MM-DD_PHASE_X_AUDIT.md`

Audit result values:
- `pass`
- `pass_with_notes`
- `needs_fix`
- `blocked`

## Release rule
No public release should happen without an audit marked either:
- `pass`
- `pass_with_notes`

