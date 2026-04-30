# GraphClerk Phase 5 — Multimodal Ingestion

## Phase Dependency
This phase must only start after:

```text
Phase 0 — Governance Baseline
Phase 1 — Foundation and Core Architecture
Phase 2 — Text-First Ingestion and Evidence Units
Phase 3 — Semantic Index and Graph Layer
Phase 4 — File Clerk and Retrieval Packets
```

Phase 5 assumes:

```text
- Governance docs exist
- Cursor rules exist
- coding standards exist
- documentation standards exist
- status reporting exists
- audit rules exist
- FastAPI backend exists
- PostgreSQL works
- Qdrant works
- Artifact and EvidenceUnit models exist
- Text/Markdown ingestion works
- Graph layer exists
- Semantic index search works
- File Clerk retrieval packets exist
- Context budget exists
- Retrieval logs exist
- Phase 4 tests pass
- Phase 4 audit is pass or pass_with_notes
```

Cursor must not implement this phase unless Phase 4 is complete and status docs confirm it.

---

## Purpose
Expand GraphClerk beyond text and Markdown into real-world multimodal knowledge.

Most RAG systems quietly assume knowledge equals text chunks.

GraphClerk must treat knowledge as artifacts that can come from:

```text
PDFs
PowerPoints
images
audio
video
screenshots
diagrams
tables
transcripts
```

The goal of Phase 5 is to normalize these modalities into the same core structure already established:

```text
Artifact → EvidenceUnits → Graph support → RetrievalPacket
```

---

## Core Objective
At the end of this phase, GraphClerk should be able to:

```text
- ingest PDF artifacts
- ingest PowerPoint artifacts
- ingest image artifacts
- ingest audio artifacts
- optionally prepare basic video ingestion
- create modality-specific EvidenceUnits
- preserve source traceability for all modalities
- store modality/location metadata
- mark source_fidelity correctly
- expose multimodal evidence through existing evidence APIs
- allow graph nodes/edges to link to multimodal EvidenceUnits
- allow File Clerk packets to include multimodal evidence references
- test multimodal extraction and traceability
- document extractor limitations
- update status docs
- produce a Phase 5 audit
```

This phase makes GraphClerk a multimodal evidence-routing system, not only a text RAG helper.

---

## Product Principle Preserved In This Phase
Every modality must normalize into EvidenceUnits.

The rule is:

> Different inputs, same evidence contract.

PDFs, slides, images, audio, and video should not each create isolated special systems.

They all become Artifacts.

They all produce EvidenceUnits.

Those EvidenceUnits can support graph nodes and edges.

Those graph paths can later appear inside RetrievalPackets.

---

## Scope

### Included

```text
- Artifact type routing by modality
- PDF ingestion
- PowerPoint ingestion
- image ingestion
- audio ingestion
- basic video groundwork optional
- local-first extraction adapters
- OCR adapter abstraction
- vision caption adapter abstraction
- transcription adapter abstraction
- modality-specific EvidenceUnit content types
- source location metadata for each modality
- source_fidelity enforcement
- multimodal evidence API compatibility
- File Clerk packet compatibility with multimodal evidence
- tests for multimodal ingestion and traceability
- status docs update
- Phase 5 audit
```

### Excluded

```text
- Production-grade OCR perfection
- Perfect table understanding
- Perfect diagram reasoning
- Full video semantic understanding
- Automatic multimodal graph construction
- Advanced multimodal embeddings across all modalities
- UI media preview unless trivial
- Autonomous agents
- Cloud LLM requirement
```

---

## Non-Negotiable Rules For This Phase

```text
1. All modalities must become Artifacts and EvidenceUnits.
2. Do not create modality-specific truth layers outside EvidenceUnits.
3. Do not overwrite original artifacts.
4. Do not mark derived captions/summaries as verbatim.
5. OCR output must be marked extracted, not verbatim.
6. Captions and visual summaries must be marked derived.
7. Transcripts should be marked extracted unless exact human transcript source is provided.
8. Extraction failures must be explicit.
9. Every extractor must have tests or documented limitations.
10. Every EvidenceUnit must link back to an Artifact.
11. Location metadata must be stored where available.
12. File Clerk packets must be able to carry modality metadata.
13. No external LLM dependency is required.
14. Every public class/function must have a docstring.
15. Status docs must be updated before phase completion.
16. Phase 5 audit must be created before phase completion.
```

