# Billable path census

Method: inspect `services/repo-truth-extractor/run_extraction_v5.py` for all provider-call entry points and routing wrappers using:

- `call_llm(`
- `call_llm_with_ladder(`
- batch submit/watch surfaces
- async submit/finalize surfaces

## Counts

- candidate call paths total: **14**
- billable paths total: **12**
- instrumented billable paths total: **12**
- non-billable paths total: **2**
- unknown paths total: **0**

## Census

| # | Surface | File line | Classification | Instrumented |
|---|---|---:|---|---|
| 1 | `run_provider_doctor_probe` | `5854` | billable | yes |
| 2 | `run_gemini_auth_probe` | `8895` | billable | yes |
| 3 | `run_auth_doctor` | `9047` | billable | yes |
| 4 | `run_comparison_lane` | `10546` | billable | yes |
| 5 | `_strict_contract_call` | `11968` | billable | yes |
| 6 | sync partition execution inside `_execute_llm_call` | `12808` | billable | yes |
| 7 | canonical `call_llm_with_ladder` wrapper | `13047` | non-billable wrapper | n/a |
| 8 | `audit_phase_sample` | `16294` | billable | yes |
| 9 | `run_batch_watch` | `16517` | billable | yes |
| 10 | `run_phase_R_async_submit` | `17371` | billable | yes |
| 11 | `run_phase_R_finalize` | `17693` | billable | yes |
| 12 | S_INT `_execute_attempt` | `18849` | billable | yes |
| 13 | S_INT `call_llm_with_ladder` wrapper | `18912` | non-billable wrapper | n/a |
| 14 | batch submit path inside `_execute_llm_call` | `12535` | billable | yes |

## Notes

- `call_llm_with_ladder(...)` routes attempts but is not itself a provider-billing surface.
- batch submit is counted separately because it can incur provider-side cost without a direct `call_llm(...)` call.
- async submit/finalize are counted separately for the same reason.
- no candidate surface remains unclassified in this census.
