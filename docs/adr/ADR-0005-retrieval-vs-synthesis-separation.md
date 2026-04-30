# ADR-0005 — Separate retrieval packets from answer synthesis

## Status
Proposed

## Context
Systems that mix retrieval with answer generation often hide missing evidence and make failures hard to detect.

## Decision
Retrieval produces structured `RetrievalPacket`s. Answer synthesis consumes those packets and must not perform hidden retrieval.

## Consequences
- Better auditability and debuggability of evidence selection.
- Retrieval services cannot “paper over” missing support by generating prose.