---

# Core Flow

```text
Multimodal artifact uploaded/imported
  ↓
Artifact created
  ↓
Modality router selects extractor
  ↓
Extractor creates EvidenceUnits
  ↓
EvidenceUnits preserve source location and source_fidelity
  ↓
Graph nodes/edges may link to multimodal EvidenceUnits
  ↓
File Clerk can include multimodal evidence references in RetrievalPacket
```

---

# Supported Modalities For Phase 5

Recommended implementation order:

```text
1. PDF
2. PowerPoint
3. Image
4. Audio
5. Video groundwork
```

Video may be partial in Phase 5.

It is acceptable to implement video as:

```text
video artifact
  → extracted audio transcript
  → keyframe placeholders or basic keyframe extraction
```

Full video understanding can be deferred.

---

# Artifact Types

Phase 5 should support or prepare for:

```text
pdf
pptx
image
audio
video
```

Example Artifact:

```json
{
  "id": "artifact_pitch_deck",
  "filename": "graphclerk_pitch.pptx",
  "title": "GraphClerk Pitch Deck",
  "artifact_type": "pptx",
  "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  "storage_uri": "local://artifacts/graphclerk_pitch.pptx",
  "checksum": "sha256...",
  "metadata": {
    "ingestion_phase": "phase_5_multimodal_ingestion"
  }
}
```

---

# EvidenceUnit Content Types For Phase 5

## PDF

```text
pdf_page_text
pdf_page_ocr_text
pdf_table_text
pdf_image_caption
pdf_page_summary optional
```

## PowerPoint

```text
slide_title
slide_body_text
slide_speaker_notes
slide_visual_summary
slide_image_caption
slide_table_text
```

## Image

```text
image_ocr_text
image_caption
image_visual_summary
image_region_caption optional
```

## Audio

```text
audio_transcript_segment
audio_topic_segment optional
audio_quote optional
```

## Video

```text
video_transcript_segment
video_keyframe_caption
video_keyframe_ocr_text
video_moment_summary optional
```

---

# Source Fidelity Rules For Multimodal

## verbatim
Use only when text is exactly present and preserved as source text.

Examples:

```text
embedded PDF text if extracted exactly from selectable text
PowerPoint speaker notes text
PowerPoint slide text
```

## extracted
Use when the system extracts text from a modality and errors are possible.

Examples:

```text
OCR text from scanned PDF
OCR text from image
transcription from audio
transcription from video
```

## derived
Use when the system generates an interpretation.

Examples:

```text
image caption
visual summary
diagram description
slide visual summary
video moment summary
```

## computed
Use for machine-generated metadata.

Examples:

```text
embedding vector reference
confidence score
checksum
scene boundary score
```

---

# PDF Ingestion

## Purpose
Turn PDF documents into page/section evidence units.

## Local-First Extractors
Possible tools:

```text
PyMuPDF
pdfplumber
pypdf
Tesseract or PaddleOCR for OCR fallback
```

## PDF Flow

```text
PDF artifact
  ↓
extract selectable text per page
  ↓
if page has little/no text, run OCR fallback if available
  ↓
extract tables if simple support exists
  ↓
create EvidenceUnits with page metadata
```

## PDF Evidence Location

```json
{
  "page": 4,
  "section": "optional if detected",
  "block_index": 2,
  "bbox": [100, 120, 400, 220]
}
```

`bbox` is optional in Phase 5.

## PDF Acceptance

```text
- PDF artifact is created.
- Page text EvidenceUnits are created.
- OCR fallback is explicit if used.
- EvidenceUnits include page metadata.
- Unsupported/failed extraction reports clear errors.
```

---

# PowerPoint Ingestion

