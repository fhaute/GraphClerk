# GraphClerk — Error-Aware Evidence Reasoning Research & Implementation Guideline

> Status: **PROPOSAL / RESEARCH NORTH STAR — NOT IMPLEMENTED**
>
> Created: 2026-11-06
>
> Scope: GraphClerk, with optional later integration to EBES and other consumers.
>
> This document is an investigation and phased engineering guideline, **not approval to modify production behavior, protected contracts, or deploy a trained detector**. Obtain explicit approval for each implementation gate.

## 1. Why this document exists

GraphClerk is an evolving, local-first, graph-guided evidence-routing layer, not a finished answer generator. Its principle remains **"Search meaning first, then retrieve evidence."** It already provides source artifacts, traceable evidence units, semantic indexes, graph links, retrieval packets, logs, warnings, and several confidence fields.

The research question emerging from our discussion is stronger than "How do we calculate a better confidence score?"

> **Can GraphClerk learn to recognize the circumstances in which its own evidence evaluation, retrieval, or interpretation is likely to fail — identify what could be wrong and why — and request the right verification before an error propagates?**

We want to **upgrade GraphClerk using lessons from uncertainty and prediction-error research**, not duplicate or replace FileClerk. A separate error-detection network is a research candidate; its superiority to simpler methods must be measured, not assumed.

The proposed direction is **claim → challenge → investigation → independently verified outcome → error pattern → future detection**. Store both mistakes and correct decisions that survived challenge so the detector does not learn that disagreement itself equals error.

## 2. Research inspiration and limits

A 2026 *Nature Neuroscience* study, discussed in our research radar, examined how human claustrum neurons encode uncertainty and prediction errors during learning:

- Original research: https://www.nature.com/articles/s41593-026-02475-x
- Its relevance here is **conceptual**, not a demonstrated architecture for software agents.
- Do not conflate neuroscientific signals with probabilities of truth, and do not claim that a brain-inspired network is necessarily better.

Three different quantities must stay distinct:

1. **Confidence / evidential support:** How strongly does available evidence support a specific proposition? A retrieval or ranking score is **not inherently** a calibrated probability that the claim is true.
2. **Uncertainty:** What remains unknown and why? Distinguish insufficient evidence, conflicting evidence, source dependence, ambiguous intent, out-of-distribution conditions, stale observations, measurement limits, and model uncertainty.
3. **Prediction error:** What was predicted, what was later observed, and what discrepancy occurred? A mismatch does **not** prove the original claim was false; the observation or environment may also have changed.

Related lines worth investigating: uncertainty decomposition (aleatoric vs epistemic), probabilistic calibration, selective prediction and abstention, NLI/contradiction detection, causal/source-dependency graphs, temporal knowledge graphs, conformal risk controls where assumptions hold, error-detection ensembles, and GNNs over evidence-claim graphs. All are candidates, not adopted components.

## 3. Current repository baseline — checked 2026-11-06

Repository: https://github.com/fhaute/GraphClerk (default branch: `master`).

Relevant existing files:

- `README.md` — honest implementation state; phases 1–8 scopes, phase 9 proposed; **no** `POST /answer` in current API.
- `docs/governance/PROJECT_PRINCIPLES.md` — artifact fidelity, source-backed evidence, FileClerk packets, warnings.
- `docs/governance/CONTRACTS.md` — protected Artifact, EvidenceUnit, Graph, RetrievalPacket and FileClerk interfaces.
- `docs/status/KNOWN_GAPS.md` — phase limitations and deferred behavior.
- `docs/audits/PHASE_4_AUDIT.md` — explicitly labels confidence scoring **simple heuristic, not calibrated**.
- `backend/app/services/retrieval_packet_builder.py` — combines route score, intent confidence and selected evidence confidence, then deducts fixed warning penalties; determines `answer_mode`.
- `backend/app/services/query_intent_service.py` — deterministic keyword classifier with fixed confidence constants.
- `backend/app/models/evidence_unit.py`, `backend/app/models/graph_edge.py`, graph-evidence link models and `backend/app/models/retrieval_log.py` — store different kinds of confidence.
- `docs/phases/graph_clerk_phase_9_ide_integration_developer_evidence_orchestration.md` — proposed IDE/MCP integration and explicit FileClerk boundary.

