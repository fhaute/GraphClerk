# GraphClerk pipeline — integration guide

| Field | Value |
|-------|--------|
| **Doc status** | **Overview — Track F F1** (+ F2 feed + F3 [`GRAPHCLERK_ARCHITECTURE.md`](GRAPHCLERK_ARCHITECTURE.md) + F4 [`TROUBLESHOOTING_AND_OPERATIONS.md`](TROUBLESHOOTING_AND_OPERATIONS.md)); not a complete cookbook. |
| **Last aligned to** | Phases **1–8** baseline as described in root `README.md` and `docs/status/*`; **Phase 9 not started**. |
| **Companion** | [`README.md`](../../README.md) in this folder — entry and links. |

---

## Audience

- **Backend / platform engineers** wiring GraphClerk into a RAG or evidence workflow.
- **Operators** running Docker, demos, and manual vector backfill.
- **Future contributors** who need one narrative before diving into `backend/` and `docs/phases/`.

---

## Current status of this guide

- **Implemented in F1:** section structure, core concepts, baseline flow steps, minimal vs rich, pointers to demo/scripts/docs, failure modes, integration patterns, security/honesty rules, explicit “not implemented” list, placeholders for later slices.
- **F2:** hands-on **PowerShell templates** in [`FEED_CONTENT_MINIMAL_GUIDE.md`](FEED_CONTENT_MINIMAL_GUIDE.md) (not duplicated here).
- **F3:** **Mermaid** as-built vs operator vs future diagrams + narrative in [`GRAPHCLERK_ARCHITECTURE.md`](GRAPHCLERK_ARCHITECTURE.md) (not duplicated here).
- **F4:** **Troubleshooting + operations** in [`TROUBLESHOOTING_AND_OPERATIONS.md`](TROUBLESHOOTING_AND_OPERATIONS.md) (not duplicated here).
- **Not yet implemented (future Track F slices):** full **curl** and **Python** cookbook (**F5**), production deployment deep-dive, multimodal ingestion how-tos, model pipeline wiring details beyond architecture labels, **`/answer`** documentation **if** the product approves and ships it.

---

## GraphClerk pipeline at a glance

For **components, stores, APIs, UI**, and **Mermaid** diagrams with explicit **`[current]`** / **`[manual/operator]`** / **`[future / not implemented]`** labels, see **[`GRAPHCLERK_ARCHITECTURE.md`](GRAPHCLERK_ARCHITECTURE.md)** (Track F Slice F3).

```text
User / system question
        │
        ▼
┌───────────────────┐     Ingest / structure (APIs)      ┌─────────────────┐
│ Artifacts         │ ────────────────────────────────►  │ EvidenceUnits   │
│ (+ graph, SI rows)│                                    │ GraphNodes/Edges│
└───────────────────┘                                    │ SemanticIndex  │
        │                                                  │ vector_status  │
        │  Manual vector indexing (operator)             └────────┬────────┘
        │  (not automatic on SI create)                            │
        ▼                                                          ▼
┌───────────────────┐                                    ┌─────────────────┐
│ Qdrant vectors    │ ◄── same embedding policy as search │ POST /retrieve  │
│ (indexed only)    │                                    │ RetrievalPacket │
└───────────────────┘                                    │ + logs / UI     │
                                                           └─────────────────┘
```

This is **evidence routing**, not answer synthesis. **`POST /answer`** is **not** in the product today.

---

## Core concepts

### Artifact

A **stored document or file** created via **`POST /artifacts`** (text/Markdown JSON body, or multipart for supported modalities). Source of truth for **raw content**; see Phase 2 and multimodal notes in [`docs/api/API_OVERVIEW.md`](../api/API_OVERVIEW.md).

### EvidenceUnit

A **traceable slice** of an artifact (or derived unit) used for retrieval and graph linking. Listed via **`GET /artifacts/{id}/evidence`**. Evidence is what the File Clerk can **route to** — not model prose.

### GraphNode

A **concept or entity** node in the knowledge graph. Created via **`POST /graph/nodes`**. Semantic indexes attach to the graph through **entry nodes**.

### GraphEdge

A **directed relationship** between nodes. **`POST /graph/edges`**. Optional evidence links on edges exist in the API surface.

### SemanticIndex

A **meaning-first index row**: `meaning`, optional `summary`, **`embedding_text`** (input to embeddings), **`entry_node_ids`**, metadata. Created via **`POST /semantic-indexes`**. **`GET /semantic-indexes/search`** considers **indexed** vectors only.

### `vector_status`

Per semantic index: typically **`pending`** after create until indexing succeeds (**`indexed`**) or fails (**`failed`**). **No automatic** transition on create — operator or integration must run indexing/backfill (Track B).

### RetrievalPacket

Structured JSON from **`POST /retrieve`**: intent, route, **`evidence_units`**, **`warnings`**, optional **Phase 7** `language_context` / `actor_context`, optional **Phase 8**-style **`graphclerk_model_pipeline`** metadata projection when present — **metadata for inspection**, not a second evidence source unless product docs say otherwise.

