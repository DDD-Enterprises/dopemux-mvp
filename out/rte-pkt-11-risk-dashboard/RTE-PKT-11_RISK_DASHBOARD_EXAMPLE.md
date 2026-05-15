# RTE Risk Dashboard

- Run ID: rte-pkt-11-static-fixture
- Generated at: 2026-05-15T00:00:00Z
- Live-use readiness: READY_FOR_LIMITED_DRY_STATIC_USE
- Static audit verdict: PASS_WITH_RISK
- Overall risk level: MEDIUM-HIGH
- Provider call status: LIVE_VALIDATION_REQUIRED
- Batch operation status: LIVE_VALIDATION_REQUIRED
- Live validation status: BLOCKED
- Proof contract status: partial

## Risk Items

| ID | Status | Evidence | Notes |
| --- | --- | --- | --- |
| LIVE_GATE | STATIC_ONLY | local runtime/proof inputs | - |
| PROVIDER_PAYLOAD_REDACTION | PASS_STATIC | static packet/runtime redaction proof when available | - |
| FAILED_SIDECARS | PASS_WITH_RISK | static failed-sidecar redaction proof when available | - |
| PRESCAN_STALENESS | ACCEPTED_WITH_RISK | prescan receipt/static packet evidence when available | - |
| PRESCAN_INFLUENCE | ACCEPTED_WITH_RISK | prescan influence labels/static packet evidence when available | - |
| PROVENANCE_FIELDS | PASS_STATIC | repair/sidefill provenance static packet evidence when available | - |
| TRUTH_LABELS | PASS_STATIC | truth-label preservation static packet evidence when available | - |
| PROVIDER_METADATA | LIVE_VALIDATION_REQUIRED | static fixture proof only unless live validation artifacts are present | - |
| BATCH_STATIC | PASS_WITH_RISK | batch static fixture proof when available | downloaded_jsonl_status=MISSING |
| LIVE_VALIDATION_PLAN | BLOCKED | local authorization/live-validation artifact inventory | - |
| PROOF_CONTRACT | PASS_WITH_RISK | RTE-PKT-10 proof-contract helper | conformance_status=partial |
| PASS1_IDENTITY | UNKNOWN | proof-contract exact Pass 1 identity classifier | exact_identity_known_or_unknown=unknown |
| GENERATED_ARTIFACT_AUTHORITY | ACCEPTED_WITH_RISK | artifact authority classifier | non_authority_label=generated artifacts are evidence, not runtime source truth |

## Blockers

- LIVE_VALIDATION_PLAN: live validation execution is not authorized

## Warnings

- BATCH_STATIC: PASS_WITH_RISK
- BATCH_STATIC: downloaded JSONL inventory is MISSING
- FAILED_SIDECARS: PASS_WITH_RISK
- PROOF_CONTRACT: PASS_WITH_RISK
- PROVIDER_METADATA: LIVE_VALIDATION_REQUIRED

## Accepted Risks

- BATCH_STATIC: accepted static proof with residual risk
- FAILED_SIDECARS: accepted static proof with residual risk
- GENERATED_ARTIFACT_AUTHORITY: accepted static proof with residual risk
- PRESCAN_INFLUENCE: accepted static proof with residual risk
- PRESCAN_STALENESS: accepted static proof with residual risk
- PROOF_CONTRACT: accepted static proof with residual risk

## Unknowns

- PASS1_IDENTITY: UNKNOWN
- PASS1_IDENTITY: exact Pass 1 artifact identity is UNKNOWN

## Next Recommended Actions

- Review RTE_RISK_DASHBOARD.md before treating static proof as live readiness.
- Run a separately authorized live-validation packet before claiming provider behavior.
- Keep downloaded batch JSONL as MISSING unless local artifacts are actually present.
- Resolve proof-contract partial/missing fields before treating run proof as a full bundle proof.
