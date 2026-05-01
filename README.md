# GraphClerk

## What GraphClerk is

GraphClerk is a **local-first, graph-guided evidence-routing layer for RAG systems**. It sits between user intent and an LLM by returning **structured retrieval packets** with traceability to **source artifacts** and **evidence units**, using a **semantic index** and **graph** layer so you can **search meaning first, then retrieve evidence**.

## What GraphClerk is not

- **Not** a chatbot or autonomous agent framework by itself.
- **Not** a replacement for your vector database, embedding service, or RAG orchestration framework.
- **Not** a full document management system or enterprise records platform.
- **Not** answer synthesis: **`POST /answer`** and LLM-driven prose from packets are **out of scope** until separately approved and implemented.
- **Not** multimodal “AI complete”: **no OCR, ASR, image captioning, or video ingestion pipeline** in the current backend; image/audio paths are largely **validation shells** (see Phase 5 docs).

## Project principle

**Search meaning first, then retrieve evidence.**

## What is implemented (honest status)

- **Phase 0**: Governance baseline (`docs/governance/*`).
- **Phase 1**: Backend foundation (FastAPI, SQLAlchemy/Alembic, Docker Compose, `/health`, `/version`).
- **Phase 2**: Text/Markdown ingestion → `Artifact` + `EvidenceUnit` with location metadata.
- **Phase 3**: Semantic index + graph layer (graph APIs, evidence links, semantic index APIs, vector index service, semantic search for **indexed** indexes, bounded traversal). **No** automatic vector backfill on index create.
- **Phase 4**: File Clerk **`POST /retrieve`**, structured `RetrievalPacket`, deterministic intent/route/evidence selection, context budgeting, `RetrievalLog.retrieval_packet` snapshots.
- **Phase 5** (**in progress**, **partial**; audit **`pass_with_notes`** — `docs/audits/PHASE_5_AUDIT.md`): multimodal routing, PDF/PPTX text to evidence when optional extras installed; image/audio **validation only** (no EU from image/audio; **503** where documented); **no** OCR/ASR/caption/video pipeline.
- **Phase 6** (**implemented `pass_with_notes`** — `docs/audits/PHASE_6_AUDIT.md`, `docs/phases/graph_clerk_phase_6_productization_ui_evaluation_hardening.md`): React/Vite UI in `frontend/` against **live** APIs; **demo/inspection productization**, **not** production enterprise software. See [Web UI](#web-ui-phase-6). **Onboarding**: this README, `docs/api/API_OVERVIEW.md`, `docs/release/RELEASE_CHECKLIST.md`, `docs/evaluation/EVALUATION_METHOD.md`, `docs/demo/PHASE_6_DEMO_CORPUS.md`.
- **Phase 7** (**baseline implemented**; audit **`pass_with_notes`** — `docs/audits/PHASE_7_AUDIT.md`, 2026-05-02): **context intelligence** layer — language **`metadata_json`** plumbing, optional **`RetrievalPacket.language_context`** from selected evidence metadata, optional **`actor_context`** on **`POST /retrieve`** recorded on **`RetrievalPacket`** (**recording only**; **no** retrieval boosting). **Not** a full personalization or translation product; **routing/interpretation metadata is not evidence** (see `docs/phases/graph_clerk_phase_7_context_intelligence.md`). **Deterministic context boosting** (Slice **7I**) remains **deferred / cancelled** pending separate approval (`docs/status/KNOWN_GAPS.md`).
- **Phase 8** (**baseline implemented**; **Slice 8I audit pending**): specialized **model pipeline contracts** — typed envelopes, **`NotConfigured`** default adapter, **deterministic test-only** adapter, **`ModelPipelineOutputValidationService`**, standalone **`graphclerk_model_pipeline`** **metadata projection** only (not wired into ingestion/retrieval/FileClerk), evaluation fixtures, and **8G local inference design-only** (no Ollama/vLLM wiring; **no** real inference). **Not** full specialized-model production (no registry, no production inference, **`POST /answer`** still deferred). See `docs/status/PHASE_STATUS.md` and [`docs/phases/graph_clerk_phase_8_specialized_model_pipeline.md`](docs/phases/graph_clerk_phase_8_specialized_model_pipeline.md).
- **Phase 9**: **`not_started`** — specification under `docs/phases/` only; **no** implementation claimed.

## What is explicitly not implemented yet

- **`POST /answer`** / `LocalRAGConsumer` / answer synthesis in the API.
- **LLM calls** inside core ingestion/retrieval paths.
- **Full** Phase 5 multimodal (OCR, transcription, captions, video; image/audio as full evidence producers).
- **Automatic semantic index vector population** after create (indexing job/backfill).
- **Phase 6 stretch items** from the phase doc (e.g. in-product demo loader vs script-only, automated UI tests, further hardening) — baseline + audit are **`pass_with_notes`**; see `docs/audits/PHASE_6_AUDIT.md`.
- **Production-grade** language detection-by-default, translation, query translation, and ActorContext-driven retrieval boosting (**Slice 7I**) — **not** claimed; Phase 7 audit is **`pass_with_notes`** with explicit gaps (`docs/audits/PHASE_7_AUDIT.md`, `docs/status/PROJECT_STATUS.md`).

## Governance and phase docs

- `docs/graph_clerk_phase_0_governance_baseline.md` — Phase 0 source narrative.
- `docs/governance/` — guardrails for assistants and humans.
- `docs/phases/PHASE_1_FOUNDATION.md`, `PHASE_2_*`, `graph_clerk_phase_3_*`, `graph_clerk_phase_4_*`, `graph_clerk_phase_5_*`, `graph_clerk_phase_6_*`, `graph_clerk_phase_7_context_intelligence.md`.
- `docs/status/` — required honesty tables.
- `docs/api/API_OVERVIEW.md` — HTTP surface summary.
- `docs/adr/` — ADRs.

---

## Quickstart (Docker)

From the **repository root**:

```bash
docker compose up -d --build
docker compose ps
```

With the default Compose mapping, the API on the host is **`http://localhost:8010`**. The **`api`** container listens on **8000** internally; **`8010:8000`** publishes it.

If **`vite`** logs **`ECONNREFUSED`** to **`127.0.0.1:8010`**, the API is not listening on that host port yet — confirm containers are **Up** and recreate after port mapping changes.

---

## Backend (local dev)

From **`backend/`**:

```bash
python -m pip install -e ".[dev]"
```

Optional multimodal extras (see `pyproject.toml`): **`pdf`**, **`pptx`**, **`image`**, **`audio`**.

```bash
python -m pip install -e ".[dev,pdf,pptx,image,audio]"
```

Run the API (port **8010** matches the default Docker host port and the default Vite proxy target):

```bash
python -m uvicorn app.main:app --reload --port 8010
```

### Running backend tests

From **`backend/`**:

```bash
python -m pytest
```

**Integration tests** (opt-in): set `RUN_INTEGRATION_TESTS=1`, `DATABASE_URL`, and where needed `QDRANT_URL`. See `docs/governance/TESTING_RULES.md`.

---

## Frontend (local dev)

From **`frontend/`**:

```bash
npm install
npm run dev
```

### Vite proxy and API base URL

- Default **`frontend/.env.development`** sets **`VITE_API_BASE_URL=/api`**. The browser calls same-origin **`/api/...`**; **Vite** proxies that to the real API.
- Proxy target defaults to **`http://127.0.0.1:8010`** (Docker host API port). Override with **`GRAPHCLERK_API_PROXY_TARGET`** in **`frontend/.env.local`** (e.g. **`http://127.0.0.1:8000`** if you run **`uvicorn`** on port **8000**). See `frontend/.env.example`.
- To bypass the proxy, set **`VITE_API_BASE_URL=http://localhost:8010`** (or your API URL). Then configure CORS on the API (**`GRAPHCLERK_CORS_ORIGINS`**, with legacy alias `GRAPHCLE_CORS_ORIGINS` if needed — see `backend/app/main.py`).

### Frontend production build

From **`frontend/`**:

```bash
npm run build
```

Use this in CI and before releases (see `docs/release/RELEASE_CHECKLIST.md`).

---

## Demo corpus (optional)

Script-only loader (no in-app “Load demo” button). From **repository root**:

```bash
set GRAPHCLERK_API_BASE_URL=http://localhost:8010
python scripts/load_phase6_demo.py --dry-run
python scripts/load_phase6_demo.py
```

On Unix shells, use `export` instead of `set`. Default in the script if env is unset may still target port **8000** — **set `GRAPHCLERK_API_BASE_URL` explicitly** to match your API (see `docs/demo/PHASE_6_DEMO_CORPUS.md`).

### Honest limitations after loading

- Demo **`POST /semantic-indexes`** rows typically have **`vector_status=pending`** until a real indexing/backfill path runs. **`GET /semantic-indexes/search`** only returns **`vector_status=indexed`** rows.
- Therefore **`POST /retrieve`** may **not** surface demo semantic routes the way a fully indexed deployment would; behavior falls back to whatever the File Clerk does when indexes are not indexed.

---

## Web UI (Phase 6)

Location: **`frontend/`**. All tabs use **live** HTTP APIs (no bundled mock corpus).

| Area | What it does |
|------|----------------|
| **Query playground** | Calls **`POST /retrieve`**; shows **`RetrievalPacket`** (readable + raw JSON). |
| **Artifacts & evidence** | Lists artifacts and evidence units from the API. |
| **Semantic indexes** | Lists/detail/search (search only meaningful for **indexed** vectors). |
| **Graph explorer** | Nodes, edges, neighborhood, evidence links. |
| **Retrieval logs** | Reads **`GET /retrieval-logs`**. |
| **Evaluation dashboard** | Aggregates from retrieval logs / stored packets — **observability-style counts and breakdowns**, not answer-quality or accuracy metrics (no LLM judge; see `docs/evaluation/EVALUATION_METHOD.md`). |

---

## API reference (summary)

See **`docs/api/API_OVERVIEW.md`** for a concise endpoint list. **`POST /answer`** is **not** listed as available.

---

## Release and evaluation docs

- **`docs/release/RELEASE_CHECKLIST.md`** — tests, build, Compose, migrations, demo loader, manual UI, audit reminder.
- **`docs/evaluation/EVALUATION_METHOD.md`** — what the Evaluation tab measures and what it does not.

---

## Running tests (summary)

| Where | Command |
|-------|---------|
| Backend | `cd backend` then `python -m pytest` |
| Frontend | `cd frontend` then `npm run build` (production compile check; no Vitest harness in-repo yet) |

---

## Database migrations (PostgreSQL / deployment)

For a **real PostgreSQL** database (staging, production, or a long-lived local DB), apply migrations from the **`backend/`** directory (where `alembic.ini` lives):

```bash
cd backend
alembic upgrade head
```

**Phase 4** adds revision **`0004_phase4_retrieval_packet_log`**, which creates the nullable JSONB column **`retrieval_log.retrieval_packet`**. If that migration has not been applied, `POST /retrieve` logging against that column will not match a migrated database.

`alembic upgrade head` applies the full chain, including `0004`. Do not rely on test `create_all()` behavior alone to prove migration correctness.
