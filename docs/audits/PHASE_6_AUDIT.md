# Phase 6 Audit — Productization, UI, Evaluation, and Hardening

**Date**: 2026-05-01  
**Result**: `pass_with_notes`

This audit **accepts the delivered Phase 6 productization baseline** (React/Vite UI against live APIs, onboarding docs, release checklist, evaluation-method documentation) as **honest and test-backed at the repository boundary**. It does **not** certify production enterprise readiness, full Phase 6 phase-doc completion, in-product demo loading, automated UI tests, or vector auto-indexing. Phase 5 remains **partial** (`pass_with_notes` — see `docs/audits/PHASE_5_AUDIT.md`). **`POST /answer`**, OCR/ASR/caption/video pipelines, and Phase 8 work are **out of scope** / **not started** as stated below.

---

## Executive notes (non-negotiable honesty)

- Phase 6 UI is **demo / productization** software, **not** production enterprise software (no built-in auth/tenancy/RBAC, no SLA claims).
- **Evaluation** metrics in the UI are **observability** metrics (counts/structure from logs and stored packets), **not** accuracy, nDCG, or LLM-judged quality (`docs/evaluation/EVALUATION_METHOD.md`).
- Demo **`POST /semantic-indexes`** rows may remain **`vector_status=pending`** until indexing/backfill exists; the demo loader does **not** fake vector indexing (`docs/demo/PHASE_6_DEMO_CORPUS.md`).
- **No** `POST /answer`, **no** `LocalRAGConsumer`, **no** `AnswerSynthesizer` in this repository state.
- **No** OCR, ASR, image captioning, or video ingestion beyond Phase 5’s documented partials.
- **No** automated frontend test harness in-repo at audit time (Vitest/Playwright not wired).

---

## Verification evidence (Slice L)

| Check | Command / artifact | Result |
|--------|----------------------|--------|
| Backend default test suite | `cd backend` → `python -m pytest -q` | **Pass** (exit 0; integration tests skipped as designed). |
| Frontend production build | `cd frontend` → `npm run build` | **Pass** (tsc + vite build succeeded). |
| Docker Compose file validity | `docker compose config` (repo root) | **Pass** (config renders; first lines validated). |
| Demo loader dry-run | `GRAPHCLERK_API_BASE_URL=http://localhost:8010` → `python scripts/load_phase6_demo.py --dry-run` | **Pass** (planned HTTP sequence printed; no hidden indexing). |

**Not executed in this audit run** (environment-dependent): `docker compose up`, live `curl` to a running API, `alembic upgrade head` on a disposable DB, full UI manual smoke — these remain operator responsibilities per `docs/release/RELEASE_CHECKLIST.md`.

---

## Required audit dimensions (condensed)

### Architecture / boundaries

| Check | Verdict |
|--------|---------|
| UI consumes **live** HTTP APIs only; no bundled mock corpus in shell | **Pass** (code review baseline: `frontend/src/api/*`, components use `apiGetJson` / `apiPostJson`; Slice B–J scope). |
| Retrieval remains packet-first; no answer synthesis in UI | **Pass.** No `/answer` client. |
| Phase 5 limits respected in UX (no OCR/ASR/video claims) | **Pass** (documented + prior slice intent). |

### Contract / status honesty

| Check | Verdict |
|--------|---------|
| README + `docs/status/*` + evaluation doc avoid implying Phase 6 “fully complete” or production-ready | **Pass with notes** — this audit updates status to **`pass_with_notes`** while preserving explicit gaps. |
| Phase 5 not claimed fully complete | **Pass.** |

### Tests

| Check | Verdict |
|--------|---------|
| Backend `pytest` passes default suite | **Pass** (see above). |
| Frontend has automated tests | **Note** — **No** in-repo harness; build-only gate. |

### Dependencies / security

| Check | Verdict |
|--------|---------|
| No new secret material in docs | **Pass** (docs-only audit). |
| CORS / proxy docs use **`GRAPHCLERK_*`** preferred names | **Pass** (README + `backend/app/main.py` alignment per prior slices). |

### Retrieval quality (UI visibility)

| Check | Verdict |
|--------|---------|
| Query Playground surfaces `RetrievalPacket` (readable + raw JSON) | **Pass** (feature slice; `QueryPlayground` + `RetrievalPacketPanel`). |
| Retrieval logs show stored packets without fabrication | **Pass** (`parseStoredRetrievalPacket` / honest error on parse — prior implementation). |

### Multimodal extraction (UI)

| Check | Verdict |
|--------|---------|
| UI does not imply image/audio produce EvidenceUnits | **Pass** (honesty rules + API truth). |

### Status honesty audit

| Check | Verdict |
|--------|---------|
| README/status will reflect **`pass_with_notes`** and remaining gaps | **Pass** (this commit). |

---

## Twelve-point checklist (audit questions)

1. **Does the UI show retrieval traceability?** **Yes** — query playground shows routes, evidence selections, and packet structure from live `POST /retrieve` responses; retrieval logs tab ties to logged packets when present.
2. **Query Playground exposes RetrievalPacket readable + raw JSON?** **Yes** (`RetrievalPacketPanel`).
3. **Artifacts/evidence visible with `source_fidelity` and location?** **Yes** where API returns those fields (detail views render API JSON; empty/missing fields not fabricated).
4. **SemanticIndexes inspectable?** **Yes** — list, detail, search (search meaningful only for **`vector_status=indexed`** indexes per backend contract).
5. **Graph nodes/edges/neighborhood/evidence refs inspectable?** **Yes** — explorers call graph APIs; neighborhood and evidence links surfaced per responses.
6. **RetrievalLogs inspectable; stored packets without reconstruction?** **Yes** — list/detail from API; invalid/missing packet JSON surfaced as errors, not invented (`RetrievalLogsExplorer` / parser behavior).
7. **Evaluation dashboard avoids fake quality claims?** **Yes** — documented as observability-only (`docs/evaluation/EVALUATION_METHOD.md` + UI positioning in README).
8. **Demo loader avoids fake semantic indexing?** **Yes** — script documents `pending` vectors; dry-run shows no indexing calls.
9. **CORS/proxy/dev docs honest?** **Yes** — README covers **8010**, **`VITE_API_BASE_URL=/api`**, **`GRAPHCLERK_API_PROXY_TARGET`**, optional direct URL + CORS env names.
10. **Unsupported features clearly absent?** **Yes** — no `/answer`, no OCR/ASR/video UI paths.
11. **README/status overclaim?** **Pass with notes** — updated in this audit commit to match **`pass_with_notes`** outcome; Phase 5 remains partial; Phase 8 not started.
12. **Tests/builds passing?** **Yes** — `pytest -q` and `npm run build` as recorded above.

---

## Notes and accepted gaps (`pass_with_notes`)

- **In-product demo workflow** still script-driven (`scripts/load_phase6_demo.py`); not a first-class UI feature.
- **Optional** API hardening slice (J) and **optional** E2E tests remain future work.
- **Vector population / backfill** still a global product gap (Phase 3 debt carries forward).
- **Manual UI smoke** and **Compose boot** not re-run as part of this automated audit record.

---

## Conclusion

Phase 6 **productization / UI baseline** is accepted at **`pass_with_notes`**: builds and default tests pass, live-contract UI is present and documented honestly, and explicit limitations remain tracked. This is **not** a statement of production readiness.
