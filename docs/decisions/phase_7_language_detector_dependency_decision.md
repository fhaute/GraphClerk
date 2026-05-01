# Phase 7 — Language Detector Dependency Decision (Research)

| Field | Value |
|-------|--------|
| **Track / slice** | **Track C — Slice C2** (Phase 1–8 Completion Program) |
| **Document type** | **Research / decision record only** — no dependency added, **no** `pyproject.toml` / `requirements*` edits, **no** backend or frontend behavior changes |
| **Phase 9** | **Not started** |
| **Baseline** | [`PHASE_7_AUDIT.md`](../audits/PHASE_7_AUDIT.md) and shipped code remain **valid**; **production language detection is not implemented** and **no** new package is installed by this slice |
| **Parent ADR** | [`phase_7_context_intelligence_completion_decisions.md`](phase_7_context_intelligence_completion_decisions.md) (Track C Slice **C1**) |
| **Gates** | **C3** (adapter implementation) **depends on** this decision |
| **Date** | 2026-05-01 |

---

## Executive summary

| Question | Answer |
|----------|--------|
| Should GraphClerk implement **production** language detection **before Phase 9**? | **Yes, optionally** — aligned with C1 option **B**: ship a **local**, **explicitly configured** detector behind the existing adapter boundary **without** making it the default install story for Phases **1–8**. |
| Which dependency is **recommended first**? | **[`lingua-language-detector`](https://pypi.org/project/lingua-language-detector/)** on PyPI (Apache-2.0; **Python ≥ 3.12**; **Production/Stable**). |
| Optional or required? | **Optional extra** only — core `graphclerk-backend` install stays free of this wheel set. |
| Default behavior? | **`NotConfigured`** remains the **only** default; **no silent fallback** when the extra is absent or config is `not_configured`. |
| Next slice? | **C3** — implement a **`LinguaLanguageDetectionAdapter`** (name TBD) behind `GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER`, plus tests and docs **without** changing default runtime behavior until operators opt in. |

**Secondary candidate (documented for C3 “multiple adapters later”):** [`cld3-py`](https://pypi.org/project/cld3-py/) — smaller wheels, prebuilt **Windows AMD64** among other platforms, **Apache-2.0**, but PyPI **Development Status :: 4 - Beta** (higher product risk than Lingua’s Stable).

---

## Current Phase 7 detector baseline

From [`backend/app/services/language_detection_service.py`](../../backend/app/services/language_detection_service.py) (read-only reference):

- **`LanguageDetectionResult`**: `language: str | None`, `confidence: float | None` in **[0.0, 1.0]** or `None`, non-empty `method: str`, `warnings: list[str]`.
- **`NotConfiguredLanguageDetectionAdapter`** — raises `LanguageDetectionUnavailableError`.
- **`DeterministicTestLanguageDetectionAdapter`** — tests / deterministic rules only; **not** a linguistics engine.
- **No** third-party detector is wired into ingestion or retrieval in the audited baseline.

GraphClerk backend declares **`requires-python = ">=3.12"`** in [`backend/pyproject.toml`](../../backend/pyproject.toml).

---

## Research method and sources

1. **PyPI project pages and JSON APIs** — `requires-python`, classifiers, license fields, release dates, wheel types where visible.  
2. **Upstream / docs sites** — licensing, model redistribution terms, maintenance (e.g. fastText archived status).  
3. **GitHub README / releases** — API guarantees (confidence ranges, determinism notes), platform notes.  

Sources are cited inline in [Candidate notes](#candidate-notes) and summarized in the [comparison table](#candidate-comparison-table).

---

## Candidate comparison table

| Candidate | Local / no network | License | Python **3.12** / **Windows** confidence | Install footprint | Confidence score | Short-text behavior | Maintenance | Fit for GraphClerk | Verdict |
|-----------|-------------------|---------|------------------------------------------|-------------------|------------------|----------------------|-------------|-------------------|---------|
| **[lingua-language-detector](https://pypi.org/project/lingua-language-detector/)** | Yes | **Apache-2.0** (PyPI classifier + [LICENSE](https://github.com/pemistahl/lingua-py/blob/main/LICENSE.txt)) | **High** — PyPI states **Python ≥ 3.12**; `bdist_wheel` releases listed on PyPI (platform-specific wheels; **large** ~170 MB per 2.2.0 file entry on [PyPI files](https://pypi.org/project/lingua-language-detector/#files)) | **Heavy** (wheel size) | **Yes** — probabilities **0.0–1.0** per [README](https://raw.githubusercontent.com/pemistahl/lingua-py/main/README.md) (`compute_language_confidence_values`) | Project positions Lingua for **short and mixed** text ([GitHub description](https://github.com/pemistahl/lingua-py)) | **Active** (e.g. [v2.2.0 release 2026-03-09](https://github.com/pemistahl/lingua-py/releases/tag/v2.2.0)) | Strong match to contract + **3.12** stack | **Recommended** |
| **fastText `lid.176` + official bindings / wrappers** | Yes (local model) | **Code**: MIT ([`facebookresearch/fastText`](https://github.com/facebookresearch/fastText)); **pretrained lid models**: **CC BY-SA 3.0** ([fastText language ID docs](https://fasttext.cc/docs/en/language-identification.html)) | Medium — native build / wheels vary; upstream repo **archived 2024-03-19** ([GitHub archive notice](https://github.com/facebookresearch/fastText)) | **Large** if using `lid.176.bin` (~126 MB per docs) or smaller `ftz` | Top-1 probability available via API patterns; not mapped here | Good on paragraphs; short text weaker than Lingua in third-party benchmarks cited by Lingua project | **Upstream archived** | **Share-alike** models + archive risk | **Not first choice** |
| **[fast-langdetect](https://pypi.org/project/fast-langdetect/)** | Yes (bundles lite model) | **MIT** (code) + **CC BY-SA 3.0** (fastText models) per [PyPI project description](https://pypi.org/project/fast-langdetect/) | **High** for Python (states **3.9–3.13** on PyPI); Windows usage depends on wheel matrix — verify at install time in C3 | **Moderate** (~0.79 MB wheel 1.0.0 on PyPI) | From fastText probabilities | Similar to fastText family | **Maintained** (2025 releases on PyPI) | Good speed; **same model license** as fastText | **Alternate**, not default vs Lingua |
| **[langdetect](https://pypi.org/project/langdetect/)** | Yes | PyPI **`license` metadata: MIT** ([PyPI JSON](https://pypi.org/pypi/langdetect/json)); classifiers also list Apache — treat **MIT** as declared license field | **Runs on 3.12** (pure Python); no `requires_python` pin on PyPI | **Light** | **Yes** via `detect_langs` probabilities | **Poor** — documentation states algorithm is **non-deterministic** for short/ambiguous text unless `DetectorFactory.seed` is set ([PyPI long description](https://pypi.org/pypi/langdetect/json)) | **Stale** (last release **2021-05-07** on [PyPI](https://pypi.org/project/langdetect/)) | Weak on **determinism** criterion | **Rejected** for default production path |
| **[langid](https://pypi.org/project/langid/)** (legacy) | Yes | **BSD** ([PyPI](https://pypi.org/project/langid/)) | Wheels **sdist-era** (last **2016** on PyPI); **not** recommended for modern pin | **Light** | Returns log-prob style scores in examples ([langid.py README](https://github.com/saffsd/langid.py)) | OK on paragraphs | **Unmaintained** | Superseded by forks | **Rejected** |
| **[py3langid](https://pypi.org/project/py3langid/)** | Yes | **BSD-3-Clause** fork ([PyPI](https://pypi.org/project/py3langid/)) | **Good** — `>=3.8`, wheel **2024-06-18**; adds **`numpy`** dependency ([PyPI description](https://pypi.org/project/py3langid/)) | Moderate + **numpy** transitive | Probabilities mappable | Better than legacy langid | **Moderate** (fork; docs note partial maintenance) | Viable **lightweight** alternative; numpy footprint | **Runner-up** |
| **[pycld3](https://pypi.org/project/pycld3/)** | Yes | Apache-2.0 ([PyPI](https://pypi.org/project/pycld3/)) | **Poor for GraphClerk** — PyPI states wheels only **CPython 3.6–3.9**; **no** Windows wheels in matrix | Medium | CLD3 returns probabilities | OK | **Stale / alpha** | **Incompatible** with **3.12** story | **Rejected** |
| **[cld3-py](https://pypi.org/project/cld3-py/)** | Yes | Apache-2.0 (PyPI classifiers) | **High** — PyPI states **Python ≥ 3.10** and prebuilt wheels including **Windows AMD64** ([PyPI](https://pypi.org/project/cld3-py/)) | **Smaller** than Lingua (~0.65 MB wheel for 3.1.0 file on PyPI) | CLD3 API exposes language probabilities | Good for mixed scripts | **Beta** on PyPI; **actively released** (e.g. 3.1.0 **2026-04-23** on PyPI) | Strong; beta status | **Secondary** |
| **[charset-normalizer](https://pypi.org/project/charset-normalizer/)** | Yes | **MIT** ([PyPI](https://pypi.org/project/charset-normalizer/)) | Excellent | **Light** | Language guess tied to **encoding detection** path | Docs: unreliable for mixed Latin languages and **tiny** content ([charset-normalizer README](https://github.com/jawah/charset_normalizer)) | **Active** | **Wrong tool** for primary Unicode EU text language ID | **Not recommended** as primary detector |

---

## Candidate notes

### lingua-language-detector

- **Summary:** Rust-backed **Lingua** bindings for Python; **local** inference; **Python ≥ 3.12** on current 2.x line ([PyPI](https://pypi.org/project/lingua-language-detector/), [release notes 2.2.0](https://github.com/pemistahl/lingua-py/releases/tag/v2.2.0)).  
- **Pros:** **Apache-2.0**; **Production/Stable**; explicit **probability 0.0–1.0** API ([README](https://raw.githubusercontent.com/pemistahl/lingua-py/main/README.md)); aligns with backend **3.12** floor; no separate **CC BY-SA** model blob like fastText lid.  
- **Cons:** **Very large** wheels (~**170 MB** for 2.2.0 per [PyPI file listing](https://pypi.org/project/lingua-language-detector/#files)); environments banning native extensions cannot use 2.x (pure-Python **1.x** branch exists per [GitHub README](https://github.com/pemistahl/lingua-py) but targets older Python — **not** aligned with `requires-python >=3.12` for GraphClerk’s default matrix).  
- **Sources:** [PyPI](https://pypi.org/project/lingua-language-detector/), [GitHub pemistahl/lingua-py](https://github.com/pemistahl/lingua-py), [Apache LICENSE](https://github.com/pemistahl/lingua-py/blob/main/LICENSE.txt), [README raw](https://raw.githubusercontent.com/pemistahl/lingua-py/main/README.md).  
- **Fit with `LanguageDetectionResult`:** Map detected ISO code → `language`; use top probability → `confidence`; `method` e.g. `lingua_v2`; optional warnings for low confidence / ambiguous top-2.  
- **Verdict:** **Selected** as first production-capable adapter target.

### fastText (official lid models + ecosystem)

- **Summary:** Industry-standard n-gram classifier; **176 languages**; models **CC BY-SA 3.0** ([fastText docs](https://fasttext.cc/docs/en/language-identification.html)).  
- **Pros:** Fast; well-known.  
- **Cons:** Upstream **[archived Mar 2024](https://github.com/facebookresearch/fastText)**; **Share-alike** model license complicates some redistribution narratives; separate **MIT** code vs **CC BY-SA** weights.  
- **Sources:** [fastText language identification](https://fasttext.cc/docs/en/language-identification.html), [GitHub archive](https://github.com/facebookresearch/fastText).  
- **Fit:** Map `__label__xx` → `language`; normalize score to `[0,1]` in adapter.  
- **Verdict:** **Not first** — maintenance + **CC BY-SA** model coupling.

### fast-langdetect

- **Summary:** Wrapper packaging **fastText** `lid.176` models; **MIT** code + **CC BY-SA 3.0** models ([PyPI](https://pypi.org/project/fast-langdetect/)).  
- **Pros:** Small wheel vs Lingua; offline; Python **3.9–3.13** stated on PyPI.  
- **Cons:** Same **model license** as fastText; historical NumPy pain with upstream fastText (project notes “no numpy required” in current generation per [GitHub](https://github.com/LlmKira/fast-langdetect) — verify in C3 CI matrix).  
- **Verdict:** **Alternate** if Lingua footprint is unacceptable.

### langdetect

- **Summary:** Port of older Google language-detection; **MIT** in PyPI metadata ([JSON](https://pypi.org/pypi/langdetect/json)).  
- **Cons:** **Non-deterministic** without seeding; **no releases since 2021** ([PyPI history](https://pypi.org/project/langdetect/#history)).  
- **Verdict:** **Rejected.**

### langid.py / py3langid

- **langid:** **BSD** but **stale** ([PyPI](https://pypi.org/project/langid/)).  
- **py3langid:** **BSD** fork, **2024** wheel, **numpy** required ([PyPI](https://pypi.org/project/py3langid/)).  
- **Verdict:** **py3langid** = **runner-up** lightweight path; not default.

### pycld3

- **Summary:** Older CLD3 bindings; **Alpha**; Python **≤3.9** on published wheel matrix ([PyPI](https://pypi.org/project/pycld3/)).  
- **Verdict:** **Rejected** for **3.12**.

### cld3-py

- **Summary:** Modernized CLD3 bindings; **Beta**; **Windows AMD64** + **Linux** wheels; **Python 3.10–3.14** per [PyPI](https://pypi.org/project/cld3-py/).  
- **Verdict:** **Secondary** adapter candidate in C3 or later slice **C3b**.

### charset-normalizer

- **Summary:** **MIT**; primary mission is **encoding** detection; optional “spoken language” hints ([docs](https://charset-normalizer.readthedocs.io/en/latest/api.html)).  
- **Verdict:** **Not** primary language ID for EvidenceUnit **Unicode** text.

---

## Decision

**Recommended (explicit):**

| Item | Value |
|------|--------|
| **Selected candidate** | **`lingua-language-detector`** ([PyPI](https://pypi.org/project/lingua-language-detector/)) |
| **Dependency mode** | **Optional** `[project.optional-dependencies]` extra (exact extra name **`language-detector`** suggested in C3 — subject to repo naming review) |
| **Default behavior** | **`GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER=not_configured`** (or absent → same) |
| **Implementation slice** | **C3** — new adapter class + factory wiring + **import guard** if extra not installed |
| **Production behavior** | **Opt-in only** — enabling adapter requires **both** installing the extra **and** explicit settings validation (fail closed) |

**If Lingua is later deemed operationally unacceptable** (wheel size / CI image caps): fall back to **`cld3-py`** as the **first alternate** implementation, then **`py3langid`**, without changing the **default** `NotConfigured` story.

**Explicit non-selection of “no detector ever” (option A from C1):** Not chosen here — C1 bias **B** is satisfied by a **safe local** primary pick; operators who never install the extra still get **A**-style behavior.

---

## Rationale

1. **License:** Apache-2.0 is straightforward for redistribution alongside GraphClerk.  
2. **Python alignment:** Backend **`>=3.12`** matches Lingua **2.x** requirement ([PyPI](https://pypi.org/project/lingua-language-detector/)).  
3. **Contract fit:** Native **0.0–1.0** confidence API ([README](https://raw.githubusercontent.com/pemistahl/lingua-py/main/README.md)) maps cleanly to `LanguageDetectionResult`.  
4. **Local-first:** No network I/O in the detector itself.  
5. **Determinism:** Prefer Lingua’s deterministic inference path over **langdetect**’s documented nondeterminism ([langdetect PyPI description](https://pypi.org/pypi/langdetect/json)).  
6. **Tradeoff accepted:** **Large wheels** — document in ops/onboarding; mitigated by **optional** extra.

---

## Dependency recommendation

- Add **`lingua-language-detector`** only under a new optional extra (e.g. **`language-detector`**) in **C3** — **not** in this slice.  
- Pin **minimum version** in C3 after one CI smoke install (e.g. `>=2.2.0` proposal — **verify** compatibility in implementation).  
- Document **disk / image** impact (~170 MB order-of-magnitude per PyPI file sizes for 2.2.0).

---

## Configuration recommendation (design only — not implemented here)

| Setting / env | Purpose |
|----------------|---------|
| **`GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER`** | Enum-like string: **`not_configured`** (default) \| **`lingua`** (production adapter when extra installed) — additional values **`cld3`** / **`py3langid`** may be added later under option **C** |
| **Guards** | Reject unknown values at settings parse; **`APP_ENV=prod`** may require explicit allowlist (mirror semantic-search embedding guard pattern from completion program **Track B**). |
| **No silent fallback** | If adapter is **`lingua`** but import fails → **startup failure** or explicit **`LanguageDetectionUnavailableError`** surface policy (choose in C3; default bias: **fail loud at factory**, not silently downgrade). |
| **Optional model path** | **None** for Lingua (models embedded in wheel / library as provided upstream). |

---

## Adapter behavior recommendation (for C3)

- **Map** Lingua `Language` / ISO codes → `language: str | None`.  
- **Map** top `compute_language_confidence_values` entry → `confidence` in **[0, 1]** or `None` if API returns unknown.  
- **`method`:** fixed string e.g. **`lingua_language_detector_v2`**.  
- **Warnings:** reuse and extend:  
  - **`language_text_empty`** — whitespace-only (align with `DeterministicTestLanguageDetectionAdapter`).  
  - **`language_text_too_short`** — below configured char threshold (adapter-level policy).  
  - **`language_detector_low_confidence`** — top probability &lt; configurable threshold.  
  - **`language_detector_unavailable`** — import / runtime init failure when config asked for Lingua.  
- **Never** mutate `text` or `source_fidelity` (unchanged from Phase 7 charter).

---

## Failure semantics

| Scenario | Recommended handling (C3/C4) |
|----------|-------------------------------|
| **Extra not installed** but config requests `lingua` | **Fail closed** at adapter construction or settings validation |
| **Detector runtime error** | Bubble as `LanguageDetectionError` or wrapped exception per existing service pattern |
| **Invalid result shape** | Existing `_validate_detection_result` rejects |
| **Unsupported / empty input** | Return `language=None` with warnings (or raise if policy prefers hard fail — **defer** to C4 for ingestion) |
| **Low confidence** | Emit **`language_detector_low_confidence`**; still may write `language` + `language_confidence` **or** leave absent — **C4 product decision** (warn vs omit metadata) |
| **Ingestion warn vs fail** | **Undecided here** — record as **C4** (enrichment wiring) decision per C1 |

---

## Testing recommendation (future C3)

- Adapter unavailable (missing extra) + bad config  
- Valid detection on representative strings  
- Empty / short text  
- Low confidence path  
- Invalid post-processed result rejected by `_validate_detection_result`  
- **Deterministic** repeat calls on same input (record seed / builder config if any)  
- Config default `not_configured`  
- Config `lingua` with extra installed  
- **No** `text` / `source_fidelity` mutation  
- **No network** (static test asserting no HTTP clients in adapter module — optional lint)

---

## Docs / onboarding impact (when C3–C4 ship)

- [`GRAPHCLERK_PIPELINE_GUIDE.md`](../onboarding/GRAPHCLERK_PIPELINE_GUIDE.md) — where language metadata appears; disk note for optional extra.  
- [`TROUBLESHOOTING_AND_OPERATIONS.md`](../onboarding/TROUBLESHOOTING_AND_OPERATIONS.md) — install failures, config typos, “detector not evidence.”  
- [`EXAMPLES_COOKBOOK.md`](../onboarding/EXAMPLES_COOKBOOK.md) — only if env / request examples change.  
- [`KNOWN_GAPS.md`](../status/KNOWN_GAPS.md) / [`TECHNICAL_DEBT.md`](../status/TECHNICAL_DEBT.md) / [`PROJECT_STATUS.md`](../status/PROJECT_STATUS.md) — honest deltas per [`STATUS_REPORTING.md`](../governance/STATUS_REPORTING.md).

---

## Implementation slice proposal

| Slice | Work |
|-------|------|
| **C3** | Optional extra + **`Lingua`** adapter + settings + factory + tests |
| **C3b** (optional) | Second adapter (**`cld3-py`**) if Fred requests smaller footprint |
| **C4** | Enrichment wiring + warn/fail policy |

---

## Risks

| Risk | Notes |
|------|--------|
| **Wheel / image size** | Lingua **~170 MB** per PyPI — CI and Docker layer bloat |
| **Native extension** | Alpine / unusual arches may need testing |
| **Over-trust in `language` metadata** | Operators may treat tags as evidence — docs must repeat “metadata only” |
| **False positives on short EU chunks** | Mitigate with thresholds + warnings |

---

## Open questions

1. Exact **optional-extra** name in `pyproject.toml` (`language-detector` vs `lingua`).  
2. **Low-confidence** policy: omit `language` vs write with warning (**C4**).  
3. Whether **`cld3-py`** should be implemented **in parallel** in C3 for footprint-sensitive deployments.

---

## Non-goals

- No **remote / LLM** language detection.  
- No **translation**.  
- No **OCR/ASR/video** coupling.  
- No **Phase 9**.  
- No **pyproject** edit **in this slice**.  
- No change to **audit** artifacts.

---

## Final recommendation

Adopt **`lingua-language-detector`** as the **first** production-capable, **optional**, **locally executed** language detector for Phase 7 completion, keeping **`NotConfigured`** as the **default** and **fail-closed** configuration semantics. Proceed to **C3** implementation planning with this dependency; keep **`cld3-py`** documented as the **first alternate** if wheel size or ops constraints dominate.

---

## References

- C1 completion ADR: [`phase_7_context_intelligence_completion_decisions.md`](phase_7_context_intelligence_completion_decisions.md)  
- Contract: [`language_detection_service.py`](../../backend/app/services/language_detection_service.py)  
- fastText model license: [fastText language identification](https://fasttext.cc/docs/en/language-identification.html)  
- fastText archive: [facebookresearch/fastText](https://github.com/facebookresearch/fastText)
