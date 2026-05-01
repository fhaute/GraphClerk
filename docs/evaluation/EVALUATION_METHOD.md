# Evaluation dashboard — method and limits

The Phase 6 **Evaluation** tab in `frontend/` helps inspect **retrieval behavior** using data already persisted by the backend. It does **not** grade answer quality.

## Data sources

- **`GET /retrieval-logs`** (list) and **`GET /retrieval-logs/{id}`** (detail).
- Stored **`RetrievalPacket`** JSON on log records when the backend wrote a snapshot.

## What the metrics are

- Counts and simple aggregates derived from **observable packet fields** (for example evidence unit counts, truncation flags, route labels where exposed).
- These are **observability / plumbing metrics**: they describe what the File Clerk returned and how it was logged — **not** accuracy, relevance, nDCG, human preference, or end-user task success.

## What the metrics are not

- **No LLM-as-judge** and no automated relevance scoring.
- **No hidden benchmark suite** or offline replay harness in the UI.
- **No naive baseline** comparison wired in the dashboard today (any future baseline must be documented honestly when added).

## Missing or invalid packets

- Logs without a stored packet, or JSON that does not parse to the expected shape, are counted or surfaced as failures/missing — the UI **does not** reconstruct or fabricate packets.

## Relation to `/answer`

- **`POST /answer`** is **not implemented**. The dashboard does **not** evaluate synthesized answers.

For product scope and honesty rules, see `docs/phases/graph_clerk_phase_6_productization_ui_evaluation_hardening.md`.
