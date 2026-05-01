# GraphClerk

GraphClerk is a **local-first, graph-guided evidence-routing layer for RAG systems**.

It is not a chatbot by itself. It does not try to replace RAG frameworks, vector databases, or LLMs.
It improves the layer between user intent and LLM context by returning **structured evidence packets**
with traceability to original source artifacts.

## Project principle
**Search meaning first, then retrieve evidence.**

## What’s implemented (honest status)
- **Phase 0**: governance baseline (`docs/governance/*`)
- **Phase 1**: backend foundation (FastAPI, SQLAlchemy/Alembic, Docker Compose, `/health`, `/version`)
- **Phase 2**: text/Markdown ingestion → `Artifact` + `EvidenceUnit` with location metadata
- **Phase 3**: semantic index + graph meaning layer (graph APIs, evidence links, semantic index APIs, vector index service, semantic index search, bounded traversal)
- **Phase 4**: File Clerk retrieval packets (`POST /retrieve`), structured `RetrievalPacket` contracts, deterministic intent + route selection + graph-linked evidence selection + context budgeting, and `RetrievalLog.retrieval_packet` JSON snapshots
- **Phase 5** (**partially implemented; in progress; audit pending** — see `docs/phases/graph_clerk_phase_5_multimodal_ingestion.md`): `EvidenceUnitCandidate` hardening, `ArtifactExtractor` + `ExtractorRegistry`, multimodal routing shell, `ArtifactTypeResolver`, PDF text via optional **`pdf`** (pypdf), PPTX slide text via optional **`pptx`** (python-pptx), image/audio **validation shells** via optional **`image`** (Pillow) / **`audio`** (mutagen) (**no** EvidenceUnits from image/audio yet), integration tests for PDF/PPTX evidence in `POST /retrieve` packets, and HTTP tests for multimodal `POST /artifacts` errors. **Not** complete: no OCR/ASR/caption, no video ingestion, no automatic multimodal graph extraction, no FileClerk or `RetrievalPacket` schema redesign.

## What is explicitly not implemented yet
- optional **`POST /answer`** / `LocalRAGConsumer` / `AnswerSynthesizer` (deferred until separately approved)
- answer synthesis / LLM calls
- automatic graph extraction / claim extraction
- **full** Phase 5 multimodal ingestion (OCR, transcription, captions, video; image/audio do not emit `EvidenceUnit`s today)
- production embedding adapter not wired (Phase 3 uses explicit placeholder adapters)
- SemanticIndex creation does not auto-index into Qdrant; no indexing job/backfill yet
- UI

## Governance first
This repository starts with Phase 0 governance guardrails. Technical implementation must not begin
until the governance baseline is present and committed.

- `docs/graph_clerk_phase_0_governance_baseline.md`: Phase 0 initialization document (source)
- `docs/governance/`: split governance documents used by prompts, reviews, and audits
- `docs/phases/PHASE_1_FOUNDATION.md`: Phase 1 implementation status and non-features
- `docs/phases/PHASE_2_TEXT_FIRST_INGESTION.md`: Phase 2 ingestion behavior (text/Markdown only)
- `docs/phases/graph_clerk_phase_3_semantic_index_and_graph_layer.md`: Phase 3 definition (meaning layer)
- `docs/phases/graph_clerk_phase_5_multimodal_ingestion.md`: Phase 5 definition and **current implementation status**
- `docs/status/`: status tracking (honesty rules)
- `docs/adr/`: architecture decision records (ADRs)

## Quickstart (Docker)
Start API + Postgres + Qdrant:

```bash
docker compose up -d --build
```

With the default Compose mapping, the API is on the host at **`http://localhost:8010`**. The **`api`** container still listens on **8000** inside the network; **`8010:8000`** publishes it on the host.

If **`vite`** logs **`connect ECONNREFUSED 127.0.0.1:8010`**, nothing is listening on that host port yet: run **`docker compose up -d --build`** from the repo root (and **`docker compose ps`** to confirm **`api`** is **Up**). After changing Compose port mappings, recreate containers so the new bind is applied.

