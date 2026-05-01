# Minimal guide — feed text content into GraphClerk

| Field | Value |
|-------|--------|
| **Doc status** | **Track F Slice F2** — practical operator walkthrough (text/markdown only). |
| **Scope** | **Not** a full production integration guide; **not** verified end-to-end in CI by this doc slice. |
| **Examples** | **Template** — request field names and response shapes match `backend/app/schemas/*` and routes as of this writing; **this slice did not execute** the PowerShell sequence against a live API. **Verify** URLs, env, and JSON on your machine. |
| **Phase 9** | **Not started** — not covered here. |

---

## What this guide proves

You can run the **smallest useful** GraphClerk path by hand:

**stack → text artifact → evidence list → graph node → evidence link → semantic index → manual vector backfill → `POST /retrieve` → retrieval logs → UI**

…with honest expectations about **`vector_status`**, **empty vs non-empty `evidence_units`**, and **no `/answer`**.

---

## What this guide does not prove

- **Production** embedding providers, scaling, or hardened security.
- **OCR / ASR / video** or non-text modalities (this path is **inline text/markdown** only).
- **`POST /answer`** — **does not exist** in the API today.
- **Automatic vector indexing** on `POST /semantic-indexes` — **does not exist**; backfill remains **manual**.
- That **`evidence_units`** will always be non-empty: **empty packet + warnings** can still be **correct** (see *Expected outcomes*).

---

## Prerequisites

- **Docker Compose** (or equivalent): API, **Postgres**, **Qdrant** per root [`README.md`](../../README.md) (default API on host: **`http://localhost:8010`**).
- **PowerShell** (examples below target Windows; adapt for bash if needed).
- Optional: **frontend** dev server for Step 11 — UI talks to the same API (Vite **`/api`** proxy; see `README.md` → *Frontend*). This guide does **not** require starting the UI for Steps 1–10.

---

## Environment variables

**Backfill script** (repo root, [`scripts/backfill_semantic_indexes.py`](../../scripts/backfill_semantic_indexes.py)) requires at least:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Same Postgres as the running API (e.g. Compose defaults). |
| `QDRANT_URL` | Same Qdrant as the API (e.g. `http://localhost:6333` from the host when Qdrant publishes **6333**). |

The script uses **`DeterministicFakeEmbeddingAdapter` (dimension 8)** — **dev/test only**, not production semantic quality.

**Optional — dev “rich” semantic retrieve:** the API’s semantic **search** path defaults to **`not_configured`** (no production embedding adapter). To align **query** vectors with the script’s **8-d** deterministic vectors on a **local** API, you may set **`GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER=deterministic_fake`** **only** with the guards in [`docs/governance/TESTING_RULES.md`](../governance/TESTING_RULES.md) (including **`RUN_INTEGRATION_TESTS=1`**, **`APP_ENV` ≠ `prod`**). Without that, you may still complete all steps but see **empty** `evidence_units` or embedding-related errors on retrieve — treat as **minimal** success if the packet and logs are coherent.

---

## Step 1 — Start the stack

From the **repository root** (template):

```powershell
docker compose up -d --build
docker compose ps
```

Confirm **api**, **postgres**, and **qdrant** are **Up**. Default host API URL:

```powershell
$api = "http://localhost:8010"
```

---

## Step 2 — Check API health / version

**Template:**

```powershell
Invoke-RestMethod -Uri "$api/health" -Method Get
Invoke-RestMethod -Uri "$api/version" -Method Get
```

---

## Step 3 — Create a text artifact

**Inline JSON** uses `ArtifactCreateInlineRequest`: `filename`, **`artifact_type`** (`"text"` or `"markdown"`), **`text`**, optional `title`, optional `mime_type`.  
Response shape: **`artifact_id`**, `status`, `artifact_type`, `evidence_unit_count` (not a field named `id`).

**Template:**

```powershell
$artifactBody = @{
  filename    = "minimal-demo.md"
  artifact_type = "markdown"
  text        = "GraphClerk routes evidence through graph-linked semantic indexes. Use a clear sentence for demos."
  title       = "Minimal demo"
} | ConvertTo-Json

$artifact = Invoke-RestMethod -Method Post -Uri "$api/artifacts" `
  -ContentType "application/json" -Body $artifactBody

