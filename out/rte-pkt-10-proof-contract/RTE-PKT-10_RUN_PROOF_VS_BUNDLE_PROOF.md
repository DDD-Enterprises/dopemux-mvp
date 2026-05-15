# RTE-PKT-10 Run Proof vs Bundle Proof

Generated: 2026-05-15T16:13:41Z

## Operator Rule

`PROOF_PACK.json`, `RUN_MANIFEST.json`, dashboards, coverage rollups, failure indexes, and packet closeout manifests are evidence surfaces. They are not automatically proof-contract-compliant governance bundles.

## Run Proof

Run proof can establish facts such as:

- A run ID existed.
- A git SHA or runner hash was recorded.
- A command or cwd was recorded.
- Phases, counts, linked artifacts, and telemetry existed.
- Static no-provider or no-live-call attestations were recorded.

Run proof cannot by itself establish:

- Authoritative vs supporting artifact roles.
- Full chain of custody.
- Handoff lineage.
- Review order.
- Exact Pass 1 identity without hashes and run IDs.
- Live provider behavior when validation is static only.

## Proof-Contract Governance Bundle

A proof-contract-compliant governance bundle requires explicit fields such as:

- `bundle_id`
- `run_id`
- `status`
- `validation_state`
- `authoritative_artifacts`
- `supporting_artifacts`
- `chain_of_custody`
- `handoff_refs`
- `parent_bundle_refs`
- `review_order_hint`
- role-specific artifact lists
- live/provider/batch/redaction statuses
- `artifact_hashes`

The helper added by this packet returns `SATISFIED` only when those fields are present or explicitly marked not applicable by the caller. Missing declarations stay `MISSING`; validation evidence without explicit `validation_state` stays `PARTIAL`.

## Current RTE Posture

Observed local RTE proof examples are best treated as run evidence or packet proof evidence. They are not full governance bundles unless the required proof-contract declarations are present and validated.

## Static Proof Boundary

Static proof artifacts and no-provider attestations do not prove live provider behavior. They should be read as:

```text
provider_call_status=NOT_RUN
live_validation_status=NOT_RUN or NOT_LIVE_VALIDATED
batch_operation_status=NOT_RUN
```

Any later live-readiness claim must cite separate live validation evidence.