**Important code-level investigation:** `retrieval_packet_builder._compute_confidence` uses `c.unit_confidence or c.support_confidence or 0.0`. Because a meaningful `0.0` is falsy in Python, an explicitly zero unit-confidence can fall back to support confidence. Reproduce with a focused regression test before labeling it a defect or changing behavior.

**Another baseline caveat:** parser/extractor `confidence=1.0` can signal high extraction fidelity; it does not certify the factual truth of source text. Do not interpret heterogeneous confidence fields as interchangeable probabilities.

Do not infer that any model, classifier, correction learner, or outcome-verification network is already implemented. No Phase 9 implementation is implied by the phase document. This document proposes a *new*, independently gated research workstream, not a unilateral renumbering of existing phases.

## 4. The target distinction: not another score formula

**Current broad pattern:**

```text
question → intent heuristic → semantic route → evidence & graph traversal
         → FileClerk RetrievalPacket → aggregate confidence / warnings / answer_mode
```

**Research target (parallel observer first):**

```text
                   ┌─────────────────────────────────┐
question → FileClerk → RetrievalPacket + source refs ├→ normal consumer (unchanged)
                   └──────────────┬──────────────────┘
                                  ↓
                     Error-aware observer (shadow)
                                  ↓
              claim/evidence/provenance graph features
                                  ↓
       suspicious mechanism + affected claims + why + next check
                                  ↓
             independent validation (not self-approval)
                                  ↓
           outcome & error-event ledger (append-only)
                                  ↓
     governed evaluation / optional offline detector training
                                  ↓
        measured proposal for advisory integration (later)
```

FileClerk remains the source of bounded retrieval packets. The detector must **not** bypass governance, secretly retrieve extra data, fabricate evidence, mutate original artifacts, or directly change answers while in shadow mode.

A detector output is **an allegation of risk** until verification. It must distinguish:
- `suspected_error` from `verified_error`;
- `user_disagreement` from `factual_error`;
- `not_what_user_asked` (intent misalignment) from `incorrect_fact`;
- `contradiction` from genuinely different conditions or time scopes;
- `no_evidence` from `negative_evidence`;
- a source **quoting** a claim from an independent source confirming that claim.

## 5. What to detect (failure taxonomy)

Minimum candidate categories, each backed by examples and evaluation rules:

| Code | Risk pattern | Verification question |
|---|---|---|
| INTENT_MISMATCH | Answer addresses the wrong request or scope | What did user actually ask? |
| UNSUPPORTED_CLAIM | Relevant evidence does not entail the claim | Which specific evidence span entails it? |
| CONTRADICTION | Claims conflict under matching scope/conditions | Are entities, times and qualifications aligned? |
| SOURCE_DEPENDENCE | Apparent multi-source agreement stems from one origin | Are provenance chains independent? |
| STALE_EVIDENCE | A claim's validity may have expired | What timestamp and change event apply? |
| OOD_OR_UNFAMILIAR | Query or evidence differs from evaluated training conditions | Is detector performance established here? |
| EXCESS_GENERALIZATION | Narrow finding treated as universal | Which boundary conditions were dropped? |
| MISSING_CONTEXT | Essential entity, jurisdiction, environment or assumption omitted | What context changes the answer? |
| RETRIEVAL_GAP | Relevant evidence not retrieved or pruned | Did budget/routing hide critical support? |
| FALSE_PRECISION | Numerical confidence presented as calibrated truth | Is this number validated against outcomes? |
| MODEL_OBSERVATION_MISMATCH | Prediction and observation differ | Which model, sensor or environment is wrong? |
| RESOLVED_CHALLENGE | Claim challenged but ultimately verified | Avoid rewarding false positives |

An event can have multiple labels and `undetermined` as a legitimate final status.

## 6. Correction and learning record — proposed schema

Never silently overwrite or discard the original response when corrected. Propose versioned, append-only events with durable links, suitable for PostgreSQL initially and possible EBES interoperability later. No new table is authorized solely by this document.

### 6.1 Main records

