# ADR-0001 — Retrieve meaning before evidence

## Status
Proposed

## Context
Classic retrieval pipelines often fetch large amounts of loosely related content, leading to context bloat and weak grounding.

## Decision
GraphClerk will **search meaning first**, then follow graph paths to retrieve **source-backed evidence**.

## Consequences
- Retrieval prioritizes structured meaning and traceable evidence over raw similarity dumps.
- Semantic indexing is treated as an access path into the graph, not a truth source.

