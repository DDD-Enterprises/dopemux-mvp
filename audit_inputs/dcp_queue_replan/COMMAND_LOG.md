# Command Log — GB-DMX-DCP-QUEUE-REPLAN-001

Captured 2026-06-19 on intake worktree `fix/task-orchestrator-startup-reliability`.

## Preflight

| Command | Exit | Notes |
|---------|------|-------|
| `git rev-parse --show-toplevel` | 0 | `/Users/hue/code/dopemux-mvp` |
| `git status --short --branch` | 0 | Dirty: `M compose.yml` (non-DCP). Untracked `audit_inputs/*`, `claudedocs/*`. **No dirty DCP paths.** |
| `git fetch origin --prune` | 0 | Pruned stale remote branches |
| `git rev-parse origin/main` | 0 | `724a25fa01c77f7f1fd6ccf8a78da09f082e0ded` |
| `git log --oneline -n 20 origin/main` | 0 | Shallow top; deepened with `--depth=500` |
| `git fetch origin main --depth=500` | 0 | Extended history for Phase 1 evidence |

## GitHub Inventory

| Command | Exit | Notes |
|---------|------|-------|
| `gh pr list --state open --limit 100 --json ...` | 0 | 4 open PRs total; 1 DCP-related (#931) |
| `gh pr list --state all --search DCP --limit 50` | 0 | Historical DCP PR scan |
| `gh pr view <873,878,885,908,909,906,923,915,920>` | 0 | Seed-state verification |
| `gh pr view 931 --json ... statusCheckRollup` | 0 | Open DCP PR detail |
| GraphQL review threads (#878, #931) | 0 | Thread state captured |

## Analysis

| Command | Exit | Notes |
|---------|------|-------|
| `git ls-tree origin/main` (DCP paths) | 0 | schemas, src, tests, docs, task-packets |
| `git merge-base --is-ancestor` (#931 base vs main) | 0 | Base is ancestor; 6 commits behind |
| `gh pr diff 931 --name-only` | 0 | 38 files |
| `gh pr checks 931 --json name,state,bucket` | 0 | 25 checks, 0 fail |
| Overlap comm (#931 vs #926 on main) | 0 | ~20 semantic duplicates across path remap |

## Deviations

- `gh pr diff --stat` unsupported; used `git diff --stat origin/main...head` instead.
- Seed state listed #873/#878/#885 as "likely remaining"; live state differs (see ledger).

## Forbidden Actions (not executed)

No merge, rebase, close, comment, patch, or file edits outside `audit_inputs/dcp_queue_replan/`.