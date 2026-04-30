# ADR-0002 — Semantic indexes are access paths, not truth

## Status
Proposed

## Context
Embeddings and vector search are useful, but they are lossy and can drift from source reality.

## Decision
`SemanticIndex` entries are **searchable entry points** into graph nodes. They are not the system of record.

## Consequences
- The graph and evidence units remain the authoritative representation.
- Index updates must not overwrite or replace source artifacts or evidence.

