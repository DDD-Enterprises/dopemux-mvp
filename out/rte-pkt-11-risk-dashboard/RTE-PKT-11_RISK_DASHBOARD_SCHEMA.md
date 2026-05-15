# RTE-PKT-11 Risk Dashboard Schema

Generated: 2026-05-15T16:46:47Z

## Top-Level Fields

Required fields emitted by `lib.risk_dashboard.build_rte_risk_dashboard`:

- `run_id_if_available`: run id when supplied by runtime/proof inputs; otherwise null.
- `generated_at`: UTC generation timestamp.
- `repo_root_if_available`: repo root observed by runtime/proof inputs.
- `git_sha_if_available`: git SHA observed by runtime/proof inputs.
- `live_use_readiness`: readiness label. Current static packet output uses `READY_FOR_LIMITED_DRY_STATIC_USE` and does not claim production-live readiness.
- `static_audit_verdict`: static audit verdict status.
- `overall_risk_level`: operator risk label.
- `provider_call_status`: aggregate provider status.
- `batch_operation_status`: aggregate batch status.
- `live_validation_status`: aggregate live-validation status.
- `proof_contract_status`: `satisfied`, `partial`, `missing`, `unknown`, or `not_applicable`.
- `artifact_authority_status`: generated artifact authority statement.
- `risk_items`: ordered list of required risk items.
- `blockers`: blocking static/live readiness issues.
- `warnings`: non-blocking risk warnings.
- `accepted_risks`: accepted residual static risks.
- `unknowns`: explicit unknowns.
- `next_recommended_actions`: operator next actions.

## Status Values

- `PASS_STATIC`
- `PASS_WITH_RISK`
- `STATIC_ONLY`
- `LIVE_VALIDATION_REQUIRED`
- `MISSING`
- `UNKNOWN`
- `BLOCKED`
- `NOT_APPLICABLE`
- `ACCEPTED_WITH_RISK`

## Required Risk Items

- `LIVE_GATE`
- `PROVIDER_PAYLOAD_REDACTION`
- `FAILED_SIDECARS`
- `PRESCAN_STALENESS`
- `PRESCAN_INFLUENCE`
- `PROVENANCE_FIELDS`
- `TRUTH_LABELS`
- `PROVIDER_METADATA`
- `BATCH_STATIC`
- `LIVE_VALIDATION_PLAN`
- `PROOF_CONTRACT`
- `PASS1_IDENTITY`
- `GENERATED_ARTIFACT_AUTHORITY`

## Redaction Boundary

Dashboard JSON and markdown are passed through the existing RTE output sanitizer. Secret-shaped strings in values such as tokens, bearer headers, passwords, private keys, and authorization fields are redacted before artifact write.

## Local Input Notes

- `accepted_packet_basis` is an input-side evidence map. Runtime collection sets each risk item to true only when the corresponding `out/rte-pkt-*` proof root exists under the current repo root. Fixture/proof examples can supply accepted packet basis explicitly.
- Missing prior packet roots must remain `UNKNOWN` or `MISSING`; they are not inferred as passing current-branch evidence.

## Authority Boundary

The dashboard is generated evidence. It does not outrank runtime source code, schemas, tests, configs, or active entrypoints. Generated proof artifacts are labeled as non-authoritative evidence.
