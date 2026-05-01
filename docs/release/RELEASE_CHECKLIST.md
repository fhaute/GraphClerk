# Release checklist (GraphClerk)

Use this list before tagging a release or handing off a demo build. It is **not** a substitute for a formal Phase 6 audit (that remains **pending** until `docs/audits/` records an explicit outcome).

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
- [ ] **Status docs honesty** — `README.md`, `docs/status/*`, and phase docs do not claim Phase 6 **complete**, Phase 8 **started**, **`/answer`**, OCR/ASR/caption/video, or full vector auto-indexing unless true in that environment.

## Governance

- [ ] **Phase 6 audit** — remains **outstanding** until an audit artifact exists under `docs/audits/` with an explicit result per `docs/governance/AUDIT_RULES.md`. Do not treat this checklist as the Phase 6 audit.