## Purpose
Turn slide decks into slide-level evidence units.

## Local-First Extractors
Possible tools:

```text
python-pptx
LibreOffice headless optional for slide rendering
Pillow/image tools for rendered slide images optional
```

## PPTX Flow

```text
PPTX artifact
  ↓
extract slide titles and text boxes
  ↓
extract speaker notes if available
  ↓
extract simple tables if available
  ↓
optional render slide image
  ↓
optional visual summary/caption adapter
  ↓
create EvidenceUnits with slide metadata
```

## Slide Evidence Location

```json
{
  "slide_number": 8,
  "shape_id": "optional",
  "region": "title|body|notes|full_slide",
  "block_index": 3
}
```

## PPTX Acceptance

```text
- PPTX artifact is created.
- Slide titles become EvidenceUnits.
- Slide body text becomes EvidenceUnits.
- Speaker notes become EvidenceUnits when available.
- Slide number metadata is present.
- Visual summaries are marked derived if implemented.
```

---

# Image Ingestion

## Purpose
Turn image files into OCR and visual evidence units.

## Local-First Extractors
Possible tools/models:

```text
Tesseract
EasyOCR
PaddleOCR
CLIP/SigLIP for image embeddings later
local vision caption model optional
```

## Image Flow

```text
Image artifact
  ↓
OCR extraction optional
  ↓
caption/visual summary optional
  ↓
create EvidenceUnits
```

## Image Evidence Location

```json
{
  "region": "full_image",
  "bbox": null
}
```

Region-level support can be deferred.

## Image Acceptance

```text
- Image artifact is created.
- OCR EvidenceUnit is created if text is detected.
- Caption/summary EvidenceUnit is marked derived.
- Failures are explicit.
```

---

# Audio Ingestion

## Purpose
Turn audio into timestamped transcript evidence units.

## Local-First Extractors
Possible tools:

```text
faster-whisper
whisper.cpp
OpenAI Whisper local model
```

## Audio Flow

```text
Audio artifact
  ↓
transcription model
  ↓
timestamped transcript segments
  ↓
EvidenceUnits
```

## Audio Evidence Location

```json
{
  "start_seconds": 128.4,
  "end_seconds": 142.9,
  "speaker": "unknown"
}
```

Speaker diarization can be deferred.

## Audio Acceptance

```text
- Audio artifact is created.
- Transcript segments become EvidenceUnits.
- Timestamps are stored.
- Transcription output is marked extracted.
```

---

# Video Groundwork

## Purpose
Prepare video ingestion without overcommitting to full video understanding.

## Local-First Tools
Possible tools:

```text
ffmpeg
PySceneDetect optional
faster-whisper for extracted audio
OCR/caption on keyframes optional later
```

## Video Flow For Phase 5

Minimum acceptable:

```text
Video artifact
  ↓
extract audio
  ↓
transcribe audio
  ↓
create video_transcript_segment EvidenceUnits
```

Optional:

```text
extract keyframes
  ↓
OCR/caption keyframes
  ↓
create video_keyframe EvidenceUnits
```

## Video Evidence Location

```json
{
  "start_seconds": 272.0,
  "end_seconds": 289.5,
  "frame_time_seconds": 275.0,
  "keyframe_uri": "optional"
}
```

## Video Acceptance

```text
- Video artifact can be stored.
- Audio transcript can be extracted if implemented.
- Keyframe support is optional.
- Full video reasoning is not required.
```

---

# Modality Router

Implement an ingestion router that selects the correct extractor.

Example:

```text
artifact_type = pdf → PDFExtractor
artifact_type = pptx → PowerPointExtractor
artifact_type = image → ImageExtractor
artifact_type = audio → AudioExtractor
artifact_type = video → VideoExtractor optional
```

The router must fail clearly for unsupported artifact types.

---

# Extractor Adapter Contracts

Each extractor should follow a common shape.

Example:

```python
class ArtifactExtractor:
    """Extract evidence units from a specific artifact modality.

    Extractors must not mutate original artifacts. They return candidate
    EvidenceUnits with source_fidelity, location metadata, and confidence.
    """

    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        """Return evidence unit candidates extracted from the artifact."""
```