**ClaimRecord:** `claim_id`, `statement`, `scope`, `entity_refs`, `time_validity`, `extraction_method`, `source_evidence_unit_ids`, `retrieval_packet_id`, `model_or_rule_version`, `captured_at`, `access_policy`. Claim text is *an assertion*, not automatically truth.

**ChallengeEvent:** `challenge_id`, `claim_ids`, `actor_or_source_ref`, `challenge_type`, `original_feedback` (if permitted), `observed_at`, `consent_scope`, `reason`, `status`. A user's correction is feedback, not automatic ground truth.

**VerificationEvent:** `verification_id`, `challenge_id`, `verification_method` (independent source / controlled test / expert review / reproducible calculation / unresolved), `evidence_refs`, `verifier`, `verified_at`, `outcome` (confirmed_error / confirmed_original / partly_correct / unresolved / changed_conditions), `reasoning_summary`, `limitations`, `reproducibility`.

**PredictionObservationEvent:** `prediction_id`, `claim_id`, `target_variable`, `expected_value_or_distribution`, `prediction_time`, `observation_id`, `observation_value`, `observation_time`, `measurement_quality`, `error_metric`, `conditions`. Only calculate a meaningful error metric for compatible measurements; keep missing outcomes as censored/unresolved.

**ErrorPatternRecord:** `pattern_id`, `taxonomy_labels`, `feature_schema_version`, `supporting_verified_event_ids`, `counterexamples`, `known_limits`, `detector_version`, `created_at`. Patterns are hypotheses until evaluated.

**DetectionEvent:** `detection_id`, `retrieval_packet_id`, `affected_claim_ids`, `detector_version`, `risk_types`, `supporting_features`, `recommended_check`, `decision` (advisory only initially), `created_at`, `validation_status`.

### 6.2 Rules

- Separate **event time** and **recording time**; retain previous states, explicit supersession and provenance.
- Record absence of evidence as missing, **not** confidence zero.
- Never treat model-generated explanations, user disagreement, or a detector's self-consistency as independent verification.
- Store accurate source quotes/locations and scoped identifiers; don't copy whole conversations into training data by default.
- Consent, deletion/erasure, retention, access control, tenant isolation and PII minimization must be designed **before** collecting conversational feedback.
- If append-only records contain personal data, plan privacy-compatible erasure or cryptographic deletion of protected payloads while retaining permissible nonidentifying audit metadata.
- Source or participant consent must govern reuse and training; avoid unapproved conversation ingestion.
- Keep model predictions, human review, verified measurements, and retrieved source statements in distinct provenance types.
- Trace every derived feature back to origin, transformation and version.

### 6.3 Example event sequence (illustrative, not actual user data)

```text
claim: "An installed PWA always opens another installed PWA."
challenge: "Platform/browser dependent; blanket claim unsupported."
verification: Compare platform specifications and repeat a browser/device test matrix.
outcome: Overgeneralization confirmed only after independent checks.
error_pattern: Dropped environment-specific constraints.
future_detector: Flag universal wording where evidence covers narrower platforms.
counterexample: A challenge to a correct platform-specific claim was rejected.
```

## 7. Network investigation: candidates, not commitments

### A. Deterministic controls (baseline)
Source independence checks, timestamp/scope mismatch detection, null-safe confidence handling, citation entailment checks where possible, duplicate-origin collapsing, explicit missing-data warnings.

### B. Lightweight supervised baseline
A calibrated classifier on claim–evidence–provenance features. Establish whether machine learning adds value beyond heuristics.

### C. Textual contradiction / entailment model
Compare claim and evidence with NLI-style models. Test domain shift, quoted speech, negation, numerical units and temporal qualifications.

### D. Graph neural network (GNN) / graph-aware detector
Candidate nodes: claims, source artifacts, evidence units, retrieval packets, predictions, observations and challenge/verification events. Candidate edges: `supports`, `contradicts`, `derived_from`, `same_origin_as`, `supersedes`, `predicted`, `observed`, `challenged_by`, `verified_by`.

Potential advantage: detect relational error motifs, correlated sources, conflicts and propagation paths that a flat score misses. Risks: label leakage, correlated splits, graph over-smoothing, brittle topology and cost. **Do not build a GNN until simple baselines and data availability justify it.**

