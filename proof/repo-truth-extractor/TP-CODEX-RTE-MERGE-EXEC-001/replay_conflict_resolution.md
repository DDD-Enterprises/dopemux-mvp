# Replay Conflict Resolution

## Summary

Conflicts occurred in the bounded runtime surface only:

- `services/repo-truth-extractor/run_extraction_v5.py`
- `services/repo-truth-extractor/validate_pre_live_gate_v25.py`
- one add/add conflict in `services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py` was resolved by keeping the already-compatible staged content

## Resolutions

### `c660ab9df`

- Conflicted file: `validate_pre_live_gate_v25.py`
- Resolution: kept the richer current branch implementation:
  - `Condition` plus `GateCondition = Condition`
  - bounded target scope logic
  - richer environment summary and sanitized JSON printing
- Semantics preserved: validator slice required for bounded `A/A2` gating

### `2144d4e36`

- Conflicted file: `run_extraction_v5.py`
- Resolution: restored pricing hash import / return behavior while preserving richer current spend-abort and resume-proof fields
- Semantics preserved: TP001 spend-cap and pricing registry logic

### `e14690d0d`

- Conflicted files:
  - `run_extraction_v5.py`
  - `tests/test_run_extraction_v5_validator.py` (add/add)
- Resolution: kept current bounded-execution and selected-step handling while preserving validator test coverage
- Semantics preserved: TP003 bounded execution path

### `0db7b8528`

- Conflict in `run_extraction_v5.py` resolved to an empty replay
- Reason: current branch already had the needed usage-summary extraction behavior

### `91868d873`

- Conflicted file: `run_extraction_v5.py`
- Resolution: kept richer current parse-provenance, safe logging, and cost-abort status handling
- Semantics preserved: repair provenance tracking and unified run-status behavior

### `6bc14c7bd`

- Conflicted files:
  - `run_extraction_v5.py`
  - `validate_pre_live_gate_v25.py`
- Resolution:
  - adopted the compact `collect_provider_routes(..., selected_step_ids_by_phase=...)` call shape
  - preserved dict-safe request metadata extraction
  - preserved richer validator scope/reporting fields while adding selected-step-aware route derivation and runtime call path
- Semantics preserved: narrow post-TP004 live fixes

## Replay-Repair Commit

After the replayed commits landed, validator execution exposed one remaining bounded defect introduced by conflict resolution:

- missing `return scope` in `derive_scope()`
- phase-wide observed contract-map keys still compared against selected-step expectations

This required bounded repair commit:

- `c7250ecaf` `fix(repo-truth-extractor): restore selected-step validator replay integrity`

Without that repair the replay branch failed the packet’s required validator command and could not be called ready.
