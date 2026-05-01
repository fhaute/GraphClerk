# Release checklist (GraphClerk)

Use this list before tagging a release or handing off a demo build. **Phase 6 audit** is recorded in [`docs/audits/PHASE_6_AUDIT.md`](../audits/PHASE_6_AUDIT.md) (**`pass_with_notes`**, 2026-05-01). This checklist complements that audit; it does **not** replace reading the audit notes and accepted gaps.

## Verification record (Slice L — 2026-05-01)

Executed in the audit pass (evidence also summarized in `docs/audits/PHASE_6_AUDIT.md`):

| Step | Command | Result |
|------|---------|--------|
| Backend tests | `cd backend` → `python -m pytest -q` | **Pass** (default suite; integration tests skipped as designed). |
| Frontend build | `cd frontend` → `npm run build` | **Pass** (`tsc --noEmit` + `vite build`). |
| Compose config | `docker compose config` (repo root) | **Pass** (config renders). |
| Demo loader dry-run | repo root, `GRAPHCLERK_API_BASE_URL=http://localhost:8010` → `python scripts/load_phase6_demo.py --dry-run` | **Pass** (planned HTTP sequence only). |

**Not run in this record** (operator / environment dependent): `docker compose up -d --build`, live `curl` against a running stack, `alembic upgrade head` on disposable Postgres, full manual UI smoke — still recommended before production-like demos.

## Verification record (Track B Slice B5.1 — 2026-05-01)

**Scope:** Gated full-stack indexed retrieval test only (`deterministic_fake` is **not** a production embedding path; this confirms dev/integration wiring against real Postgres + Qdrant, not production indexing quality).

**Environment (no secrets):** Repo `docker compose` stack on the host: Postgres **5433→5432**, Qdrant **6333**, `APP_ENV=test`, `RUN_INTEGRATION_TESTS=1`, `DATABASE_URL=postgresql+psycopg://…@127.0.0.1:5433/graphclerk` (compose default user/db), `GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER=deterministic_fake` for the B5 module only. `QDRANT_URL` for pytest integration fixtures is **`http://localhost:6333`** (see `backend/tests/conftest.py`).

**Postgres / Qdrant:** `docker compose ps` — `graphclerk-postgres-1` and `graphclerk-qdrant-1` **Up** (api container also up).

| Step | Command | Result |
|------|---------|--------|
| B5 full-stack (first attempt) | `cd backend` → env as above → `python -m pytest tests/test_phase1_8_track_b_full_stack_retrieve.py -q` | **Fail** — indexing returned `failed` / `VectorIndexOperationError`: existing Qdrant collection **`semantic_indexes`** had vector **size=3**; Track B deterministic stack expects **dimension 8**. **Class:** environment / stale Qdrant state (not application logic under correct collection config). |
| Qdrant remediation (operator dev only) | Deleted collection `semantic_indexes` via `qdrant_client` so the next indexer run recreates it with the correct size. | — |
| B5 full-stack (after remediation) | Same pytest command with same env | **Pass** (1 test). **B5 verified** in gated integration env. |
| Related backend tests | Same `cd backend`; `RUN_INTEGRATION_TESTS=1`, `DATABASE_URL`, `APP_ENV=test`; **`GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER` unset** for this invocation to avoid leaking into `test_config.py::test_config_loads_from_environment` → `python -m pytest tests/test_phase1_8_track_b_indexed_retrieval.py tests/test_config.py tests/test_phase3_semantic_index_search_api.py tests/test_phase4_retrieve_api.py -q` | **Pass** (19 tests). |
| Full backend suite (default skips) | `python -m pytest -q` (integration env vars **not** set) | **Pass** |

**Note:** If `GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER=deterministic_fake` is exported in the shell while running the mixed suite above, `test_config_loads_from_environment` may fail (**test isolation / env pollution**), not product behavior.

## Operator note — Qdrant `semantic_indexes` dimension (Track B Slice B5.2)