## EvidenceUnitCandidate

Suggested fields:

```text
artifact_id
modality
content_type
text
location
source_fidelity
confidence
metadata
```

---

# File Clerk Compatibility

Phase 5 should not redesign the File Clerk.

Instead, it should make sure RetrievalPackets can include multimodal evidence metadata.

Evidence in packets should already carry:

```text
evidence_unit_id
artifact_id
modality
content_type
source_fidelity
text or summary
location
confidence
```

That should be enough for Phase 5.

If any schema update is needed, it must go through change-control.

---

# Graph Compatibility

Phase 5 does not need automatic graph construction.

But graph nodes and edges should be able to link to multimodal EvidenceUnits.

Example:

```text
GraphNode: Retrieval Packet Diagram
supported_by:
- slide_visual_summary EvidenceUnit
- image_caption EvidenceUnit
- video_transcript_segment EvidenceUnit
```

No special graph layer should be created for each modality.

---

# Error Handling Requirements

Errors must be explicit.

Examples:

```text
UnsupportedArtifactTypeError
ExtractorUnavailableError
PdfExtractionError
PowerPointExtractionError
ImageOcrError
ImageCaptionError
AudioTranscriptionError
VideoExtractionError
EvidenceUnitCreationError
InvalidSourceFidelityError
```

If an extractor is unavailable because a local model/tool is not installed, return a clear error.

Do not pretend extraction succeeded.

---

# Required Tests

Minimum tests:

```text
test_pdf_artifact_ingestion_creates_evidence_units
test_pdf_evidence_units_include_page_metadata
test_pptx_artifact_ingestion_creates_slide_evidence_units
test_pptx_slide_text_has_slide_number
test_image_artifact_ingestion_creates_ocr_or_caption_evidence
test_image_caption_marked_derived
test_audio_artifact_ingestion_creates_transcript_segments
test_audio_transcript_marked_extracted
test_unsupported_artifact_type_fails_clearly
test_multimodal_evidence_units_link_to_artifact
test_file_clerk_packet_can_include_multimodal_evidence_metadata
test_extraction_failure_is_explicit
```

Optional tests:

```text
test_pdf_ocr_fallback_marked_extracted
test_pptx_speaker_notes_extracted
test_video_audio_transcript_segments_created
test_video_keyframe_metadata_if_implemented
test_missing_extractor_dependency_fails_clearly
test_graph_edge_can_be_supported_by_image_evidence
```

---

# Documentation Requirements

Phase 5 must create or update:

```text
docs/phases/PHASE_5_MULTIMODAL_INGESTION.md
docs/status/PROJECT_STATUS.md
docs/status/PHASE_STATUS.md
docs/status/KNOWN_GAPS.md
docs/status/TECHNICAL_DEBT.md
docs/audits/PHASE_5_AUDIT.md
README.md
```

## README Must Say

```text
Implemented:
- Text/Markdown ingestion
- Graph and SemanticIndex layer
- File Clerk retrieval packets
- PDF ingestion basic support
- PowerPoint ingestion basic support
- Image ingestion basic support
- Audio ingestion basic support
- Video groundwork if implemented

Not implemented or limited:
- Perfect OCR
- Perfect table understanding
- Perfect diagram reasoning
- full video semantic understanding
- automatic multimodal graph construction
- production-grade UI
```

Do not claim perfect multimodal understanding.

Do not claim production-ready OCR/vision quality.

---

# Status Document Requirements

`PROJECT_STATUS.md` should update the current state.

Example:

```text
Current phase: Phase 5 — Multimodal Ingestion

Implemented:
- PDF extraction into EvidenceUnits
- PPTX extraction into EvidenceUnits
- image OCR/caption EvidenceUnits
- audio transcription EvidenceUnits
- multimodal EvidenceUnits compatible with File Clerk packets

Not implemented:
- full video understanding
- automatic graph construction from multimodal evidence
- advanced visual reasoning
- production-grade OCR accuracy
```

