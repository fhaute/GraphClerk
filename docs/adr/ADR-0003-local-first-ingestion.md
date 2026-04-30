# ADR-0003 — Local-first ingestion by default

## Status
Proposed

## Context
Many ingestion pipelines depend on external LLMs/OCR services, increasing cost, latency, and operational risk.

## Decision
Core ingestion is **local-first**. External LLMs are optional adapters, not mandatory dependencies.

## Consequences
- The system remains usable offline or in restricted environments.
- External model adapters, when enabled, must be explicit and auditable.

