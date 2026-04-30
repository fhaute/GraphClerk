# ADR-0007: PowerPoint (.pptx) text extraction library (Phase 5)

## Status

Accepted.

## Context

Phase 5 Slice E needs **basic text** from PowerPoint decks (slide titles, body text, notes, simple tables) for `EvidenceUnitCandidate` ingestion. The stack must stay **local-first**, avoid LibreOffice/headless Office, slide rendering, and vision/caption pipelines in this slice, and keep the default install light via **optional dependencies**.

## Decision

- Use **python-pptx** as the PPTX text library.
- Declare it under an optional **`pptx`** extra in `graphclerk-backend` (e.g. `pip install -e ".[pptx]"`).
- **Do not** adopt LibreOffice, slide rasterization, image-based slide understanding, or automatic graph extraction in Slice E.

## Consequences

- **Pros:** Permissive license, pure-Python OOXML access, deterministic slide order, straightforward title/body/notes/table text flattening without rendering.
- **Cons:** Text-only; no visual summaries, layout fidelity, or embedded media transcription; complex SmartArt/legacy shapes may yield incomplete text.
- **Runtime:** If the `pptx` extra is not installed, `POST /artifacts` for PPTX uses a registry placeholder that raises **`ExtractorUnavailableError`** → **HTTP 503** with an install hint (no fake success).
- **Fidelity:** Text from python-pptx is labeled **`SourceFidelity.extracted`** (not `verbatim`).

## Alternatives considered

- **LibreOffice headless / COM automation:** Rejected for Slice E (operational weight, rendering scope, and explicit non-goals).
