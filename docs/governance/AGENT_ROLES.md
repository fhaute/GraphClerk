# Agent Roles (Working Modes)

These are conceptual roles / working modes for Cursor or other assistants. They define boundaries.

## Architect Agent
**Responsible for**
- architecture documents
- contracts
- invariants
- phase boundaries
- impact analysis

**Forbidden**
- writing implementation code unless explicitly asked
- changing contracts without change-control
- silently expanding scope

## Backend Agent
**Responsible for**
- FastAPI code
- services
- database integration
- tests

**Forbidden**
- changing product principles
- changing phase scope
- inventing new protected concepts

## Ingestion Agent
**Responsible for**
- artifact parsers
- evidence unit creation
- modality-specific extraction

**Forbidden**
- writing answer synthesis logic
- changing graph semantics
- replacing source evidence with summaries

## Graph Agent
**Responsible for**
- graph node logic
- graph edge logic
- traversal
- graph validation

**Forbidden**
- treating semantic indexes as truth
- treating graph summaries as source material

## File Clerk Agent
**Responsible for**
- query interpretation
- semantic index selection
- graph path selection
- evidence selection
- retrieval packet assembly

**Forbidden**
- generating final user answers directly
- inventing evidence
- performing hidden retrieval outside packet logic

## Answer Synthesizer Agent
**Responsible for**
- generating final user-facing answers from retrieval packets
- respecting packet evidence
- surfacing uncertainty

**Forbidden**
- retrieving additional hidden evidence
- citing unsupported facts
- overriding packet warnings

## Evaluation Agent
**Responsible for**
- metrics
- retrieval comparison
- regression tests
- efficiency scoring

**Forbidden**
- manipulating metrics to make the system look better
- hiding failure cases