### E. Temporal / sequential error detector
Study whether repeated verification failures or prediction–observation differences improve *future* error risk detection. Avoid training on future outcomes as features of past decisions.

### F. Active verification policy
Propose the cheapest next test with the greatest expected reduction in uncertainty; may recommend "abstain" or "ask for clarification." No unbounded autonomous browsing or user-data access.

## 8. Training and evaluation: prevent self-confirming errors

**Ground truth acquisition:** independent reproducible tests, primary references with appropriate domain expertise, adjudicated reviewer labels, controlled benchmarks and measured outcomes. Distinguish gold, silver and disputed labels.

**Dataset design:** positives (confirmed errors), negatives (confirmed correct despite challenge), near-miss conflicts, unresolved examples; diversity across domains, languages, model versions and source families.

**Leakage protections:** split by time and shared source lineage, not just random event; hold out entire source families, projects, tasks and challenge threads; deduplicate paraphrases and neighboring graph components where necessary.

**Baselines to compare:** (1) current GraphClerk confidence and warnings, (2) deterministic error checks, (3) calibrated linear/tree classifier, (4) NLI detector, (5) GNN/temporal model only if warranted. Measure added value, not novelty.

**Metrics:** precision/recall and PR-AUC per error class, false-alarm burden per 100 packets, missed critical errors, calibration (Brier/ECE only where the target probability is defined), risk–coverage curves, time to detection, verification cost, domain-shift robustness, throughput and latency, privacy/safety failures, and whether recommendations actually improve verified outcomes.

**Decision gates:** preregister success criteria before training; report confidence intervals and failure cases; demonstrate out-of-sample gains; perform ablations for source lineage, temporal signals and challenge outcomes. No automatic self-training on unverified model judgments.

## 9. Phased investigation / implementation roadmap

### Gate 0 — Repository baseline and contract audit (no behavior changes)
- Inventory confidence fields, their semantic definitions and sources.
- Reproduce zero-confidence fallback issue; classify and test without silently patching.
- Map FileClerk, model adapter, ingestion, retrieval logs and protected contracts.
- Check phase dependencies, data rights and privacy/erasure requirements.
- Deliver: baseline report, schema proposal, risk register, explicit approval request.

### Gate 1 — Error taxonomy and labeled fixtures (offline only)
- Develop annotation handbook for disagreement vs error, support vs relevance, temporal qualification and independent provenance.
- Assemble synthetic, public-domain, licensed and explicitly opted-in cases.
- Include verified-correct challenged claims and unresolvable cases.
- Deliver: anonymized fixture dataset, labeling agreement report, data cards, evaluation protocol.

### Gate 2 — Event ledger and shadow observer (feature-flagged)
- Propose schema/migrations only after review; version events, not original artifacts.
- Subscribe to bounded retrieval packet/log output; preserve idempotency, permissions, exact traceability and failure isolation.
- Expose advisory detections without changing `RetrievalPacket`, `answer_mode`, retrieval ranking or existing confidence values.
- Deliver: migration design, privacy threat model, shadow-run tests and rollback plan.

### Gate 3 — Baselines and experiment harness
- Implement deterministic checks and minimal statistical baseline.
- Add reproducible benchmarking with source-family/time splits.
- Quantify bottlenecks and false alarms.
- Deliver: results and **go/no-go on neural model investment**.

### Gate 4 — Candidate neural detectors (conditional)
- Compare NLI, flat classifier, graph-aware and temporal approaches using identical holdouts.
- Calibrate **defined outcomes**, not arbitrary confidence-field numbers.
- Persist model version, training lineage and false-positive counterexamples.
- Deliver: model card, benchmark, inference cost assessment; no promotion without evidence.

### Gate 5 — Advisory integration pilot (explicit approval)
- Provide `risk_type`, `claim_refs`, `why_flagged`, `source_refs`, `suggested_verification`, `uncertainty_type`, `detector_version`.
- Suggest additional bounded retrieval or abstention through governed interfaces only.
- Preserve original retrieval output and show side-by-side baseline versus detector.
- Deliver: user/IDE visibility, audit trail and opt-in pilot results.

