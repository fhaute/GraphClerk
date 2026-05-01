# GraphClerk — examples cookbook

| Field | Value |
|-------|--------|
| **Doc status** | **Track F Slice F5** — copy-paste examples for the **current baseline** (Phases **1–8**). |
| **Scope** | HTTP examples only; **no** repo script files added. No **`POST /answer`**, no production inference, no OCR/ASR/video paths. **Phase 9** has **not** started. |
| **Verification** | Mixed — see [Metadata / verification status](#metadata--verification-status). |

---

## Metadata / verification status

| Label | Meaning |
|-------|---------|
| **VERIFIED LOCALLY** | Command was run in this doc slice against a live API; response shape recorded. |
| **TEMPLATE — NOT EXECUTED IN THIS SLICE** | Request/response fields match schemas/routes as written; **not** run end-to-end here — **verify** on your stack. |
| **EXPECTED SHAPE ONLY** | Illustrates JSON or headers without a full round-trip claim. |

**Smoke run in this slice (non-destructive):**

- **API base:** `http://localhost:8010`
- **Command family:** PowerShell `Invoke-WebRequest -UseBasicParsing`
- **`GET /health`:** HTTP **200**, body `{"status":"ok"}` — **VERIFIED LOCALLY**
- **`GET /version`:** HTTP **200**, body included `name`, `version`, `phase` keys — **VERIFIED LOCALLY**

**Not verified in this slice:** full minimal path (artifact → retrieve), **curl** blocks, **Python** blocks, backfill CLI execution — all marked **TEMPLATE — NOT EXECUTED IN THIS SLICE** below unless explicitly stated otherwise.

**No secrets** in this document. **Not** a production readiness sign-off.

---

## Audience

Developers who prefer **PowerShell**, **bash/curl**, or **Python** over reading route code first.

---

## Before you run examples

1. Start the stack (e.g. `docker compose up -d` from repo root) — see root [`README.md`](../../README.md).
2. Confirm **`DATABASE_URL`** / **`QDRANT_URL`** for **backfill** only when you run Example set D (separate shell env).
3. Read **`GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER`** implications for **rich** vs **minimal** retrieve — [`TROUBLESHOOTING_AND_OPERATIONS.md`](TROUBLESHOOTING_AND_OPERATIONS.md), [`TESTING_RULES.md`](../governance/TESTING_RULES.md).

---

## Environment setup

| Variable / URL | Typical use |
|----------------|-------------|
| **`$api` / `API`** | **`http://localhost:8010`** (default Compose host port) |
| **`DATABASE_URL`** | Required for **`scripts/backfill_semantic_indexes.py`** |
| **`QDRANT_URL`** | Required for backfill; often **`http://localhost:6333`** from host |

---

## Example set A — PowerShell minimal path

**Label:** **TEMPLATE — NOT EXECUTED IN THIS SLICE** (full sequence; only **§Metadata** smoke was run against `/health` and `/version`).

```powershell
$api = "http://localhost:8010"

# Health / version (subset VERIFIED LOCALLY in doc slice — re-run to confirm your host)
Invoke-RestMethod -Method Get -Uri "$api/health"
Invoke-RestMethod -Method Get -Uri "$api/version"

# --- Artifact: ArtifactCreateInlineRequest (filename, artifact_type text|markdown, text; optional title, mime_type)
$artifactBody = @{
  filename      = "cookbook-demo.md"
  artifact_type = "markdown"
  text          = "GraphClerk cookbook demo body. Evidence routing example sentence."
  title         = "Cookbook demo"
} | ConvertTo-Json
$artifact = Invoke-RestMethod -Method Post -Uri "$api/artifacts" -ContentType "application/json; charset=utf-8" -Body $artifactBody
$artifactId = $artifact.artifact_id   # response: artifact_id, status, artifact_type, evidence_unit_count

# --- Evidence list: EvidenceUnitListResponse { items: [...] }
$evidence = Invoke-RestMethod -Method Get -Uri "$api/artifacts/$artifactId/evidence"
$evidenceUnitId = $evidence.items[0].id

# --- Graph node: GraphNodeCreateRequest { node_type, label, optional summary, metadata }
$nodeBody = @{ node_type = "concept"; label = "Cookbook node" } | ConvertTo-Json
$node = Invoke-RestMethod -Method Post -Uri "$api/graph/nodes" -ContentType "application/json; charset=utf-8" -Body $nodeBody
$nodeId = $node.id

# --- Evidence link: GraphEvidenceLinkCreateRequest { evidence_unit_id, support_type, optional confidence }
$linkBody = @{
  evidence_unit_id = $evidenceUnitId
  support_type     = "supports"
  confidence       = 0.9
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$api/graph/nodes/$nodeId/evidence" -ContentType "application/json; charset=utf-8" -Body $linkBody | Out-Null

# --- Semantic index: SemanticIndexCreateRequest { meaning, optional summary, embedding_text, entry_node_ids, optional metadata }
# Use -Depth so entry_node_ids serializes as a JSON array, not a single string.
$semanticText = "GraphClerk cookbook demo body. Evidence routing example sentence."
$siBody = [ordered]@{
  meaning        = "cookbook_demo"
  embedding_text = $semanticText
  entry_node_ids = @($nodeId)
} | ConvertTo-Json -Depth 5
$si = Invoke-RestMethod -Method Post -Uri "$api/semantic-indexes" -ContentType "application/json; charset=utf-8" -Body $siBody
$semanticIndexId = $si.id
$si.vector_status   # expect "pending" until backfill

# --- Retrieve: RetrieveRequest { question, optional options, optional actor_context }
$retrieveBody = @{ question = $semanticText } | ConvertTo-Json
$packet = Invoke-RestMethod -Method Post -Uri "$api/retrieve" -ContentType "application/json; charset=utf-8" -Body $retrieveBody
$packet.packet_type
$packet.evidence_units.Count
$packet.warnings

# --- Retrieval logs (list envelope)
$logs = Invoke-RestMethod -Method Get -Uri "$api/retrieval-logs?limit=10"
$logs.items | Select-Object -First 5 id, question, has_retrieval_packet
```

---

## Example set B — curl minimal path

**Label:** **TEMPLATE — NOT EXECUTED IN THIS SLICE** (bash/macOS/Linux friendly).

Set base URL:

```bash
API=http://localhost:8010
```

**Health / version** (shape check — same endpoints as verified smoke; **this curl block** not re-run in slice):

```bash
curl -sS "$API/health"
curl -sS "$API/version"
```

**Artifact** (`artifact_id` in response):

```bash
curl -sS -X POST "$API/artifacts" \
  -H "Content-Type: application/json" \
  -d '{"filename":"cookbook-curl.md","artifact_type":"markdown","text":"Curl cookbook demo line for evidence."}'
```

**Evidence list** — replace `$ARTIFACT_ID`:

```bash
curl -sS "$API/artifacts/$ARTIFACT_ID/evidence"
```

**Graph node** — capture `id` from JSON (optional helper **`jq`**, not a GraphClerk dependency):

```bash
curl -sS -X POST "$API/graph/nodes" \
  -H "Content-Type: application/json" \
  -d '{"node_type":"concept","label":"Curl node"}'
```

**Evidence link** — replace `$NODE_ID` and `$EU_ID`:

```bash
curl -sS -X POST "$API/graph/nodes/$NODE_ID/evidence" \
  -H "Content-Type: application/json" \
  -d "{\"evidence_unit_id\":\"$EU_ID\",\"support_type\":\"supports\",\"confidence\":0.9}"
```

**Semantic index** — replace `$NODE_ID`; ensure JSON array for `entry_node_ids`:

```bash
curl -sS -X POST "$API/semantic-indexes" \
  -H "Content-Type: application/json" \
  -d "{\"meaning\":\"curl_cookbook\",\"embedding_text\":\"Curl cookbook demo line for evidence.\",\"entry_node_ids\":[\"$NODE_ID\"]}"
```

**Retrieve**:

```bash
curl -sS -X POST "$API/retrieve" \
  -H "Content-Type: application/json" \
  -d '{"question":"Curl cookbook demo line for evidence."}'
```

**Logs**:

```bash
curl -sS "$API/retrieval-logs?limit=10"
```

---

## Example set C — Python minimal path

**Label:** **TEMPLATE — NOT EXECUTED IN THIS SLICE**. Uses **stdlib only** (`urllib.request`, `json`) — **no** extra pip dependency.

```python
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API = "http://localhost:8010"


def post_json(path: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = Request(
        f"{API}{path}",
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json(path: str) -> dict:
    req = Request(f"{API}{path}", method="GET")
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# --- Run (TEMPLATE — adjust error handling for production scripts)
if __name__ == "__main__":
    print(get_json("/health"))
    print(get_json("/version"))

    art = post_json(
        "/artifacts",
        {
            "filename": "cookbook-py.md",
            "artifact_type": "markdown",
            "text": "Python urllib cookbook demo line.",
            "title": "Cookbook",
        },
    )
    artifact_id = art["artifact_id"]

    ev = get_json(f"/artifacts/{artifact_id}/evidence")
    evidence_unit_id = ev["items"][0]["id"]

    node = post_json("/graph/nodes", {"node_type": "concept", "label": "Python node"})
    node_id = node["id"]

    post_json(
        f"/graph/nodes/{node_id}/evidence",
        {
            "evidence_unit_id": evidence_unit_id,
            "support_type": "supports",
            "confidence": 0.9,
        },
    )

    si = post_json(
        "/semantic-indexes",
        {
            "meaning": "py_cookbook",
            "embedding_text": "Python urllib cookbook demo line.",
            "entry_node_ids": [node_id],
        },
    )
    semantic_index_id = si["id"]
    print("vector_status:", si.get("vector_status"))

    packet = post_json("/retrieve", {"question": "Python urllib cookbook demo line."})
    print("packet_type:", packet.get("packet_type"), "evidence count:", len(packet.get("evidence_units") or []))

    logs = get_json("/retrieval-logs?limit=10")
    print("log items:", len(logs.get("items") or []))
```

**Optional `requests` variant (user-installed):** same payloads with `requests.post(..., json=body)` — **TEMPLATE — NOT EXECUTED IN THIS SLICE**.

---

## Example set D — manual vector backfill

**Label:** **TEMPLATE — NOT EXECUTED IN THIS SLICE** (command shape from [`scripts/backfill_semantic_indexes.py`](../../scripts/backfill_semantic_indexes.py)).

From **repository root**, with env aligned to the API’s Postgres and Qdrant:

```bash
export DATABASE_URL="postgresql+psycopg://USER:PASS@HOST:PORT/DB"
export QDRANT_URL="http://localhost:6333"

python scripts/backfill_semantic_indexes.py --dry-run
python scripts/backfill_semantic_indexes.py --semantic-index-id "<UUID>"
# python scripts/backfill_semantic_indexes.py --all-pending --limit 50
# python scripts/backfill_semantic_indexes.py --semantic-index-id "<UUID>" --force
```

- **stderr** prints a **NOTICE** about **`DeterministicFakeEmbeddingAdapter` (8 dims)** — **dev/test**, not production semantics.
- **Exit `2`** if indexing outcome **`failed`** (single-id mode).
- **Automatic indexing on `POST /semantic-indexes` is not implemented.**
- **Dimension mismatch:** [`TESTING_RULES.md`](../governance/TESTING_RULES.md) — Qdrant `semantic_indexes` collection vs **8**.

---

## Example set E — retrieve + logs

**Label:** **TEMPLATE — NOT EXECUTED IN THIS SLICE**.

- **`POST /retrieve`** with body `{"question": "..."}` — optional `options`, optional `actor_context` (recording-only; see [`retrieval.py`](../../backend/app/schemas/retrieval.py) / [`retrieval_packet.py`](../../backend/app/schemas/retrieval_packet.py)).
- **Minimal:** HTTP **200**, **`evidence_units`** may be **empty** — read **`warnings`** and **`vector_status`** ([`TROUBLESHOOTING_AND_OPERATIONS.md`](TROUBLESHOOTING_AND_OPERATIONS.md)).
- **Rich indexed:** requires **`vector_status=indexed`** **and** a valid semantic-search embedding path (default adapter **`not_configured`** — often need guarded **`deterministic_fake`** for dev alignment per [`TESTING_RULES.md`](../governance/TESTING_RULES.md)).
- **Logs:** `GET /retrieval-logs`, `GET /retrieval-logs/{id}` — **best-effort**; absence of a row does **not** prove retrieve failed.

---

## Minimal vs rich results

| Mode | `vector_status` / search | `evidence_units` | Adapter note |
|------|--------------------------|------------------|--------------|
| **Minimal** | Often **`pending`** or not selected | Often **empty** | Default **`not_configured`** may prevent semantic hits |
| **Rich indexed** | **`indexed`** + Qdrant aligned | May be **non-empty** when graph + question align | May need **`deterministic_fake`** + `RUN_INTEGRATION_TESTS=1` for dev |
| **Failure / misconfigured** | **`failed`** or Qdrant errors | Empty or error path | See troubleshooting + SI **`metadata_json.graphclerk_vector_indexing`** |

---

## Cleanup / reset notes

- **Qdrant dimension mismatch** — dev-only collection handling: [`TESTING_RULES.md`](../governance/TESTING_RULES.md), [`TROUBLESHOOTING_AND_OPERATIONS.md`](TROUBLESHOOTING_AND_OPERATIONS.md).
- **Do not** delete production Qdrant data or Postgres rows casually.
- **Unset** `GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER` when running unrelated **pytest** / config tests — env pollution: [`TESTING_RULES.md`](../governance/TESTING_RULES.md).

---

## Troubleshooting links

Primary guide: [`TROUBLESHOOTING_AND_OPERATIONS.md`](TROUBLESHOOTING_AND_OPERATIONS.md).  
Walkthrough with the same field names: [`FEED_CONTENT_MINIMAL_GUIDE.md`](FEED_CONTENT_MINIMAL_GUIDE.md).

---

## What these examples do not prove

- **No** automatic vector backfill.
- **No** **`POST /answer`**.
- **No** OCR/ASR/video pipelines.
- **No** production model inference.
- **No** Phase **9**.
- **No** guaranteed **RetrievalLog** rows.
- **`graphclerk_model_pipeline`** is **not** shown as wired into these HTTP flows.

---

## Next examples / future slices

- **Production** embedding + auth patterns — outside this cookbook until product decisions land.
- **Multipart** artifact uploads — follow [`API_OVERVIEW.md`](../api/API_OVERVIEW.md) and route docstrings when extending examples.
