# Phase 6 demo corpus

## Purpose

The Phase 6 demo loader seeds a **small, API-created** dataset so the GraphClerk UI can be exercised against **real backend rows** (no frontend mocks).

## Files

| Path | Role |
|------|------|
| `demo/phase6_demo_corpus.md` | Markdown ingested via `POST /artifacts` |
| `scripts/load_phase6_demo.py` | HTTP client loader |

## Run

From the **repository root**. Point the script at the same URL as your API (Docker default host port is **8010**):

```bash
# Windows PowerShell example:
$env:GRAPHCLERK_API_BASE_URL = "http://localhost:8010"

python scripts/load_phase6_demo.py --dry-run
python scripts/load_phase6_demo.py
```

```bash
# Unix example:
export GRAPHCLERK_API_BASE_URL=http://localhost:8010
python scripts/load_phase6_demo.py --dry-run
python scripts/load_phase6_demo.py
```

If `GRAPHCLERK_API_BASE_URL` is unset, the script falls back to **`http://localhost:8000`** — override when using the default **8010** Compose mapping (see root **`README.md`**).

The alternate env name **`GRAPHCLE_API_BASE_URL`** is accepted only if `GRAPHCLERK_API_BASE_URL` is unset (legacy typo tolerance in the script — prefer **`GRAPHCLERK_API_BASE_URL`**).

## Metadata tagging

Where the public API allows `metadata` on the request body, the loader sets:

```json
{
  "demo_corpus": "phase_6",
  "created_by": "demo_loader"
}
```

**Artifact:** `POST /artifacts` inline JSON schema does **not** expose artifact `metadata`; the loader uses a clear filename/title instead (`phase6_demo_corpus.md`). Evidence units created during ingestion inherit whatever the backend stores today — there is no separate “demo” flag on EvidenceUnits via this loader.

## Reruns

Each run creates **new** artifacts, nodes, edges, links, and semantic indexes (UUIDs always fresh). **Nothing is deleted.** Repeated runs **duplicate** demo-shaped rows unless you clean the database manually.

Timestamps are embedded in some labels to make rows easier to spot in the UI.

## Semantic index / vector search (honest limitation)

`POST /semantic-indexes` creates rows with `vector_status` typically **`pending`** until a separate vector-indexing path runs (not invoked by this loader).

Therefore:

- **`GET /semantic-indexes/search`** may return **no** hits for the demo index until it is **indexed** in your deployment’s vector backend.
- **`POST /retrieve`** may not route through the demo semantic index the way a fully indexed deployment would; behavior follows the File Clerk when indexes are not **`indexed`**.

This loader **does not** write to the database directly and **does not** fake indexing through hidden APIs.

## APIs used

1. `POST /artifacts` — markdown inline body  
2. `GET /artifacts/{artifact_id}/evidence` — resolve an evidence unit id  
3. `POST /graph/nodes` — two nodes  
4. `POST /graph/edges` — one directed edge  
5. `POST /graph/nodes/{node_id}/evidence` — node evidence support link  
6. `POST /semantic-indexes` — index with `entry_node_ids` pointing at one graph node  

No LLM, OCR, ASR, or video.
