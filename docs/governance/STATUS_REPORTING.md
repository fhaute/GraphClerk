# Status Reporting (Honesty Rules)

The project must always make clear what is done, partial, blocked, deferred, or unimplemented.

## Required status files
- `docs/status/PROJECT_STATUS.md`
- `docs/status/PHASE_STATUS.md`
- `docs/status/KNOWN_GAPS.md`
- `docs/status/TECHNICAL_DEBT.md`
- `docs/status/ROADMAP.md`

## Status categories
- `not_started`
- `in_progress`
- `implemented`
- `tested`
- `documented`
- `blocked`
- `deferred`
- `failed`
- `removed`

## Status rules
1. A feature is not "done" until it is implemented, tested, and documented.
2. Partially working features must be marked partial.
3. Known gaps must be written down, not hidden.
4. Deferred work must have a reason.
5. Technical debt must be tracked when intentionally accepted.
6. Status docs must be updated at the end of every phase.

## Example status entry
```text
Feature: Markdown ingestion
Status: tested
Evidence:
- backend/tests/test_markdown_ingestion.py
- docs/phases/PHASE_2_TEXT_INGESTION.md
Notes:
- Tables inside Markdown are currently stored as table_text evidence units.
- No semantic table interpretation yet.
```

