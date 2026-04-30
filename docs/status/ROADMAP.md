# Roadmap

## Phase 0 — Governance Baseline
- Establish governance docs, protected terms, contracts, invariants, testing and documentation rules.
- **Status**: implemented

## Phase 1 — Foundation and Core Architecture
- **Defined in**: `docs/phases/graph_clerk_phase_1_foundation_core_architecture.md`
- **Goal**: build a stable technical spine (not RAG intelligence).
- **Deliverables**:
  - backend skeleton (FastAPI)
  - Docker Compose local boot
  - PostgreSQL connectivity
  - Qdrant connectivity
  - Alembic migrations
  - core persistence models: `Artifact`, `EvidenceUnit`, `GraphNode`, `GraphEdge`, `SemanticIndex`, `RetrievalLog`
  - infrastructure endpoints: `GET /health`, `GET /version`
  - baseline tests + Phase 1 audit + status doc updates
- **Status**: implemented (see `docs/phases/PHASE_1_FOUNDATION.md`)
- **Audit**: pass_with_notes (see `docs/audits/PHASE_1_AUDIT.md`)

## Phase 2 — Text-First Ingestion and Evidence Units
- **Defined in**: `docs/phases/graph_clerk_phase_2_text_first_ingestion_evidence_units.md`
- **Goal**: first real ingestion pipeline: `Artifact → EvidenceUnits` (text + Markdown only).
- **Deliverables**:
  - text and Markdown ingestion
  - raw source preservation + checksums
  - EvidenceUnit creation with location metadata and `source_fidelity` (mostly `verbatim`)
  - inspection APIs:
    - `POST /artifacts`
    - `GET /artifacts`
    - `GET /artifacts/{artifact_id}`
    - `GET /artifacts/{artifact_id}/evidence`
    - `GET /evidence-units/{evidence_unit_id}`
  - explicit error handling (no silent parsing failures)
  - required tests for source preservation + parser behavior
  - Phase 2 docs/status updates + Phase 2 audit
- **Status**: implemented
- **Audit**: pass_with_notes (see `docs/audits/PHASE_2_AUDIT.md`)

## Phase 3 — Semantic Index and Graph Layer
- **Defined in**: `docs/phases/graph_clerk_phase_3_semantic_index_and_graph_layer.md`
- **Goal**: add meaning-first search: `EvidenceUnits → Graph → SemanticIndex → Meaning-first Search`.
- **Deliverables**:
  - graph node/edge creation APIs/services
  - evidence support links for nodes/edges
  - semantic index creation + entry-point links
  - local-first embedding adapter + embedding service
  - Qdrant collection for semantic index vectors + vector upsert/search
  - semantic index search endpoint + entry-point resolution
  - bounded graph traversal (depth/max nodes/edges + relation filtering)
  - required tests + docs/status updates + Phase 3 audit
- **Status**: not_started

## Phase 4 — File Clerk and Retrieval Packets
- **Defined in**: `docs/phases/graph_clerk_phase_4_file_clerk_retrieval_packets.md`
- **Goal**: implement the File Clerk evidence-routing engine that returns structured `RetrievalPacket`s (not final prose).
- **Deliverables**:
  - `FileClerkService` orchestration
  - `RetrievalPacket` schema + contract tests
  - query intent classification (deterministic/local-first to start)
  - route selection (primary + alternatives), ambiguity representation
  - evidence collection from graph support links
  - explicit context budgeting + pruning reasons
  - retrieval logging updates
  - endpoints:
    - `POST /retrieve`
    - optional `POST /answer` (AnswerSynthesizer must consume packet only)
  - required tests + docs/status updates + Phase 4 audit
- **Status**: not_started

## Phase 5 — Multimodal Ingestion
- **Defined in**: `docs/phases/graph_clerk_phase_5_multimodal_ingestion.md`
- **Goal**: normalize PDFs/slides/images/audio/(optional video groundwork) into `EvidenceUnit`s with correct `source_fidelity`.
- **Deliverables**:
  - modality router + extractor adapter contracts
  - extractors (local-first):
    - PDF
    - PPTX
    - image (OCR/caption)
    - audio (transcription)
    - optional video groundwork (audio transcript, optional keyframes)
  - modality-specific evidence content types + location metadata
  - File Clerk packet compatibility with multimodal evidence metadata
  - explicit extractor failure behavior + required tests
  - docs/status updates + Phase 5 audit
- **Status**: not_started

## Phase 6 — Productization, UI, Evaluation, and Hardening
- **Defined in**: `docs/phases/graph_clerk_phase_6_productization_ui_evaluation_hardening.md`
- **Goal**: make GraphClerk usable/demo-ready and make retrieval trace visible.
- **Deliverables**:
  - frontend skeleton (React/Vite/TypeScript/Tailwind)
  - query playground + retrieval packet viewer (readable + raw JSON)
  - artifact/evidence viewers; semantic index explorer; graph explorer; retrieval log viewer
  - basic evaluation/comparison dashboard (honest, reproducible)
  - demo corpus + loader
  - API hardening pass (consistent errors, clear failures)
  - onboarding docs + release checklist + Phase 6 audit
- **Status**: not_started

## Guardrails (apply to all phases)
- Do not overclaim in README/status docs.
- Keep retrieval separate from answer synthesis (packets first).
- No silent fallbacks; failures must be explicit.
- Protected terms/contracts require change-control.

## Later phases (high level)
- Semantic index population + search (indexes as access paths, not truth).
- Graph traversal logic with bounded context budgets.
- FileClerk retrieval packet assembly.
- Optional model adapters and answer synthesis (strictly separate from retrieval).
- UI (only after retrieval/packets are stable and audited).

