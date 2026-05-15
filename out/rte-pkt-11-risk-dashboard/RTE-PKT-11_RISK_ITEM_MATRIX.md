# RTE-PKT-11 Risk Item Matrix

| Risk Item | Status | Source Inputs | Notes |
| --- | --- | --- | --- |
| `LIVE_GATE` | `STATIC_ONLY` | local runtime/proof inputs | - |
| `PROVIDER_PAYLOAD_REDACTION` | `PASS_STATIC` | static packet/runtime redaction proof when available | - |
| `FAILED_SIDECARS` | `PASS_WITH_RISK` | static failed-sidecar redaction proof when available | - |
| `PRESCAN_STALENESS` | `ACCEPTED_WITH_RISK` | prescan receipt/static packet evidence when available | - |
| `PRESCAN_INFLUENCE` | `ACCEPTED_WITH_RISK` | prescan influence labels/static packet evidence when available | - |
| `PROVENANCE_FIELDS` | `PASS_STATIC` | repair/sidefill provenance static packet evidence when available | - |
| `TRUTH_LABELS` | `PASS_STATIC` | truth-label preservation static packet evidence when available | - |
| `PROVIDER_METADATA` | `LIVE_VALIDATION_REQUIRED` | static fixture proof only unless live validation artifacts are present | - |
| `BATCH_STATIC` | `PASS_WITH_RISK` | batch static fixture proof when available | downloaded_jsonl_status=MISSING |
| `LIVE_VALIDATION_PLAN` | `BLOCKED` | local authorization/live-validation artifact inventory | - |
| `PROOF_CONTRACT` | `PASS_WITH_RISK` | RTE-PKT-10 proof-contract helper | conformance_status=partial |
| `PASS1_IDENTITY` | `UNKNOWN` | proof-contract exact Pass 1 identity classifier | exact_identity_known_or_unknown=unknown |
| `GENERATED_ARTIFACT_AUTHORITY` | `ACCEPTED_WITH_RISK` | artifact authority classifier | non_authority_label=generated artifacts are evidence, not runtime source truth |

## Blockers

- LIVE_VALIDATION_PLAN: live validation execution is not authorized

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
