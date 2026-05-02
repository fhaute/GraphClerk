# GraphClerk — troubleshooting and operations

| Field | Value |
|-------|--------|
| **Doc status** | **Track F Slice F4** — operator-facing failure modes and Qdrant/HTTP notes for the **current baseline** (Phases **1–8**). |
| **Not** | A production **SRE** runbook; **not** a source of new product behavior. |
| **Phase 9** | **Not started** — not covered here as shipped work. |

---

## Audience

Operators and developers diagnosing **empty packets**, **stuck `vector_status`**, **Qdrant/env** issues, and **HTTP errors** without reading the whole codebase.

---

## Quick triage table

| Symptom | Likely cause | First check | Expected or bug? | Where to read |
|---------|--------------|-------------|------------------|----------------|
| **`POST /retrieve`** **200** but **`evidence_units`** empty | **`pending`** SI, no indexed semantic hit, **`NotConfigured`** search embeddings, or question not aligned with route | **`warnings`**, **`vector_status`**, `GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER` | Usually **expected** (minimal pipeline) | [Expected vs bug](#expected-vs-bug); [`FEED_CONTENT_MINIMAL_GUIDE.md`](FEED_CONTENT_MINIMAL_GUIDE.md) |
| **`SemanticIndex.vector_status=pending`** | No successful manual indexing yet | After create, before backfill | **Expected** | [Semantic index lifecycle](#semantic-index-lifecycle) |
| **`SemanticIndex.vector_status=failed`** | Empty `embedding_text`, Qdrant/embedding error | `metadata_json.graphclerk_vector_indexing` on the SI row | **Expected** after a real failure; **bug** if Qdrant succeeded but row says failed | [Manual vector backfill failures](#manual-vector-backfill-failures) |
| **`GET /semantic-indexes/search`** empty list | No **indexed** match, or `q` empty / no hits | Indexed SIs exist; query text | Often **expected** | [`docs/api/API_OVERVIEW.md`](../api/API_OVERVIEW.md) |
| Backfill exits **1** / stderr **`DATABASE_URL` required** | Env not set in shell | `echo` / env pane | **Operator setup** | [Environment checklist](#environment-checklist) |
| Backfill exits **1** / **`QDRANT_URL` required** or connection errors | Env wrong or Qdrant down | `docker compose ps`, ping Qdrant | **Setup** until fixed | [Qdrant operations](#qdrant-operations) |
| Qdrant upsert / **VectorIndexOperationError** / dimension errors | Collection **`semantic_indexes`** size ≠ adapter **8** | `get_collection` / dashboard | **Setup** (stale collection) | [`TESTING_RULES.md`](../governance/TESTING_RULES.md) — dimension mismatch |
| **`deterministic_fake`** rejected at startup | **`APP_ENV=prod`** or **`RUN_INTEGRATION_TESTS` ≠ `1`** | [`backend/app/core/config.py`](../../backend/app/core/config.py) validator | **By design** | [Deterministic fake embedding mode](#deterministic-fake-embedding-mode) |
| **`test_config.py`** fails on adapter assertion | **`GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER`** leaked into shell | Unset var for that pytest run | **Test env pollution** | [`TESTING_RULES.md`](../governance/TESTING_RULES.md) — B5 / mixed suite note |
| Unsupported file → **400** / **503** | Modality not supported or optional extra missing | `API_OVERVIEW`; route **503** hints | **Expected** per route | [Modality support](#modality-support--unsupported-files) |
| **Retrieval log** row missing | Best-effort logging failed or disabled path | API logs; same retrieve still **200**? | **Can be expected** | [Retrieval logs expectations](#retrieval-logs-expectations) |
| Browser **cannot** reach API / “network” errors | Wrong host/port; Vite proxy; CORS if bypassing proxy | `8010` vs `8000`; `VITE_API_BASE_URL` / proxy target | **Setup** | Root [`README.md`](../../README.md) — Frontend |
| **422** on JSON body | Missing/invalid required fields | FastAPI detail | **Expected** validation | [HTTP error guide](#http-error-guide) |
| **404** on graph/evidence | Bad UUID or deleted row | IDs from latest `GET` | **Expected** if wrong id | [HTTP error guide](#http-error-guide) |
| **409** on node evidence link | Duplicate link | Use new node or EU | **Expected** | [HTTP error guide](#http-error-guide) |
| B5 full-stack test **skipped** | Gate env not set | `RUN_INTEGRATION_TESTS`, `DATABASE_URL`, `QDRANT_URL`, adapter, `APP_ENV` | **Expected** when not running integration | [`TESTING_RULES.md`](../governance/TESTING_RULES.md) |
| B5 first run **failed** indexing then **pass** after reset | Qdrant collection wrong dimension | Collection vector size vs **8** | **Setup** | [`RELEASE_CHECKLIST.md`](../release/RELEASE_CHECKLIST.md) B5.1 note |

---

## Expected vs bug

### Expected baseline behavior

- **`POST /retrieve`** returns **200** with **empty** `evidence_units` when semantic indexes are **`pending`**, when semantic search returns no indexed hit, when the default **`NotConfigured`** embedding adapter cannot embed the query (semantic path), or when the File Clerk honestly finds no graph-linked evidence — read **`warnings`** and packet fields instead of assuming failure.
- **`vector_status=pending`** immediately after **`POST /semantic-indexes`** — **automatic vector indexing on create is not implemented.**
- Default app config: **`GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER=not_configured`** — semantic search / query embedding for that path is **explicitly not a production embedding stack.**
- **No `POST /answer`** — answer synthesis is **out of scope** until a future track ships and audits it.
- **No OCR/ASR/video** as complete first-class evidence pipelines — Phase 5 is **partial**; see status/README.
- **RetrievalLog** may be **absent** for a given retrieve — logging is **best-effort**; the HTTP retrieve can still succeed.
- **`language_context`** is **metadata from selected evidence `metadata_json`**, **not** translation; the packet builder does **not** pull from **`Artifact.metadata_json["graphclerk_language_aggregation"]`** — that subtree is an **artifact-level** post-ingest summary (UI: **Artifacts & evidence** detail shows both raw metadata and a readable aggregation block when present).
- **`GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER=lingua`** requires the **`language-detector`** optional extra; if Lingua cannot be constructed, **`POST /artifacts`** returns **503** — **no** silent fallback to **`not_configured`** (see [`TESTING_RULES.md`](../governance/TESTING_RULES.md)).
- **Future (Track C):** optional **production** language detection is **not** in baseline installs; dependency choice and config policy are documented in [`docs/decisions/phase_7_language_detector_dependency_decision.md`](../decisions/phase_7_language_detector_dependency_decision.md) (**research only** until **C3** ships).
- **`actor_context`** is **recording-only** — it does **not** change routing or evidence selection.
- **`graphclerk_model_pipeline`** on the packet is a **standalone metadata projection** in the Phase **8** baseline — **not** automatically merged into File Clerk evidence selection.

### Likely bug (investigate / file issue)

- **`indexed`** semantic index, **aligned** deterministic dev env and question/text, **B5-style** path still never returns traceable evidence (regression candidate).
- Backfill/API reports **`indexed`** without a successful Qdrant upsert (integrity violation — should not happen if services are consistent).
- **`failed`** indexing with **no** diagnostic under `metadata_json.graphclerk_vector_indexing` when the code path should have written one.
- **`POST /retrieve`** fabricates or omits **`evidence_unit_id`** traceability contrary to invariants ([`ARCHITECTURAL_INVARIANTS.md`](../governance/ARCHITECTURAL_INVARIANTS.md)).
- **`deterministic_fake`** accepted when **`APP_ENV=prod`** (settings should **reject** at parse time).
- A live **`POST /answer`** route appears **without** Track **E**-style implementation and audit (today: **deferred**).

---

## Environment checklist

| Item | Typical value / note |
|------|----------------------|
| **Docker services** | **api**, **postgres**, **qdrant** — `docker compose ps` from repo root |
| **API base (host)** | **`http://localhost:8010`** (Compose publishes **8010→8000**) |
| **Qdrant (host)** | **`http://localhost:6333`** (per default Compose) |
| **Postgres (host port)** | **`5433→5432`** with default Compose user/db (see compose file — **no secrets** in this doc) |
| **`DATABASE_URL`** | Required for API container and for **`scripts/backfill_semantic_indexes.py`** |
| **`QDRANT_URL`** | Required; must match the Qdrant instance the API uses |
| **`RUN_INTEGRATION_TESTS`** | Must be **`1`** for **`deterministic_fake`** adapter validation (see config) |
| **`APP_ENV`** | **`local`**, **`dev`**, or **`test`** for non-prod; **`prod`** rejects **`deterministic_fake`** |
| **`GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER`** | Default **`not_configured`**; **`deterministic_fake`** only for guarded dev/integration |
| **`GRAPHCLERK_MODEL_PIPELINE_*`** | Adapter-key env (**D2**); **`ollama`** requires non-empty **`BASE_URL`** + **`MODEL`** or registry build fails (**`model_pipeline_ollama_misconfigured`**); default **`not_configured`** — **no** automatic model calls on ingest/retrieve ([`TESTING_RULES.md`](../governance/TESTING_RULES.md)). **Per-purpose** mapping is **D4** ([**D2.5**](../decisions/phase_8_model_pipeline_completion_decisions.md)). |

**When to unset `GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER`:** before running **mixed pytest** suites that expect the default adapter in process env (e.g. settings tests), or when switching shells to avoid accidental leakage — see [`TESTING_RULES.md`](../governance/TESTING_RULES.md).

---

## Qdrant operations

- **Postgres** holds **canonical** app rows (`vector_status`, `embedding_text`, graph links). **Qdrant** holds **vectors** for semantic search; payload is convenience metadata only.
- **Collection vector size is fixed** at **`semantic_indexes`** create time. `VectorIndexService.ensure_semantic_indexes_collection` **reuses** an existing collection and **does not** resize it.
- **Dimension mismatch** (e.g. collection created at size **3**, current stack uses **8** for deterministic fake / backfill) causes **upsert** failures → indexing outcome **`failed`** / `VectorIndexOperationError`-class handling.
- **Deterministic dev path** uses **dimension 8** (backfill script and factory when `deterministic_fake` is active).

### Dev-only remediation (destructive)

**Only disposable / local Qdrant:** deleting the **`semantic_indexes`** collection **removes all vectors** in that collection for that instance. There is **no** automatic migration tool in-repo today.

**Do not** run deletes against production without an approved runbook.

**Operator pattern:** after deletion, rerun **manual backfill** so the collection is **recreated** at the correct dimension. Step-by-step narrative: [`TESTING_RULES.md`](../governance/TESTING_RULES.md) — *Qdrant `semantic_indexes` vector dimension mismatch*; verification context: [`RELEASE_CHECKLIST.md`](../release/RELEASE_CHECKLIST.md).

**Dev-only REST template (verify URL and collection name before use):** some operators use Qdrant’s HTTP API, e.g. `DELETE /collections/semantic_indexes` against **`QDRANT_URL`**. **Template only** — confirm host, port, and auth (if any) match your dev instance; **never** assume a default without checking.

---

## Semantic index lifecycle

1. **`POST /semantic-indexes`** → row created; **`vector_status`** typically **`pending`** (**automatic indexing on create is not implemented**).
2. **Manual backfill** (script or in-process indexer) embeds **`embedding_text`**, upserts to Qdrant, updates Postgres.
3. **`indexed`** — success path; **`failed`** — empty text, embedding error, or vector/Qdrant error; diagnostics are merged under **`metadata_json["graphclerk_vector_indexing"]`** (see `SemanticIndexVectorIndexingService` / Track B B1).
4. **`GET /semantic-indexes/search`** returns hits from **indexed** vectors only — **`pending`** rows do not appear as search hits.

---

## Manual vector backfill failures

| Failure | Notes |
|---------|--------|
| **Empty `embedding_text`** | Row should become **`failed`** with explicit metadata — fix text, retry. |
| **DB connection errors** | Check **`DATABASE_URL`**, Postgres up, network. |
| **Qdrant unavailable** | Check **`QDRANT_URL`**, Qdrant container, firewall. |
| **Vector dimension mismatch** | [Qdrant operations](#qdrant-operations) — dev collection reset. |
| **Already `indexed` without `--force`** | Script/service **skips** re-upsert unless **`--force`** (re-upsert even if indexed — see script `--help`). |
| **Exit code `2`** | Script reports at least one **`failed`** outcome in batch mode — inspect printed lines and SI metadata. |
| **Semantics** | Script uses **`DeterministicFakeEmbeddingAdapter` (8 dims)** — **dev/test**, not production quality. |

---

## Retrieve / File Clerk symptoms

- **Empty `evidence_units` + honest `warnings`** — common **minimal** outcome; check **`vector_status`**, semantic search configuration, and graph/evidence linkage.
- **No semantic route** — no **indexed** hit for the question / embedding policy; or **`NotConfigured`** prevents query embedding for search (**503** on `GET /semantic-indexes/search` when that path raises).
- **Graph traversal** — bounded from **entry nodes** on selected semantic indexes; evidence must be **linked** on the graph path the File Clerk uses.
- **`actor_context`** — **recording-only** on the packet; **no** retrieval boost.
- **`language_context`** — aggregates from **selected evidence `metadata_json`** only; **not** translation; **not** sourced from **`graphclerk_language_aggregation`** on the artifact row.
- **`metadata_json.graphclerk_language_aggregation`** (artifact) — optional **ingest-time** summary over that artifact’s evidence units; compare to packet **`language_context`** only when debugging **ingest vs retrieve** visibility (they can differ if retrieve selects a different evidence set).
- **`graphclerk_model_pipeline`** — optional packet metadata for inspection; **not** wired into File Clerk selection in the baseline. **Real outbound model inference** on ingest/retrieve is **not** implemented until Completion Program **Track D D2+**; design record: [`docs/decisions/phase_8_model_pipeline_completion_decisions.md`](../decisions/phase_8_model_pipeline_completion_decisions.md).
- **No answer synthesis** — use your own LLM layer after the packet if needed.

---

## Retrieval logs expectations

- **Best-effort** — a successful **`POST /retrieve`** may occur **without** a persisted log row.
- Inspect via **`GET /retrieval-logs`** / **`GET /retrieval-logs/{id}`** and the **Retrieval logs** UI tab; detail includes **`retrieval_packet`** when stored.
- **Absence of a log** alone is **not** proof the retrieve failed.

---

## HTTP error guide

Statuses **vary by route**; always read the response **`detail`**. Common patterns:

| Code | Common meaning |
|------|----------------|
| **400** | Invalid business rules (e.g. unsupported artifact type, bad graph/SI payload) — see route docs. |
| **404** | Unknown artifact, node, evidence unit, semantic index, or retrieval log id. |
| **409** | Duplicate graph–evidence link where implemented. |
| **422** | Request body/query validation (FastAPI) — e.g. empty `question` on retrieve, empty search `q`. |
| **500** | Unexpected server error — e.g. **`POST /retrieve`** maps **`SemanticIndexSearchInconsistentIndexError`** to **500** with detail `semantic_index_search_inconsistent_index`; some embedding vector errors on search map to **500**. |
| **502** | **`GET /semantic-indexes/search`** maps **`VectorIndexOperationError`** to **502** (Qdrant/client operation failure). |
| **503** | **`ExtractorUnavailableError`** on multimodal ingest; **`EmbeddingAdapterNotConfiguredError`** on semantic search; **`VectorIndexUnavailableError`** — dependency or adapter not usable. |

**Frontend “network error” / CORS-like symptoms** — usually wrong **API URL**, proxy target (**`GRAPHCLERK_API_PROXY_TARGET`**), or browser blocked request; **not** always a GraphClerk logic bug.

See [`docs/api/API_OVERVIEW.md`](../api/API_OVERVIEW.md) and route modules for authoritative mapping.

---

## Modality support / unsupported files

- **Minimal path:** **`text`** / **`markdown`** inline JSON on **`POST /artifacts`**.
- **PDF/PPTX:** text extraction when optional **extras** are installed; otherwise **503** with install hints (see `API_OVERVIEW` / Phase 5).
- **Image/audio:** largely **validation** or **503** until OCR/ASR products exist — **do not** treat as full evidence producers.
- **Video:** **not** a supported ingest path for this troubleshooting doc’s expectations.
- An **unsupported** upload is often **expected** API behavior, not “GraphClerk routing is broken.”

---

## Deterministic fake embedding mode

- **Purpose:** align **query** embeddings with **backfill** vectors in **dev/integration** (same **8-d** deterministic math).
- **Requires:** **`GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER=deterministic_fake`**, **`RUN_INTEGRATION_TESTS=1`**, **`APP_ENV` ≠ `prod`** — enforced in **`Settings`** ([`config.py`](../../backend/app/core/config.py)).
- **Default remains `not_configured`** — **not** production semantics; **do not** enable **`deterministic_fake`** in production.
- **Unset** the adapter env var when running unrelated tests that assume defaults ([`TESTING_RULES.md`](../governance/TESTING_RULES.md)).

---

## Common runbooks

1. **Minimal packet is empty but valid** — Confirm **200**, read **`warnings`**, confirm **`pending`** or no indexed SI; treat as **minimal** success if coherent ([`PHASE_6_DEMO_CORPUS.md`](../demo/PHASE_6_DEMO_CORPUS.md) C5).
2. **Rich demo expected but empty** — Run **manual backfill**; align **`embedding_text`** / **`question`** with embedding policy; check **`deterministic_fake`** vs **`not_configured`**.
3. **Backfill failed** — Read stderr, script exit code, SI **`metadata_json.graphclerk_vector_indexing`**, Qdrant connectivity, dimension mismatch.
4. **B5 full-stack skipped** — Set integration gate env per [`TESTING_RULES.md`](../governance/TESTING_RULES.md) Track B Slice B5.
5. **B5 first run failed indexing (dimension)** — Dev-only collection reset narrative: [`RELEASE_CHECKLIST.md`](../release/RELEASE_CHECKLIST.md) B5.1 + [`TESTING_RULES.md`](../governance/TESTING_RULES.md).
6. **Frontend cannot reach API** — Fix **8010** / proxy / `VITE_API_BASE_URL` per root README.
7. **Unsupported file upload** — Use **text/markdown** minimal path or install documented extras; do not expect OCR/video.

---

## What not to do

- **Do not** mark **`indexed`** in Postgres without a **successful** Qdrant upsert (integrity lie).
- **Do not** use **`deterministic_fake`** in **production**.
- **Do not** delete **production** Qdrant collections casually.
- **Do not** treat **`graphclerk_model_pipeline`** metadata as **evidence**.
- **Do not** assume **`actor_context`** boosts retrieval.
- **Do not** claim **`POST /answer`** exists today.
- **Do not** hide empty evidence by inventing snippets outside evidence units.

---

## Links to related docs

| Doc | Use |
|-----|-----|
| [`GRAPHCLERK_PIPELINE_GUIDE.md`](GRAPHCLERK_PIPELINE_GUIDE.md) | Concepts + short failure table |
| [`FEED_CONTENT_MINIMAL_GUIDE.md`](FEED_CONTENT_MINIMAL_GUIDE.md) | Hands-on minimal path |
| [`EXAMPLES_COOKBOOK.md`](EXAMPLES_COOKBOOK.md) | PowerShell / curl / Python copy-paste; **VERIFIED** vs **TEMPLATE** |
| [`GRAPHCLERK_ARCHITECTURE.md`](GRAPHCLERK_ARCHITECTURE.md) | Components + data flow |
| [`TESTING_RULES.md`](../governance/TESTING_RULES.md) | Integration env, dimension mismatch, **`deterministic_fake`** |
| [`RELEASE_CHECKLIST.md`](../release/RELEASE_CHECKLIST.md) | Verification records |
| [`PHASE_6_DEMO_CORPUS.md`](../demo/PHASE_6_DEMO_CORPUS.md) | Minimal vs rich demo policy |
| [`API_OVERVIEW.md`](../api/API_OVERVIEW.md) | HTTP surface |

---

## Open follow-ups

- **Examples cookbook** shipped as **[`EXAMPLES_COOKBOOK.md`](EXAMPLES_COOKBOOK.md)** (F5); extend with multipart or auth when product adds stable patterns.
- **Production** embedding provider choice, **OCR/ASR/video**, **`/answer`**, Phase **9** — **program / status** decisions, not resolved here ([`phase_1_8_completion_program.md`](../plans/phase_1_8_completion_program.md) §15).
