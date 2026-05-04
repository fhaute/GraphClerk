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
  - **drops** Qdrant hits whose `semantic_index_id` is **missing in Postgres** (stale/orphan vectors after row delete or DB restore without Qdrant cleanup); Postgres remains source of truth — **no** HTTP 500 for that case
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
- **No automatic** indexing job on create; **operator** vector backfill exists post-audit ([`scripts/backfill_semantic_indexes.py`](../scripts/backfill_semantic_indexes.py) — Track B Slice B1; see `PROJECT_STATUS.md`).

## Verification amendment (2026-05-04)

Semantic index **search** behavior was tightened: orphan Qdrant payloads are **filtered** rather than failing the request (`SemanticIndexSearchService`). This audit’s historical “fail on inconsistency” line is **superseded** by that shipped behavior; see `docs/onboarding/TROUBLESHOOTING_AND_OPERATIONS.md` (HTTP semantics table).

## Documentation consistency checks
- README does not claim full RAG, FileClerk, RetrievalPackets, answer generation, multimodal ingestion, or UI.
- Status documents agree that Phase 3 is implemented with limitations noted above.

