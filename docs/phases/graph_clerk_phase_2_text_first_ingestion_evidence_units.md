# GraphClerk Phase 2 — Text-First Ingestion and Evidence Units

## Phase Dependency
This phase must only start after **Phase 0 — Governance Baseline** and **Phase 1 — Foundation and Core Architecture** are complete.

Phase 2 assumes:

```text
- Git governance exists
- Cursor rules exist
- coding standards exist
- documentation standards exist
- status reporting exists
- audit rules exist
- FastAPI backend exists
- PostgreSQL is connected
- Qdrant is connected, but not yet used for ingestion
- Alembic migrations work
- core persistence models exist
- tests run
```

Cursor must not implement this phase unless Phase 1 tests pass and Phase 1 audit is `pass` or `pass_with_notes`.

---

## Purpose
Build the first real ingestion pipeline for GraphClerk.

This phase supports text and Markdown artifacts and turns them into source-backed evidence units.

This phase proves the first core flow:

```text
Artifact → EvidenceUnits
```

It does not yet build semantic indexes, graph traversal, retrieval packets, or answers.

---

## Core Objective
At the end of this phase, GraphClerk should be able to:

```text
- ingest plain text files
- ingest Markdown files
- create Artifact records
- preserve original source content
- split source content into EvidenceUnits
- store source location metadata
- expose APIs to inspect artifacts and evidence units
- test source preservation
- document current ingestion limitations
- update status docs
- produce a Phase 2 audit
```

---

## Product Principle Preserved In This Phase
The original source must stay traceable.

GraphClerk must never replace source truth with derived summaries.

The rule is:

> Source first. Interpretation later.

This means Phase 2 creates evidence units mostly as `verbatim` source-backed records.

---

## Scope

### Included

```text
- Plain text ingestion
- Markdown ingestion
- Artifact creation from uploaded/imported file
- Raw source preservation
- EvidenceUnit creation
- Basic section/paragraph/list/code-block parsing
- Source location metadata
- EvidenceUnit API endpoints
- Artifact inspection endpoints
- Ingestion service
- Parser service
- Tests for ingestion and source fidelity
- Status document updates
- Phase 2 audit
```

### Excluded

```text
- PDF ingestion
- PowerPoint ingestion
- image ingestion
- audio ingestion
- video ingestion
- OCR
- visual captioning
- embeddings
- Qdrant vector writes
- semantic index search
- graph node/edge creation from ingestion
- automatic claim extraction
- File Clerk logic
- retrieval packets
- LLM answer synthesis
- UI
```

---

## Non-Negotiable Rules For This Phase

```text
1. Do not implement semantic search.
2. Do not implement graph traversal.
3. Do not implement retrieval packets.
4. Do not implement LLM answer synthesis.
5. Do not call external LLMs.
6. Do not summarize source text unless explicitly marked as derived.
7. Do not discard original source text.
8. Do not mutate source artifact content after ingestion.
9. Do not silently ignore parsing errors.
10. Every public class/function must have a docstring.
11. Every endpoint must have tests.
12. Every parser behavior must have tests.
13. Status docs must be updated before phase completion.
14. Phase 2 audit must be created before phase completion.
```

---

# Core Flow

```text
Input text/Markdown file
  ↓
Artifact created
  ↓
Raw source stored or referenced
  ↓
Parser reads structure
  ↓
EvidenceUnits created
  ↓
EvidenceUnits preserve source text and location
  ↓
API allows inspection
```

---

# Key Concepts

## Artifact
An Artifact represents the original source object.

For Phase 2, supported artifact types are:

```text
text
markdown
```

Example Artifact:

```json
{
  "id": "artifact_001",
  "filename": "rag_notes.md",
  "title": "RAG Notes",
  "artifact_type": "markdown",
  "mime_type": "text/markdown",
  "storage_uri": "local://artifacts/rag_notes.md",
  "checksum": "sha256...",
  "metadata": {
    "ingestion_phase": "phase_2_text_first_ingestion"
  }
}
```

---

## EvidenceUnit
An EvidenceUnit represents a source-backed unit of usable evidence.

For Phase 2, most EvidenceUnits should use:

```text
source_fidelity = verbatim
```

Example EvidenceUnit:

