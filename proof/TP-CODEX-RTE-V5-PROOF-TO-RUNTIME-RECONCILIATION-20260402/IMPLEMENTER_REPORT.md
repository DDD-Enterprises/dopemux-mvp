# TP8C Implementer Report

## Inspection findings

- TP7 proof on the current branch claimed scan modes, normalized resume bucket names, grouped warnings, and runbooks that were not present on `main`.
- The missing behavior was not fictional. It existed in reachable commits:
  - `2c38e8a8c` runtime changes
  - `250c039ce` test changes
  - `b5c4afcc0` docs changes
- Current `main` contained the TP7 proof bundle without those commits.

## Root cause

`Partial commit isolation failure`

The repo carried forward proof artifacts describing TP7 while leaving the corresponding runtime, tests, and docs on a side branch.

## Reconciliation path chosen

Path A: bring runtime up to TP7 truth.

I restored the previously implemented hygiene behavior on the scoped surfaces instead of downgrading the proof to the older `main` implementation.

## Before and after

### Before

- No `--scan-mode`
- Resume buckets: `stale_failed`, `orphan_failed`, `blocked_promptset`
- Default scan emitted per-path warnings
- `docs/92-runbooks/repo-truth-extractor-v5-hygiene-cleanup.md` missing
- `docs/92-runbooks/repo-truth-extractor-v5-offline-envelope.md` missing

### After

- `scan --scan-mode actionable|full` restored
- Resume buckets: `stale_resume_state`, `orphaned_resume_state`, `blocked_promptset`
- Actionable mode groups warnings and preserves counts in summaries
- Full mode preserves per-path inventory
- Missing runbook and offline-envelope docs restored
- Existing truth-run how-to updated to mention full scan mode

## Verification

- `pytest -q services/repo-truth-extractor/tests/test_hygiene_resume_state.py services/repo-truth-extractor/tests/test_hygiene_noise_detection.py services/repo-truth-extractor/tests/test_hygiene_nondestructive.py`
- `python services/repo-truth-extractor/extraction_hygiene.py scan --json`
  - `warnings=4`
  - `resume_state_issues=7372`
  - `resume_state_summary.by_issue_type.blocked_promptset=4`
  - `resume_state_summary.by_issue_type.stale_resume_state=7368`
- `python services/repo-truth-extractor/extraction_hygiene.py scan --scan-mode full --json`
  - `warnings=10245`
  - `resume_state_issues=7372`
  - `resume_state_summary.by_issue_type.blocked_promptset=4`
  - `resume_state_summary.by_issue_type.stale_resume_state=7368`

## Remaining limits

- The worktree still has unrelated untracked docs under `docs/03-reference/systems/`; they were intentionally left untouched.
- This packet did not attempt TP9 cleanup mutation work.
- The TP7 proof bundle itself was not rewritten; TP8C records the reconciliation and the missing lineage explicitly.
