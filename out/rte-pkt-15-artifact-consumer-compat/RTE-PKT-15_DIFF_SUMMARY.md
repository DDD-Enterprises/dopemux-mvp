# RTE-PKT-15 Diff Summary

## Changed Runtime Code

None in the RTE-PKT-15 delta. The branch is stacked on RTE-PKT-14 at `5f13537668787baa3f52a6a634fcd17fa2eec16a`, which contains the predecessor pricing-surface implementation.

## Changed Tests

- `services/repo-truth-extractor/tests/test_artifact_consumer_static_compatibility.py`
  - Adds static compatibility coverage for enriched request metadata, route fingerprint material, status/proof/dashboard snapshots, proof-contract classification, risk-dashboard inputs, pricing coverage rows, direct-model spend estimates, and `spend_ledger.json` load paths.
  - Uses controlled assertions over stable required fields plus intentional additive fields.
  - Does not compare whole JSON artifacts for exact equality.

## Proof Outputs

- `out/rte-pkt-15-artifact-consumer-compat/RTE-PKT-15_MANIFEST.json`
- `out/rte-pkt-15-artifact-consumer-compat/RTE-PKT-15_DIFF_SUMMARY.md`
- `out/rte-pkt-15-artifact-consumer-compat/RTE-PKT-15_CONSUMER_COMPATIBILITY_MATRIX.md`
- `out/rte-pkt-15-artifact-consumer-compat/RTE-PKT-15_STATIC_FIXTURE_EXAMPLES.md`
- `out/rte-pkt-15-artifact-consumer-compat/RTE-PKT-15_TEST_REPORT.md`
- `out/rte-pkt-15-artifact-consumer-compat/RTE-PKT-15_NO_PROVIDER_CALLS_ATTESTATION.md`
- `out/rte-pkt-15-artifact-consumer-compat/RTE-PKT-15_REMAINING_UNKNOWNS.md`
- `out/rte-pkt-15-artifact-consumer-compat/RTE-PKT-15_TASK_PACKET.json`

## Non-Goals Preserved

- No live extraction was run.
- No provider preflight was run.
- No provider client behavior, provider dispatch, promptset, model map, route selection, provider pricing rate, compose, config, or deployment file was changed by RTE-PKT-15.
- No live billing, retention, ZDR, returned-model behavior, schema acceptance, or rate-limit equivalence claim was introduced.

## Base / Stack Note

`main` was observed at `655c4196ea4c51b7e0898224af9ed15b0451f53f`. RTE-PKT-14 was observed on `codex/rte-pkt-14-pricing-visibility` at `5f13537668787baa3f52a6a634fcd17fa2eec16a` with open PR `#637`. RTE-PKT-15 is therefore stacked on the RTE-PKT-14 branch.