```json
{
  "id": "ev_001",
  "artifact_id": "artifact_001",
  "modality": "text",
  "content_type": "paragraph",
  "text": "GraphClerk searches meaning first, then retrieves evidence.",
  "location": {
    "section_path": ["Architecture", "Retrieval"],
    "line_start": 12,
    "line_end": 14,
    "block_index": 3
  },
  "source_fidelity": "verbatim",
  "confidence": 1.0,
  "metadata": {}
}
```

---

# EvidenceUnit Content Types For Phase 2

Supported content types should include:

```text
heading
paragraph
list_item
code_block
blockquote
table_text
raw_text_block
```

Optional if simple to support:

```text
frontmatter
horizontal_rule
```

Do not overcomplicate Markdown parsing in this phase.

The goal is predictable evidence units, not perfect document understanding.

---

# Source Fidelity Rules

## verbatim
Exact source text copied from the original artifact.

Used for:

```text
paragraphs
headings
list items
code blocks
plain text blocks
```

## extracted
Text extracted from a source where extraction may introduce errors.

Not heavily used in Phase 2, but reserved for future modalities.

## derived
AI-generated or algorithmic interpretation.

Avoid in Phase 2 unless explicitly needed.

## computed
Hashes, metrics, embeddings, scores.

Not used for EvidenceUnit text in Phase 2.

---

# Source Preservation Requirements

Phase 2 must preserve source traceability.

Minimum requirements:

```text
- Artifact checksum is stored.
- Original content is stored or referenced.
- EvidenceUnit text matches the source block exactly where source_fidelity is verbatim.
- EvidenceUnit has location metadata when possible.
- EvidenceUnit links to Artifact.
```

Location metadata should include as much as reasonably possible:

```text
line_start
line_end
section_path
block_index
character_start optional
character_end optional
```

---

# Parser Design

## Plain Text Parser
The plain text parser should:

```text
- split content into paragraphs
- preserve blank-line block boundaries where useful
- create raw_text_block or paragraph evidence units
- track line numbers
```

It should not invent headings unless a simple, clearly documented heuristic is used.

## Markdown Parser
The Markdown parser should support:

```text
- headings
- paragraphs
- unordered lists
- ordered lists
- fenced code blocks
- blockquotes
- simple tables as table_text
```

The parser should track:

```text
current section path
line numbers
block index
content type
```

## Parser Output Contract
Parser output should be an internal structure before persistence.

Example:

```json
{
  "content_type": "paragraph",
  "text": "GraphClerk retrieves meaning first.",
  "location": {
    "section_path": ["Core Idea"],
    "line_start": 8,
    "line_end": 8,
    "block_index": 2
  },
  "source_fidelity": "verbatim",
  "confidence": 1.0
}
```

---

# API Endpoints For Phase 2

## Create artifact from upload

```text
POST /artifacts
```

Purpose:

```text
Upload or submit a text/Markdown artifact for ingestion.
```

Expected output:

```json
{
  "artifact_id": "artifact_001",
  "status": "ingested",
  "artifact_type": "markdown",
  "evidence_unit_count": 24
}
```

## Get artifact

```text
GET /artifacts/{artifact_id}
```

Purpose:

```text
Return artifact metadata.
```

## List artifacts

```text
GET /artifacts
```

Purpose:

```text
Return known artifacts with basic metadata.
```

## List evidence for artifact

```text
GET /artifacts/{artifact_id}/evidence
```

Purpose:

```text
Return evidence units created from an artifact.
```

## Get evidence unit

```text
GET /evidence-units/{evidence_unit_id}
```

Purpose:

```text
Return one evidence unit.
```

---

# Services To Implement

## ArtifactService
Responsible for:

```text
- artifact creation
- checksum calculation
- artifact metadata persistence
- raw source storage/reference
- artifact retrieval
```

Forbidden:

```text
- parsing content directly
- creating graph nodes
- generating embeddings
- calling LLMs
```

## TextIngestionService
Responsible for:

```text
- orchestrating text/Markdown ingestion
- selecting correct parser
- creating evidence units from parser output
- handling ingestion errors explicitly
```

Forbidden:

```text
- graph construction
- semantic indexing
- answer generation
```

## MarkdownParser
Responsible for:

```text
- parsing Markdown into structured parser blocks
- preserving line/location metadata
```

## PlainTextParser
Responsible for:

```text
- parsing text into paragraph/raw text evidence blocks
- preserving line/location metadata
```

## EvidenceUnitService
Responsible for:

```text
- creating evidence units
- validating source fidelity
- retrieving evidence units
```

---

# Error Handling Requirements

Errors must be explicit.