### RetrievalLog

**Best-effort** persistence of retrieve outcomes for inspection (**`GET /retrieval-logs`**). UI **Retrieval logs** tab; logging can fail without blocking the HTTP retrieve response (see Phase 6 docs).

### `language_context`

**Optional** packet field derived from **selected evidence metadata** — **context, not evidence**. Phase 7 baseline; see phase doc and status.

### `actor_context`

**Optional** request-supplied context on **`POST /retrieve`**, **recording only** on the packet — **not** used for boosting in the current baseline; do not treat as hidden personalization.

### `graphclerk_model_pipeline` metadata

**Phase 8** contract: **standalone metadata projection** for pipeline outputs where configured — **not** wired as automatic evidence in ingestion/File Clerk in the baseline described in status docs. Treat as **typed observability**, not a substitute for evidence units unless product scope changes.

---

## What GraphClerk does not do by default

| Topic | Status |
|-------|--------|
| **`POST /answer`** | **Not implemented** — no answer synthesis API in this repo state. |
| **Automatic vector backfill** on **`POST /semantic-indexes`** | **Not implemented** — use manual backfill / operator flow (below). |
| **Production model inference** inside core retrieve | **Not claimed** — Phase 8 baseline is contracts + validation + **NotConfigured** defaults; see `README.md` Phase 8 bullet. |
| **OCR / ASR / video ingestion** | **Not implemented** as full evidence pipelines; PDF/PPTX text paths exist when extras installed; image/audio largely **validation** / **503** where documented. |

---

## Baseline pipeline flow

1. **Start API, database, Qdrant** — e.g. `docker compose up` from repo root; default API host port **8010** (see root `README.md`).
2. **Ingest artifact** — **`POST /artifacts`** with text or supported file type.
3. **Inspect evidence units** — **`GET /artifacts/{artifact_id}/evidence`** (and detail endpoints per API overview).
4. **Create graph nodes / edges** — **`POST /graph/nodes`**, **`POST /graph/edges`**.
5. **Attach evidence to graph** — **`POST /graph/nodes/{node_id}/evidence`** (or edge variant).
6. **Create semantic index** — **`POST /semantic-indexes`** with `embedding_text` and `entry_node_ids`; expect **`vector_status=pending`** until indexing.
7. **Run manual vector indexing / backfill** — see *Manual vector indexing / backfill* below (**required** for semantic search hits on indexed-only paths).
8. **Retrieve packet** — **`POST /retrieve`** with a **`question`**; inspect **`evidence_units`** and **`warnings`**.
9. **Inspect retrieval logs** — **`GET /retrieval-logs`** when logging succeeds.
10. **Inspect UI** — see *UI inspection map* below (Query Playground, artifacts, graph, semantic indexes, logs, evaluation).

**Hands-on minimal path (F2):** step-by-step **PowerShell templates** (artifact → retrieve) live in [`FEED_CONTENT_MINIMAL_GUIDE.md`](FEED_CONTENT_MINIMAL_GUIDE.md); this file stays the **conceptual** overview.

---

## Minimal vs rich pipeline

| Mode | What you prove | Vector / evidence expectation |
|------|----------------|--------------------------------|
| **Minimal** | Control plane + valid **`RetrievalPacket`** + logs/UI visibility | **`evidence_units`** may be **empty**; **`vector_status`** may still be **`pending`**; **warnings** should be **honest**. |
| **Rich** | Meaning-first route with **non-empty** evidence | At least one **`SemanticIndex`** with **`vector_status=indexed`**, Qdrant aligned, question aligned with indexed meaning / embedding policy. |

See [`docs/demo/PHASE_6_DEMO_CORPUS.md`](../demo/PHASE_6_DEMO_CORPUS.md) — *Minimal vs rich demo* and *Policy decision (C5)*.

---

## Manual vector indexing / backfill

- **Script (repo root):** [`scripts/backfill_semantic_indexes.py`](../../scripts/backfill_semantic_indexes.py) — **`--help`**, **`--semantic-index-id`**, **`--all-pending`**; requires **`DATABASE_URL`** and **`QDRANT_URL`** aligned with the API. Uses **`DeterministicFakeEmbeddingAdapter` (dimension 8)** in the shipped script path — **dev/test**, not production semantics.
- **Demo doc:** [`docs/demo/PHASE_6_DEMO_CORPUS.md`](../demo/PHASE_6_DEMO_CORPUS.md) → *Manual vector indexing (rich demo — Track B Slice B1)* and *Qdrant collection `semantic_indexes` — vector dimension mismatch*.
- **Qdrant dimension mismatch:** if upserts fail after switching adapter/size, see [`docs/governance/TESTING_RULES.md`](../governance/TESTING_RULES.md) → *Qdrant `semantic_indexes` vector dimension mismatch* and [`docs/release/RELEASE_CHECKLIST.md`](../release/RELEASE_CHECKLIST.md) operator note.

---

## UI inspection map

