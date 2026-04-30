# GraphClerk Phase 3 — Semantic Index and Graph Layer

## Phase Dependency
This phase must only start after:

```text
Phase 0 — Governance Baseline
Phase 1 — Foundation and Core Architecture
Phase 2 — Text-First Ingestion and Evidence Units
```

Phase 3 assumes:

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
- Alembic migrations work
- Artifact model exists
- EvidenceUnit model exists
- Text/Markdown ingestion works
- EvidenceUnits are source-backed and traceable
- Phase 2 tests pass
- Phase 2 audit is pass or pass_with_notes
```

Cursor must not implement this phase unless Phase 2 is complete and the status docs confirm it.

---

## Purpose
Add the meaning layer that makes GraphClerk different from normal chunk-based RAG.

This phase introduces:

```text
- Graph nodes
- Graph edges
- Evidence support links
- Semantic indexes
- Semantic index embeddings
- Meaning-first search
- Basic graph traversal
```

This phase proves the second core flow:

```text
EvidenceUnits → Graph → SemanticIndex → Meaning-first Search
```

---

## Core Objective
At the end of this phase, GraphClerk should be able to:

```text
- create graph nodes
- create graph edges
- link graph nodes/edges to EvidenceUnits
- create semantic indexes
- link semantic indexes to graph entry nodes
- generate embeddings for semantic indexes using a local-first embedding adapter
- store semantic index vectors in Qdrant
- search semantic indexes by user query
- resolve selected semantic indexes into graph entry nodes
- traverse the graph with bounded depth
- return graph paths and supporting evidence references
- test graph/index behavior
- document current limits
- update status docs
- produce a Phase 3 audit
```

This phase does **not** yet build the File Clerk retrieval packet or final answer synthesis.

---

## Product Principle Preserved In This Phase
GraphClerk searches meaning before evidence.

Normal RAG starts here:

```text
Question → chunk search
```

GraphClerk starts here:

```text
Question → semantic index search → graph entry points → evidence support
```

Semantic indexes are not truth.

They are meaning doors into the graph.

The graph is not the source artifact either.

The graph organizes source-backed meaning.

EvidenceUnits remain the link back to original source material.

---

## Scope

### Included

```text
- GraphNode creation API/service
- GraphEdge creation API/service
- Evidence support linking for graph nodes/edges
- SemanticIndex creation API/service
- SemanticIndex ↔ GraphNode entry-point links
- Local-first embedding adapter for semantic index text
- Qdrant collection for semantic index vectors
- Semantic index search endpoint
- Basic graph traversal endpoint/service
- Manual seed data support for demo graph
- Graph/index tests
- Status docs update
- Phase 3 audit
```

### Excluded

```text
- Automatic claim extraction from EvidenceUnits
- Automatic graph building from ingested documents
- Automatic semantic index generation
- File Clerk retrieval packets
- Query ambiguity handling
- Alternative interpretation packets
- LLM answer synthesis
- PDF/PowerPoint/image/audio/video ingestion
- UI
- Advanced graph ranking
- Agentic retrieval loops
```

---

## Non-Negotiable Rules For This Phase

```text
1. Do not implement File Clerk logic.
2. Do not implement retrieval packets.
3. Do not implement final answer generation.
4. Do not call external LLMs.
5. Do not create automatic graph extraction unless explicitly scoped later.
6. Do not treat semantic indexes as truth.
7. Do not create graph claims without optional support metadata when support exists.
8. Do not allow unbounded graph traversal.
9. Do not silently ignore missing graph nodes or invalid edges.
10. Every public class/function must have a docstring.
11. Every public endpoint must have tests.
12. Every graph traversal behavior must have tests.
13. Every embedding/vector behavior must have tests or a clearly isolated test adapter.
14. Status docs must be updated before phase completion.
15. Phase 3 audit must be created before phase completion.
```

---

# Core Flow

```text
Existing EvidenceUnits
  ↓
Manual or API-created GraphNodes
  ↓
Manual or API-created GraphEdges
  ↓
Graph nodes/edges linked to supporting EvidenceUnits
  ↓
SemanticIndexes created as meaning entry points
  ↓
SemanticIndexes embedded and stored in Qdrant
  ↓
User query searches SemanticIndexes
  ↓
Selected SemanticIndexes resolve to Graph entry nodes
  ↓
