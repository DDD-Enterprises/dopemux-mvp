---
id: RTE_BENCHMARK_STORAGE_CONTRACT
title: Repo Truth Extractor Benchmark Storage Contract
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-10'
last_review: '2026-04-10'
next_review: '2026-07-09'
prelude: Canonical storage and linkage contract for the M0 benchmark spine in repo-truth-extractor.
---
# Repo Truth Extractor Benchmark Storage Contract

## Purpose

Define the benchmark storage, execution, derived-artifact, governance packet, and operator-reporting contract for the M0 through M5 benchmark spine without inventing UI infrastructure or scheduling workflow behavior.

## Canonical Root

Benchmark storage root:

`extraction/repo-truth-extractor/benchmarks/`

Subdirectories:

- `index/benchmark_catalog.sqlite`: canonical query/catalog layer
- `runs/<BENCHMARK_RUN_ID>/...`: immutable run-scoped evidence tree

This root is separate from general governance proof storage under `proof/`. Benchmark evidence lives under `extraction/...` because Prompt 4 defines it as an execution artifact tree, not a cross-skill proof bundle root.

## DB Role vs Filesystem Role

SQLite catalog role:

- typed entity registry for benchmark metadata and linkage
- foreign-keyed references between runs, attempts, and evidence bundles
- operator query layer over immutable filesystem evidence

Filesystem role:

- immutable benchmark evidence per run / case-set / attempt
- deterministic JSON manifests for operator-visible artifacts
- content-hashed artifact inventory for each attempt bundle

Rollups, recommendations, and governance directories are reserved in M0 but not populated with substantive logic.

## Registry and Snapshot Semantics

M1 extends the same catalog with frozen registry truth for:

- `contract_snapshot`
- `validator_suite`
- `control_anchor_group`
- `benchmark_case`
- `benchmark_case_set`

SPLIT-001 formalizes benchmark lane separation in the control plane:

- `runtime_route`: executable runtime-under-test evidence
- `direct_model`: executable direct provider/model evidence without route truth claims
- `profile_synthesis_input`: downstream synthesis input that references upstream evidence and is not stored as a raw attempt

Candidate typing is explicit and not inferred from naming:

- `route_candidate`
- `model_candidate`
- `profile_candidate`

Registry capture rules:

1. Snapshots are built from real repo-truth files, not invented payloads.
2. Snapshot hashes are deterministic over sorted JSON payloads and file SHA-256 values.
3. `runtime_version` and `contract_version` remain separate fields on `contract_snapshot`.
4. `validator_suite` may carry weaker-contract caveat notes for `phase_s` and schema-driven notes for FL_INT.
5. Control anchors remain separate from candidate routes; anchor groups do not collapse the two.
6. Case definitions link to one archetype, one validator suite, one contract snapshot, and declared surface scope.
7. Case definitions now declare `benchmark_mode`, `candidate_type`, `execution_family`, route-distinctness relevance, pricing relevance, and governance relevance explicitly.
8. `profile_synthesis_input` remains downstream-only and must reference upstream attempt or rollup ids rather than masquerading as a raw execution row.
9. Case-set definitions link to fixed case ids and one control-anchor group when the lane requires route-control comparison.

Real repo-truth sources used by M1 include:

- `services/repo-truth-extractor/run_extraction_v5.py`
- `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
- `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- `services/repo-truth-extractor/promptsets/v4/model_map.yaml`
- `services/repo-truth-extractor/promptsets/v4/prompt_artifact_coverage_map.json`
- `services/repo-truth-extractor/prompts/phase_s/registry.json`
- `services/repo-truth-extractor/fl_int/schema_input.json`
- `services/repo-truth-extractor/lib/structured_output_contracts.py`
- `services/repo-truth-extractor/run_prescan.py`

## Required Layout

```text
extraction/repo-truth-extractor/benchmarks/
  index/
    benchmark_catalog.sqlite
  runs/
    <BENCHMARK_RUN_ID>/
      BENCHMARK_RUN_MANIFEST.json
      SNAPSHOT_MANIFEST.json
      registry_snapshots/
      case_sets/
        <CASE_SET_ID>/
          CASESET_MANIFEST.json
          attempts/
            <CASE_ATTEMPT_ID>/
              ATTEMPT_SUMMARY.json
              ROUTE_TRACE.json
              VALIDATOR_RESULTS.json
              TASK_EVAL.json
              CONTROL_DELTA.json
              EXECUTOR_LINKS.json
              EVIDENCE_MANIFEST.json
              outputs/
      rollups/
      recommendations/
      governance/
```