**Frontend + API in dev:** the default **`frontend/.env.development`** uses **`VITE_API_BASE_URL=/api`**. Vite proxies **`/api`** to the backend; the proxy target defaults to **`http://127.0.0.1:8010`**. Override with **`GRAPHCLERK_API_PROXY_TARGET`** in **`frontend/.env.local`** if the API is elsewhere (for example **`http://127.0.0.1:8000`** when running **`uvicorn`** on port **8000**). You can also set **`VITE_API_BASE_URL=http://localhost:8010`** to call the API directly (ensure CORS allows the UI origin).

If you run **`uvicorn`** directly on **8010** to match Docker’s host URL, **`--port 8010`** is enough with the default proxy target.

## Quickstart (local dev)
From `backend/`:

```bash
python -m pip install -e ".[dev]"
```

Optional multimodal libraries (from `backend/pyproject.toml`): **`pdf`** → pypdf, **`pptx`** → python-pptx, **`image`** → Pillow, **`audio`** → mutagen. Example:

```bash
python -m pip install -e ".[dev,pdf,pptx,image,audio]"
```

```bash
python -m pytest
python -m uvicorn app.main:app --reload --port 8010
```

## Running tests
- **Default** (fast, no external services): `python -m pytest`
- **Integration tests** (opt-in): set:
  - `RUN_INTEGRATION_TESTS=1`
  - `DATABASE_URL=...`
  - `QDRANT_URL=...` (only for Qdrant tests)

**Tests and schema:** some integration tests build schema with SQLAlchemy `Base.metadata.create_all()`. That is **not** a substitute for running Alembic on real databases. Deployments and local Postgres that should match production must apply migrations (see below).

## Database migrations (PostgreSQL / deployment)

For a **real PostgreSQL** database (staging, production, or a long-lived local DB), apply migrations from the `backend/` directory (where `alembic.ini` lives):

```bash
cd backend
alembic upgrade head
```

**Phase 4** adds revision **`0004_phase4_retrieval_packet_log`**, which creates the nullable JSONB column **`retrieval_log.retrieval_packet`** (canonical `RetrievalPacket` snapshot for retrieval logs). If that migration has not been applied, `POST /retrieve` logging against that column will not match a migrated database.

`alembic upgrade head` applies the full chain, including `0004`. Do not rely on test `create_all()` behavior alone to prove migration correctness.

## API surface (current)
Infrastructure:
- `GET /health`
- `GET /version`

Artifacts / Evidence (Phase 2 + partial Phase 5):
- `POST /artifacts`: JSON or multipart **text/Markdown** (unchanged). Multipart **PDF** / **PPTX** create `EvidenceUnit`s when optional **`pdf`** / **`pptx`** extras are installed. **Image** / **audio** uploads are validated when **`image`** / **`audio`** extras are present but return **503** (OCR/ASR/caption backends not configured — no text evidence units). **Video** is unsupported (**400**). See phase doc for details; full HTTP error matrix stays in tests, not here.
- `GET /artifacts`
- `GET /artifacts/{artifact_id}`
- `GET /artifacts/{artifact_id}/evidence`
- `GET /evidence-units/{evidence_unit_id}`

Graph (Phase 3):
- `POST /graph/nodes`
- `GET /graph/nodes/{node_id}`
- `GET /graph/nodes`
- `POST /graph/edges`
- `GET /graph/edges/{edge_id}`
- `GET /graph/edges`
- `POST /graph/nodes/{node_id}/evidence`
- `POST /graph/edges/{edge_id}/evidence`

Semantic indexes (Phase 3):
- `POST /semantic-indexes`
- `GET /semantic-indexes/{semantic_index_id}`
- `GET /semantic-indexes/{semantic_index_id}/entry-points`
- `GET /semantic-indexes/search`

Graph traversal (Phase 3):
- `GET /graph/nodes/{node_id}/neighborhood`

Retrieval (Phase 4):
- `POST /retrieve`