$artifactId = $artifact.artifact_id
$artifactId
```

---

## Step 4 — Get artifact evidence

**`GET /artifacts/{artifact_id}/evidence`** returns **`items`**: a list of evidence units; each unit includes **`id`** (use as `$evidenceUnitId`).

**Template:**

```powershell
$evidence = Invoke-RestMethod -Method Get -Uri "$api/artifacts/$artifactId/evidence"
$evidence.items | Format-Table id, artifact_id, content_type
$evidenceUnitId = $evidence.items[0].id
$evidenceUnitId
```

---

## Step 5 — Create a graph node

**`POST /graph/nodes`** with `GraphNodeCreateRequest`: **`node_type`** (e.g. `"concept"`), **`label`** (required), optional `summary`, optional `metadata`.  
Response includes **`id`** as `$nodeId`.

**Template:**

```powershell
$nodeBody = @{
  node_type = "concept"
  label     = "Minimal feed node"
} | ConvertTo-Json

$node = Invoke-RestMethod -Method Post -Uri "$api/graph/nodes" `
  -ContentType "application/json" -Body $nodeBody

$nodeId = $node.id
$nodeId
```

---

## Step 6 — Attach evidence to graph node

**`POST /graph/nodes/{node_id}/evidence`** with `GraphEvidenceLinkCreateRequest`: **`evidence_unit_id`**, **`support_type`**, optional **`confidence`** (0–1).

**Template:**

```powershell
$linkBody = @{
  evidence_unit_id = $evidenceUnitId
  support_type     = "supports"
  confidence       = 0.9
} | ConvertTo-Json

$link = Invoke-RestMethod -Method Post `
  -Uri "$api/graph/nodes/$nodeId/evidence" `
  -ContentType "application/json" -Body $linkBody

$link
```

---

## Step 7 — Create a semantic index with entry node

**`POST /semantic-indexes`** with `SemanticIndexCreateRequest`: **`meaning`**, optional `summary`, **`embedding_text`** (used for embeddings at index time), **`entry_node_ids`** (non-empty list of node id strings), optional `metadata`.  
Response includes **`id`**, **`vector_status`** (typically **`pending`** until backfill).

Use text in **`embedding_text`** that you can repeat as the retrieve **`question`** if you later enable **`deterministic_fake`** for query/search alignment (same string → same 8-d vector).

**Template:**

```powershell
$semanticText = "GraphClerk routes evidence through graph-linked semantic indexes. Use a clear sentence for demos."

$siBody = @{
  meaning          = "minimal_feed_demo"
  embedding_text   = $semanticText
  entry_node_ids   = @($nodeId)
} | ConvertTo-Json

$si = Invoke-RestMethod -Method Post -Uri "$api/semantic-indexes" `
  -ContentType "application/json" -Body $siBody

$semanticIndexId = $si.id
$si.vector_status
$semanticIndexId
```

---

## Step 8 — Run manual vector backfill

From **repository root** (where `scripts/` lives), with **`DATABASE_URL`** and **`QDRANT_URL`** set to the **same** services the API uses. **CLI** (from script): `--semantic-index-id <UUID>` or `--all-pending`; optional `--force`, `--dry-run`.

**Template:**

```powershell
cd <repository-root>
$env:DATABASE_URL = "postgresql+psycopg://<user>:<password>@127.0.0.1:5433/<db>"
$env:QDRANT_URL   = "http://127.0.0.1:6333"

python scripts/backfill_semantic_indexes.py --semantic-index-id $semanticIndexId
```

Use your real Compose host ports and credentials (Compose defaults are in root `README.md` / `docker-compose.yml`). The script prints stderr **NOTICE** about **8-d deterministic** embeddings.

**Qdrant dimension mismatch:** if upsert fails, see [`docs/governance/TESTING_RULES.md`](../governance/TESTING_RULES.md) → *Qdrant `semantic_indexes` vector dimension mismatch*.

**Re-check status (template):**

```powershell
$si2 = Invoke-RestMethod -Method Get -Uri "$api/semantic-indexes/$semanticIndexId"
$si2.vector_status
```

Expect **`indexed`** on success, **`failed`** with honest metadata on failure.

---

## Step 9 — Retrieve a packet

**`POST /retrieve`** body: **`RetrieveRequest`** — required **`question`**, optional **`options`**, optional **`actor_context`** (recording-only).

**Template:**

```powershell
$retrieveBody = @{
  question = $semanticText
} | ConvertTo-Json

