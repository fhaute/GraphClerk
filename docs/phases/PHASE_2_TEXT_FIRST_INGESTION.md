---
phase: 2
title: Text-first ingestion & EvidenceUnits
status: implemented
date: 2026-04-30
---

# Phase 2 — Text-first ingestion & EvidenceUnits

## What Phase 2 adds
- **Artifacts can be created** from plain text or Markdown.
- **Raw source preservation (hybrid)**:
  - If artifact content is small (\(\le\) `RAW_TEXT_DB_THRESHOLD_BYTES = 256_000`), the raw UTF-8 text is stored in Postgres (`artifact.raw_text`) for traceability.
  - Larger sources are stored on disk under `ARTIFACTS_DIR` and referenced via a deterministic checksum-based `storage_uri`.
- **EvidenceUnits are created** from the source text/Markdown with location metadata (line ranges, section path, block index).
- **Inspection APIs** to list/get artifacts and evidence units.

## Endpoints (Phase 2)
- `POST /artifacts`
  - **JSON** inline: `{ filename, artifact_type: "text"|"markdown", text, ... }`
  - **Multipart**: `file=@...` (Phase 2 rejects non-text/Markdown)
- `GET /artifacts`
- `GET /artifacts/{artifact_id}`
- `GET /artifacts/{artifact_id}/evidence`
- `GET /evidence-units/{evidence_unit_id}`

## Storage URI formats (deterministic)
- **DB-backed (small sources)**: `localdb://artifacts/sha256/<checksum>.<ext>`
- **Disk-backed (large sources)**: `local://artifacts/sha256/<first2>/<checksum>.<ext>`

## Limitations (by design)
- No PDF/PPTX parsing.
- No embeddings, semantic search, Qdrant writes, or retrieval packets.
- No graph traversal.
- No UI.

