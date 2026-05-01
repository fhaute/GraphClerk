# Known Gaps

This file tracks known missing pieces so they are explicit and not hidden.

- **Text ingestion (Markdown/plain text)**: implemented (Phase 2)
- **Multimodal ingestion (Phase 5 — partial)**:
  - **PDF / PPTX**: basic **text** extraction to `EvidenceUnit`s when optional **`pdf`** (pypdf) / **`pptx`** (python-pptx) extras are installed; quality and edge cases remain ongoing constraints
  - **Image / audio**: **validation shells only** (optional **`image`** / Pillow, **`audio`** / mutagen); **OCR, captioning/visual summaries, and transcription/ASR are not implemented**; image/audio **do not** emit `EvidenceUnit`s (typically **503** after validation)
  - **Video**: ingestion **not supported** (**400**); deferred / cancelled for this codebase state
  - **No** automatic multimodal graph extraction; **no** FileClerk or `RetrievalPacket` schema redesign for multimodal
- **Embedding adapter interface**: implemented (Phase 3; production adapter not wired)
- **Qdrant VectorIndexService**: implemented (Phase 3; integration tests are opt-in/gated)
- **Semantic index search**: implemented (Phase 3; only returns `vector_status=indexed`)
- **Graph traversal logic**: implemented (Phase 3; bounded traversal only)
- **Embeddings / semantic index population**: not_started (indexing job/backfill; automatic indexing on create)
- **FileClerk retrieval packet assembly**: implemented (Phase 4; deterministic/heuristic components)
- **Optional packet-only answer synthesis (`POST /answer`)**: not_started (deferred; requires separate approval)
- **Answer synthesis / LLM calls**: not_started (future phase)
- **Phase 6 UI / productization**: **in_progress** / **partial** — `frontend/` implements main explorers and query playground against live APIs; **Phase 6 audit**, in-product **demo corpus loader**, and several onboarding/release items from `docs/phases/graph_clerk_phase_6_productization_ui_evaluation_hardening.md` remain **not done**. **`POST /answer`** / answer-in-UI remains blocked on backend deferral.

## Known limitations (Phase 1)
- **Integration tests are opt-in**: DB/Qdrant tests require `RUN_INTEGRATION_TESTS=1` and explicit env vars.

## Operational / CI gaps
- **Migration chain verification in CI**: not implemented yet. CI should eventually run `alembic upgrade head` (from `backend/`) against a disposable Postgres database so Alembic revisions (including Phase 4 `0004_phase4_retrieval_packet_log`) are proven on upgrade paths, not only via `Base.metadata.create_all()` in tests.

## Known limitations (Phase 3)
- **Production embedding adapter not wired**: default wiring is explicitly “not configured”.
- **SemanticIndex creation does not auto-index into Qdrant**.
- **No indexing job/backfill** exists yet for vector population.

## Known limitations (Phase 4)
- **Query intent classification is simple/deterministic** (keyword/heuristic).
- **Alternative interpretation detection is basic** (mostly derived from semantic index alternates + ambiguity warnings).
- **Context budget uses simple ranking rules** (fidelity + confidence + dedupe + optional token cap).
- **LocalRAGConsumer / answer synthesis** is not implemented (packet-only `/answer` remains deferred).

## Known limitations (Phase 5 — in progress)
- **Phase 5 audit** is **`pass_with_notes`** (`docs/audits/PHASE_5_AUDIT.md`): partial implementation is accepted; **full** multimodal completion (OCR, ASR, image/audio EUs, etc.) remains **not done**.
- **Optional dependency matrix**: local/CI coverage for all combinations of extras + integration tests may need hardening later.