| UI area | What to verify |
|---------|----------------|
| **Query Playground** | **`POST /retrieve`** packet shape, warnings, empty vs filled evidence. |
| **Artifacts & evidence** | Ingested artifacts and evidence units. |
| **Graph explorer** | Nodes, edges, evidence links. |
| **Semantic indexes** | **`vector_status`**, `embedding_text`, entry nodes; search only meaningful for **indexed**. |
| **Retrieval logs** | Stored packet snapshots when logging works. |
| **Evaluation dashboard** | Evaluation flows per [`docs/evaluation/EVALUATION_METHOD.md`](../evaluation/EVALUATION_METHOD.md) (honest scope). |

---

## Failure modes

**Expanded operator guide:** **[`TROUBLESHOOTING_AND_OPERATIONS.md`](TROUBLESHOOTING_AND_OPERATIONS.md)** (Track F Slice F4) — triage table, Qdrant lifecycle, HTTP codes, **`deterministic_fake`** pitfalls, runbooks, expected vs bug. The table below stays a **short** index.

| Symptom | Likely cause | Where to read |
|---------|--------------|---------------|
| Semantic route never hits | **`vector_status=pending`** or not **indexed** | Demo corpus *Minimal vs rich*; this guide baseline flow. |
| Qdrant errors / unavailable | Misconfigured **`QDRANT_URL`**, service down | API logs; `RELEASE_CHECKLIST`; `TESTING_RULES`. |
| Upsert dimension errors | Existing **`semantic_indexes`** collection **wrong vector size** | `TESTING_RULES` dimension mismatch section. |
| Search / retrieve embedding errors | **`NotConfigured`** embedding adapter for semantic search | `TESTING_RULES` — `GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER`; default **`not_configured`**. |
| Unsupported modality | Video / unsupported file path | `API_OVERVIEW`; Phase 5 docs; **503**/**400** behavior. |
| Empty **`evidence_units`** with 200 | Valid **minimal** outcome; check **warnings** and **`vector_status`** | File Clerk design; not automatically a bug. |

---

## Integration patterns

### GraphClerk as evidence-routing service

Your orchestrator calls **`POST /retrieve`**, receives a **`RetrievalPacket`**, then **your** layer decides prompts, citations, and model calls. GraphClerk **does not** hide that boundary.

### GraphClerk before an external LLM

Typical order: **retrieve packet → build prompt with explicit evidence snippets → call LLM**. Keeps **provenance** in user-visible or logged structures.

### GraphClerk without answer synthesis

Current default: **no `/answer`** — all “answer” behavior is **outside** this API unless Track **E** (or successor) ships.

### Future packet-only `/answer` (if approved)

Placeholder only — if implemented later, it must respect **packet-only** and **no FileClerk/DB fetch for hidden evidence** invariants (see [`docs/governance/ARCHITECTURAL_INVARIANTS.md`](../governance/ARCHITECTURAL_INVARIANTS.md)). **No commitment** in Phases **1–8** completion program without explicit track delivery.

---

## Security / honesty rules

- **Model output is not evidence** — only **evidence units** and governed artifact paths count as evidence for routing claims.
- **Context is not evidence** — `language_context`, `actor_context`, and similar fields are **interpretive metadata**; UI and docs must not equate them with provenance.
- **No silent fallbacks** — governance baseline; misconfigured adapters and modes **fail loud** where designed.
- **No `source_fidelity` override** — do not bypass ingestion fidelity rules (see invariants and phase docs).

---

## Placeholder sections (future slices)

The following are **intentional stubs** — links may point here until **F2–F5** or later tracks fill them in.

### curl examples

*To be added (Track F5 — examples cookbook):* representative **`curl`** sequences for artifacts → graph → semantic index → retrieve → logs. Until then, see [`FEED_CONTENT_MINIMAL_GUIDE.md`](FEED_CONTENT_MINIMAL_GUIDE.md) for **PowerShell / `Invoke-RestMethod`** templates (F2).

### Python client examples

*To be added:* minimal **`httpx` / `requests`** client patterns mirroring integration tests (without copying secrets).

### Architecture diagram

**Delivered (F3):** **[`GRAPHCLERK_ARCHITECTURE.md`](GRAPHCLERK_ARCHITECTURE.md)** — component + data-flow **Mermaid** (as-built vs **manual/operator** vs **future / not implemented**). This pipeline guide keeps the ASCII glance above for a quick read without opening that file.

### Production deployment notes

*To be added:* scaling, secrets, migrations, embedding provider choice, **separate** from dev **`DeterministicFakeEmbeddingAdapter`** paths. **Requires** product decisions not made in F1.

### OCR / ASR multimodal ingestion

*Deferred to Track A / Phase 5 completion narratives* — do not implement from this doc; link to phase/status when those ships.

### Model pipeline integration

*Phase 8 and beyond* — wire-up beyond metadata projection is **out of scope** for this skeleton; follow phase docs and **`KNOWN_GAPS`**.

### `/answer` (if approved)

*Track E or successor* — document only when shipped and audited; until then **`POST /answer`** remains **deferred** in [`docs/api/API_OVERVIEW.md`](../api/API_OVERVIEW.md).