$packet = Invoke-RestMethod -Method Post -Uri "$api/retrieve" `
  -ContentType "application/json" -Body $retrieveBody

$packet.packet_type
$packet.evidence_units.Count
$packet.warnings
```

If **`evidence_units`** is empty, read **`warnings`** and confirm **`vector_status`** / embedding configuration (*Expected outcomes*).

---

## Step 10 — Inspect retrieval logs

**`GET /retrieval-logs`** — paged list with summary fields. **`GET /retrieval-logs/{id}`** — detail including **`retrieval_packet`** when stored.

**Template:**

```powershell
$logs = Invoke-RestMethod -Method Get -Uri "$api/retrieval-logs?limit=10"
$logs.items | Select-Object -First 3 id, question, has_retrieval_packet

# If you have a log id from the newest row:
# $logDetail = Invoke-RestMethod -Method Get -Uri "$api/retrieval-logs/<log_id>"
```

Logging is **best-effort**; absence of a row does not by itself mean retrieve failed.

---

## Step 11 — Inspect the UI

With **`npm run dev`** in `frontend/` (see root `README.md`), open **Query Playground**, **Artifacts & evidence**, **Graph explorer**, **Semantic indexes**, **Retrieval logs**, and **Evaluation dashboard** as needed. The browser typically hits **`/api/...`** via the Vite proxy to the same backend as `$api`.

---

## Expected outcomes

| Step | Typical success signal |
|------|-------------------------|
| 1–2 | Containers **Up**; health/version JSON. |
| 3–4 | **`artifact_id`** returned; **`items`** non-empty for text ingest. |
| 5–6 | Node **`id`**; link response **200**. |
| 7 | **`vector_status`** **`pending`** before backfill. |
| 8 | Script prints **`indexed`** (or **`failed`** with reason); GET SI shows **`indexed`**. |
| 9 | **HTTP 200**; **`packet_type`** `retrieval_packet`; **`evidence_units`** may be **empty** or populated depending on route + **embedding** configuration (see below). |
| 10–11 | Logs and UI reflect the same API state. |

**Rich vs minimal (retrieve):**

- **`vector_status=indexed`** is **necessary** for semantic search over vectors, but **not sufficient** for non-empty evidence: the API still needs a **valid query embedding path** for semantic search unless your deployment configures one (default: **`not_configured`** — see [`TESTING_RULES.md`](../governance/TESTING_RULES.md)).
- **`embedding_text`** (index) and **`question`** (retrieve) should **match** your chosen embedding policy (for **`deterministic_fake`**, identical strings yield identical 8-d vectors).

---

## Troubleshooting

| Issue | Notes |
|-------|--------|
| **422** on JSON bodies | Check required fields (`artifact_type` + `text`, `node_type` + `label`, `meaning` + `entry_node_ids`, non-empty `question`). |
| **404** on graph/evidence | Wrong UUID string; confirm `$nodeId` / `$evidenceUnitId`. |
| **409** on evidence link | Link already exists; pick another node or evidence unit. |
| Backfill **ERROR: DATABASE_URL** | Export env in the same shell before `python scripts/...`. |
| Upsert / **VectorIndexOperationError** | Qdrant **`semantic_indexes`** collection dimension drift — see [`TESTING_RULES.md`](../governance/TESTING_RULES.md). |
| Retrieve **empty evidence** | Often **expected** under **minimal** conditions; read **`warnings`** and SI **`vector_status`**. |
| Semantic search / embedding errors | Default adapter **`not_configured`**; dev-only **`deterministic_fake`** requires explicit env guards — [`TESTING_RULES.md`](../governance/TESTING_RULES.md). |

---

## Next guides

- **[`GRAPHCLERK_PIPELINE_GUIDE.md`](GRAPHCLERK_PIPELINE_GUIDE.md)** — concepts, integration patterns, placeholders for **F3–F5**.
- **[`docs/demo/PHASE_6_DEMO_CORPUS.md`](../demo/PHASE_6_DEMO_CORPUS.md)** — scripted multi-step demo and **C5** minimal vs rich policy.
- **[`docs/api/API_OVERVIEW.md`](../api/API_OVERVIEW.md)** — full HTTP surface.

---

## Open decisions (not blocked by F2)

Production embedding vendor, multimodal engines, **`/answer`**, and Phase **9** scope remain **program / status** decisions — this guide does not define them.
