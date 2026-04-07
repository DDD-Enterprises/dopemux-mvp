# Live Execution Plan

## Target
- **Phase**: A
- **Step**: A2
- **Routing Policy**: `balanced_grok_openrouter`
- **Run ID**: `tp_codex_rte_prelive_005_phase_a_step_a2_v13`

## Exact Command
```bash
DPMX_LIVE_OK=1 python services/repo-truth-extractor/run_extraction_v5.py \
  --phase A \
  --step A2 \
  --routing-policy balanced_grok_openrouter \
  --run-id tp_codex_rte_prelive_005_phase_a_step_a2_v13 \
  --max-cost-usd 0.10
```

## Declared Limits
- **Cost Cap**: 0.10 USD (Absolute Max: 0.25 USD)
- **Time Limit**: None (bounded to single step)

## Success Criteria
1. Step A2 completes successfully.
2. `SPEND_LEDGER.json` records billable usage.
3. Artifacts (`RUN_MANIFEST.json`, `RESUME_PROOF.json`, `COVERAGE_ROLLUP.json`) are coherent and agree on `OK` status.
4. If JSON repair occurs, provenance is recorded and surfaced.
