# Phase 6 demo corpus

Short markdown used by `scripts/load_phase6_demo.py` to create a **traceable** demo chain:

Artifact → EvidenceUnit → GraphNode evidence link → SemanticIndex entry node.

## Retrieval trace hook

This paragraph exists so ingestion yields at least one evidence unit with stable text.
The demo loader attaches that evidence unit to a graph node and indexes from that node.

## Checklist

- One markdown artifact
- Graph nodes and an edge
- Node–evidence support link
- Semantic index pointing at an entry graph node
