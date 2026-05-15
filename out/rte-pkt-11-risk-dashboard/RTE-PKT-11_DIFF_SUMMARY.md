# RTE-PKT-11 Diff Summary

## Code Files

- `services/repo-truth-extractor/run_extraction_v5.py`: wires central risk dashboard generation into the existing run dashboard telemetry writer. No extraction, routing, prompt, provider, batch, or live-validation behavior is changed.
- `services/repo-truth-extractor/lib/proof_contract.py`: carries forward the accepted RTE-PKT-10 proof-contract helper so dashboard generation can consume proof-contract and artifact-authority classification without changing those semantics.
- `services/repo-truth-extractor/lib/risk_dashboard.py`: adds pure local aggregation, redaction, markdown rendering, and artifact writing for `telemetry/RTE_RISK_DASHBOARD.json` and `telemetry/RTE_RISK_DASHBOARD.md`.

## Test Files

- `services/repo-truth-extractor/tests/test_proof_contract.py`: focused proof-contract helper tests carried forward from RTE-PKT-10 semantics.
- `services/repo-truth-extractor/tests/test_risk_dashboard.py`: targeted dashboard tests for static/live boundaries, provider lanes, batch JSONL absence, proof-contract partial status, generated artifact authority, prescan/provenance/truth-label summaries, redaction, and no-provider-call behavior.

## Proof Files

- `out/rte-pkt-11-risk-dashboard/`: packet proof bundle and generated dashboard examples.

## Forbidden Paths

No prompt files, promptsets, model maps, provider routes, provider clients, batch protocol files, pricing files, config roots, compose files, or deployment files were changed.
