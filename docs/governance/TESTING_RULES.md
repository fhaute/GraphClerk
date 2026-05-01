# Testing Rules

## Minimum rules
1. Every service gets unit tests.
2. Every public endpoint gets API tests.
3. Every schema contract gets validation tests.
4. Ingestion must test source preservation.
5. Retrieval must test packet structure.
6. Graph traversal must test limits and edge filtering.
7. Model outputs must be validated before persistence.
8. No test may be removed just to make implementation pass.
9. Regressions must receive regression tests.
10. Multimodal extractors must test traceability to artifacts.

## Future test categories
- contract tests
- unit tests
- API tests
- ingestion tests
- retrieval tests
- graph traversal tests
- vector search tests
- evaluation tests
- UI smoke tests

## Semantic search embedding mode (Track B Slice B2)

For **integration tests** that need the API’s semantic search path to embed query text with the **same deterministic algorithm** as the B1 backfill script (so Qdrant vectors from backfill match query vectors), you may set:

| Variable | Value | Notes |
|----------|--------|--------|
| `RUN_INTEGRATION_TESTS` | `1` | Required for `deterministic_fake` (see `conftest.py` integration fixtures). |
| `APP_ENV` | `local`, `dev`, or `test` | **`deterministic_fake` is rejected when `APP_ENV=prod`** (fail closed at settings validation). |
| `GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER` | `deterministic_fake` | Optional; default is **`not_configured`** (search uses `NotConfiguredEmbeddingAdapter` and returns explicit errors when search runs without another test override). |

**This is not a production embedding provider.** `deterministic_fake` produces **non-semantic** hash-derived vectors for test/dev alignment only. Production must use a **real** embedding adapter when that product work ships; do not treat deterministic mode as retrieval quality.

**No silent fallback:** unset or `not_configured` keeps the historical **`NotConfigured`** behavior. The app does **not** fall back to deterministic embeddings when the configured adapter fails.

**Clearing settings cache:** tests that toggle these variables must call `app.core.config.get_settings.cache_clear()` before `get_settings()` / `create_app()` so the process does not reuse a stale `lru_cache` entry.

## Track B Slice B5 — gated full-stack indexed retrieve (no factory / FileClerk monkeypatch)

[`backend/tests/test_phase1_8_track_b_full_stack_retrieve.py`](../../backend/tests/test_phase1_8_track_b_full_stack_retrieve.py) exercises **HTTP ingest → evidence → graph link → semantic index → in-process `SemanticIndexVectorIndexingService` → `POST /retrieve`** with **`create_app()`** and **no** monkeypatch of `FileClerkService` or `build_semantic_index_search_service`. It **skips** unless **all** of the following are satisfied (read from the real process environment; the test does not inject `GRAPHCLERK_*` for the gate):

| Variable | Requirement |
|----------|----------------|
| `RUN_INTEGRATION_TESTS` | `1` |
| `DATABASE_URL` | non-empty (Postgres; same as other integration tests) |
| `QDRANT_URL` | non-empty (same name as the rest of the backend) |
| `GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER` | `deterministic_fake` |
| `APP_ENV` | not `prod` (case-insensitive) |

Also requires a reachable Qdrant at `QDRANT_URL` (the test pings collections after settings load). Default CI / local runs **skip** this module when the gate is not met.

**Before running B5 (or any integration path that upserts with `DeterministicFakeEmbeddingAdapter`):** ensure the Qdrant collection **`semantic_indexes`** already exists with vector **size 8**, or **does not exist** yet (the app will create it at the correct size on first indexing). If the collection was created earlier with another dimension (for example size **3** from experiments), upserts will fail until you reset the collection in **local/dev Qdrant only** — see *Qdrant `semantic_indexes` vector dimension mismatch* below.

**Mixed pytest runs:** if `GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER=deterministic_fake` is exported in the shell while running tests that expect the default adapter (for example `test_config_loads_from_environment`), **unset** that variable for that invocation so process env does not leak into unrelated settings tests.

## Qdrant `semantic_indexes` vector dimension mismatch (Track B Slice B5.2)

### Symptom

- **Vector indexing fails at upsert** (during `SemanticIndexVectorIndexingService` / `VectorIndexService.upsert_semantic_index_vector` or equivalent operator backfill).
- The row may end as **`vector_status=failed`** with indexing metadata pointing at a **`VectorIndexOperationError`** (underlying Qdrant client error often mentions **vector size** / **dimension** mismatch).
- **Concrete example:** the collection **`semantic_indexes`** already exists with vector **size 3**, while the current dev path uses **`DeterministicFakeEmbeddingAdapter` at dimension 8** (B1 backfill script, B5 test indexer, and the guarded `deterministic_fake` search path all align on **8**).

### Cause

- Qdrant collections are **dimension-specific**: the configured vector size is fixed at **collection create** time.
- `VectorIndexService.ensure_semantic_indexes_collection` **reuses** an existing `semantic_indexes` collection if `get_collection` succeeds; it does **not** alter an existing collection’s vector size. If you **switch embedding adapters** or **dimensions** in dev, vectors you upsert must match that collection’s size or Qdrant rejects the write.
- **Remediation at the data plane:** recreate the collection (or use a separate Qdrant instance / volume) whose **`semantic_indexes`** definition matches the adapter dimension you use today.

### Safe dev-only fix

- **Only on local or disposable dev Qdrant** — **never** delete production vector data without an approved runbook.
- **Delete** (or recreate) **only** the **`semantic_indexes`** collection on that instance. After deletion, the next successful indexing or backfill run will **`create_collection`** with the **current** `expected_dimension` (8 for deterministic fake in this repo’s Track B paths).
- **Then** rerun **`scripts/backfill_semantic_indexes.py`** (or your API-driven indexing flow) so vectors are upserted again. Postgres `vector_status` rows that were **`failed`** may need a **retry** (`force` / `--all-pending` / re-run per id) depending on how you operate.

### What this is **not**

- **Not** automatic vector backfill on semantic index create (still manual / operator-triggered per Track B policy).
- **Not** production embedding support: **`deterministic_fake`** and the B1 script adapter remain **integration / dev** tooling, not a semantic production model.
- **Not** a claim that GraphClerk auto-heals dimension drift; operators must align Qdrant with the embedding dimension in use.

