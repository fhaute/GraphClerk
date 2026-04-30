# Phase 3 — Semantic Index and Graph Layer (implemented)

This document records the **implemented** subset of Phase 3 in the codebase and the **explicit limitations** that remain.

Canonical phase definition lives in:
- `docs/phases/graph_clerk_phase_3_semantic_index_and_graph_layer.md`

## Status
- **Status**: implemented (**pass_with_notes**; see `docs/audits/PHASE_3_AUDIT.md`)

## Implemented capabilities (honest)

### Graph layer
- **Graph nodes and edges** persisted in Postgres.
- **Graph APIs**:
  - `POST /graph/nodes`, `GET /graph/nodes/{id}`, `GET /graph/nodes`
  - `POST /graph/edges`, `GET /graph/edges/{id}`, `GET /graph/edges`
- **Evidence support links**:
  - `POST /graph/nodes/{node_id}/evidence`
  - `POST /graph/edges/{edge_id}/evidence`
  - Link tables enforce uniqueness and use `RESTRICT` on delete.

### Semantic index layer
- **SemanticIndex API**:
  - `POST /semantic-indexes`
  - `GET /semantic-indexes/{semantic_index_id}`
  - `GET /semantic-indexes/{semantic_index_id}/entry-points`
- **Normalized entry points**:
  - `semantic_index_entry_node` join table is the **source of truth** for entry nodes.
  - The legacy `semantic_index.entry_node_ids` JSONB field is not treated as canonical.
- **`vector_status`** exists on `SemanticIndex` and is enforced by a constraint:
  - `pending | indexed | failed`

### Embedding layer (adapter interface only)
- `EmbeddingAdapter` interface exists.
- `DeterministicFakeEmbeddingAdapter` exists for tests/dev.
- `NotConfiguredEmbeddingAdapter` exists and fails explicitly.
- `EmbeddingService` performs strict validation (non-empty text; numeric/finite vectors; dimension checks).

### Vector index layer (Qdrant wiring)
- Qdrant `VectorIndexService` exists:
  - collection name: `semantic_indexes`
  - distance: cosine
  - explicit expected dimension validation
  - explicit error behavior (no silent fallback)

### Search + traversal
- **Semantic index search endpoint** exists:
  - `GET /semantic-indexes/search?q=...&limit=...`
  - embeds query via `EmbeddingService`
  - searches Qdrant via `VectorIndexService`
  - hydrates structured metadata from Postgres (Qdrant payload is convenience only)
  - returns only `vector_status=indexed` results
  - explicit consistency error when Qdrant returns IDs not in Postgres
- **Bounded graph traversal endpoint** exists:
  - `GET /graph/nodes/{node_id}/neighborhood`
  - bounded BFS neighborhood traversal (incident edges both directions)
  - defaults: `depth=1`, `max_nodes=25`, `max_edges=50`
  - absolute max depth: `3` (depth > 3 → 422)
  - relation filter via repeatable `relation_types=...`
  - **truncation reporting**: `truncated` + `truncation_reasons`
  - evidence support references included (IDs only; no EvidenceUnit bodies)

## Explicit limitations / non-features (Phase 3)
- **No FileClerk**
- **No RetrievalPackets**
- **No answer synthesis**
- **No LLM calls**
- **No automatic graph extraction**
- **No multimodal ingestion**
- **No UI**
- **Production embedding adapter not wired**
- **SemanticIndex creation does not auto-index into Qdrant**
- **No indexing job/backfill**
- **Integration tests are opt-in/gated** via env vars (DB/Qdrant)