Bounded graph traversal returns nodes, edges, and evidence references
```

---

# Key Concepts

## GraphNode
A GraphNode represents structured meaning.

Possible node types:

```text
concept
claim
entity
artifact
source
technique
problem
decision
metric
modality
```

Example:

```json
{
  "id": "node_hybrid_retrieval",
  "node_type": "concept",
  "label": "Hybrid Retrieval",
  "summary": "Hybrid retrieval combines semantic and lexical search to improve evidence discovery.",
  "metadata": {}
}
```

### GraphNode Rules

```text
- A GraphNode may represent an interpretation of source evidence.
- A GraphNode does not replace the EvidenceUnit.
- Claim-like nodes should link to supporting EvidenceUnits when available.
- GraphNode labels should be specific enough to be useful.
```

Bad:

```text
AI
Documents
Search
```

Better:

```text
Hybrid Retrieval
Context Compression
Retrieval Confidence Gate
Semantic Index Entry Point
```

---

## GraphEdge
A GraphEdge represents a typed relationship between two GraphNodes.

Possible relation types:

```text
supports
explains
improves
causes
reduces
contradicts
depends_on
part_of
related_to
mentions
represents
has_source
```

Example:

```json
{
  "id": "edge_hybrid_retrieval_improves_recall",
  "from_node_id": "node_hybrid_retrieval",
  "to_node_id": "node_retrieval_recall",
  "relation_type": "improves",
  "summary": "Hybrid retrieval can improve recall by combining semantic and keyword search.",
  "confidence": 0.82,
  "supported_by": ["ev_001"]
}
```

### GraphEdge Rules

```text
- GraphEdge must connect valid existing GraphNodes.
- relation_type must be controlled.
- GraphEdge may link to supporting EvidenceUnits.
- GraphEdge must not contain hidden traversal logic.
```

---

## Evidence Support Link
GraphNodes and GraphEdges can be supported by EvidenceUnits.

This support link preserves traceability.

Suggested tables:

```text
graph_node_evidence
graph_edge_evidence
```

Example:

```json
{
  "graph_edge_id": "edge_hybrid_retrieval_improves_recall",
  "evidence_unit_id": "ev_001",
  "support_type": "supports",
  "confidence": 0.86
}
```

### Support Link Rules

```text
- Evidence support is not mandatory for every early demo node.
- But when a graph object is making a claim, support should be added when available.
- Unsupported graph objects should be clearly identifiable.
- No graph object should pretend to be source truth without evidence support.
```

---

## SemanticIndex
A SemanticIndex is a searchable meaning entry point into the graph.

It exists to match user intent to graph regions.

It is not truth.

Example:

```json
{
  "id": "idx_reduce_rag_hallucination",
  "meaning": "Ways to reduce hallucination in RAG systems",
  "summary": "This index connects grounding, retrieval confidence, reranking, hybrid search, and source citation.",
  "embedding_text": "Reduce hallucination in RAG by improving grounding, retrieval precision, reranking, hybrid retrieval, confidence gates, and source citation.",
  "entry_node_ids": [
    "node_hallucination",
    "node_grounding",
    "node_reranking",
    "node_hybrid_retrieval"
  ]
}
```

### SemanticIndex Rules

```text
- SemanticIndex is an access path.
- SemanticIndex must resolve to one or more GraphNodes.
- embedding_text should match how users ask questions.
- SemanticIndex summaries should not replace evidence.
- A GraphNode can appear in multiple SemanticIndexes.
```

---

# Embedding Strategy For Phase 3

Phase 3 introduces embeddings only for SemanticIndexes.

Do not embed all EvidenceUnits yet unless explicitly added later.

## Local-First Rule
The embedding service should prefer local/open models.

Possible early options:

```text
sentence-transformers
FastEmbed via Qdrant
Ollama embeddings
```

The adapter should be swappable.

## EmbeddingAdapter Contract
Suggested interface:

```python
class EmbeddingAdapter:
    """Generate vector embeddings for searchable text.

    Implementations must be deterministic for the same configured model
    where possible and must raise explicit errors when embedding generation
    fails.
    """

    def embed_text(self, text: str) -> list[float]:
        """Return an embedding vector for the provided text."""
