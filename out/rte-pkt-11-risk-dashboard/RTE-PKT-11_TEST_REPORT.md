# RTE-PKT-11 Test Report

## PASS

- `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/lib/risk_dashboard.py services/repo-truth-extractor/lib/proof_contract.py` -> exit 0.
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest services/repo-truth-extractor/tests -k 'risk and dashboard' -q` -> exit 0, 9 passed, 1 pytest config warning about unknown `asyncio_mode`.
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest services/repo-truth-extractor/tests -k 'proof_contract or artifact_authority' -q` -> exit 0, 10 passed, 1 pytest config warning about unknown `asyncio_mode`.
- `python -m json.tool out/rte-pkt-11-risk-dashboard/RTE-PKT-11_MANIFEST.json >/dev/null` -> exit 0.
- `python -m json.tool out/rte-pkt-11-risk-dashboard/RTE-PKT-11_RISK_DASHBOARD_EXAMPLE.json >/dev/null` -> exit 0.
- `git diff --check` -> exit 0.
- `pre-commit run --files <changed packet files>` -> exit 0.

## NOT_RUN

- Live extraction was not run.
- Provider preflight/doctor calls were not run.
- Batch submit/poll/retrieve/cancel operations were not run.
- Broad full-suite pytest was not run because packet scope is narrow and expected validation requested targeted local tests.

## Warning

Pytest emitted an existing configuration warning: `PytestConfigWarning: Unknown config option: asyncio_mode`.
