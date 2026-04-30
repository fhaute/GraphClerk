# Known Gaps

This file tracks known missing pieces so they are explicit and not hidden.

- **Text ingestion (Markdown/plain text)**: implemented (Phase 2)
- **EvidenceUnit extraction from real files on disk**: not_started (future follow-up)
- **Multimodal ingestion (PDF/slides/images/audio/video)**: not_started (future phase)
- **Embedding adapter interface**: implemented (Phase 3; production adapter not wired)
- **Qdrant VectorIndexService**: implemented (Phase 3; integration tests are opt-in/gated)
- **Semantic index search**: implemented (Phase 3; only returns `vector_status=indexed`)
- **Graph traversal logic**: implemented (Phase 3; bounded traversal only)
- **Embeddings / semantic index population**: not_started (indexing job/backfill; automatic indexing on create)
- **FileClerk retrieval packet assembly**: not_started (future phase)
- **Answer synthesis / LLM calls**: not_started (future phase)
- **UI**: not_started (future phase)

## Known limitations (Phase 1)
- **Integration tests are opt-in**: DB/Qdrant tests require `RUN_INTEGRATION_TESTS=1` and explicit env vars.

## Known limitations (Phase 3)
- **Production embedding adapter not wired**: default wiring is explicitly “not configured”.
- **SemanticIndex creation does not auto-index into Qdrant**.
- **No indexing job/backfill** exists yet for vector population.

