# Review Classification Matrix

| Reviewer | Comment / Area | Classification | Justification |
| --- | --- | --- | --- |
| `github-actions[bot]` | unused `args` parameter on `evaluate_online_preflight` | `NON_BLOCKING_IMPROVEMENT` | The parameter is optional and currently harmless. It does not change runtime behavior or falsify the PR claims. |
| `github-actions[bot]` | possible `IndexError` in `observed_target_keys` | `NON_BLOCKING_IMPROVEMENT` | Canonical writer `services/repo-truth-extractor/lib/phase_contract_map.py` emits `steps` keys as `PHASE:STEP`. The comment is defensive hardening, not a proven correctness break on the bounded slice. |
| `github-actions[bot]` | possible `IndexError` in `expected_contract_map_target_keys` | `NON_BLOCKING_IMPROVEMENT` | Same authority as above: the canonical contract-map writer emits colon-delimited keys only. No repo-truth evidence shows malformed keys in this contract. |
| `Copilot` | claims `run_gate(... evaluate_online_preflight(runner, config, args))` breaks tests | `MISUNDERSTANDING` | Live PR head calls `evaluate_online_preflight(runner, config)`, and `pytest -q services/repo-truth-extractor/tests/test_pre_live_gate_v25.py` passes on the review branch. |
| `github-actions[bot]` summary | positive review with note about edge cases | `NON_BLOCKING_IMPROVEMENT` | Summary only. The only concrete follow-up is the same defensive colon-splitting hardening noted above. |
| `copilot-pull-request-reviewer[bot]` summary | PR overview | `NON_BLOCKING_IMPROVEMENT` | No new blocking claim beyond the inline comment already classified. |
