# Phase 4 Audit — File Clerk and Retrieval Packets

**Date**: 2026-04-30  
**Result**: `pass_with_notes`

## Questions

### Does the File Clerk return structured RetrievalPackets?
**Yes.** `POST /retrieve` returns a JSON body validated by the `RetrievalPacket` Pydantic model (`backend/app/schemas/retrieval_packet.py`), including empty-match cases.

### Does the File Clerk avoid generating final prose answers directly?
**Yes.** `FileClerkService` assembles structured fields only. No answer synthesis endpoint is implemented in this phase (optional Slice I remains deferred).

### Does the File Clerk avoid inventing evidence?
**Yes.** Evidence rows are loaded only for `EvidenceUnit` ids referenced by `GraphNodeEvidence` / `GraphEdgeEvidence` tuples produced by bounded graph neighborhoods (`EvidenceSelectionService`).

### Does answer synthesis consume only the packet?
**Not applicable / not implemented.** `POST /answer`, `LocalRAGConsumer`, and `AnswerSynthesizer` are intentionally not implemented pending a separate approved plan.

### Does the optional LocalRAGConsumer avoid bypassing the File Clerk?
**Not applicable / not implemented.**

### Are context budget decisions visible?
**Yes.** The packet includes `context_budget` with `pruning_reasons` populated by `ContextBudgetService`.

### Are ambiguity and alternatives represented?
**Partially.** Close semantic scores can emit `ambiguous_query` warnings, and optional `alternative_interpretations` entries are included when `options.include_alternatives` is true and alternates exist. This is intentionally basic/deterministic.

### Are retrieval warnings machine-readable?
**Yes.** Warnings are string codes such as `no_semantic_index_match`, `vector_index_unavailable`, and `no_evidence_support_found`.

### Were multimodal ingestion or automatic graph extraction features implemented early?
**No.**

### Are endpoints tested?
**Yes.** Unit tests cover services and packet contracts; integration-gated tests cover `POST /retrieve` and `RetrievalLog.retrieval_packet` persistence when enabled.

### Are known gaps listed?
**Yes** (see `docs/status/KNOWN_GAPS.md`).

### Does the README overclaim?
**No** (README distinguishes implemented vs not implemented, including deferred optional answer path).

## Notes (non-blocking)
- `RetrievalLog` persistence is best-effort: failures while writing logs roll back the log transaction but the API still returns a valid `RetrievalPacket`.
- Confidence scoring is a simple heuristic and should be treated as directional, not calibrated.
- **Deployment hygiene (`pass_with_notes`)**: real Postgres must run Alembic through revision **`0004_phase4_retrieval_packet_log`** so `retrieval_log.retrieval_packet` exists. Tests that use `Base.metadata.create_all()` do not replace that operator requirement; see README and `docs/status/TECHNICAL_DEBT.md`.
