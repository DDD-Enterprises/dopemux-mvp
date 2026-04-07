# TP007 Live Revalidation Plan

## Intended Live Command

```bash
env XAI_API_KEY='<masked>' DPMX_LIVE_OK=1 python services/repo-truth-extractor/run_extraction_v5.py --phase A --step A2 --routing-policy balanced_grok_openrouter --run-id tp_codex_rte_prelive_007_phase_a_step_a2_v1 --max-cost-usd 0.10
```

## Execution Rule

- Run exactly once if and only if validator returns `GO_NOW`

## Actual TP007 Outcome

- Not executed

## Why Not Executed

- Current validator verdict was `NO_GO`
- Current validator authority is broader than the TP006 bounded `A2` target
- The validator now requires successful OpenRouter preflight for active phase-`A` routes outside `A2`
- Those OpenRouter probes returned `401 Unauthorized`

## Truthful Plan Result

- TP007 closes as blocked before live execution
- No live revalidation run was attempted
