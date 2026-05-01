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

## Manual end-to-end smoke path

Use this path to verify **control plane + UI + retrieval logging** with the Phase 6 demo. There is **no** `POST /answer`, **no** answer synthesis step, **no** OCR/ASR/video pipeline on this path, and **no** claim of production model inference — only public APIs and the script-only loader.

**Truth baseline**

- The demo loader is **script-only** (see `scripts/load_phase6_demo.py`). It creates **new** rows each run: artifact, evidence units, graph nodes/edges/links, and a semantic index row — all via HTTP.
- **`vector_status`** on the created semantic index may stay **`pending`** until a separate indexing/backfill path runs.
- **`GET /semantic-indexes/search`** returns only **`vector_status=indexed`** rows; pending indexes do not appear in search results.
- **`POST /retrieve`** can still return a **schema-valid** `RetrievalPacket` with **empty** `evidence_units` and honest **warnings** (for example when no indexed semantic route matches). That outcome is **coherent**, not automatically a bug.
- **`RetrievalLog`**: when logging succeeds, the UI’s **Retrieval logs** tab should still show an entry with the stored packet snapshot even if evidence is empty.
- The UI can inspect **Artifacts & evidence**, **Graph explorer**, **Semantic indexes**, **Query playground**, and **Retrieval logs** — all against **live** APIs (no bundled mock corpus).

**Steps**

1. **Start Docker / API** — from repo root, e.g. `docker compose up -d --build` and confirm the API is reachable (default host port **8010**; see root `README.md`).
2. **Run loader dry-run** — set `GRAPHCLERK_API_BASE_URL` to match the API (e.g. `http://localhost:8010`), then `python scripts/load_phase6_demo.py --dry-run`. Confirm the printed HTTP plan looks correct.
3. **Run loader** — `python scripts/load_phase6_demo.py` (no `--dry-run`). Confirm success (new artifact, graph, semantic index created each run).
4. **Open UI** — run the Vite dev server from `frontend/` (`npm run dev`) or your preview setup; ensure the UI targets the same API (proxy / `VITE_API_BASE_URL`).
5. **Inspect Artifacts & evidence** — confirm the new markdown artifact and at least one evidence unit appear.
6. **Inspect Graph** — confirm demo nodes, edge, and node–evidence link are visible in **Graph explorer**.
7. **Inspect Semantic indexes** — open the new index; note **`vector_status`** (often **`pending`** after a stock loader run). Use search only if you expect **indexed** rows; pending rows will not surface in **`GET /semantic-indexes/search`**.
8. **Query playground** — submit a question grounded in the ingested text, for example: *“What is the retrieval trace hook in the Phase 6 demo corpus?”* or *“What checklist items does the demo markdown mention?”* Inspect the returned **RetrievalPacket** (readable sections + raw JSON): intent, warnings, `evidence_units`, optional Phase 7 context fields.
9. **Retrieval logs** — open **Retrieval logs**; confirm a log row exists for the retrieve when logging succeeds, and that you can open the stored packet even if evidence was empty.
10. **Interpret empty evidence** — if **`vector_status`** is still **`pending`**, empty or sparse evidence from **`POST /retrieve`** is expected for the current File Clerk design (vector route over **indexed** indexes only). Do not treat that alone as a failed smoke unless you intended a **rich** demo (see below).
11. **Confirm no `/answer` step** — there is no endpoint or UI tab that performs **`POST /answer`** or LLM answer synthesis; the trace ends at the packet and logs.

## Minimal vs rich demo

**Minimal demo (default expectation after script load)**

- **Proves:** ingest and row visibility; graph and semantic index **rows** exist; **`POST /retrieve`** returns a valid packet; **RetrievalLog** / UI can show the packet; warnings and empty evidence are interpretable.
- **Does not require:** non-empty semantic vector search hits or filled **`evidence_units`** from the demo semantic index while **`vector_status`** is **`pending`**.

**Rich demo (optional “evidence-filled” tier)**

- **Requires:** at least one semantic index with **`vector_status=indexed`** (dev backfill, Qdrant upsert, integration harness, or a future first-class indexing story — **not** performed by `load_phase6_demo.py` today).
- **Then:** `GET /semantic-indexes/search` and File Clerk route selection can attach traversal and you may see **non-empty** `evidence_units` when the question aligns with indexed meaning.

For release-style verification, record whether your run was **minimal** (empty evidence acceptable with pending indexes) or **rich** (indexed vectors present).

## APIs used

1. `POST /artifacts` — markdown inline body  
2. `GET /artifacts/{artifact_id}/evidence` — resolve an evidence unit id  
3. `POST /graph/nodes` — two nodes  
4. `POST /graph/edges` — one directed edge  
5. `POST /graph/nodes/{node_id}/evidence` — node evidence support link  
6. `POST /semantic-indexes` — index with `entry_node_ids` pointing at one graph node  

No LLM, OCR, ASR, or video.
