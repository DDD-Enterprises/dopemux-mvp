# Codex Benchmark Audit 2026-04-11

## Scope

This audit is limited to the repo-truth-extractor benchmark system and the proof/artifact chain exercised by:

- `TP-RTE-BENCH-SPLIT-001`
- `TP-RTE-BENCH-DMB-001`
- `TP-RTE-BENCH-PRICE-001`
- `TP-RTE-BENCH-PROFILE-SYNTH-001`
- `TP-RTE-BENCH-R1C`
- `TP-RTE-BENCH-R1D`

This is a blocker-focused audit. It does not assign a single trustworthiness score.

## Verdicts By Axis

- `truth_grade_today = YES`
  - Lane separation exists in storage and reporting.
  - Advisory profile synthesis preserves uncertainty instead of laundering it.
  - Governance and evidence surfaces are append-oriented and reviewable.
- `live_grade_today = LANE_SPECIFIC_ONLY`
  - Direct-model live evidence exists.
  - The owned strict-extraction runtime-route lane is not live-ready in this environment.
- `cost_profile_design_ready = PARTIAL`
  - Pricing truth materially improved.
  - Remaining unknown/stale xAI pricing prevents clean cost-aware profile design across the active universe.
- `dynamic_profile_update_ready = NO`
  - The feedback loop exists in reviewable form only.
  - `PROFILE-SYNTH-001` explicitly disables auto-apply and all routing diffs are blocked in the latest proof.
- `phase_s_contract_parity = NO`
  - Phase S has fail-closed prompt/step controls.
  - It does not yet share the same live route identity, admissibility, or provider-backed execution rigor as the core runtime-route lane.
- `overall_restart_readiness_for_R1 = NO`
  - `R1C` proved dry-run distinctness.
  - `R1D` proved live restart is still blocked.

## Priority Findings

### 1. Route collapse and route ownership are no longer the primary unresolved design blocker

Observed:

- `R1C` produced `bounded_admissibility_result.json` with:
  - `status = admissible`
  - `lane_distinctness_proven = true`
  - `proof_execution_mode = dry_run`
  - `r1_restart_truthful = false`
- This means benchmark-mode route ownership restored bounded dry-run distinctness for the owned strict-extraction lane without claiming live restart truth.

Assessment:

- The benchmark system is now structurally capable of representing a distinct owned strict-extraction contest.
- Architectural ambiguity is no longer the main blocker for R1.

### 2. Live execution readiness is the current hard blocker for R1

Observed in `TP-RTE-BENCH-R1D`:

- `provider_readiness_report.json` shows no ready routes.
- OpenRouter-owned routes failed with `401 auth_rejected`.
- Direct OpenAI failed with `429 quota_or_billing`.
- `live_admissibility_result.json` shows:
  - `status = blocked`
  - `campaign_state = invalidated`
  - `blocking_reason_codes = ["INSUFFICIENT_PREFLIGHT_EVIDENCE"]`
  - `benchmark_run_ids = []`
- `live_distinctness_result.json` shows:
  - `status = blocked`
  - `live_attempted_route_ids = []`
  - `r1_restart_truthful = false`

Assessment:

- This is a clean fail-closed result.
- The system did not pretend that declared route ownership plus present env vars equals live readiness.
- R1 remains blocked for operational reasons, not for unresolved route-identity design.

### 3. The benchmark-to-profile feedback loop is now truthful but intentionally non-self-writing

Observed in `TP-RTE-BENCH-PROFILE-SYNTH-001`:

- `PROFILE_SYNTHESIS_SUMMARY.json` reports:
  - `feedback_loop_exists_in_reviewable_form = true`
  - `auto_apply_enabled = false`
  - `blocked_lane_count = 3`
- Eligible/caveated/blocked synthesis inputs remain separated:
  - `openrouter/openai/gpt-5.4` is synthesis-eligible.
  - `openrouter/x-ai/grok-4.1-fast` is caveated-only.
  - `xai/grok-4.20` is blocked by pricing uncertainty.
  - runtime-route candidates are blocked by admissibility.
- All routing diffs are blocked in the current proof bundle.

Assessment:

- This is good enough for review-grade advisory synthesis.
- It is not good enough for dynamic profile updates.
- The system is correctly refusing to auto-propose live routing changes from incomplete route or pricing truth.

### 4. Pricing integration is materially better but not complete enough for broad cost-driven profile design

Observed in `TP-RTE-BENCH-PRICE-001`:

- `coverage_counts`:
  - `priced = 4`
  - `partially_priced = 2`
  - `stale = 1`
  - `unknown = 1`
- Confirmed priced examples:
  - `openai/gpt-5.4`
  - `openai/gpt-5.4-mini`
  - `openrouter/openai/gpt-5.3-codex`
  - `openrouter/openai/gpt-5.4`
- Caveated:
  - `openrouter/x-ai/grok-4.1-fast`
  - `gemini/gemini-3.1-pro-preview`
- Blocked/stale:
  - `xai/grok-4.20`
  - `xai/grok-4.20-beta-0309-reasoning`

