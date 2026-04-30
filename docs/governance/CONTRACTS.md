# Contracts (Protected Interfaces)

Contracts start high-level in Phase 0 and become stricter during implementation phases.

## Protected contracts
- Artifact Contract
- EvidenceUnit Contract
- GraphNode Contract
- GraphEdge Contract
- SemanticIndex Contract
- RetrievalPacket Contract
- FileClerk Contract
- ModelAdapter Contract
- IngestionPipeline Contract

## Contract format
Each contract should define:
- purpose
- required fields
- optional fields
- forbidden behavior
- lifecycle
- validation rules
- example JSON
- test expectations

## Artifact contract (summary)
An `Artifact` represents original source material (Markdown file, PDF, PowerPoint, image, audio, video, web page).

**Rules**
- Must preserve reference to original content.
- Must not be overwritten by derived data.

## EvidenceUnit contract (summary)
An `EvidenceUnit` is a source-backed piece of usable evidence extracted from an `Artifact`.

**Must include**
- `artifact_id`
- `modality`
- `content_type`
- `text` or a modality-specific representation
- location metadata when available
- `source_fidelity`
- `confidence`

### SourceFidelity values
- `verbatim`
- `extracted`
- `derived`
- `computed`

## SemanticIndex contract (summary)
A `SemanticIndex` is a searchable meaning entry point.

**Rules**
- Must point to graph nodes.
- Must not replace graph truth or source evidence.

## RetrievalPacket contract (summary)
A `RetrievalPacket` is the structured object returned by the File Clerk.

**Should include**
- `question`
- `interpreted_intent`
- `selected_indexes`
- `graph_paths`
- `evidence_units`
- `claims`
- `alternative_interpretations`
- `confidence`
- `warnings`
- `context_budget`
- `answer_mode`

