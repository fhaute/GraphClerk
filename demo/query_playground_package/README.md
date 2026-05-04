# Large query-playground demo package

Public-domain text (**Project Gutenberg #11**, *Alice’s Adventures in Wonderland*) packaged for GraphClerk demos: many evidence units after ingest, plus a loader that wires **graph + semantic index** like the Phase 6 script.

## Files

| File | Role |
|------|------|
| `corpus_alice_in_wonderland.md` | Markdown artifact body (~155 KiB) + operator instructions |
| `../../scripts/load_query_playground_demo_package.py` | HTTP loader (stdlib only) |

## Prerequisite: embeddings for semantic route

Default API settings use **`not_configured`** for semantic-search embeddings, so **`POST /retrieve`** will not traverse into graph evidence. For a **rich** playground response you need either:

- **Local / Docker (recommended for this package):** set **`GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER=deterministic_fake`** and **`RUN_INTEGRATION_TESTS=1`** (and **`APP_ENV` ≠ `prod`**) on the API — see root `docker-compose.yml` for the bundled defaults, and [`docs/governance/TESTING_RULES.md`](../../docs/governance/TESTING_RULES.md).
- **Production-style:** configure a real embedding adapter when one exists for your deployment.

## Run the loader

From the **repository root** (same pattern as Phase 6):

```powershell
$env:GRAPHCLERK_API_BASE_URL = "http://localhost:8010"
python scripts/load_query_playground_demo_package.py --dry-run
python scripts/load_query_playground_demo_package.py
```

Options:

- `--base-url` — overrides `GRAPHCLERK_API_BASE_URL`
- `--max-evidence-links` — cap node–evidence links created on the entry graph node (default `32`)

## Index vectors (required for semantic hits)

After the loader prints a **semantic index UUID** with `vector_status=pending`, move it to **`indexed`** using the same Postgres + Qdrant as the API (see [`docs/demo/PHASE_6_DEMO_CORPUS.md`](../../docs/demo/PHASE_6_DEMO_CORPUS.md)):

```powershell
python scripts/backfill_semantic_indexes.py --semantic-index-id "<UUID>"
```

## Ask in the Query playground

1. **Deterministic fake embeddings:** paste **exactly**  
   `GRAPHCLERK_LARGE_DEMO_QUERY_PLAYGROUND_V1`  
   (same string as the semantic index `embedding_text` the loader registers). That lines up query and index vectors so the File Clerk can reach your linked evidence.

2. **Real embeddings + clean DB:** natural-language questions about Alice / the Mad Tea Party / the Queen of Hearts, etc., work once your index is indexed and routing is meaningful.

## License

The novel text is from **Project Gutenberg** (ebook #11), public domain in the United States. GraphClerk-specific headers and scripts are project-licensed.
