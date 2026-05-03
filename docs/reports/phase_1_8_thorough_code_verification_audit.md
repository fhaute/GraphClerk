# Phase 1–8 Thorough Code & Verification Audit (Drift Check)

## 1. Metadata

| Field | Value |
|-------|--------|
| **Date** | 2026-05-01 |
| **Git baseline** | `7da09b2` — `docs: list onboarding updates in phase 8 full audit` |
| **Purpose** | Verify **executable** and **surface** behavior has not **drifted** from documented public API and major phase claims (post–Track C/D). |
| **Scope** | Backend tests, frontend build, route inventory vs `docs/api/API_OVERVIEW.md`, absence of `POST /answer`, Phase 8 config route + model pipeline module lint subset, spot-read of `main.py`, `artifacts` ingestion wiring. |
| **Out of scope** | Gated integration (B5, DB+Qdrant) not re-run here; live Ollama; full-repo Ruff clean (see §7). |

---

## 2. Executive summary

**Verdict: `pass` (no drift blockers found)** for the checks executed.

- **Backend:** `python -m pytest -q` — **exit 0** (many tests **skipped by design**; see §3).
- **Frontend:** `npm run build` — **exit 0**.
- **HTTP surface:** Every path documented in **`API_OVERVIEW.md`** through the model-pipeline section has a matching **`@router.*` handler** in `backend/app/api/routes/*` and routers are included from **`create_app()`** in `main.py`.
- **`POST /answer`:** **No** route registration; only schema / packet **`answer_mode`** and docstrings reference “answer” semantics — consistent with “deferred / not implemented.”
- **Phase 8 read-only config:** `GET /model-pipeline/config` implemented in `model_pipeline.py`; handler calls **`build_model_pipeline_config_response(get_settings())`** only (**no** adapter `run`).
- **Import boundary (spot):** `model_pipeline_*.py` services do **not** import FileClerk/retrieve modules; **artifacts** route composes enrichment + optional model pipeline (**expected** coupling).
- **Ruff (narrow):** Phase 8 model-pipeline paths listed in §7 — **clean**. **Full** `ruff check app/` — **fails** with many pre-existing issues (not treated as product drift for this pass).

**Residual honesty:** Documentation **outside** this file may still be internally inconsistent (e.g. `PROJECT_STATUS` Phase 7 “limitations” vs full-completion audit) — flagged in the **global inventory**; **not corrected** in this slice.

---

## 3. Test commands and results

### 3.1 Backend — full default suite

```powershell
cd backend
python -m pytest -q
```

| Result | Detail |
|--------|--------|
| **Exit code** | **0** |
| **Skips** | Heavy use of **`s`** in progress output — **expected** for gated integration / optional deps (unchanged from normal CI posture). |
| **Warnings** | `UserWarning: Api key is used with an insecure connection` from **`QdrantClient`** in Track B–related tests (`semantic_index_search_factory`) — **known**; not a functional failure. |

### 3.2 Frontend — production build

```powershell
cd frontend
npm run build
```

| Result | Detail |
|--------|--------|
| **Exit code** | **0** |
| **Tooling** | `tsc --noEmit` + `vite build` — **succeeded** |

### 3.3 Not run (this pass)

| Suite | Reason |
|-------|--------|
| `RUN_INTEGRATION_TESTS=1` + Postgres + Qdrant + B5 | Environment-dependent; last recorded evidence remains **`RELEASE_CHECKLIST.md`** (B5.1). |
| Live Ollama | Not required for default truth; Phase 8 suite uses mocks/fakes per prior audits. |

---

## 4. Route registration vs `API_OVERVIEW.md`

**`create_app()`** (`main.py`) includes, in order: `health`, `version`, **`model_pipeline`**, `artifacts`, `evidence_units`, graph routers, `semantic_indexes`, `retrieve`, `retrieval_logs`.

| `API_OVERVIEW` path | Route module | Decorator path |
|---------------------|--------------|----------------|
| `GET /health` | `health.py` | `/health` |
| `GET /version` | `version.py` | `/version` |
| `POST /artifacts` | `artifacts.py` | `/artifacts` |
| `GET /artifacts` | `artifacts.py` | `/artifacts` |
| `GET /artifacts/{artifact_id}` | `artifacts.py` | `/artifacts/{artifact_id}` |
| `GET /artifacts/{artifact_id}/evidence` | `evidence_units.py` | `/artifacts/{artifact_id}/evidence` |
| `GET /evidence-units/{evidence_unit_id}` | `evidence_units.py` | `/evidence-units/{evidence_unit_id}` |
| `POST /graph/nodes` | `graph_nodes.py` | prefix `/graph` + `/nodes` |
| `GET /graph/nodes` | `graph_nodes.py` | `/graph/nodes` |
| `GET /graph/nodes/{node_id}` | `graph_nodes.py` | `/graph/nodes/{node_id}` |
| `POST /graph/edges` | `graph_edges.py` | `/graph/edges` |
| `GET /graph/edges` | `graph_edges.py` | `/graph/edges` |
| `GET /graph/edges/{edge_id}` | `graph_edges.py` | `/graph/edges/{edge_id}` |
| `POST /graph/nodes/{node_id}/evidence` | `graph_node_evidence.py` | `/graph/nodes/...` |
| `POST /graph/edges/{edge_id}/evidence` | `graph_edge_evidence.py` | `/graph/edges/...` |
| `GET /graph/nodes/{node_id}/neighborhood` | `graph_traversal.py` | `/graph/nodes/{node_id}/neighborhood` |
| `POST /semantic-indexes` | `semantic_indexes.py` | `/semantic-indexes` |
| `GET /semantic-indexes` | `semantic_indexes.py` | `/semantic-indexes` |
| `GET /semantic-indexes/{id}` | `semantic_indexes.py` | `/semantic-indexes/{semantic_index_id}` |
| `GET /semantic-indexes/{id}/entry-points` | `semantic_indexes.py` | `/semantic-indexes/{semantic_index_id}/entry-points` |
| `GET /semantic-indexes/search` | `semantic_indexes.py` | `/semantic-indexes/search` |
| `POST /retrieve` | `retrieve.py` | `/retrieve` |
| `GET /retrieval-logs` | `retrieval_logs.py` | `/retrieval-logs` |
| `GET /retrieval-logs/{log_id}` | `retrieval_logs.py` | `/retrieval-logs/{retrieval_log_id}` (**param name** `retrieval_log_id` in code — **API shape** matches overview) |
| `GET /model-pipeline/config` | `model_pipeline.py` | `/model-pipeline/config` |