## Required Linkage Rules

M0 enforces these linkage rules:

1. Every persisted `benchmark_case_attempt` stores exactly one `evidence_bundle_id`.
2. Every persisted `evidence_bundle` stores one `benchmark_run_id` and one immutable `root_path`.
3. `benchmark_case_attempt.evidence_bundle_id` is unique in SQLite.
4. `evidence_bundle.root_path` is unique in SQLite.
5. `EVIDENCE_MANIFEST.json` is written inside the bundle directory and records artifact hashes plus relative refs.
6. Filesystem bundle path must resolve back to the SQLite `evidence_bundle.root_path`.

## Runtime / Contract Separation

M0 keeps runtime and contract authority separate:

- `runtime_version`
- `contract_version`
- `contract_snapshot_id`

This is required because current runtime authority is v5 while contract authority may still live under `promptsets/v4`.

## Surface Isolation

`surface_class` is enum-constrained to:

- `direct_provider_api`
- `openrouter_routed`
- `chat_or_subscription_surface`
- `local_or_open_weight`

M0 stores this explicitly on `provider_surface`, `control_anchor_group`, and `benchmark_case_attempt`. It does not collapse surfaces across routes or recommendations.

## Determinism and Immutability

M0 writes manifests with:

- sorted JSON keys
- ASCII-safe serialization
- stable separators
- SHA-256 content hashes

If an existing benchmark artifact path already exists with different content, the writer raises instead of mutating the artifact. Rewriting the same content is tolerated.

## What M0 Intentionally Does Not Implement

M0 does not implement:

- live provider or model execution
- real executor adapters
- scoring formulas beyond structural placeholders
- rollup synthesis
- profile fit synthesis
- promotion decision logic
- governance workflow orchestration
- OpenClaw overlay semantics
- scheduling or cadence automation

M0 only establishes the typed models, catalog schema, immutable evidence bundle layout, and a synthetic smoke path proving DB ↔ filesystem linkage.

M1 adds deterministic snapshot capture, registry-backed benchmark cases, registry-backed case-sets, validator-suite definitions, and seeded control-anchor groups. It still does not implement live execution, scoring, rollups, or promotion logic.

M2 adds bounded execution adapters and validator wrappers over real local runtime surfaces:

- `run_prescan.py --dry-run` against the small repo fixture
- `run_extraction_v5.py --phase A --dry-run` against the small repo fixture
- `phase_s` registry/prompt resolution via runtime helpers
- `run_fl_int.py --dry-run` against a prepared deterministic run-root fixture

These adapters populate:

- `benchmark_run`
- `benchmark_case_attempt`
- `validator_result`
- `evidence_bundle`

And they write real execution-linked artifacts for:

- `ROUTE_TRACE.json`
- `VALIDATOR_RESULTS.json`
- `TASK_EVAL.json`
- `EXECUTOR_LINKS.json`
- output artifacts copied from the bounded runtime surface

M2 remains fail-closed on structural validation failures and still does not add scoring formulas, rollups, profile synthesis, or recommendation logic.

SPLIT-001 keeps the existing runtime-route execution spine intact while making the lane boundary explicit:

1. `benchmark_case` and `benchmark_case_attempt` declare `benchmark_mode`, `candidate_type`, and `execution_family`.
2. Runtime-route attempts carry explicit `runtime_route_attempt` payloads with declared route identity, selected route identity, effective route signature, signature hash, admissibility status, and telemetry refs.
3. Direct-model attempts are a separate structural shape with declared and selected provider/model identity plus pricing and latency refs.
4. `profile_synthesis_input` is represented as downstream referenced input and is not a `benchmark_case_attempt`.
5. Scoring, governance synthesis, and operator reporting are runtime-route scoped and fail closed rather than mixing direct-model evidence into route/profile truth.

