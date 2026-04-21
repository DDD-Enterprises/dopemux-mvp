# Pre-Live Gate v2.5 Summary

- Verdict: NO_GO
- Target policy: cost
- Target phases: A
- Target mode: direct
- Run ID: pre_live_gate_v25_20260418T031613Z

## Layers
- import_cli_smoke: PASS
- target_prompt_integrity: PASS
- truth_split_audit: PASS
- contract_map_determinism: PASS
- route_derived_readiness: PASS
- critical_tests: PASS
- repo_drift_tests: FAIL
- pal_provider_validation: SKIPPED
- online_provider_preflight: FAIL
- smoke_and_verify_evidence: PASS

## Operator Verdict
- NO_GO_EXTERNAL

## Reason Codes
- ONLINE_PREFLIGHT_FAILURE

## Conditions
- PAL_REQUIRED_UNAVAILABLE: PAL validation was not provided for the selected routes. Runtime eligibility remains environment-based.

## Environment Status
- Tooling status: NO_GO
- Live online status: environment_blocked_or_unverified
- Note: Repo and tooling checks can pass while live online readiness remains blocked or unverified by current provider credentials, PAL evidence, or online preflight.

## Evidence
- Scope: /Users/hue/code/dopemux-mvp/services/repo-truth-extractor/run_extraction_v5.py
- Output dir: /Users/hue/code/dopemux-mvp/reports/repo-truth-extractor/pre_live_gate_v25/pre_live_gate_v25_20260418T031613Z