```

## Embedding Rules

```text
- No external LLM dependency required.
- Embedding model/provider must be documented.
- Embedding dimension must be stored/configured.
- Failures must be explicit.
- Tests may use a deterministic fake adapter, but production code must not fake embeddings silently.
```

---

# Qdrant Collection For Phase 3

Create a Qdrant collection for semantic indexes.

Suggested collection name:

```text
semantic_indexes
```

Each vector payload should include:

```text
semantic_index_id
meaning
summary optional
entry_node_ids optional
```

Qdrant is used only for search in this phase.

PostgreSQL remains the source of structured metadata.

---

# Search Flow

```text
1. User submits query text.
2. EmbeddingAdapter embeds the query.
3. Qdrant searches semantic_indexes collection.
4. Top matching SemanticIndexes are returned.
5. PostgreSQL loads SemanticIndex metadata.
6. Entry GraphNodes are resolved.
7. GraphTraversalService traverses bounded graph neighborhood.
8. Result includes nodes, edges, and evidence support references.
```

---

# Graph Traversal Rules

Traversal must be bounded.

Minimum controls:

```text
depth
max_nodes
max_edges
allowed_relation_types optional
blocked_relation_types optional
```

Recommended defaults:

```text
depth = 1
max_nodes = 25
max_edges = 50
```

Phase 3 traversal should be simple and deterministic.

No agentic planning yet.

No LLM reasoning yet.

---

# API Endpoints For Phase 3

## Create graph node

```text
POST /graph/nodes
```

## Get graph node

```text
GET /graph/nodes/{node_id}
```

## List graph nodes

```text
GET /graph/nodes
```

## Create graph edge

```text
POST /graph/edges
```

## Get graph edge

```text
GET /graph/edges/{edge_id}
```

## List graph edges

```text
GET /graph/edges
```

## Attach evidence to graph node

```text
POST /graph/nodes/{node_id}/evidence
```

## Attach evidence to graph edge

```text
POST /graph/edges/{edge_id}/evidence
```

## Create semantic index

```text
POST /semantic-indexes
```

## Get semantic index

```text
GET /semantic-indexes/{semantic_index_id}
```

## Search semantic indexes

```text
GET /semantic-indexes/search?q=...&limit=5
```

## Resolve semantic index entry points

```text
GET /semantic-indexes/{semantic_index_id}/entry-points
```

## Traverse graph from node

```text
GET /graph/nodes/{node_id}/neighborhood?depth=1&max_nodes=25
```

---

# Services To Implement

## GraphService
Responsible for:

```text
- creating graph nodes
- creating graph edges
- validating relation types
- validating node existence
- retrieving graph objects
```

Forbidden:

```text
- semantic index search
- answer generation
- File Clerk packet assembly
```

## GraphEvidenceService
Responsible for:

```text
- linking EvidenceUnits to GraphNodes
- linking EvidenceUnits to GraphEdges
- validating support links
```

Forbidden:

```text
- modifying EvidenceUnit source text
- creating graph claims automatically
```

## SemanticIndexService
Responsible for:

```text
- creating SemanticIndexes
- linking SemanticIndexes to entry GraphNodes
- preparing embedding_text
- storing metadata in PostgreSQL
```

Forbidden:

```text
- treating SemanticIndex as source truth
- creating final retrieval packets
```

## EmbeddingService
Responsible for:

```text
- calling configured EmbeddingAdapter
- validating embedding dimensions
- returning explicit errors
```

## VectorIndexService
Responsible for:

```text
- creating Qdrant collection if needed
- upserting SemanticIndex vectors
- searching SemanticIndex vectors
```

## GraphTraversalService
Responsible for:

```text
- bounded traversal from entry nodes
- relation filtering
- max node/edge limits
- returning traversal results
```

Forbidden:

```text
- LLM reasoning
- final answer generation
- hidden retrieval outside provided graph parameters
```

---

# Error Handling Requirements

Errors must be explicit.

Examples:

```text
GraphNodeNotFoundError
GraphEdgeNotFoundError
InvalidRelationTypeError
InvalidGraphEdgeError
EvidenceUnitNotFoundError
SemanticIndexNotFoundError
SemanticIndexHasNoEntryNodesError
EmbeddingGenerationError
VectorIndexUnavailableError
GraphTraversalLimitError
```

Do not silently return empty results when the request is invalid.

Empty search results are allowed when no semantic index matches, but should be represented clearly.

---

# Required Tests

Minimum tests:

```text
test_create_graph_node
test_get_graph_node
test_create_graph_edge
test_graph_edge_requires_valid_from_node
test_graph_edge_requires_valid_to_node
test_invalid_relation_type_fails
test_attach_evidence_to_graph_node
test_attach_evidence_to_graph_edge
test_create_semantic_index
test_semantic_index_requires_entry_node
test_semantic_index_embedding_is_stored
test_semantic_index_search_returns_matches
test_semantic_index_search_empty_result
test_resolve_semantic_index_entry_points
test_graph_traversal_depth_1
test_graph_traversal_respects_max_nodes
test_graph_traversal_respects_relation_filter
test_vector_index_unavailable_fails_clearly
```

Optional tests:

```text
test_graph_node_supported_by_evidence_roundtrip
test_graph_edge_supported_by_evidence_roundtrip
test_embedding_adapter_dimension_validation
test_semantic_index_update_reindexes_vector
test_delete_semantic_index_removes_or_disables_vector
```

---

# Documentation Requirements

Phase 3 must create or update:

```text
docs/phases/PHASE_3_SEMANTIC_INDEX_AND_GRAPH.md
docs/status/PROJECT_STATUS.md
docs/status/PHASE_STATUS.md
docs/status/KNOWN_GAPS.md
docs/status/TECHNICAL_DEBT.md
docs/audits/PHASE_3_AUDIT.md
README.md
```

## README Must Say

```text
Implemented:
- Text/Markdown ingestion from Phase 2
- Graph nodes and graph edges
- Evidence support links
- Semantic indexes
- Local-first semantic index embeddings
- Semantic index search
- Basic bounded graph traversal