Examples:

```text
UnsupportedArtifactTypeError
ArtifactNotFoundError
EvidenceUnitNotFoundError
IngestionParseError
InvalidSourceFidelityError
RawSourceStorageError
```

Do not silently return empty evidence when parsing fails.

If ingestion partially fails, the response should clearly indicate partial failure and the status docs should later reflect the behavior.

For Phase 2, it is acceptable to fail the whole ingestion if parsing fails.

---

# Required Tests

Minimum tests:

```text
test_create_text_artifact
test_create_markdown_artifact
test_artifact_checksum_is_stored
test_plain_text_ingestion_creates_evidence_units
test_markdown_ingestion_creates_heading_evidence_units
test_markdown_ingestion_creates_paragraph_evidence_units
test_markdown_ingestion_preserves_code_blocks
test_markdown_ingestion_preserves_list_items
test_evidence_unit_links_to_artifact
test_verbatim_evidence_matches_source_text
test_evidence_unit_location_metadata_exists
test_get_artifact_endpoint
test_list_artifacts_endpoint
test_list_artifact_evidence_endpoint
test_get_evidence_unit_endpoint
test_unsupported_file_type_fails_clearly
```

Optional tests:

```text
test_markdown_table_stored_as_table_text
test_duplicate_artifact_checksum_detection
test_ingestion_error_does_not_create_orphan_evidence_units
test_parser_tracks_section_path
```

---

# Documentation Requirements

Phase 2 must create or update:

```text
docs/phases/PHASE_2_TEXT_FIRST_INGESTION.md
docs/status/PROJECT_STATUS.md
docs/status/PHASE_STATUS.md
docs/status/KNOWN_GAPS.md
docs/status/TECHNICAL_DEBT.md
docs/audits/PHASE_2_AUDIT.md
README.md
```

## README Must Say

```text
Implemented:
- Text artifact ingestion
- Markdown artifact ingestion
- EvidenceUnit creation
- source traceability for text/Markdown

Not implemented yet:
- PDF ingestion
- PowerPoint ingestion
- multimodal ingestion
- semantic index search
- graph traversal
- File Clerk retrieval packets
- LLM answer synthesis
- UI
```

No README language should imply that GraphClerk can answer questions yet.

---

# Status Document Requirements

`PROJECT_STATUS.md` should update the current state.

Example:

```text
Current phase: Phase 2 — Text-First Ingestion

Implemented:
- Artifact creation for text and Markdown
- EvidenceUnit generation
- source fidelity tracking
- evidence inspection APIs

Not implemented:
- embeddings
- graph traversal
- retrieval packets
- LLM answer synthesis
- multimodal extraction
```

`KNOWN_GAPS.md` should include:

```text
- Markdown parsing is structural, not semantic.
- Markdown tables are stored as text, not interpreted.
- No PDF support yet.
- No automatic claim extraction yet.
- No semantic indexes yet.
```

`TECHNICAL_DEBT.md` should include any accepted shortcuts.

---

# Phase 2 Audit Requirements

Create:

```text
docs/audits/PHASE_2_AUDIT.md
```

Audit must answer:

```text
- Did Phase 2 preserve source artifacts?
- Did every EvidenceUnit link to an Artifact?
- Were any summaries stored as verbatim evidence incorrectly?
- Were any future phase features implemented early?
- Are all ingestion endpoints tested?
- Are parser behaviors tested?
- Does README overclaim?
- Are known gaps listed?
- Were dependencies added and documented?
```

Allowed audit result:

```text
pass
pass_with_notes
needs_fix
blocked
```

Phase 2 is not complete if audit result is `needs_fix` or `blocked`.

---

# Implementation Tasks

## Task 1 — Add artifact API endpoints
Implement:

```text
POST /artifacts
GET /artifacts
GET /artifacts/{artifact_id}
```

Acceptance:

```text
- text/Markdown artifacts can be created
- artifacts can be listed
- artifact metadata can be retrieved
```

## Task 2 — Implement checksum and raw source storage/reference
Add checksum calculation and raw content preservation.

Acceptance:

```text
- checksum is stored
- original source can be recovered or referenced
- no source overwrite occurs
```

## Task 3 — Implement PlainTextParser
Parse plain text into evidence blocks.

Acceptance:

```text
- paragraphs/raw blocks are created
- line metadata exists
- source text is preserved
```

## Task 4 — Implement MarkdownParser
Parse Markdown into evidence blocks.

