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
- **Status**: implemented (**pass_with_notes**; see `docs/audits/PHASE_3_AUDIT.md`)

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
    - optional `POST /answer` (AnswerSynthesizer must consume packet only) — **not implemented** (deferred)
  - required tests + docs/status updates + Phase 4 audit
- **Status**: implemented (**pass_with_notes**; see `docs/audits/PHASE_4_AUDIT.md`)

## Phase 5 — Multimodal Ingestion
- **Defined in**: `docs/phases/graph_clerk_phase_5_multimodal_ingestion.md`
- **Goal**: normalize PDFs/slides/images/audio into `EvidenceUnit`s with correct `source_fidelity` where extraction exists; preserve honest handling for shells and unsupported types.
- **Status**: **in progress** / **partially implemented** (**not fully complete**)
- **Audit**: **pass_with_notes** (see `docs/audits/PHASE_5_AUDIT.md`; **not** a sign-off of full multimodal completion)
- **Delivered so far (implementation truth)**:
  - `EvidenceUnitCandidate` contract hardening
  - `ArtifactExtractor` protocol + `ExtractorRegistry`
  - multimodal routing shell + `ArtifactTypeResolver`
  - PDF basic text extraction (optional **`pdf`** / pypdf)
  - PPTX basic slide text extraction (optional **`pptx`** / python-pptx)
  - image/audio **validation shells** (optional **`image`** / Pillow, **`audio`** / mutagen) — **no** EvidenceUnits from image/audio yet
  - tests: File Clerk + graph + `POST /retrieve` compatibility for PDF/PPTX multimodal evidence; multimodal `POST /artifacts` HTTP error hardening
  - docs/status updates (this slice)
- **Remaining / not done** (non-exhaustive; see phase doc):
  - OCR, image captioning/visual summaries, audio transcription/ASR
  - image/audio extractors that emit `EvidenceUnit`s
  - video ingestion (unsupported / deferred)
  - further extraction quality, edge cases, and optional CI matrix for extras
- **Optional install (from `backend/`)**: `python -m pip install -e ".[pdf]"`, `".[pptx]"`, `".[image]"`, `".[audio]"`, or e.g. `python -m pip install -e ".[dev,pdf,pptx,image,audio]"`

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

## Later work (high level; Phases 3–4 already cover parts of this list)
- Semantic index **vector population** (auto-index on create, backfill jobs) — indexing/search APIs exist; population workflow remains a gap.
- **Embedding production adapter** wiring and calibration (Phase 3 placeholder today).
- **Optional** packet-only **`POST /answer`** / consumer (strictly separate from retrieval; not implemented).
- **UI** and demo tooling (Phase 6).