### Gate 6 — Controlled influence on retrieval policy (separate approval)
- Consider only after longitudinal evaluation: rerank, ask clarification, escalate verification, or abstain for well-defined scenarios.
- Maintain fail-closed behavior where authority is missing; prevent detector from laundering a guess into evidence.
- Provide rollback, human review, continuous drift monitoring and documented authority rules.

**At every gate:** tests, docs/status changes, change review, backup/migration plan if relevant, privacy review, negative-case tests, and explicit approval before scope expansion. Do not claim Phase 9 complete or modify preexisting phase labels through this proposal.

## 10. Integration boundaries

- **GraphClerk:** evidence retrieval, provenance graph, retrieval packets, proposed error-observer / advisory risks.
- **FileClerk:** protected bounded retrieval orchestration; **not recreated** by the detector.
- **Model pipeline:** optional governed adapters, not general autonomous self-approval. Model output is not evidence.
- **EBES (future possibility):** append-only, authority-aware temporal truth/event substrate for claim, challenge, verification, prediction and observation history; **integration is proposed, not implemented or required** for early tests.
- **Axondrya / IDE agents:** future consumers of risk and verification signals; GraphClerk must not silently become an agent or code editor.
- **TLOT or other domains:** potential consumers only under their own subject-level policies and data rights.

## 11. Open research questions

1. Which meaningful errors can be detected **before** an answer exists, using retrieval-packet-only inputs?
2. How do we extract atomic claims if GraphClerk currently does not synthesize answers? Can a downstream opted-in consumer supply claim envelopes without expanding GraphClerk scope?
3. Which event types are observable versus merely inferred?
4. Can source dependence be inferred reliably from citations, metadata and textual similarity?
5. How do source recency and bitemporal validity affect contradiction detection?
6. What independently verifiable outcomes can be obtained without exposing private conversations?
7. Does separating evidence reliability, epistemic uncertainty, ambiguity and prediction error improve selective decisions?
8. Does a GNN beat cheaper baselines on real held-out cases?
9. How should models respond to stale or missing feedback without treating silence as success?
10. How can EBES interoperate without duplicating protected evidence or creating multiple sources of truth?
11. How should model/version changes be evaluated without confusing deployment change with environmental drift?
12. Which errors require human adjudication rather than automated verification?

## 12. Acceptance criteria for the research program

A proposal can progress beyond shadow mode only when:
- every flagged event is traceable to its source and detector version;
- disagreement, uncertainty, and confirmed error are separated;
- no private conversations are repurposed without appropriate authorization;
- original artifacts, existing confidence values and FileClerk contracts remain intact unless separately approved;
- independently validated error cases and challenged-but-correct counterexamples are included;
- held-out performance demonstrates a useful precision/recall and operational tradeoff against simple baselines;
- failures, unresolved cases and distribution shift are surfaced openly;
- rollback and safe disabling are verified;
- documentation accurately distinguishes **implemented**, **experimental**, **planned**, and **not supported**.

## 13. Immediate next action

**Do not start by building the neural network.** Begin with Gate 0 and Gate 1: a precise inventory of where GraphClerk confidence values originate, then a small independently labeled corpus of claim/challenge/verification events. Only then evaluate what a network can learn that rules and simpler classifiers cannot.

The engineering objective is not "make the score larger" or "always agree with user correction." It is:

> **Recognize recurring failure conditions, explain the suspected mechanism with source-linked evidence, ask for the right verification, and measurably reduce future verified errors.**

---

### Related references

- GraphClerk repository: https://github.com/fhaute/GraphClerk
- GraphClerk README and protected contracts: `README.md`, `docs/governance/CONTRACTS.md`
- Phase 4 audit / existing scoring: `docs/audits/PHASE_4_AUDIT.md`, `backend/app/services/retrieval_packet_builder.py`
- Human claustrum uncertainty/prediction-error research: https://www.nature.com/articles/s41593-026-02475-x

*Research and architecture proposal prepared from our 2026-11-06 discussion. Nothing herein is a claim that the proposed network, ledger, or EBES integration exists today.*
