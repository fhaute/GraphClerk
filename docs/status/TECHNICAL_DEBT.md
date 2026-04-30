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

