# GraphClerk Phase 8 — Specialized Model Pipeline and Model Governance

## Status

Draft / proposed

## Phase Dependency

This phase should only start after:

```text
Phase 0 — Governance Baseline
Phase 1 — Foundation and Core Architecture
Phase 2 — Text-First Ingestion and Evidence Units
Phase 3 — Semantic Index and Graph Layer
Phase 4 — File Clerk and Retrieval Packets
Phase 5 — Multimodal Ingestion
Phase 6 — Productization, UI, Evaluation, and Hardening
Phase 7 — Context Intelligence: Language and Actor Context
```

Prerequisites before **starting Phase 8 implementation** (gated on prior phases; **not** assertions about the current repo unless `docs/status/*` explicitly says so):

```text
- Governance baseline, Cursor rules, coding/documentation standards, status reporting, and audit rules exist as living docs
- FastAPI backend, PostgreSQL, and Qdrant are operational for the deployment target
- Artifact and EvidenceUnit models exist; text/Markdown ingestion works
- Multimodal ingestion works at the **documented Phase 5** level (honest partials per status)
- Graph layer, semantic index search, FileClerk retrieval packets, context budget, and retrieval logs exist per their phase docs
- Phase 6 — **baseline accepted** per `docs/status/*` (e.g. audit **`pass_with_notes`** on record); **not** full enterprise or stretch closure; until that baseline exists Phase 8 remains **not_started**
- Phase 7 — **baseline accepted** per `docs/status/*` and [`docs/audits/PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md) (**`pass_with_notes`**): LanguageContext / ActorContext as **recording/metadata** without retrieval routing influence; **does not** require translation, production detector-by-default, or **Slice 7I** boosting (deferred/cancelled pending separate approval); this satisfies the **Phase 8 planning / dependency gate**; **Phase 8 implementation** stays **`not_started`** until explicitly kicked off and scoped
- Where Phase 7 implemented them: EvidenceUnits may carry language metadata; RetrievalPackets may record language_context and/or actor_context
- ActorContext remains a routing prior, not evidence
- LanguageContext remains metadata/routing context, not source truth
```

Cursor or any coding agent must not implement **Phase 8 product code** until Phase 7 **baseline** is **accepted** per `docs/status/*` and audits as above **and** Phase 8 receives an explicit implementation kickoff; **Phase 8** remains **`not_started`** until then.

---

## Purpose

Phase 8 introduces a controlled specialized-model architecture for GraphClerk after the Phase 7 context-intelligence layer.

Phase 7 teaches GraphClerk to represent language and actor context explicitly without treating context as evidence. Phase 8 builds on that discipline by making model usage explicit, specialized, traceable, and role-bound.

The goal is to avoid using one large general-purpose model for every task.

GraphClerk should prefer narrow local models for modality-specific extraction and only use larger or more general models when cross-evidence interpretation is required.

The core idea:

```text
Use the smallest model that can reliably satisfy the contract.
Escalate only when the contract cannot be satisfied.
```

This phase exists because specialized smaller models have narrower responsibilities, simpler output contracts, lower drift risk, and clearer evaluation paths.

GraphClerk must not become:

```text
Artifact → big model → graph
```

GraphClerk should remain:

```text
Artifact
  ↓
modality-specific extraction
  ↓
EvidenceUnits
  ↓
language/context enrichment where applicable
  ↓
model-assisted interpretation
  ↓
IngestionProposals
  ↓
validation / review
  ↓
GraphNode / GraphEdge / SemanticIndex
```

---

## Core Objective

At the end of this phase, GraphClerk should have:

```text
- A model registry for specialized local models
- Separate model roles for extraction, transcription, vision, embedding, reranking, and interpretation
- Strict model output contracts per role
- A model routing layer that selects the correct model for each task
- Validation gates for every model output
- Evaluation metrics per model role
- Drift detection and contract-failure tracking
- Escalation rules from deterministic parser → specialized model → larger model → human review
- UI or logs showing which model produced which candidate output
- Documentation explaining why specialized models are preferred
- Explicit compatibility with Phase 7 LanguageContext and ActorContext
```

---

## Product Principle Preserved In This Phase

GraphClerk values traceability over model cleverness.

Phase 7 established that context can influence retrieval routes, but it must not become evidence. Phase 8 applies the same discipline to models: model output can extract, enrich, rank, or propose, but it must not silently become truth.

A model is not truth.

A model is an adapter that produces one of the following:

```text
- extracted EvidenceUnits
- derived EvidenceUnits
- embeddings
- reranking scores
- IngestionProposals
- interpretation metadata
- context-aware routing suggestions
```

Only validated services may persist accepted graph/index structures.

Models must never silently create source truth.

---

## Specialization Principle

GraphClerk prefers narrow local models for modality-specific extraction because narrow models reduce behavioral drift, simplify validation, and preserve source-fidelity boundaries.

General models may be used for cross-evidence interpretation, but only after extracted EvidenceUnits exist and only to produce reviewable IngestionProposals.

Hard rule:

```text
A model may only output objects matching its assigned contract.
```

Examples:

```text
OCR model:
  may output image_ocr_text EvidenceUnit candidates
  may not create GraphNodes

Audio transcription model:
  may output timestamped transcript EvidenceUnit candidates
  may not create SemanticIndexes

Vision caption model:
  may output derived captions or visual summaries
  may not mark visual interpretation as verbatim truth

Embedding model:
  may output vectors
  may not summarize or interpret content

Reranker:
  may reorder candidate results
  may not invent new candidates

Ingestion understanding model:
  may propose nodes, edges, semantic indexes, and support links
  may not directly persist them
```

---

## Scope

### Included

```text
- ModelRole definitions
- ModelRegistry
- ModelAdapter contract
- Specialized extractor adapter contracts
- Model routing by task and modality
- Model output validation
- Model capability metadata
- Per-role evaluation metrics
- Drift and contract-failure logging
- Escalation policy
- Model usage traceability in logs/UI
- compatibility with Phase 7 language_context and actor_context
- optional model roles for language detection / translation proposal if explicitly scoped
- Configuration for Ollama and/or vLLM-backed local models
- Documentation and audit updates
```

### Excluded

```text
- Cloud-only model requirement
- Direct model writes to graph tables
- Autonomous agent loops
- Unreviewed graph construction
- Unbounded multimodal reasoning
- Replacing EvidenceUnits with summaries
- Replacing FileClerk RetrievalPackets with answer-only output
- Fine-tuning unless explicitly scoped later
- automatic persistent actor memory
- hidden personalization based on actor context
- source evidence translation marked as verbatim
- Production model serving cluster automation
```

---

## Non-Negotiable Rules

```text
1. Models must have explicit roles.
2. Models must have explicit output schemas.
3. Model output must be validated before use.
4. Model output must be traceable to input Artifact/EvidenceUnit IDs.
5. No model may write directly to GraphNode, GraphEdge, or SemanticIndex persistence.
6. Extraction models may only create EvidenceUnit candidates.
7. Interpretation models may only create IngestionProposals.
8. Source fidelity must be enforced after model output.
9. OCR/transcription output must be marked extracted.
10. Visual summaries/captions must be marked derived.
11. Embedding models may only output vectors.
12. Rerankers may only score or reorder candidates.
13. Escalation to larger models must be explicit and logged.
14. Human review must remain available for low-confidence or contract-failing outputs.
15. Drift and schema failures must be counted and inspectable.
16. No silent fallback may make a failed model call look successful.
17. ActorContext must remain a routing prior, not evidence.
18. LanguageContext must remain metadata/routing context, not source truth.
19. Any model-assisted query translation must be recorded in the RetrievalPacket.
20. No model may silently translate source evidence and mark it verbatim.
21. Every public class/function must have docstrings.
22. Tests must cover contract validation and failure behavior.
23. Status docs must be updated before phase completion.
24. Phase 8 audit must be created before phase completion.
```

---

## Core Architecture

```text
Artifact
  ↓
ModalityRouter
  ↓
Specialized Extraction Layer
  ├── TextExtractor
  ├── PdfTextExtractor
  ├── OcrExtractor
  ├── SlideExtractor
  ├── AudioTranscriber
  └── VisionCaptioner
  ↓
EvidenceUnitCandidate validation
  ↓
EvidenceEnrichmentService / LanguageContext metadata where applicable
  ↓
EvidenceUnits
  ↓
Understanding Layer
  ├── EvidenceClassifier
  ├── ClaimExtractor
  ├── RelationProposer
  ├── SemanticIndexProposer
  └── DeduplicationAssistant
  ↓
Phase 7 context-aware routing metadata may inform interpretation only if recorded
  ↓
IngestionProposal validation
  ↓
Review / approval / deterministic checks
  ↓
GraphNode / GraphEdge / SemanticIndex
  ↓
FileClerk
  ↓
RetrievalPacket
```

---

## Model Roles

### TextExtractor

Responsible for deterministic or model-assisted extraction from text-like sources.

Allowed output:

```text
EvidenceUnitCandidate[]
```

Forbidden:

```text
- GraphNodes
- GraphEdges
- SemanticIndexes
- final answers
```

---

### OcrExtractor

Responsible for extracting visible text from images, scanned PDFs, screenshots, and rendered slides.

Allowed output:

```text
image_ocr_text
pdf_page_ocr_text
video_keyframe_ocr_text
```

Required source_fidelity:

```text
extracted
```

Forbidden:

```text
- marking OCR output as verbatim
- creating graph structures
- interpreting diagrams beyond text extraction
```

---

### VisionCaptioner

Responsible for derived visual summaries, captions, and diagram descriptions.

Allowed output:

```text
image_caption
image_visual_summary
slide_visual_summary
video_keyframe_caption
```

Required source_fidelity:

```text
derived
```

Forbidden:

```text
- claiming visual interpretation is source truth
- creating graph structures directly
```

---

### AudioTranscriber

Responsible for timestamped speech transcription.

Allowed output:

```text
audio_transcript_segment
video_transcript_segment
```

Required source_fidelity:

```text
extracted
```

Forbidden:

```text
- marking transcription as verbatim unless a verified human transcript is provided
- creating graph structures
- summarizing as transcript
```

---

### EmbeddingModel

Responsible for vectorizing searchable text.

Allowed output:

```text
list[float]
```

Forbidden:

```text
- summaries
- claims
- semantic indexes
- graph structures
```

---

### Reranker

Responsible for scoring and ordering candidate retrieval results.

Allowed output:

```text
candidate_id
score
rank
reason optional
```

Forbidden:

```text
- adding new evidence candidates
- inventing missing candidates
- rewriting evidence content
```

---

### IngestionUnderstandingModel

Responsible for cross-evidence interpretation after EvidenceUnits exist.

This model may consider Phase 7 language metadata and allowed actor/request context only as interpretation metadata. It must not treat actor context as source evidence.

Allowed output:

```text
IngestionProposal
CandidateGraphNode[]
CandidateGraphEdge[]
CandidateSemanticIndex[]
CandidateSupportLink[]
warnings[]
confidence
```

Forbidden:

```text
- direct graph persistence
- unsupported claims
- hidden source lookup
- hidden retrieval
- final answer generation
- treating ActorContext as evidence
- treating LanguageContext as source truth
```

---

## Suggested Local Models

Model names are implementation candidates, not hard requirements.

### Text / interpretation

```text
Qwen 2.5 / Qwen 3 Instruct 7B–14B
Mistral Small 3.x 24B for stronger interpretation
Gemma 3 4B/12B as comparison candidates
```

### Vision / images / diagrams / slides

```text
Qwen2.5-VL 7B
Gemma vision-capable models
Mistral vision-capable models where available
```

### Audio

```text
faster-whisper
whisper.cpp
local Whisper-compatible model
```

### Embeddings

```text
Qwen3-Embedding 0.6B / 4B
bge-m3
nomic-embed-text
```

### Reranking

```text
Qwen3-Reranker
bge-reranker
```

### Serving options

```text
Ollama first for local development
vLLM later for throughput, batching, and service deployment
```

---

## Escalation Policy

GraphClerk should use an explicit escalation ladder.

```text
1. deterministic parser
2. specialized extractor
3. small local model
4. stronger local model
5. human review
```

Escalation must be logged with a reason.

Example reasons:

```text
low_confidence
schema_validation_failed
unsupported_modality
ambiguous_visual_content
ocr_quality_low
transcription_quality_low
proposal_conflict
human_review_required
```

Forbidden:

```text
- silently retrying with a larger model without recording why
- using a larger model as default for every task
- accepting larger-model output without validation
```

---

## Model Registry

Phase 8 should introduce a model registry.

Example conceptual shape:

```json
{
  "model_id": "qwen2_5_14b_ingestion",
  "provider": "ollama",
  "role": "ingestion_understanding",
  "capabilities": ["structured_json", "text_reasoning"],
  "input_modalities": ["text"],
  "output_contract": "IngestionProposal",
  "default_temperature": 0.0,
  "max_context_tokens": 8192,
  "enabled": true
}
```

Required fields:

```text
model_id
provider
role
input_modalities
output_contract
enabled
configuration
```

Optional fields:

```text
capabilities
max_context_tokens
expected_latency_ms
memory_requirement
quality_notes
fallback_model_id
```

---

## Model Output Validation

Every model output must pass through validation.

Validation should check:

```text
- JSON/schema validity
- required fields
- allowed enum values
- source_fidelity correctness
- EvidenceUnit references exist
- Artifact references exist
- relation_type is allowed
- confidence range is valid
- no forbidden fields appear
- no final-answer prose appears where structured output is required
```

Invalid output must produce a visible error or review state.

It must not be silently coerced into accepted graph data.

---

## Drift Detection

Phase 8 should track model drift and contract instability.

Minimum metrics:

```text
model_calls_total
model_calls_failed
schema_validation_failures
contract_violation_count
low_confidence_outputs
human_review_required_count
accepted_proposal_count
rejected_proposal_count
average_confidence_by_model
average_latency_ms_by_model
escalation_count_by_reason
```

Drift indicators:

```text
- increasing schema failures
- increasing unsupported claims
- increasing human review rate
- decreasing acceptance rate
- inconsistent outputs for stable regression fixtures
```

---

## Evaluation Strategy

Each model role should have its own evaluation.

### OCR

```text
text extraction accuracy
coordinate/location quality
false text rate
empty extraction rate
```

### Audio transcription

```text
word error rate if references exist
timestamp quality
hallucinated transcript detection
empty segment rate
```

### Vision captioning

```text
caption usefulness
source_fidelity correctness
human review acceptance rate
visual hallucination rate
```

### Embedding model

```text
semantic retrieval hit rate
top-k relevance
latency
vector dimension consistency
```

### Reranker

```text
top-k ordering improvement
relevance lift over embedding-only ranking
latency impact
```

### Ingestion understanding model

```text
candidate node precision
candidate edge precision
support-link correctness
duplicate proposal rate
accepted proposal rate
human correction rate
```

---

## UI / Traceability Requirements

The UI or logs should show:

```text
- which model was used
- which role the model performed
- input Artifact/EvidenceUnit IDs
- output candidate IDs
- validation result
- confidence
- escalation reason if any
- accepted/rejected status
```

This should be visible in developer/admin views, not necessarily in the public query flow.

---

## Relationship With Phase 7 Context Intelligence

Phase 8 must remain compatible with Phase 7.

Phase 7 says:

```text
Context can influence retrieval routes, but it must not become evidence.
```

Phase 8 extends that rule to models:

```text
Models can use context to choose or explain a task route only when the influence is explicit, validated, and recorded.
```

Allowed:

```text
- ActorContext helps choose explanation depth for an IngestionProposal review view
- LanguageContext selects a language detection or query-variant model
- language metadata helps select multilingual embedding or reranking strategy
- model traces record that context was used
```

Forbidden:

```text
- ActorContext creates graph claims
- ActorContext bypasses authorization
- LanguageContext rewrites EvidenceUnit text
- translated source evidence is marked verbatim
- model calls use hidden context not recorded in traces or packets
```

---

## API / Service Components

Recommended components:

```text
ModelRegistryService
ModelRoutingService
ModelInvocationService
ModelOutputValidationService
ModelEvaluationService
ModelTraceService
EscalationPolicyService
ContextAwareModelRoutingService optional
```

Adapters:

```text
OllamaModelAdapter
VllmModelAdapter
WhisperTranscriptionAdapter
OcrAdapter
VisionModelAdapter
EmbeddingModelAdapter
RerankerAdapter
```

Schemas:

```text
ModelRole
ModelProvider
ModelCapability
ModelInvocationTrace
ModelValidationResult
ModelEscalationDecision
```

---

## Required Tests

Minimum tests:

```text
test_model_registry_registers_model_roles
test_model_registry_rejects_unknown_role
test_model_router_selects_text_extractor_for_text
test_model_router_selects_ocr_for_image_ocr
test_model_router_rejects_unsupported_modality
test_ocr_output_must_be_extracted_fidelity
test_vision_caption_output_must_be_derived_fidelity
test_audio_transcript_output_must_be_extracted_fidelity
test_embedding_model_output_must_be_vector_only
test_reranker_cannot_add_candidates
test_ingestion_model_outputs_proposal_only
test_model_output_validation_rejects_missing_evidence_ids
test_model_output_validation_rejects_invalid_relation_type
test_model_output_validation_rejects_direct_graph_write_shape
test_escalation_policy_logs_reason
test_schema_failure_does_not_create_graph_node
test_model_trace_records_model_id_and_role
test_actor_context_never_becomes_model_evidence
test_language_context_never_rewrites_evidence_text
test_model_assisted_translation_variant_is_recorded_when_used
```

Optional tests:

```text
test_fallback_model_used_after_schema_failure
test_human_review_required_after_repeated_failures
test_regression_fixture_output_stability
test_model_acceptance_rate_metric_updates
test_ui_model_trace_payload_shape
```

---

## Documentation Requirements

Phase 8 must create or update:

```text
docs/phases/PHASE_8_SPECIALIZED_MODEL_PIPELINE.md
docs/status/PROJECT_STATUS.md
docs/status/PHASE_STATUS.md
docs/status/KNOWN_GAPS.md
docs/status/TECHNICAL_DEBT.md
docs/audits/PHASE_8_AUDIT.md
docs/modeling/MODEL_ROLES.md
docs/modeling/MODEL_REGISTRY.md
docs/modeling/MODEL_EVALUATION.md
docs/modeling/MODEL_CONTEXT_COMPATIBILITY.md
```

Optional:

```text
docs/adr/ADR-000X-specialized-models-over-one-big-model.md
```

---

## README Must Say

```text
Implemented:
- Specialized model registry
- Role-based model routing
- Model output validation
- Model traceability
- Phase 7 context compatibility
- Escalation policy
- Per-role evaluation metrics

Limitations:
- Models propose, extract, enrich, rank, or route; they do not create truth directly
- Larger models may still be needed for difficult interpretation cases
- Human review remains required for low-confidence or high-impact graph changes
- Quality depends on local model configuration and hardware
```

Do not claim:

```text
- fully autonomous graph construction
- perfect OCR/transcription/vision understanding
- model outputs are source truth
- no human review is needed
```

---

## Phase 8 Audit Requirements

Create:

```text
docs/audits/PHASE_8_AUDIT.md
```

Audit must answer:

```text
- Are model roles explicit?
- Does every model role have an output contract?
- Can any model write directly to graph/index persistence?
- Are source_fidelity rules enforced for OCR, vision, and transcription?
- Are embeddings isolated from interpretation?
- Are rerankers prevented from inventing candidates?
- Are model calls traceable?
- Are validation failures visible?
- Are escalation decisions logged?
- Are per-role evaluation metrics present?
- Does README avoid claiming autonomous truth creation?
- Does Phase 8 preserve Phase 7's rule that ActorContext and LanguageContext are not evidence?
- Are model-assisted translations recorded and prevented from becoming verbatim evidence?
- Are known gaps listed?
```

Allowed audit result:

```text
pass
pass_with_notes
needs_fix
blocked
```

Phase 8 is not complete if audit result is `needs_fix` or `blocked`.

---

## Implementation Tasks

### Task 1 — Define model role contracts

Create controlled model roles and output contracts.

Acceptance:

```text
- ModelRole enum exists
- each role has allowed input/output shape
- forbidden behavior is documented
- tests cover unknown role rejection
```

---

### Task 2 — Implement ModelRegistry

Create a registry for local model configuration.

Acceptance:

```text
- models can be registered/configured
- roles and capabilities are explicit
- disabled models are not selected
- invalid model config fails clearly
```

---

### Task 3 — Implement ModelRoutingService

Route tasks to appropriate models based on modality and role.

Acceptance:

```text
- text extraction routes to text extractor
- image OCR routes to OCR model/tool
- audio routes to transcriber
- interpretation routes to ingestion understanding model
- unsupported modality fails clearly
```

---

### Task 4 — Implement output validators

Validate model outputs before use.

Acceptance:

```text
- EvidenceUnitCandidate outputs validate source_fidelity
- IngestionProposal outputs validate support EvidenceUnit IDs
- invalid relation types fail
- direct graph write shapes fail
```

---

### Task 5 — Implement model invocation traces

Record model calls and validation results.

Acceptance:

```text
- model_id recorded
- role recorded
- input references recorded
- output candidate references recorded
- validation status recorded
- latency recorded if available
```

---

### Task 6 — Implement escalation policy

Add deterministic escalation logic.

Acceptance:

```text
- low confidence can request escalation
- schema failure can request fallback
- repeated failure can require human review
- escalation reason is logged
```

---

### Task 7 — Add adapter interfaces

Create adapter interfaces for Ollama/vLLM and specialized tools.

Acceptance:

```text
- common ModelAdapter interface exists
- Ollama adapter can be configured
- vLLM adapter can be configured or stubbed explicitly
- unavailable adapters fail clearly
```

---

### Task 8 — Add per-role evaluation metrics

Track basic quality and reliability metrics.

Acceptance:

```text
- schema failures counted
- accepted/rejected proposals counted
- latency tracked
- human review count tracked
- metrics can be inspected
```

---

### Task 9 — Add admin/UI trace view if applicable

Expose model traces in UI or developer endpoint.

Acceptance:

```text
- user/developer can inspect which model produced which output
- validation errors are visible
- escalation reason is visible
```

---

### Task 10 — Update docs and audit

Update phase docs, status docs, known gaps, technical debt, and audit.

Acceptance:

```text
- documentation matches implementation
- limitations are explicit
- audit result is pass or pass_with_notes
```

---

## Acceptance Criteria

```text
Given a model task,
when the router selects a model,
then the selected model has an explicit role and output contract.

Given OCR output,
then source_fidelity must be extracted.

Given visual caption output,
then source_fidelity must be derived.

Given transcription output,
then source_fidelity must be extracted unless a verified human transcript is provided.

Given an embedding model,
then it can only return vectors.

Given a reranker,
then it can only score/reorder existing candidates.

Given an ingestion understanding model,
then it can only return IngestionProposals.

Given invalid model output,
then no GraphNode, GraphEdge, or SemanticIndex is created.

Given a fallback or escalation,
then the reason is logged.

Given model traces are inspected,
then the model id, role, input references, validation result, and output references are visible.

Given docs are inspected,
then they do not claim that model output is source truth or that graph construction is fully autonomous.
```

---

## Known Non-Features After Phase 8

After this phase, GraphClerk may still not support:

```text
- fully autonomous graph construction
- perfect OCR
- perfect transcription
- perfect visual understanding
- automatic trust in model-created graph proposals
- production-scale model serving
- fine-tuned GraphClerk-specific models
```

This is intentional.

---

## Risks

### Risk 1 — Model sprawl

Too many specialized models can become operationally messy.

Mitigation:

```text
- model registry
- enabled/disabled flags
- per-role default model
- documented fallback policy
```

### Risk 2 — Big model shortcut returns

A general model may slowly become responsible for everything.

Mitigation:

```text
- role-specific contracts
- forbidden output validation
- audit check for direct graph writes
```

### Risk 3 — Specialized model quality varies

Small models may be cheaper but worse on some content.

Mitigation:

```text
- evaluation metrics
- escalation policy
- human review fallback
```

### Risk 4 — Source fidelity confusion

OCR, vision captions, and transcripts may be mislabeled.

Mitigation:

```text
- validators enforce source_fidelity
- tests for modality-specific source_fidelity
- audit checks
```

### Risk 5 — Hidden drift

Models may change behavior after updates or quantization changes.

Mitigation:

```text
- model version tracking
- regression fixtures
- schema failure metrics
- acceptance/rejection tracking
```

---

## Suggested Duration

```text
Fast mode: 1–2 weeks
Clean mode: 3–5 weeks
```

Fast mode should prioritize:

```text
- ModelRole enum
- ModelRegistry
- ModelRoutingService
- output validation
- traces
- escalation policy
- documentation/audit
```

---

## Phase Completion Definition

Phase 8 is complete when GraphClerk can route model tasks through explicit specialized roles, validate every model output against role-specific contracts, preserve source-fidelity boundaries, log model usage and escalation, evaluate reliability per role, and document honestly that models extract or propose but do not create truth directly.

The output of this phase is controlled model specialization.