`KNOWN_GAPS.md` should include:

```text
- OCR quality depends on installed local extractor.
- Visual summaries are derived and may be imperfect.
- Table extraction is basic.
- Diagrams are not deeply reasoned about yet.
- Speaker diarization is not implemented unless explicitly added.
- Video support is partial if only audio transcript is implemented.
```

`TECHNICAL_DEBT.md` should include any accepted shortcuts.

---

# Phase 5 Audit Requirements

Create:

```text
docs/audits/PHASE_5_AUDIT.md
```

Audit must answer:

```text
- Do all modalities normalize into EvidenceUnits?
- Does every EvidenceUnit link to an Artifact?
- Are source_fidelity values correct?
- Are OCR/transcription outputs marked extracted?
- Are visual summaries/captions marked derived?
- Are extraction failures explicit?
- Did any modality create a separate truth layer outside EvidenceUnits?
- Are File Clerk packets still compatible with multimodal evidence?
- Were any unsupported capabilities overclaimed in README?
- Are known extraction limitations documented?
- Are all implemented extractors tested?
```

Allowed audit result:

```text
pass
pass_with_notes
needs_fix
blocked
```

Phase 5 is not complete if audit result is `needs_fix` or `blocked`.

---

# Implementation Tasks

## Task 1 — Generalize artifact ingestion routing
Implement modality router.

Acceptance:

```text
- artifact_type selects extractor
- unsupported artifact type fails clearly
- text/Markdown ingestion remains working
```

## Task 2 — Add EvidenceUnitCandidate contract
Create internal candidate structure returned by extractors.

Acceptance:

```text
- all extractors return the same candidate shape
- source_fidelity is required
- location metadata is supported
```

## Task 3 — Implement PDFExtractor
Basic PDF text extraction.

Acceptance:

```text
- PDF creates EvidenceUnits
- page metadata exists
- OCR fallback is explicit if implemented
```

## Task 4 — Implement PowerPointExtractor
Basic PPTX slide text/notes extraction.

Acceptance:

```text
- slide titles/body text become EvidenceUnits
- speaker notes become EvidenceUnits when available
- slide number metadata exists
```

## Task 5 — Implement ImageExtractor
Basic OCR and/or caption support.

Acceptance:

```text
- image artifacts produce OCR and/or caption EvidenceUnits
- OCR is extracted
- caption/summary is derived
```

## Task 6 — Implement AudioExtractor
Local transcription into timestamped segments.

Acceptance:

```text
- audio artifacts produce transcript segment EvidenceUnits
- timestamps are stored
- transcription output is extracted
```

## Task 7 — Optional VideoExtractor groundwork
Implement video artifact handling and audio transcription.

Acceptance:

```text
- video artifact can be stored
- audio extraction/transcription works if implemented
- video transcript segments include timestamps
```

## Task 8 — Ensure File Clerk packet compatibility
Confirm RetrievalPackets can include multimodal evidence metadata.

Acceptance:

```text
- packet evidence entries include modality/content_type/location
- tests cover multimodal evidence in packets
```

## Task 9 — Add graph support compatibility tests
Ensure graph nodes/edges can link to multimodal EvidenceUnits.

Acceptance:

```text
- graph support links work for image/audio/PDF/PPTX evidence units
```

## Task 10 — Add required tests
Implement all required tests for Phase 5.

Acceptance:

```text
- pytest passes
- extractor behavior is tested
- source_fidelity is tested
```

## Task 11 — Update docs and status
Update README, phase docs, status docs, known gaps, and technical debt.

Acceptance:

```text
- documentation matches actual behavior
- limitations are clear
```

## Task 12 — Add Phase 5 audit
Create the Phase 5 audit file.

Acceptance:

```text
- audit result is pass or pass_with_notes
```

---

# Cursor Prompt Template For Phase 5 Tasks

Every Cursor prompt for this phase should begin with:

