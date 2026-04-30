---
phase: 2
title: Phase 2 Audit
status: pass_with_notes
date: 2026-04-30
---

# Phase 2 Audit — Text-first ingestion & EvidenceUnits

## Scope compliance
- **In scope implemented**: text/Markdown ingestion, checksum + storage_uri, hybrid raw source preservation, EvidenceUnit generation with location metadata, inspection APIs, tests.
- **Out of scope not implemented**: PDF/PPTX ingestion, embeddings/Qdrant writes, semantic search, graph traversal, FileClerk/retrieval packets, LLM calls, UI.

## Architecture invariants
- **Artifacts are the source of truth**: EvidenceUnits always reference `artifact_id`.
- **Traceability**: EvidenceUnits store verbatim blocks and location metadata.

## Tests and verification
- `pytest` passes with integration disabled.
- Phase 2 DB-backed tests are **opt-in** via `RUN_INTEGRATION_TESTS=1` and `DATABASE_URL`.

## Notes / follow-ups
- Large text/Markdown is disk-backed but still parsed from request bytes in Phase 2; future phases may add reading from `storage_uri` for reprocessing.

