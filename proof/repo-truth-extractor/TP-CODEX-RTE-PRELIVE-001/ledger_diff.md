# Spend ledger diff

## Previous observed shape

- global `total_cost_usd`
- per-phase totals
- global `models`
- legacy `unknown_model_events`
- no public rate registry accessor
- no provider totals
- `accumulate(...)` had no `route` input

## Current shape

- public `MODEL_COST_RATES`
- public `get_model_cost_rate(provider, model_id, route)`
- `accumulate(phase, input_tokens, output_tokens, provider=None, model_id=None, route=None)`
- persisted global totals:
  - `total_cost_usd`
  - `models`
  - `providers`
  - `fallback_usage_count`
  - legacy `unknown_model_events`
- persisted per-phase totals:
  - `models`
  - `providers`
- backward-compatible load for older ledger files that do not contain provider maps or fallback counters

## Runtime accounting changes

- sync canonical path now records one accumulated spend record instead of a helper call plus an extra raw ledger increment
- batch and async submit lanes reserve projected spend at submit time
- batch watch and async finalize consume observed usage without double-counting previously reserved spend
- cost-abort persistence now records the active ledger totals in `COST_ABORT.json` and linked run artifacts
