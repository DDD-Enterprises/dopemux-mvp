# PR #1136 repair diagnosis (bounded)

## Current state (observed)

| Field | Value |
|---|---|
| PR | https://github.com/DDD-Enterprises/dopemux-mvp/pull/1136 |
| Head branch | `claude/rte-truth-program` |
| Base | `main` |
| Files (paginated API) | **366** (155 added, 210 modified, 1 removed) |
| Additions / deletions | +46846 / −3533 |
| Labels | **none** (no `intentional-deletion`) |
| Clobber Guard | **FAIL** — `LARGE_DELETION: 3533 lines / 1 files deleted` (`INTENTIONAL=false`) |
| Embedded audit | **FAIL** (stale run; needs rebind to refreshed head) |
| PR Steward | **FAIL** (audit not READY) |

## Deletion ledger

| Status | Count |
|---|---|
| added | 155 |
| modified | 210 |
| removed | 1 |

Removed file:

- `docs/04-explanation/root-relocated/user-journey.md` (drives the 3533-line LARGE_DELETION signal)

## Clobber-guard clear path

1. Human confirms the single large deletion is intentional.
2. Add PR label `intentional-deletion`.
3. Re-run clobber-guard (workflow treats label as `--allow-intentional` warnings path).
4. Do **not** admin-merge around the gate.

## Refresh recommendation

1. Fetch current `origin/main` (advanced past original baseline; includes at least #1162, #1164, #1175, #1177 as of this validation).
2. Create repair worktree from `claude/rte-truth-program`.
3. Attempt `git merge origin/main` (prefer merge over rebase to avoid force-push).
4. If conflicts are mechanical, resolve; if patch identity would be destroyed, **STOP** and request operator decision.
5. Re-confirm 366-file inventory + deletion ledger on the new head.
6. Independent embedded audit on **exact final head**.
7. PR Steward on that head.
8. Rerun RTE + full CI suites.
9. **No force-push** without explicit operator approval.

## Follow-up stack

- Branch `claude/rte-truth-followup` is **6 commits ahead** of `claude/rte-truth-program` and is a clean stack (`FOLLOWUP_STACKED_OK`).
- Draft PR opened targeting programme branch (not main): see VERDICT / operator return.
- Retarget to main only after #1136 lands and follow-up is refreshed + revalidated.

## Explicit non-actions

- Do not admin-merge #1136.
- Do not claim the 19 “already implemented” RTE packets are on main until #1136 merges.
- Do not bundle follow-up into #1136 without a separate identity-preserving plan.
