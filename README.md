# GraphClerk

GraphClerk is a **local-first, graph-guided evidence-routing layer for RAG systems**.

It is not a chatbot by itself. It does not try to replace RAG frameworks, vector databases, or LLMs.
It improves the layer between user intent and LLM context by returning **structured evidence packets**
with traceability to original source artifacts.

## Project principle
**Search meaning first, then retrieve evidence.**

## Governance first
This repository starts with Phase 0 governance guardrails. Technical implementation must not begin
until the governance baseline is present and committed.

- `docs/graph_clerk_phase_0_governance_baseline.md`: Phase 0 initialization document (source)
- `docs/governance/`: split governance documents used by prompts, reviews, and audits
- `docs/phases/PHASE_1_FOUNDATION.md`: Phase 1 implementation status and non-features
- `docs/phases/PHASE_2_TEXT_FIRST_INGESTION.md`: Phase 2 ingestion behavior (text/Markdown only)
- `docs/status/`: status tracking (honesty rules)
- `docs/adr/`: architecture decision records (ADRs)

