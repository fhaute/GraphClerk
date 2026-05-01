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
- **Phase 6 UI / productization**: **implemented (`pass_with_notes`)** — `frontend/` explorers + query playground against live APIs; **audit** [`docs/audits/PHASE_6_AUDIT.md`](../audits/PHASE_6_AUDIT.md) (2026-05-01). **Still gaps (explicit)**: in-product **demo loader** only as script (`scripts/load_phase6_demo.py`); **no** automated frontend tests; **not** production enterprise stack; optional hardening/E2E per roadmap. **`POST /answer`** / answer-in-UI remains blocked on backend deferral.

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

## Known limitations (Phase 7 — context intelligence, baseline)
- **Phase 7 audit**: **`pass_with_notes`** — [`docs/audits/PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md) (2026-05-02); remaining gaps are **notes**, not a claim of full phase-doc/product closure.
- **`LanguageDetectionService`**: adapter shell exists (**NotConfigured** / test adapters); **not** wired as automatic production language detection on ingest **by default**; **no** “always-on” remote detector claimed.
- **`language_context`**: derived from **selected evidence `metadata_json`** only when language fields exist — **not** from silent text guessing or mandatory detection in packet assembly.
- **Translation / query translation**: **not implemented**; GraphClerk is **not** a translation engine in this baseline.
- **ActorContext**: accepted on `POST /retrieve` and recorded on `RetrievalPacket` (`PacketActorContextRecording`); **does not** influence route selection, evidence ranking, traversal, budget, warnings, confidence, or **`answer_mode`**.
- **Deterministic context boosting** (Slice **7I**): **not implemented** — **deferred / cancelled** pending **separate approval**, evaluation fixtures, and audit-ready rules; must prove ActorContext cannot override evidence or bypass source grounding; any future influence must remain explicit on the packet (no hidden retrieval).

## Known limitations (Phase 5 — in progress)
- **Phase 5 audit** is **`pass_with_notes`** (`docs/audits/PHASE_5_AUDIT.md`): partial implementation is accepted; **full** multimodal completion (OCR, ASR, image/audio EUs, etc.) remains **not done**.
- **Optional dependency matrix**: local/CI coverage for all combinations of extras + integration tests may need hardening later.

## Known limitations (Phase 8 — specialized model pipeline baseline)
- **Phase 8 audit**: **Slice 8I** — **pending**; baseline code/docs honesty does **not** replace a formal audit artifact.
- **No production inference adapter**: **`NotConfigured`** is the default story; **no** Ollama, **no** vLLM, **no** HTTP inference client in shipped product paths; **8G** is **design-only**.
- **No adapter registry** and **no** model-pipeline configuration in app settings for inference.
- **`ModelPipelineCandidateMetadataProjectionService`** is **standalone** — **not** wired into text/multimodal ingestion, **`EvidenceEnrichmentService`**, FileClerk, or **`POST /retrieve`**.
- **Model output is not evidence**: projection remains **metadata-only** under **`metadata_json["graphclerk_model_pipeline"]`** (when callers attach it); **no** automatic **`EvidenceUnit`** / candidate **`text`** / **`source_fidelity`** mutation from model pipeline modules.
- **`POST /answer`** / answer synthesis: **not implemented**; Phase 8 baseline must **not** be read as answer/RAG completion.