DMB-001 adds the first bounded executable `direct_model` lane on top of the split:

1. Fixed MVP candidates may be preflighted and executed directly against provider adapters without routing through runtime-route semantics.
2. Direct-model attempts remain `model_candidate` rows with `direct_api_execution`; they do not populate route identity, admissibility, or profile truth claims.
3. Retry policy is bounded to one transport/provider retry only; semantic or validator failures remain benchmark failures.
4. Spend guard semantics remain explicit: measured spend, catalog-derived expected spend, partial estimate, and unknown spend are not flattened into one truth field.
5. Direct-model reporting artifacts are lane-specific and must preserve the disclaimer that they support admission, schema survivability, latency, and spend comparison only.

Direct-model proof and comparison artifact names introduced by DMB-001:

- `DIRECT_MODEL_CAMPAIGN_MANIFEST.json`
- `DIRECT_MODEL_MATRIX.json`
- `DIRECT_MODEL_RETRY_POLICY.json`
- `DIRECT_MODEL_SPEND_GUARD.json`
- `DIRECT_MODEL_COMPARISON.json`
- `DIRECT_MODEL_SUMMARY__<MODEL>.json`
- `DIRECT_MODEL_FAILURES.json`

PRICE-001 upgrades the pricing authority from a sparse rate map to an explicit truth layer:

1. `config/pricing.yaml` is now `RTE_PRICING_V2` and remains the benchmark pricing catalog authority.
2. Catalog entries preserve `pricing_source_type`, `pricing_source_ref`, `pricing_confidence`, `pricing_status`, `surface_scope`, and currency alongside the legacy `input_cost_per_m` and `output_cost_per_m` compatibility fields.
3. Unknown or stale pricing remains explicit. Entries with no verified token price keep null rate fields and are excluded from rate-registry loading rather than silently coerced.
4. Aggregator pricing and first-party provider pricing remain distinct in both storage and reporting.
5. Spend reporting must distinguish measured spend, catalog-derived expected spend, partial estimate, and unknown spend.

PRICE-001 reporting artifacts introduced for benchmark pricing coverage:

- `pricing_coverage_report.json`
- `priced_candidate_matrix.json`
- `sample_spend_truth.json`
- `pricing_gap_list.json`
- `pricing_source_audit.json`

PROFILE-SYNTH-001 adds a downstream review-first synthesis layer:

1. Profile synthesis consumes `direct_model`, `runtime_route`, pricing, and governance/admissibility evidence without flattening them into one score.
2. Synthesis outputs are advisory artifacts only. They must not auto-apply routing or profile changes.
3. Pricing uncertainty remains explicit in proposal classes. Unknown or stale pricing blocks cost-optimized proposals; caveated pricing remains caveated in output artifacts.
4. Blocked runtime-route lanes must remain blocked in synthesis outputs instead of being optimized around.

PROFILE-SYNTH-001 proof and proposal artifact names:

- `PROFILE_SYNTHESIS_SUMMARY.json`
- `PROFILE_PROPOSAL__*.json`
- `ROUTING_DIFF_PROPOSAL__*.json`
- `BLOCKED_LANES.json`
- `PROFILE_REVIEW_PACKET__*.json`

M3 adds the measurement and aggregation spine on top of persisted M2 attempts:

- contract gate finalization from persisted validator results
- archetype-scoped task scoring with versioned policies
- operational metric normalization
- control-anchor delta computation
- case-set and archetype rollups
- profile-fit rows
- portfolio view skeleton
- regression comparison skeleton

M3 storage and derivation rules:

1. Scoring reads persisted attempts, validator rows, and bundle artifacts; it does not rewrite raw execution evidence.
2. Contract failure remains fail-closed and blocks task scoring.
3. Operational metrics are modifiers and summaries only; they do not rescue structurally invalid attempts.
4. Control deltas are only computed for like-for-like attempts matching `case_id`, `surface_class`, `runtime_version`, `contract_snapshot_id`, `validator_suite_id`, and `retry_policy_id`.
5. Rollups are emitted under the run `rollups/` directory as derived artifacts, not as replacement truth for atomic attempt evidence.
6. Portfolio output remains matrix-shaped and explicitly avoids a universal leaderboard.