When **manual vector indexing** or **gated B5 integration** fails at **upsert** with a **dimension / vector size** mismatch, the usual cause is an **existing** Qdrant collection **`semantic_indexes`** created at a **different** vector size than the current dev adapter (**8** for `DeterministicFakeEmbeddingAdapter` / `deterministic_fake`). **Dev-only:** delete/recreate **only** that collection on a disposable instance, then rerun backfill or indexing — **not** for production without a runbook. Full symptom → cause → safe fix → “what this is not” lives in [`docs/governance/TESTING_RULES.md`](../governance/TESTING_RULES.md) (*Qdrant `semantic_indexes` vector dimension mismatch*). Demo-specific wording: [`docs/demo/PHASE_6_DEMO_CORPUS.md`](../demo/PHASE_6_DEMO_CORPUS.md) → *Manual vector indexing* → *Qdrant collection `semantic_indexes`*.

---

## Automated / scripted

- [ ] **Backend unit/API tests** — from `backend/`:
  ```bash
  python -m pytest
  ```
- [ ] **Frontend production build** — from `frontend/`:
  ```bash
  npm ci
  npm run build
  ```
- [ ] **Docker Compose boot** — from repo root:
  ```bash
  docker compose up -d --build
  docker compose ps
  ```
- [ ] **Health and version** — default API host port **8010**:
  ```bash
  curl -s http://localhost:8010/health
  curl -s http://localhost:8010/version
  ```
- [ ] **Database migrations** — for a real Postgres (not `create_all()` in tests only); from `backend/`:
  ```bash
  alembic upgrade head
  ```
- [ ] **Demo loader dry-run** — from repo root (see `docs/demo/PHASE_6_DEMO_CORPUS.md`):
  ```bash
  python scripts/load_phase6_demo.py --dry-run
  ```
- [ ] **Demo loader real run** (optional; creates real rows):
  ```bash
  python scripts/load_phase6_demo.py
  ```
- [ ] **Optional rich demo — manual semantic index backfill** (Track B Slice B1): after a loader run, `python scripts/backfill_semantic_indexes.py --help` then index the new semantic index id with `DATABASE_URL` + `QDRANT_URL` aligned to the API stack (see `docs/demo/PHASE_6_DEMO_CORPUS.md` → *Manual vector indexing*). Confirms `vector_status` transitions to **`indexed`** or explicit **`failed`**, not silent **`pending`**.

## Manual

- [ ] **C5 demo policy (pre–Phase 9)** — **Option C** is recorded: minimal E2E does **not** block Phase **9** planning; **stakeholder-facing** demos that promise evidence snippets must use **rich** (indexed) conditions **or** explicitly disclose **minimal** / **pending** behavior. See **`docs/demo/PHASE_6_DEMO_CORPUS.md`** → *Policy decision (Phase 0–8 completion — C5)* and **`docs/reports/phase_0_8_completion_hardening_plan.md`** → *C5 policy decision*.
- [ ] **Minimal demo E2E checklist** — follow **`docs/demo/PHASE_6_DEMO_CORPUS.md`** → *Manual end-to-end smoke path*. Record whether **`POST /retrieve`** showed **empty** `evidence_units` because semantic indexes were still **`vector_status=pending`**, or whether vectors were **indexed** / **rich** demo conditions applied.
- [ ] **UI smoke test** — with API and `frontend` dev server (or preview) running, exercise: health banner, Query playground, Artifacts & evidence, Semantic indexes, Graph explorer, Retrieval logs, Evaluation dashboard. Confirm errors are readable and no tab implies OCR/ASR/video or **`POST /answer`**.
- [ ] **Status docs honesty** — `README.md`, `docs/status/*`, and phase docs do not claim GraphClerk is **production-enterprise ready**, Phase 8 **started**, **`/answer`**, OCR/ASR/caption/video, or full vector auto-indexing unless true in that environment.

## Governance

- [ ] **Phase 6 audit** — [`docs/audits/PHASE_6_AUDIT.md`](../audits/PHASE_6_AUDIT.md) — outcome **`pass_with_notes`** as of 2026-05-01. Re-audit after major UI/API contract changes.
