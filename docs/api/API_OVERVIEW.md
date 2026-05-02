# GraphClerk API overview

High-level summary of **current** public HTTP APIs. For request/response shapes, see route modules under `backend/app/api/routes/` and phase documents. This file is **not** an OpenAPI dump.

## Infrastructure

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness (`{"status":"ok"}` style). |
| `GET` | `/version` | Build metadata (`name`, `version`, `phase`). |

## Artifacts and evidence (Phase 2 + multimodal shell)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/artifacts` | Create artifact: JSON (text/Markdown) or multipart file (PDF/PPTX when extras installed; image/audio validation shells may return **503**; video **400**). |
| `GET` | `/artifacts` | List artifacts (pagination as implemented). |
| `GET` | `/artifacts/{artifact_id}` | Artifact detail. |
| `GET` | `/artifacts/{artifact_id}/evidence` | Evidence units for artifact. |
| `GET` | `/evidence-units/{evidence_unit_id}` | Evidence unit detail. |

## Graph (Phase 3)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/graph/nodes` | Create graph node. |
| `GET` | `/graph/nodes` | List nodes. |
| `GET` | `/graph/nodes/{node_id}` | Node detail. |
| `POST` | `/graph/edges` | Create edge. |
| `GET` | `/graph/edges` | List edges. |
| `GET` | `/graph/edges/{edge_id}` | Edge detail. |
| `POST` | `/graph/nodes/{node_id}/evidence` | Link evidence to node. |
| `POST` | `/graph/edges/{edge_id}/evidence` | Link evidence to edge. |
| `GET` | `/graph/nodes/{node_id}/neighborhood` | Bounded neighborhood traversal. |

## Semantic indexes (Phase 3)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/semantic-indexes` | Create semantic index (vectors may stay **`pending`** until indexing exists). |
| `GET` | `/semantic-indexes` | List indexes (bounded `limit`, typically max **200**). |
| `GET` | `/semantic-indexes/{semantic_index_id}` | Index detail. |
| `GET` | `/semantic-indexes/{semantic_index_id}/entry-points` | Entry-point nodes. |
| `GET` | `/semantic-indexes/search` | Meaning-first search (**indexed** vectors only; see phase doc). |

## Retrieval (Phase 4)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/retrieve` | File Clerk: return a structured **`RetrievalPacket`** (no answer prose). |

## Retrieval logs (Phase 6 inspection)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/retrieval-logs` | List retrieval logs (pagination envelope). |
| `GET` | `/retrieval-logs/{log_id}` | Log detail including stored packet snapshot when present. |

## Model pipeline configuration (Phase 8 — read-only)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/model-pipeline/config` | **Read-only** snapshot of env-derived model pipeline settings and per-purpose registry status. **Does not** call Ollama or any model provider; **does not** return **`GRAPHCLERK_MODEL_PIPELINE_API_KEY`** or raw **`GRAPHCLERK_MODEL_PIPELINE_BASE_URL`**. |

There is **no** `POST` / `PUT` / `PATCH` configuration endpoint for model pipeline settings in this repository state.

## Explicitly deferred

- **`POST /answer`** — optional packet-only answer synthesis; **not implemented** in this repository state (separate approval and design). Do not assume it exists in clients or UI.