Acceptance:

```text
- headings are captured
- paragraphs are captured
- lists are captured
- fenced code blocks are captured
- section path metadata exists
```

## Task 5 — Implement EvidenceUnitService
Create and retrieve EvidenceUnits.

Acceptance:

```text
- EvidenceUnits validate source_fidelity
- EvidenceUnits link to Artifact
- EvidenceUnits can be listed by artifact
```

## Task 6 — Implement TextIngestionService
Orchestrate artifact creation, parser selection, and evidence creation.

Acceptance:

```text
- text ingestion works end to end
- Markdown ingestion works end to end
- parser errors fail clearly
```

## Task 7 — Add evidence API endpoints
Implement:

```text
GET /artifacts/{artifact_id}/evidence
GET /evidence-units/{evidence_unit_id}
```

Acceptance:

```text
- evidence units can be inspected through API
```

## Task 8 — Add required tests
Implement all required tests for Phase 2.

Acceptance:

```text
- pytest passes
- ingestion source preservation is tested
```

## Task 9 — Update docs and status
Update README, phase docs, status docs, known gaps, and technical debt.

Acceptance:

```text
- documentation matches actual implemented behavior
- limitations are clear
```

## Task 10 — Add Phase 2 audit
Create the Phase 2 audit file.

Acceptance:

```text
- audit result is pass or pass_with_notes
```

---

# Cursor Prompt Template For Phase 2 Tasks

Every Cursor prompt for this phase should begin with:

```text
You are working on GraphClerk Phase 2 — Text-First Ingestion and Evidence Units.
You must follow docs/governance/*.
Do not implement PDF, PowerPoint, image, audio, video, embeddings, semantic search, graph traversal, File Clerk logic, retrieval packets, LLM answer synthesis, or UI.
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
At the end of Phase 2:

```text
- Text artifact ingestion
- Markdown artifact ingestion
- Artifact inspection APIs
- EvidenceUnit creation
- EvidenceUnit inspection APIs
- Source preservation
- Source location metadata
- Parser tests
- Ingestion tests
- API tests
- Phase 2 documentation
- Phase 2 status update
- Phase 2 audit
```

---

# Acceptance Criteria

```text
Given a plain text file,
when it is ingested,
then an Artifact is created and EvidenceUnits are generated.

Given a Markdown file,
when it is ingested,
then headings, paragraphs, lists, and code blocks become EvidenceUnits.

Given a verbatim EvidenceUnit,
when its text is compared to the original source block,
then the text matches.

Given an EvidenceUnit,
then it links to its source Artifact.

Given an Artifact,
then its evidence units can be listed through the API.

Given an unsupported file type,
then ingestion fails clearly.

Given pytest is run,
then all Phase 2 tests pass.

Given docs are inspected,
then they do not claim semantic search, graph traversal, or answer generation exists.

Given the Phase 2 audit is inspected,
then the result is pass or pass_with_notes.
```

---

# Known Non-Features After Phase 2

After this phase, GraphClerk still cannot:

```text
- ingest PDFs
- ingest PowerPoints
- ingest images
- ingest audio
- ingest video
- generate embeddings
- search semantic indexes
- traverse the graph
- create retrieval packets
- answer questions
- provide UI
```

This is intentional.

---

# Risks

## Risk 1 — Bad source preservation
If source text cannot be recovered, future citations and evidence paths will be weak.

Mitigation:

```text
- checksum storage
- raw source preservation
- verbatim text tests
```

## Risk 2 — Parser complexity creep
Markdown parsing can become a rabbit hole.

Mitigation:

```text
- support basic Markdown only
- document limitations
- avoid semantic interpretation
```

## Risk 3 — Premature semantic extraction
Cursor may try to extract claims or create graph nodes.

Mitigation:

```text
- strict phase scope
- forbidden feature list
- audit check
```

## Risk 4 — Fake source fidelity
Derived or cleaned text might accidentally be marked verbatim.

Mitigation:

```text
- source_fidelity validation
- tests comparing source blocks
```

---

# Suggested Duration

```text
Fast mode: 1 day
Clean mode: 2–4 days
```

---

# Phase Completion Definition
Phase 2 is complete when text and Markdown artifacts can be ingested into traceable EvidenceUnits, source preservation is tested, APIs expose artifacts and evidence, status docs are honest, and the Phase 2 audit passes.

The output of this phase is a reliable source-to-evidence pipeline for text-based artifacts.

