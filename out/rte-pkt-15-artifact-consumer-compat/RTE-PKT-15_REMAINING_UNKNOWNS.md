# RTE-PKT-15 Remaining Unknowns

- OpenRouter x-ai live upstream metadata remains UNKNOWN.
- OpenRouter x-ai returned-model behavior remains UNKNOWN unless separately live-validated.
- OpenRouter x-ai schema acceptance remains LIVE_VALIDATION_REQUIRED.
- OpenRouter x-ai retention, ZDR, billing, and rate-limit equivalence remain UNKNOWN.
- Direct xAI live safety remains LIVE_VALIDATION_REQUIRED.
- Live provider billing equivalence is not inferred from `upstream_provider`, model prefixes, pricing catalog entries, or static route metadata.
- `services/repo-truth-extractor/lib/proof_contract.py` is OBSERVED present in this checkout.
- `services/repo-truth-extractor/lib/risk_dashboard.py` is OBSERVED present in this checkout.
- Historical generated artifacts under `services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/*` were read-only context only; this packet does not prove every downstream consumer outside checked-in runtime/test selectors.
- Optional pytest selector `failure_index or coverage_rollup` selected no tests and is recorded as NOT_RUN_NO_TESTS_SELECTED; direct function-level coverage exists in `test_artifact_consumer_static_compatibility.py`.