Not implemented yet:
- File Clerk retrieval packets
- answer synthesis
- automatic graph extraction
- multimodal ingestion
- UI
```

No README language should imply that GraphClerk can fully answer user questions yet.

---

# Status Document Requirements

`PROJECT_STATUS.md` should update the current state.

Example:

```text
Current phase: Phase 3 — Semantic Index and Graph Layer

Implemented:
- Graph node and edge persistence
- Evidence support links
- Semantic index creation
- Semantic index vector search
- basic graph traversal

Not implemented:
- File Clerk retrieval packets
- answer synthesis
- multimodal extraction
- automatic graph building
```

`KNOWN_GAPS.md` should include:

```text
- Graph nodes and edges are manually created in this phase.
- Semantic indexes are manually created in this phase.
- No automatic claim extraction yet.
- Graph traversal is bounded and simple.
- No ranking beyond semantic index vector score and traversal limits.
```

`TECHNICAL_DEBT.md` should include any accepted shortcuts.

---

# Phase 3 Audit Requirements

Create:

```text
docs/audits/PHASE_3_AUDIT.md
```

Audit must answer:

```text
- Did Phase 3 preserve the distinction between source evidence, graph meaning, and semantic indexes?
- Did any SemanticIndex become treated as source truth?
- Are graph nodes/edges linked to EvidenceUnits where support exists?
- Is graph traversal bounded?
- Were any File Clerk or answer synthesis features implemented early?
- Are semantic index embeddings local-first or adapter-based?
- Are vector failures explicit?
- Are all endpoints tested?
- Are known gaps listed?
- Does the README overclaim?
```

Allowed audit result:

```text
pass
pass_with_notes
needs_fix
blocked
```

Phase 3 is not complete if audit result is `needs_fix` or `blocked`.

---

# Implementation Tasks

## Task 1 — Finalize graph schemas and APIs
Implement graph node and edge creation/retrieval endpoints.

Acceptance:

```text
- graph nodes can be created and retrieved
- graph edges can be created and retrieved
- invalid relation types fail clearly
- invalid node references fail clearly
```

## Task 2 — Add graph evidence support links
Implement support links from graph nodes/edges to EvidenceUnits.

Acceptance:

```text
- graph node can link to EvidenceUnit
- graph edge can link to EvidenceUnit
- invalid EvidenceUnit references fail clearly
```

## Task 3 — Implement SemanticIndex persistence and APIs
Create semantic index model/service/endpoints.

Acceptance:

```text
- SemanticIndex can be created
- SemanticIndex requires at least one entry GraphNode
- SemanticIndex can be retrieved
```

## Task 4 — Implement EmbeddingAdapter and EmbeddingService
Create local-first embedding abstraction.

Acceptance:

```text
- embedding provider is configurable
- deterministic test adapter exists for tests
- production adapter does not fake embeddings silently
- dimension validation exists
```

## Task 5 — Implement VectorIndexService for Qdrant
Create semantic index collection and vector upsert/search.

Acceptance:

```text
- semantic index vectors are stored in Qdrant
- query vector search returns matching SemanticIndexes
- Qdrant failures are explicit
```

## Task 6 — Implement semantic index search endpoint
Implement:

```text
GET /semantic-indexes/search?q=...&limit=5
```

Acceptance:

```text
- query returns matching SemanticIndexes
- empty results are represented clearly
- endpoint is tested
```

## Task 7 — Implement entry-point resolution
Resolve SemanticIndex to GraphNodes.

Acceptance:

```text
- entry nodes are returned
- missing nodes fail clearly
```

## Task 8 — Implement bounded graph traversal
Implement GraphTraversalService.

Acceptance:

```text
- traversal supports depth
- traversal respects max_nodes/max_edges
- traversal can filter relation types
- traversal returns nodes, edges, and evidence support references
```

## Task 9 — Add manual seed data support
Add optional dev seed data for demo/testing.

Seed concepts could include:

```text
RAG
Hybrid Retrieval
BM25
Vector Search
Reranking
Hallucination
Grounding
Context Compression
Retrieval Packet
Semantic Index
Graph Traversal
Evidence Unit
```

Acceptance:

```text
- seed data can be loaded intentionally
- seed data is not required in production
```

## Task 10 — Add required tests
Implement all required tests for Phase 3.

Acceptance:

```text
- pytest passes
- graph/index/vector behavior is tested
```

## Task 11 — Update docs and status
Update README, phase docs, status docs, known gaps, and technical debt.

Acceptance:

```text
- documentation matches actual behavior
- limitations are clear
```

## Task 12 — Add Phase 3 audit
Create the Phase 3 audit file.

Acceptance:

```text
- audit result is pass or pass_with_notes
```

---

# Cursor Prompt Template For Phase 3 Tasks

Every Cursor prompt for this phase should begin with:

```text
You are working on GraphClerk Phase 3 — Semantic Index and Graph Layer.
You must follow docs/governance/*.
Do not implement File Clerk retrieval packets, final answer synthesis, LLM calls, multimodal ingestion, automatic graph extraction, or UI.
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
At the end of Phase 3:

```text
- Graph node APIs/services
- Graph edge APIs/services
- Evidence support links
- SemanticIndex APIs/services
- SemanticIndex entry-node links
- EmbeddingAdapter abstraction
- SemanticIndex vector storage in Qdrant
- SemanticIndex search
- Entry-point resolution
- Bounded graph traversal
- Required tests
- Phase 3 documentation
- Phase 3 status update
- Phase 3 audit
```

---

# Acceptance Criteria

```text
Given existing EvidenceUnits,
when a GraphNode or GraphEdge is created,
then it can link to supporting EvidenceUnits.

Given a SemanticIndex,
when it is created,
then it links to one or more graph entry nodes.

Given a user query,
when semantic index search is performed,
then matching SemanticIndexes are returned.

Given a SemanticIndex,
when entry points are resolved,
then the linked GraphNodes are returned.

Given a GraphNode,
when bounded traversal is requested,
then the system returns connected nodes, edges, and evidence references within limits.

Given Qdrant is unavailable,
then semantic index search fails clearly rather than pretending success.

Given pytest is run,
then all Phase 3 tests pass.

Given docs are inspected,
then they do not claim File Clerk packets, answer synthesis, automatic graph extraction, or multimodal ingestion exists.

Given the Phase 3 audit is inspected,
then the result is pass or pass_with_notes.
```

---

# Known Non-Features After Phase 3

After this phase, GraphClerk still cannot:

```text
- automatically extract claims from EvidenceUnits
- automatically build the graph
- assemble File Clerk retrieval packets
- handle query ambiguity in structured packets
- generate final answers
- ingest PDFs
- ingest PowerPoints
- ingest images
- ingest audio
- ingest video
- provide UI
```

This is intentional.

---

# Risks

## Risk 1 — SemanticIndex becomes fake truth
If SemanticIndexes are used as answers instead of access paths, the architecture breaks.

Mitigation:

```text
- enforce entry-node links
- keep evidence support separate
- audit distinction between index, graph, and evidence
```

## Risk 2 — Graph relation chaos
Too many uncontrolled relation types will make traversal unreliable.

Mitigation:

```text
- controlled relation type enum
- tests for invalid relation types
- document allowed relation types
```

## Risk 3 — Traversal explosion
Graph traversal can grow quickly.

Mitigation:

```text
- default depth = 1
- max_nodes
- max_edges
- relation filters
- traversal tests
```

## Risk 4 — Embedding provider lock-in
Hardcoding one embedding provider makes the system less flexible.

Mitigation:

```text
- EmbeddingAdapter interface
- provider configuration
- tests with deterministic adapter
```

## Risk 5 — Fake vector success
Tests or services may pretend vectors were stored/searched.

Mitigation:

```text
- explicit Qdrant connectivity tests
- no silent fake production behavior
- test adapter only in test scope
```

---

# Suggested Duration

```text
Fast mode: 2–4 days
Clean mode: 1–2 weeks
```

---

# Phase Completion Definition
Phase 3 is complete when GraphClerk can search semantic meaning entry points, resolve them into graph nodes, traverse the graph within limits, and return source-backed graph context without yet assembling final retrieval packets or answers.

The output of this phase is the meaning layer.

