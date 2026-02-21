# Git Cleanup Audit (2026-02-21)

## Repository state
- Branch: `main`
- HEAD: `29746e77f`
- Status: clean (`git status -sb`)
- Local branches remaining: `main` only
- Worktrees remaining: `/Users/hue/code/dopemux-mvp` only
- Stash entries remaining: none
- Open PRs: none

## Worktrees removed
- `/private/tmp/dopemux-main-merge`
- `/Users/hue/code/cc-work`
- `/Users/hue/code/dopemux-mvp-tpx-fix`
- `/Users/hue/code/dopemux-mvp-v4-prompts-full-coverage`

Backup for removed worktree untracked files:
- `/tmp/dopemux_cleanup_backup_20260220_164324`

## Branch cleanup
- Deleted all local branches except `main`.
- Branch deletion log:
  - `/tmp/local_branch_delete_20260220_164336.log`

## Stash cleanup
- Exported stash patch/stat backups then cleared all stashes.
- Backup dirs:
  - `/tmp/dopemux_cleanup_backup_20260220_164351`
  - `/tmp/dopemux_cleanup_backup_20260220_164354`

## PRs merged to main
- #63, #56, #54, #53, #52, #50, #49, #47, #46, #45, #44, #33, #31, #29, #20
- `gh pr list --state open` now returns empty.

## CI/Workflow status (latest on `main` SHA `29746e77f`)
- `ci-complete.yml`: [failed run 22246968504](https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/22246968504)
- `docs`: [failed run 22246968770](https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/22246968770)
- `security-review.yml`: [failed run 22246968383](https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/22246968383)
- `CodeQL`: [failed run 22246968276](https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/22246968276)
- `Repo Identity Check`: [failed run 22246968808](https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/22246968808)

Observed failure annotation (all failing jobs):
- "The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings."

## Local verification run
- `pytest tests/unit --maxfail=1 --disable-warnings --no-cov -q` -> pass
- `pytest -q --no-cov services/repo-truth-extractor/tests` -> pass
- `python -m py_compile services/repo-truth-extractor/run_extraction_v3.py src/dopemux/cli.py` -> pass

## Additional CI stabilization commits
- `29746e77f` `fix(ci): restore extractor/test stability after branch consolidation`
  - fixed prompt root + parse retry scope/escalation handling in `services/repo-truth-extractor/run_extraction_v3.py`
  - fixed indentation error in `services/task-orchestrator/app/services/task_coordinator.py`
  - fixed test-order-dependent mocking in `tests/unit/test_health.py`
