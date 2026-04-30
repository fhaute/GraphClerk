# Phase 3 Audit — Semantic Index and Graph Layer

## Result
- **Result**: pass_with_notes

## Scope of this audit
This audit covers Phase 3 “meaning layer” capabilities that are implemented in the repository, and verifies that the status documents describe them honestly.

It does **not** audit later-phase features (FileClerk/RetrievalPackets/LLM/UI/multimodal).

## Implemented capabilities (verified)
- **Graph nodes and edges** exist in persistence and APIs.
- **Graph evidence support links** exist for nodes and edges.
- **SemanticIndex API** exists (create/get/entry-points).
- **Normalized entry nodes**: `semantic_index_entry_node` is the source of truth.
- **`vector_status`** exists (`pending | indexed | failed`) and is enforced by constraint.
- **Embedding adapter interface exists**:
  - `EmbeddingAdapter`
  - `DeterministicFakeEmbeddingAdapter`
  - `NotConfiguredEmbeddingAdapter`
  - `EmbeddingService` validation exists.
- **Qdrant VectorIndexService exists** with explicit errors and dimension validation.
- **Semantic index search endpoint exists** (`GET /semantic-indexes/search`) and:
  - embeds query via `EmbeddingService`
  - searches Qdrant via `VectorIndexService`
  - hydrates structured metadata from Postgres
  - returns only `vector_status=indexed`
  - fails explicitly on Qdrant/Postgres inconsistency
- **Bounded graph traversal endpoint exists** (`GET /graph/nodes/{node_id}/neighborhood`) and:
  - bounded BFS
  - deterministic ordering
  - bounds enforced (depth/max nodes/max edges)
  - truncation reporting is present
  - evidence support references included (no EvidenceUnit bodies)

## Notes (why pass_with_notes)
- **Production embedding adapter not wired**: default embedding wiring remains an explicit “not configured” placeholder.
- **No automatic vector indexing on SemanticIndex creation**: creating a SemanticIndex does not upsert vectors to Qdrant.
- **Integration tests are gated**: DB/Qdrant integration tests require opt-in env vars.
- **Traversal is bounded and may need optimization later**: bounded behavior is correct, but performance work may be needed at larger scales.

## Explicit non-features (verified)
- No FileClerk / RetrievalPackets
- No answer synthesis / LLM calls
- No automatic graph extraction
- No multimodal ingestion
- No UI
- No indexing job/backfill

## Documentation consistency checks
- README does not claim full RAG, FileClerk, RetrievalPackets, answer generation, multimodal ingestion, or UI.
- Status documents agree that Phase 3 is implemented with limitations noted above.

