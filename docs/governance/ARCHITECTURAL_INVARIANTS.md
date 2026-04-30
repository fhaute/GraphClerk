# Architectural Invariants (Non-Negotiable)

## Invariant 1 — Source artifacts are immutable
Original artifact content must not be overwritten by derived summaries, extracted claims, embeddings, or graph structures.

## Invariant 2 — Evidence units are traceable
Every `EvidenceUnit` must link back to an `Artifact` and, when possible, to a specific source location.

## Invariant 3 — Semantic indexes are not truth
`SemanticIndex` records are searchable access paths into the graph. They are not the source of truth.

## Invariant 4 — Graph claims require support
Claim-like `GraphNode`s and meaningful `GraphEdge`s should link to supporting `EvidenceUnit`s whenever possible.

## Invariant 5 — File Clerk returns structured data
The retrieval layer returns `RetrievalPacket`s, not unstructured answer prose.

## Invariant 6 — Answer synthesis is separate from retrieval
The answer generator consumes `RetrievalPacket`s. It must not perform hidden retrieval.

## Invariant 7 — Multimodal content becomes evidence units
PDFs, slides, images, audio, and video must normalize into `EvidenceUnit`s.

## Invariant 8 — No silent fallbacks
If a parser, model, vector store, graph operation, or retrieval step fails, the system must expose the failure clearly.

## Invariant 9 — Local-first ingestion
External LLMs are optional adapters, not required core dependencies.

## Invariant 10 — Phase boundaries matter
A phase must not implement future phase scope unless the phase docs are updated first.

## Invariant 11 — Context budget must be explicit
Retrieval packets should manage evidence size intentionally. Context bloat is a failure mode.

## Invariant 12 — Ambiguity should be represented
When user intent is ambiguous, `RetrievalPacket`s should include alternatives instead of pretending certainty.