**Conclusion:** **No missing** documented route from the overview table; **no extra** public routes in overview that lack handlers for the listed scope.

---

## 5. Negative checks (security / product claims)

| Check | Method | Result |
|-------|--------|--------|
| **`POST /answer`** | `rg` / `grep` on `backend/app` for route-like `answer` usage | **No** `APIRouter` path for `/answer`; **`retrieve.py`** is only **`POST /retrieve`**. Occurrences of “answer” are **packet `answer_mode`**, model-pipeline **prompt bans**, or **comments** — **consistent** with deferred synthesis route. |
| **Model pipeline config calls provider** | Read `model_pipeline.py` | **No** — settings snapshot only. |
| **Model pipeline → FileClerk** | `grep` imports in `model_pipeline*.py` services | **No** imports of `file_clerk` / `FileClerkService`; docstrings state non-coupling. **`artifacts.py`** correctly orchestrates ingestion (**by design**). |

---

## 6. Settings env names (spot vs `config.py`)

These **`GRAPHCLERK_*`** aliases are present in `backend/app/core/config.py` and align with documented Track **B** / **C** / **D** behavior:

- `GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER` (+ validators for `deterministic_fake`)
- `GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER`
- `GRAPHCLERK_MODEL_PIPELINE_ADAPTER`, `BASE_URL`, `MODEL`, `TIMEOUT`, `API_KEY`
- `GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_*` (+ cross-field validators)

**No drift** detected between **field names** in code and **Phase 8 / Track D** documentation expectations from prior audits.

---

## 7. Ruff

| Command | Result |
|---------|--------|
| `python -m ruff check app/api/routes/model_pipeline.py app/services/model_pipeline_ollama_adapter.py app/services/model_pipeline_registry.py app/services/model_pipeline_purpose_registry.py app/services/model_pipeline_metadata_enrichment_service.py` | **All checks passed** |
| `python -m ruff check app/` | **Fails** — large volume (e.g. **E402** import order in multiple route files, and many other rules). Treated as **existing technical debt**, **not** a regression signal for this drift audit unless CI starts gating full-app Ruff. |

---

## 8. Code vs doc nits (non-blocking)

| ID | Severity | Note |
|----|----------|------|
| N1 | **C** | `create_app()` docstring still opens with “**Phase 0–2 scope**” while listing Phases **5–8** behavior — **stale comment**, not behavior. |
| N2 | **C** | `API_OVERVIEW` uses `{log_id}`; FastAPI path is `{retrieval_log_id}` — **cosmetic** naming difference only. |

---

## 9. Findings summary

| Severity | Count | Description |
|----------|-------|-------------|
| **A / BLOCKER** | **0** | None for drift checks performed. |
| **B** | **0** | None in code/API parity for this scope. |
| **C** | **2+** | `main.py` docstring; full-app Ruff debt; optional integration not re-run. |

---

## 10. Decision

For **default CI-equivalent verification** plus **HTTP surface parity** and **Phase 8 narrow lint**, the codebase **matches** the **documented public API** and **does not** show **`/answer`** drift or **model-pipeline config → provider** drift at **`7da09b2`**.

---

## 11. Relationship to other reports

- **`docs/reports/phase_1_8_global_completion_audit_inventory.md`** — program/status **inventory** (mostly docs); identified **status wording** issues **not** fixed here.
- **This report** — **executable + route-level** evidence.

---

## 12. Primary handoff (parent)

1. **Mission:** Thorough **code-backed** drift check after user **“proceed”** — **tests + build + routes + spot code**.
2. **Evidence:** Pytest **pass**, **`npm run build` pass**, route table **matches** `API_OVERVIEW`, **no** `/answer` route, **`GET /model-pipeline/config`** read-only, narrow Ruff **pass**.
3. **Drift:** **None blocking**; **full Ruff app/** and **`main.py` docstring** are **polish/debt**.
4. **Follow-ups:** Optional — fix **`PROJECT_STATUS`** Phase 7 limitation bullets (doc-only); optional gated **B5** re-run in CI or release checklist cadence.
5. **Recommended next:** If a **single Track H** artifact is desired, merge **this file** + global inventory + any **status** edits in **one** delivery with PM approval.

---

*End of report.*
