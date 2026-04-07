# Live Run Execution Record

## Run ID: `tp_codex_rte_prelive_005_phase_a_step_a2_v13`
- **Target**: Phase A, Step A2
- **Command**: `DPMX_LIVE_OK=1 python services/repo-truth-extractor/run_extraction_v5.py --phase A --step A2 --routing-policy balanced_grok_openrouter --run-id tp_codex_rte_prelive_005_phase_a_step_a2_v13 --max-cost-usd 0.10`
- **Start Time**: 2026-04-05T09:00:36Z
- **End Time**: 2026-04-05T09:00:57Z
- **Exit Code**: 1
- **Billable Execution Began**: YES (xAI Grok reasoning model)

## Outcome
`COST_ABORTED` (as expected, single request cost $0.124 exceeding $0.10 cap)

## Logs Evidence
```
02:00:56 [INFO] Step summary A2 partitions_total=28 ok=0 failed=28 retries=0 elapsed_ms=20209 workers=1
...
RUN_DASHBOARD source=run_complete PASS=0 FAIL=1 IN_PROGRESS=0 NOT_STARTED=13
```
Note: Step failure `missing_expected_artifacts:28` triggered by cost abort of remaining partitions.
