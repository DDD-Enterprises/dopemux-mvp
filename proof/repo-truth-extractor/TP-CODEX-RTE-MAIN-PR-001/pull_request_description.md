## What this PR is

Clean replay of the bounded prelive extractor runtime slice for:

- phase `A`
- step `A2`
- routing policy `balanced_grok_openrouter`

This PR is based on `codex/rte-merge-exec-001` and is intended to present the bounded merge candidate to reviewers without reusing the earlier contaminated local `main` integration path.

## What was proven

- bounded target validated for `A / A2 / balanced_grok_openrouter`
- `python -m py_compile` passed for:
  - `services/repo-truth-extractor/run_extraction_v5.py`
  - `services/repo-truth-extractor/validate_pre_live_gate_v25.py`
- targeted pytest slice passed:
  - `cost_cap`
  - `validator`
  - `phase_execution_step_filter`
  - `validator_repair_provenance`
- validator result:
  - `CONDITIONAL_GO`
  - `operator_verdict = GO_NOW`

## What changed

Runtime code diff is limited to:

- `services/repo-truth-extractor/run_extraction_v5.py`
- `services/repo-truth-extractor/validate_pre_live_gate_v25.py`

The branch also carries replay proof artifacts from `TP-CODEX-RTE-MERGE-EXEC-001`.

## Replay notes

- replay was not purely mechanical
- five required source commits landed as replay commits
- three required source commits replayed as empty because their behavior was already preserved after earlier conflict resolution
- one bounded repair commit was required:
  - `c7250ecaf`

Reason for `c7250ecaf`:

- restore validator step-scope correctness after replay conflict resolution
- specifically restore missing `return scope` and selected-step contract-map filtering

## What is NOT claimed

- not full extractor correctness
- not all phases or all steps
- not production-wide readiness
- not proof of correctness outside the bounded target described above

## Remaining conditions

- PAL validation was not provided
- validator result remains `CONDITIONAL_GO`, not flat `GO`
- reviewer should treat the current evidence as bounded-target validation only

## Reviewer guidance

- verify the runtime diff scope is limited to the two files above
- verify the branch also includes the replay proof bundle and no unrelated runtime surfaces
- verify replay integrity against the source replay slice and the empty-replay notes
- verify `c7250ecaf` is bounded to validator step-scope repair and does not widen runtime scope
- confirm the branch preserves the bounded `A / A2 / balanced_grok_openrouter` behavior without contamination from prior branch history
