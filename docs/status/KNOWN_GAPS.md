# Known Gaps

This file tracks known missing pieces so they are explicit and not hidden.

- **Text ingestion (Markdown/plain text)**: implemented (Phase 2)
- **EvidenceUnit extraction from real files on disk**: not_started (future follow-up)
- **Multimodal ingestion (PDF/slides/images/audio/video)**: not_started (future phase)
- **Embeddings / semantic index population**: not_started (future phase)
- **Semantic index search**: not_started (future phase)
- **Graph traversal logic**: not_started (future phase)
- **FileClerk retrieval packet assembly**: not_started (future phase)
- **Answer synthesis / LLM calls**: not_started (future phase)
- **UI**: not_started (future phase)

## Known limitations (Phase 1)
- **Integration tests are opt-in**: DB/Qdrant tests require `RUN_INTEGRATION_TESTS=1` and explicit env vars.