Assessment:

- Cost-profile design is now possible for a subset of the active universe.
- It is not yet clean across the whole candidate set.
- The current pricing layer is good enough to block unsafe cost synthesis and good enough to support partial advisory design.

### 5. Phase S has real contract hygiene, but not core-phase parity

Observed:

- `PhaseSAdapter` resolves registry/prompt metadata and emits `phase_s_registry_summary.json`.
- `PhaseSValidatorWrapper` only checks that registry output exists and is non-empty, with `strength_class = "moderate"`.
- Phase S tests cover:
  - registry selection and fail-closed invalid registry behavior
  - canonical step selection and duplicate rejection
  - post-tail prompt existence and redaction/secret-avoidance expectations

Assessment:

- Phase S is not sloppy.
- It is also not at parity with the runtime-route lane, which has explicit route identity, admissibility, live readiness, and provider telemetry surfaces.
- The gap is not just test count. It is contract depth and execution-surface depth.

## Medium-Priority Findings

### 6. Scoring is deterministic but not yet deeply calibratable

Observed:

- `benchmarking/scoring/task_scoring.py` is deterministic and policy-driven.
- `benchmarking/rollups/regression_compare.py` remains a regression skeleton with only a small delta surface.

Assessment:

- Scoring is reviewable and consistent.
- Calibration depth still looks limited.
- This is good enough for bounded comparative work, not for claiming a mature performance science layer.

### 7. Model and pricing coverage are sufficient for bounded decisions, not full-profile automation

Observed:

- `DMB-001` exercised three direct-model candidates with lane-distinct comparison output.
- `PRICE-001` covers the active benchmark universe but still contains caveated/stale/unknown lanes.

Assessment:

- Coverage is enough to support bounded advisory reasoning.
- Coverage is not enough to support broad automatic profile mutation across providers.

### 8. Prescan cost prediction is still heuristic

Observed:

- `lib/prescan/cost_estimator.py` uses approximate token and output heuristics and a hard-coded pricing basis.
- Prescan tests demonstrate truthfulness and incremental correctness, but not close coupling to benchmark pricing truth.

Assessment:

- Prescan cost prediction is useful as a planning hint.
- It should not be treated as the same authority class as benchmark pricing truth.

## Light Re-Verification

### 9. Hallucination prevention

Observed:

- Phase S prompt tests explicitly check for fail-closed wording and secret-leak anti-patterns.
- The benchmarking system separates direct-model, runtime-route, and profile-synthesis lanes in storage and output contracts.

Assessment:

- Strong enough for this audit.

### 10. Measurement immutability

Observed:

- Attempt persistence smoke verifies DB/filesystem linkage and evidence bundle references.
- Governance decision logging is append-only and supports supersession without mutation of prior rows.

Assessment:

- Strong enough for benchmark auditability.

### 11. Comparability controls

Observed:

- Comparison-lane tests assert canonical/comparison isolation and non-blocking comparison behavior.
- Route admissibility uses explicit blocker codes and fails closed when preflight evidence is missing.

Assessment:

- Strong enough for bounded contests.

### 12. Governance auditability

Observed:

- Governance packet tests require evidence refs and required actions.
- Governance history tests distinguish current effective decision from historical decisions.

Assessment:

- Strong enough for human review and audit traceability.

## Decision-Grade Conclusion

The benchmark system is now truth-grade for bounded operator decisions. It is not yet fully live-grade. The decisive blocker is not route-ownership ambiguity anymore; it is live provider readiness for the owned strict-extraction lane in this environment.

The current state supports:

- truthful lane separation
- reviewable direct-model evidence
- pricing-aware blocking and caveating
- review-first profile synthesis
- append-oriented governance evidence

The current state does not support:

- truthful restart of R1
- dynamic profile updates
- broad cost-profile design without lane caveats
- claiming Phase S contract parity with the core runtime-route lane

## Recommended Next Packets

1. Environment/provider readiness packet
   - Goal: fix or explicitly reclassify OpenRouter auth and OpenAI quota readiness for the owned R1 live lane.
2. Phase S contract parity packet
   - Goal: raise Phase S from registry/prompt hygiene to stronger contract and execution parity where appropriate.
3. Pricing truth follow-up
   - Goal: resolve xAI unknown/stale pricing blockers that still limit cost-profile design.

## Key Evidence

- `proof/benchmarking/TP-RTE-BENCH-SPLIT-001/20260411T001636Z/`
- `proof/benchmarking/TP-RTE-BENCH-DMB-001/20260411T030110Z/`
- `proof/benchmarking/TP-RTE-BENCH-PRICE-001/20260411T033247Z/`
- `proof/benchmarking/TP-RTE-BENCH-PROFILE-SYNTH-001/20260411T040331Z/`
- `proof/benchmarking/TP-RTE-BENCH-R1C/benchmarking-20260410-001/`
- `proof/benchmarking/TP-RTE-BENCH-R1D/20260411T051526Z/`
