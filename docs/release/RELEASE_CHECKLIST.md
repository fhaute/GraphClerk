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

## Manual

- [ ] **UI smoke test** — with API and `frontend` dev server (or preview) running, exercise: health banner, Query playground, Artifacts & evidence, Semantic indexes, Graph explorer, Retrieval logs, Evaluation dashboard. Confirm errors are readable and no tab implies OCR/ASR/video or **`POST /answer`**.
- [ ] **Status docs honesty** — `README.md`, `docs/status/*`, and phase docs do not claim GraphClerk is **production-enterprise ready**, Phase 8 **started**, **`/answer`**, OCR/ASR/caption/video, or full vector auto-indexing unless true in that environment.

## Governance

- [ ] **Phase 6 audit** — [`docs/audits/PHASE_6_AUDIT.md`](../audits/PHASE_6_AUDIT.md) — outcome **`pass_with_notes`** as of 2026-05-01. Re-audit after major UI/API contract changes.
