# ADR-0006: PDF text extraction library (Phase 5)

## Status

Accepted.

## Context

Phase 5 Slice D needs **basic selectable text** from PDF pages for `EvidenceUnitCandidate` ingestion. The stack must stay **local-first**, avoid heavy native OCR stacks in this slice, and keep the default install light via **optional dependencies**.

## Decision

- Use **pypdf** as the PDF text library.
- Declare it under an optional **`pdf`** extra in `graphclerk-backend` (e.g. `pip install -e ".[pdf]"`).
- **Do not** adopt PyMuPDF, OCR (Tesseract/Paddle), pdfplumber, or similar in Slice D.

## Consequences

- **Pros:** Permissive license, pure-Python wheels, small surface, easy optional install; sufficient for many born-digital PDFs with a normal text layer.
- **Cons:** Weaker layout / column ordering than richer engines; no OCR or bbox fidelity in Slice D.
- **Runtime:** If the `pdf` extra is not installed, `POST /artifacts` for PDF uses a registry placeholder that raises **`ExtractorUnavailableError`** → **HTTP 503** with an install hint (no fake success).
- **Fidelity:** Page text from pypdf is labeled **`SourceFidelity.extracted`** (not `verbatim`).

## Alternatives considered

- **PyMuPDF:** Stronger extraction and geometry, but AGPL and native dependency trade-offs were rejected for the baseline Slice D scope.
