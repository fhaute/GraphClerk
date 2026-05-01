# GraphClerk — onboarding and integration

**Status:** **Living docs (Track F Slice F1 + F2).** [`GRAPHCLERK_PIPELINE_GUIDE.md`](GRAPHCLERK_PIPELINE_GUIDE.md) is the **overview** skeleton; [`FEED_CONTENT_MINIMAL_GUIDE.md`](FEED_CONTENT_MINIMAL_GUIDE.md) is the **minimal hands-on** path (PowerShell templates — **verify locally**). **curl/Python cookbooks**, diagrams, and production runbooks remain **planned** (**F3–F5**). **Onboarding is not complete.**

**Phase 9** has **not** started — no Phase 9 implementation is described here.

---

## What GraphClerk is

A **local-first, graph-guided evidence-routing layer** for RAG-style systems: ingest **artifacts**, derive or attach **evidence units**, organize **graph** structure and **semantic indexes**, optionally **index vectors** in Qdrant, then **`POST /retrieve`** to obtain a structured **`RetrievalPacket`** with traceability — **search meaning first, then retrieve evidence** (see root [`README.md`](../../README.md) and [`docs/governance/PROJECT_PRINCIPLES.md`](../governance/PROJECT_PRINCIPLES.md)).

---

## What GraphClerk is not

- **Not** a built-in chatbot or **`POST /answer`** (answer synthesis is **out of scope** until separately approved).
- **Not** automatic vector backfill on semantic index create (manual / operator path today).
- **Not** production multimodal OCR/ASR/video pipelines (Phase 5 is **partial**; see status and phase docs).
- **Not** a replacement for your embedding provider, orchestrator, or enterprise records platform.

---

## Current implementation status

Honest high-level state lives in [`docs/status/PROJECT_STATUS.md`](../status/PROJECT_STATUS.md), [`docs/status/KNOWN_GAPS.md`](../status/KNOWN_GAPS.md), and the root [`README.md`](../../README.md). This onboarding set **does not** supersede those tables — it **routes** readers to them.

---

## Start here

1. Read **[`GRAPHCLERK_PIPELINE_GUIDE.md`](GRAPHCLERK_PIPELINE_GUIDE.md)** — pipeline at a glance, core concepts, baseline flow, minimal vs rich, failure modes, integration patterns, security/honesty rules, placeholders for future slices.
2. Follow **[`FEED_CONTENT_MINIMAL_GUIDE.md`](FEED_CONTENT_MINIMAL_GUIDE.md)** — smallest useful path: stack → artifact → evidence → graph → semantic index → backfill → retrieve → logs → UI (text/markdown; **template** examples).
3. Skim **[`docs/api/API_OVERVIEW.md`](../api/API_OVERVIEW.md)** — HTTP surface in one table.
4. Run or read **[`docs/demo/PHASE_6_DEMO_CORPUS.md`](../demo/PHASE_6_DEMO_CORPUS.md)** — script-driven demo corpus and **manual vector indexing** notes (including Qdrant **dimension mismatch** — [`docs/governance/TESTING_RULES.md`](../governance/TESTING_RULES.md)).
5. Use **[`docs/release/RELEASE_CHECKLIST.md`](../release/RELEASE_CHECKLIST.md)** before release-style handoffs.

---

## Guides

| Document | Purpose |
|----------|---------|
| [`GRAPHCLERK_PIPELINE_GUIDE.md`](GRAPHCLERK_PIPELINE_GUIDE.md) | Main pipeline / integration story (overview skeleton). |
| [`FEED_CONTENT_MINIMAL_GUIDE.md`](FEED_CONTENT_MINIMAL_GUIDE.md) | Minimal operator path: feed text → graph → SI → backfill → retrieve (F2; **template** examples). |
| [`docs/api/API_OVERVIEW.md`](../api/API_OVERVIEW.md) | Endpoint summary. |
| [`docs/demo/PHASE_6_DEMO_CORPUS.md`](../demo/PHASE_6_DEMO_CORPUS.md) | Demo loader, rich vs minimal demo, backfill pointers. |
| [`docs/governance/TESTING_RULES.md`](../governance/TESTING_RULES.md) | Integration env, deterministic embedding mode, Qdrant collection reset. |
| [`docs/governance/ARCHITECTURAL_INVARIANTS.md`](../governance/ARCHITECTURAL_INVARIANTS.md) | Non-negotiables (e.g. model output ≠ evidence). |

---

## Existing references

- **[`docs/plans/phase_1_8_completion_program.md`](../plans/phase_1_8_completion_program.md)** — Tracks **A–H**; **Track F** = this onboarding series (**F1** + **F2** shipped; **F3–F5** open).
- **`docs/phases/`** — phase narratives (read for depth; do not assume every aspirational line is shipped).
- **`docs/governance/`** — assistant/human guardrails, documentation standards, status reporting rules.

---

## Known limitations (onboarding-relevant)

- **Onboarding is not finished** — F2 adds a **minimal** hands-on guide; **F3–F5** (diagram, expanded failure/Qdrant narrative, curl/Python cookbook) are **future work**.
- **`vector_status=pending`** is common until **manual** indexing/backfill; empty **`evidence_units`** can be **coherent** for a **minimal** pipeline (see pipeline guide).
- **Production embeddings**, **OCR/ASR/video**, **Phase 7 boosting**, **`/answer`**, and **Phase 9** scope are **not** decided in this slice — follow [`docs/plans/phase_1_8_completion_program.md`](../plans/phase_1_8_completion_program.md) and status docs.

---

## Next onboarding slices (Track F)

| Slice | Intent (from completion program) |
|-------|----------------------------------|
| **F3** | Full pipeline narrative + architecture diagram |
| **F4** | Failure modes + Qdrant operator detail (beyond F2 troubleshooting links) |
| **F5** | Examples cookbook (curl / Python) |

---

## Open decisions (do not block F1 / F2)

Product and research calls for **production embeddings**, **multimodal engines**, **Phase 7 Slice 7I**, **model adapters**, and **`/answer`** remain **outside** this document — see **§15 Open decisions** in [`docs/plans/phase_1_8_completion_program.md`](../plans/phase_1_8_completion_program.md) and governance/status tables. This skeleton **does not** invent answers for those topics.
