# ADR-0004 — Evidence units as multimodal normalization

## Status
Proposed

## Context
Multimodal artifacts (PDFs, slides, images, audio, video) require a consistent unit of retrieval and traceability.

## Decision
All ingested modalities normalize into `EvidenceUnit`s, each traceable back to an `Artifact` and (when possible) a precise location.

## Consequences
- Retrieval and graph claims can require evidence support regardless of modality.
- Evidence units must carry source fidelity and confidence metadata.

