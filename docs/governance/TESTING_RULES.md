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

