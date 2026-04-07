# Billable call paths

Repo truth inspected in `services/repo-truth-extractor/run_extraction_v5.py`.

## Instrumented paths

- `run_provider_doctor_probe`
  - direct `call_llm(...)`
  - now gated by `_check_projected_cost_limit(...)` and accumulated via `_accumulate_runtime_spend(...)`
- `run_gemini_auth_probe`
  - direct `call_llm(...)`
  - now gated and accumulated
- `run_auth_doctor`
  - direct `call_llm(...)` across auth modes
  - now gated and accumulated
- `run_comparison_lane`
  - comparison-only secondary lane
  - now gated and accumulated; raises cost abort on breach
- `_strict_contract_call`
  - strict repair and sidefill path
  - now gated and accumulated
- sync partition execution inside `_execute_llm_call`
  - canonical per-partition live path
  - now gated and accumulated once; duplicate raw `ledger.accumulate(...)` block removed
- `audit_phase_sample`
  - judge-model lane
  - now gated and accumulated
- batch submit in `_execute_llm_call`
  - projected pre-check retained
  - submit now reserves spend via `_reserve_projected_spend(...)`
- `run_batch_watch`
  - accumulates only when submit did not already reserve spend
  - stops after the first over-cap result
- `run_phase_R_async_submit`
  - projected pre-check retained
  - submit now reserves spend
- `run_phase_R_finalize`
  - skips double-counting when submit already reserved spend
  - otherwise accumulates and can abort
- S_INT prompt executor
  - now projected-gated and accumulated

## Deterministic stop mechanics

- when `--max-cost-usd` is active on a live run, `partition_workers` is clamped to `1`
- sequential partition application writes the current partition output first, then raises `CostLimitExceededError`
- top-level phase/batch/finalize handlers persist `COST_ABORT.json` plus manifest/proof updates and exit non-zero

## Non-authoritative notes

- `call_llm_with_ladder(...)` is a routing wrapper, not a provider call by itself
- provider billing/export remains external and was not changed by this packet
