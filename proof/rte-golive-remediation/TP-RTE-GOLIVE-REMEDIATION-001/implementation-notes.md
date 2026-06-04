---
id: TP-RTE-GOLIVE-REMEDIATION-001-IMPLEMENTATION-NOTES
title: RTE Go-Live Remediation Slice 1 Implementation Notes
type: reference
owner: '@hu3mann'
author: codex
date: '2026-06-04'
last_review: '2026-06-04'
next_review: '2026-07-04'
prelude: Implementation notes for the first RTE go-live remediation slice.
---

# RTE Go-Live Remediation Slice 1 Implementation Notes

## Scope

- Task Packet: `task-packets/generated/TP-RTE-GOLIVE-REMEDIATION-001.json`
- Branch: `codex/rte-golive-remediation-001`
- Worktree: `/Users/hue/code/dopemux-mvp/.worktrees/rte-golive-remediation-001`
- Base: `origin/main` at `2f6f362236aa8429877664c675a5373cd9acf16e`

## Changes

- `value-default` now applies a default `--max-cost-usd` cap of `5.00`.
- `quality` now applies a default `--max-cost-usd` cap of `25.00`.
- Live pre-flight validator subprocess calls now forward the active `--s-prompts` mode.
- The pre-live validator now stores and applies `s_prompts_mode` before deriving route scope or prompt views.
- `collect_truth_split` now emits target-scoped rows from active runner prompt specs, promptset declarations, model-map declarations, and prompt output/contract metadata.
- Selected SP registry steps without phase contracts now produce a P0 `SP_CONTRACT_MISSING` blocker.

## Validation

- `python -m json.tool task-packets/generated/TP-RTE-GOLIVE-REMEDIATION-001.json >/dev/null` - PASS
- `python -m jsonschema -i task-packets/generated/TP-RTE-GOLIVE-REMEDIATION-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` - PASS
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 PYTHONPATH=services/repo-truth-extractor python -m pytest services/repo-truth-extractor/tests/test_cost_profiles.py services/repo-truth-extractor/tests/test_pre_live_gate_v25.py services/repo-truth-extractor/tests/test_run_extraction_v5_cost_cap.py services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py -q --tb=short --disable-warnings --no-cov` - PASS, 49 passed
- `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/validate_pre_live_gate_v25.py` - PASS
- `git diff --check` - PASS
- `pre-commit run --files ...` on the Task Packet allowlist - PASS
- Offline direct probe for `target_phases=("S",)`, `target_step="SP4"`, `s_prompts_mode="registry"` - PASS; returned `FAIL`, one target row, and P0 `SP_CONTRACT_MISSING`.

## Not Run

- Live extraction.
- Live provider calls.
- Network provider preflight.
- Full RTE suite.
- Follow-up slices for network/secrets containment, pre-live UX cleanup, and prescan closeout.
- `ruff check` as a completion gate. A focused run was attempted, but `run_extraction_v5.py` has pre-existing import-order and unused-import findings outside this slice. One new validator unused import surfaced by that run was removed.

## Residual Risk

- This slice blocks missing SP contracts but does not add the missing SP contracts themselves.
- Route-readiness evidence remains bounded to existing offline tests and local route derivation; provider availability was not exercised.
- Full-suite regressions remain possible outside the targeted files and are left to CI or a separate full-suite packet.
