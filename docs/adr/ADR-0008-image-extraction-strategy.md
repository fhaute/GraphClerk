# ADR-0008: Image extraction strategy (Phase 5 Slice F shell)

## Status

Accepted.

## Context

Image ingestion can mean several different backends: **OCR** (text from pixels), **captioning** or **visual summaries** (semantic descriptions), often with heavy ML stacks or cloud vision APIs. Phase 5 must stay **local-first**, avoid **dependency creep**, and **never** imply multimodal evidence exists when it does not.

## Decision

- **Slice F** adds only:
  - Optional **`image`** extra with **Pillow** for **decode/validation** of uploaded image bytes.
  - An **`ImageExtractor`** that loads persisted bytes via **`RawSourceStore.read_persisted_bytes`**, opens the image with Pillow, and then raises **`ExtractorUnavailableError`** with an explicit message that **OCR/caption extraction is not configured** (to be enabled in a later slice after approval).
- **No** pytesseract, system Tesseract, EasyOCR, PaddleOCR, Torch, cloud vision, captioning, or visual summaries in Slice F.
- **No** `EvidenceUnitCandidate` emission in Slice F, so **no** `source_fidelity` on image evidence yet.
- **Reserved** future `content_type` strings (documentation only in this slice): `image_ocr_text`, `image_caption`, `image_visual_summary`.

## Consequences

- **Routing:** Multipart image uploads resolve to `artifact_type=image` / `Modality.image` (see artifact type resolver); registry registers **`ImageExtractor`** when Pillow is installed, or a **placeholder** that raises **`ExtractorUnavailableError`** (**HTTP 503**) when Pillow is missing.
- **User-visible behavior:** With Pillow installed, **`POST /artifacts`** for a valid image returns **503** after validation with a clear “OCR/caption not configured” message — **not** 200 with zero evidence.
- **Corrupt bytes:** **`ImageExtractionError`** (**HTTP 400**), not **`ExtractorUnavailableError`**.
- **Future OCR** (when approved) should label text as **`SourceFidelity.extracted`**; **captions / visual summaries** as **`derived`**; **no** image pipeline should mark evidence **`verbatim`** per Phase 5 fidelity rules.

## Alternatives considered

- **Ship OCR in Slice F (e.g. pytesseract + Tesseract):** Rejected for this slice to limit system and Python dependency surface.
- **Return empty candidate list:** Rejected — would risk fake “success”; explicit **`ExtractorUnavailableError`** after validation keeps semantics honest.