```text
You are working on GraphClerk Phase 5 — Multimodal Ingestion.
You must follow docs/governance/*.
All modalities must normalize into Artifacts and EvidenceUnits.
Do not create separate modality-specific truth layers.
Do not implement automatic graph extraction, autonomous agent loops, advanced UI, or cloud LLM requirements.
Only modify the files listed below.
Add or update tests as specified.
Add docstrings to public classes/functions.
Update status docs only if this task requires it.
```

Then specify:

```text
Allowed files:
Forbidden files:
Task:
Acceptance criteria:
Required tests:
Documentation updates:
```

---

# Deliverables
At the end of Phase 5:

```text
- Modality router
- EvidenceUnitCandidate contract
- PDFExtractor
- PowerPointExtractor
- ImageExtractor
- AudioExtractor
- optional VideoExtractor groundwork
- multimodal EvidenceUnits
- correct source_fidelity usage
- source location metadata per modality
- File Clerk compatibility with multimodal evidence
- graph support compatibility with multimodal evidence
- required tests
- Phase 5 documentation
- Phase 5 status update
- Phase 5 audit
```

---

# Acceptance Criteria

```text
Given a PDF artifact,
when it is ingested,
then page-level EvidenceUnits are created with page metadata.

Given a PowerPoint artifact,
when it is ingested,
then slide-level EvidenceUnits are created with slide metadata.

Given an image artifact,
when it is ingested,
then OCR and/or caption EvidenceUnits are created with correct source_fidelity.

Given an audio artifact,
when it is ingested,
then timestamped transcript EvidenceUnits are created.

Given any multimodal EvidenceUnit,
then it links back to its Artifact.

Given a graph node or edge,
then it can link to multimodal EvidenceUnits as support.

Given a File Clerk packet,
then it can include multimodal evidence metadata without schema breakage.

Given an extractor dependency is missing,
then the system fails clearly.

Given pytest is run,
then all Phase 5 tests pass.

Given docs are inspected,
then they do not claim perfect OCR, perfect visual reasoning, or full video understanding.

Given the Phase 5 audit is inspected,
then the result is pass or pass_with_notes.
```

---

# Known Non-Features After Phase 5

After this phase, GraphClerk may still not support:

```text
- full video semantic understanding
- perfect OCR
- perfect diagram interpretation
- perfect table extraction
- automatic graph construction from multimodal evidence
- advanced multimodal embeddings
- UI media preview
- production-grade evaluation dashboard
```

This is intentional.

---

# Risks

## Risk 1 — Multimodal scope explosion
PDFs, slides, images, audio, and video can each become a full project.

Mitigation:

```text
- basic extractors first
- document limitations
- no perfect extraction claims
```

## Risk 2 — Source fidelity confusion
OCR, transcripts, and captions may be incorrectly treated as verbatim.

Mitigation:

```text
- enforce source_fidelity rules
- tests for extracted/derived labeling
- audit check
```

## Risk 3 — Modality-specific architecture drift
Each modality may tempt a separate pipeline and truth model.

Mitigation:

```text
- all outputs normalize to EvidenceUnits
- common Extractor contract
- no separate truth layers
```

## Risk 4 — Heavy dependency friction
OCR/audio/video tools may be hard to install.

Mitigation:

```text
- optional extractor adapters
- clear dependency docs
- explicit unavailable errors
```

## Risk 5 — Overclaiming multimodal intelligence
Basic extraction is not the same as deep understanding.

Mitigation:

```text
- README honesty
- known gaps
- phase audit
```

---

# Suggested Duration

```text
Fast mode: 1–3 weeks depending on depth
Clean mode: 1–2 months
```

A fast version should prioritize:

```text
PDF basic text extraction
PPTX slide text extraction
image OCR/caption basic support
audio transcription basic support
video only as optional groundwork
```

---

# Phase Completion Definition
Phase 5 is complete when GraphClerk can ingest multiple non-text modalities into traceable EvidenceUnits, preserve source fidelity, expose those units through existing evidence structures, and include them in graph support and File Clerk packets without breaking the core architecture.

The output of this phase is multimodal evidence ingestion.