Derived M3 rollup artifact names:

- `CASESET_ROLLUP__<CASE_SET_ID>.json`
- `ARCHETYPE_ROLLUP__<ARCHETYPE_ID>.json`
- `PROFILE_FIT__<PROFILE_ID>.json`
- `PORTFOLIO_VIEW.json`
- `REGRESSION_COMPARISON__<CASE_SET_ID>.json`

M4 adds the decision layer on top of M3 rollups:

- recommendation-state generation
- freshness and dispute handling
- governance blocker codes
- promotion recommendation packets
- append-only governance decision logging
- recommendation-aware profile-fit and portfolio outputs

M4 governance rules:

1. Recommendation state is derived from benchmark evidence, control deltas, profile fit, freshness state, and policy.
2. Production promotion remains human-reviewed; M4 may recommend review, but it does not auto-promote.
3. Local/open-weight routes remain confined to experimental handling by policy unless operator policy changes later.
4. Contract failure can quarantine a candidate and cannot be rescued by operational metrics.
5. Missing comparable control anchors block production recommendation.
6. Stale or disputed evidence cannot remain in a recommended state.
7. Governance decisions are append-only; supersession links prior decisions rather than erasing them.
8. Governance packets do not replace attempt evidence, bundle evidence, or rollup artifacts.

Derived M4 governance artifact names:

- `PROMOTION_RECOMMENDATIONS.json`
- `GOVERNANCE_PACKET__<RECOMMENDATION_ID>.json`
- `GOVERNANCE_DECISIONS.json`

Recommendation-state values currently emitted by M4:

- `quarantined`
- `ineligible`
- `experimental_only`
- `stale_disputed`
- `eligible_for_review`
- `recommended_for_review`

M5 adds operator-readable reporting and explainability views on top of M4 outputs:

- portfolio summary
- profile summary
- archetype summary
- candidate detail views
- governance history views
- change summaries

M5 reporting rules:

1. Reports are derived from existing benchmark, scoring, rollup, recommendation, and governance data; they do not mutate benchmark truth.
2. The canonical explanation chain is:
   `recommendation_state -> profile_fit -> rollup(s) -> control_delta(s) -> benchmark_case_attempt(s) -> evidence_bundle(s) -> governance_decision`
3. Reports must keep evidence classes explicit:
   - `METADATA_ONLY`
   - `BENCHMARK_DERIVED`
   - `GOVERNANCE_DERIVED`
   - `MIXED_EVIDENCE`
4. Current effective state and historical state remain distinct in governance history views.
5. Portfolio summaries remain matrix-like and do not become winner-take-all rankings.
6. `phase_s` caveats must remain visible in candidate detail views where relevant.
7. Governance history is reconstructed from append-only decisions plus run-scoped recommendation rows; recommendation history is not yet a first-class persisted table.
8. Reporting must preserve benchmark lane boundaries explicitly; runtime-route summaries cannot be used as a synonym for direct-model evidence, and profile synthesis remains downstream-only.

Derived M5 reporting artifact names:

- `PORTFOLIO_SUMMARY.json`
- `PROFILE_SUMMARY__<PROFILE_ID>.json`
- `ARCHETYPE_SUMMARY__<ARCHETYPE_ID>.json`
- `CANDIDATE_DETAIL__<RECOMMENDATION_ID>.json`
- `GOVERNANCE_HISTORY__<CANDIDATE_KEY>.json`
- `CHANGE_SUMMARY__<RECOMMENDATION_ID>.json`

S1 hardens the existing stack without changing the architecture:

- the bounded starter corpus now exercises all six archetypes by default in the execution smoke path
- deterministic hardening fixtures cover stale/disputed evidence, missing comparable control anchor, regression degradation, unresolved governance posture, and explicit `phase_s` caveat paths
- scoring, recommendation, freshness, and control-anchor comparison policies now load from versioned JSON policy packs under `services/repo-truth-extractor/benchmarking/policies/`
- reporting smoke appends a superseding governance decision to exercise current-vs-history reporting views deterministically

Current S1 limitation:

- `promotion_recommendation` remains a current-state run-scoped row; historical recommendation views are reconstructed across runs by candidate identity rather than stored in a dedicated recommendation-history table
