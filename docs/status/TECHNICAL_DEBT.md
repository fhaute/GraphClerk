# Technical Debt

## Phase 1
- **Dependency install workflow is not documented yet**: we have `backend/pyproject.toml` (uv/pip-friendly) but no short “how to set up venv + install dev deps + run Ruff” section yet.
- **Integration tests are gated behind env vars**: intentional, but we should standardize a single documented command to run them in CI or locally.
- **Health endpoint does not yet report DB/Qdrant status**: intentional until dependency checks are wired; when added, it must reflect real connectivity and surface failures explicitly.

## Phase 2
- **Best-effort cleanup edge case**: if a disk write succeeds but the DB transaction fails, we attempt to delete the written file; failures are best-effort only (may leave an orphaned file on disk).

## Phase 3
- **Embedding configuration is not centralized**: embedding/vector expected dimension is explicit but not yet surfaced as a single settings value.
- **Production embedding adapter not wired**: default wiring uses an explicit “not configured” adapter (intentional placeholder).
- **SemanticIndex creation does not auto-index into Qdrant**: vector upsert/backfill workflow is not implemented yet.
- **Integration tests are gated**: Postgres/Qdrant tests are opt-in via env vars; provide a single documented “run integration tests” command set.
- **Traversal performance may need optimization later**: traversal is bounded/deterministic, but may need more batching/SQL tuning as graph sizes grow.

## Phase 4
- **RetrievalLog write failures are swallowed** (API still returns a packet; observability may be lost without separate error reporting).
- **Route selection duplicates semantic search calls** if other callers also search separately (acceptable for now; revisit if latency becomes an issue).
- **Alembic migration chain vs tests**: integration tests may use `Base.metadata.create_all()`, which can create the current ORM shape (including `retrieval_log.retrieval_packet`) without exercising the Alembic revision graph. That does **not** prove that `alembic upgrade head` from an older base revision succeeds on a real database.
- **Future CI task**: run `alembic upgrade head` against a throwaway Postgres instance (from `backend/`) so migration ordering and upgrade scripts are validated automatically, not only implied by ORM metadata in tests.

## Phase 5 (in progress)
- **OCR / caption backend selection and wiring**: deferred (not implemented); image path intentionally ends in **503** after validation until a backend is chosen and approved.
- **ASR / transcription backend selection and wiring**: deferred (not implemented); audio path intentionally ends in **503** after validation.
- **Image/audio validation shells** returning **503**: explicit product choice for now; must stay honest in docs and APIs until extractors emit `EvidenceUnit`s.
- **Optional dependency install + test matrix** (`pdf`, `pptx`, `image`, `audio` extras vs CI): may need a documented/standardized CI job later so regressions in placeholder vs real extractor paths are caught consistently.

## Phase 6 (`pass_with_notes` baseline)
- **No automated frontend tests yet** (`frontend/` has no `*.test.*` / `*.spec.*` harness wired in-repo): consider Vitest/Playwright (or equivalent) once UI contracts stabilize.
- **Phase 6 audit** completed **`pass_with_notes`** — `docs/audits/PHASE_6_AUDIT.md` (2026-05-01); remaining items called out in audit + this section (not production-ready; script-only demo; optional E2E/hardening).
- **Onboarding**: README + `docs/api/API_OVERVIEW.md` + `docs/release/RELEASE_CHECKLIST.md` + `docs/evaluation/EVALUATION_METHOD.md` + demo corpus doc (Slice K); release checklist records verification commands/results (Slice L).

