# G02 return — PR 1513 reviews settled, head frozen (second freeze)

**Status**: READY_FOR_AUDIT (the team lead's word; acceptance belongs to the
auditor and the operator).

**Subject (frozen content head)**: `7a469cb21d185b45d8e10fe0013e7f5d860b68f6` on
`fix/guard-file-repo-root`, PR
https://github.com/DDD-Enterprises/dopemux-mvp/pull/1513, base `main` at
`ba5c3e07b01ad46cae0d55cefdfbb9f9b3b647d7` (merge base; `origin/main` unchanged
at freeze, so the PR is 0 commits behind).

**Audit**: NOT_RUN on this head. No audit has been run on any head that contains
Amendments 02-07.

The commit that adds this version of the file changes only this file, so it sits
on top of the frozen head as a proof-only commit.

## This record replaces the first freeze

The first version of this file (commit `0dfc7220a`) froze content head
`6212c8db4ac325c86e55c040fbefd3234c7ea83d`. The Grok audit run on that subject
returned NEEDS_SUPERVISOR. Its findings led to Amendment 02, and Copilot's reviews
of each later head led to Amendments 03-07. That first freeze and that audit
attempt are spent. They are kept in git history and in the evidence folder; they
say nothing about the head named above.

## What changed between the two frozen heads

`6212c8db4..7a469cb21`, in order:

| Commit | What |
|---|---|
| `0dfc7220a` | first freeze record (this file, earlier version) |
| `0faa34d15` | Amendment 02: check `notebook_path` as well as `file_path` |
| `e2bc70673` | Amendment 03: cwd-relative and symlinked sibling paths; per-path warn cache |
| `19ea99626` | Amendment 04: read the `..`-collapsed spelling of a path |
| `9795635ca` | Amendment 05: resolve `..` through the filesystem |
| `fe2b54471` | Amendment 06: root discovery reads the resolved `..` spelling |
| `79dded62a` | merge of `origin/main` at `ba5c3e07b` (PRs 1516 and 1517) |
| `7a469cb21` | Amendment 07: one filesystem walk yields every alias spelling |

Each amendment has its own record (`AMENDMENT_02.md` to `AMENDMENT_07.md`) with
the operator's words, the reason, and the validation at that edit. Amendments
02-07 were written by the supervisor session directly under a one-off writer
exception the operator granted for each; no child was dispatched for them.

Against `main`, the PR changes 20 files: `.claude/hooks/dcp_surface_guard.py`,
`tests/unit/dcp_surface_guard/__init__.py`,
`tests/unit/dcp_surface_guard/test_file_repo_root.py`, and 17 files under
`proof/MACRO-DMX-GUARD-FILE-REPO-001/`. It touches no workflow file.

## State at freeze (observed 2026-11-19, after 12:14Z)

| Item | Result | Evidence |
|---|---|---|
| Local head equals remote head | PASS | both `7a469cb21d185b45d8e10fe0013e7f5d860b68f6`; worktree clean |
| PR up to date with `main` | PASS | 0 behind, 15 ahead; merge base `ba5c3e07b` |
| PR out of draft | PASS | `isDraft=false` |
| Review threads | PASS | 0 unresolved of 7 |
| Copilot review of the frozen head | PASS | submitted 2026-11-19T12:14:38Z: "No open issues", both findings from the review of `79dded62a` marked resolved |
| CI on the frozen head | 20 pass, 2 fail, 3 skipped | see below |

The two failing checks are `independent embedded audit` and
`PR Steward / final readiness`. Both wait for the audit and have failed on every
head of this PR. The three skipped checks are Installer Smoke, Integration Tests
and Scoped Coverage. `mergeStateStatus` is `BLOCKED` for the same reason.

Copilot's review also says a human should check whether the recorded freeze still
matches the code after the amendments. This rewrite is the answer to that.

## Local validation on the frozen head

Clean env (`env -i`, `HOME`, `PATH=/usr/bin:/bin`, `PYTHONPATH=<worktree>/src`),
repo `.venv` Python. Run on the working tree that became `7a469cb21`:

| Check | Result |
|---|---|
| `tests/unit/dcp_surface_guard/test_file_repo_root.py` | PASS — 35 passed |
| Same test file against the guard at `79dded62a` | 3 failed, 32 passed (the three Amendment 07 tests that cover the new findings) |
| Every test file under `tests/` that mentions `dcp_surface_guard`, `native_hooks` or `red_lane` (32 files) | 1025 passed, 1 failed |
| `flake8 --select=E9,F,W` on the guard and its test file | PASS — 0 findings |
| Reproduction probe for both Copilot findings on `79dded62a` | PASS — both blocked; plain sibling path and real red-lane path still blocked |
| Full `make test` | NOT_RUN |

The one failure is
`tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`.
It fails the same way on `main` and on every earlier head of this branch: it flags
`.github/workflows/` changes that come from `main`'s history.

## Known limits carried into the audit

- `_alias_forms` keeps at most 64 spellings per path. The fully resolved spelling
  and the one that keeps only the most recent symlink name are always kept. A path
  with more than six symlink components can lose other spellings. No test covers
  that case. (Recorded in `AMENDMENT_07.md`.)
- Copilot found a new variant of the symlink / `..` gap on five successive heads
  before this one. The Amendment 07 walk is meant to close the family; that claim
  is untested beyond the cases in the test file.

## Route

- Session model: requested `claude-fable-5-2` (set by the operator with `/model`
  during this session; earlier amendments were written under the previous session
  model). Provider-attested model: UNKNOWN. Effort: UNKNOWN (not read for this
  record).
- Subagents spawned for this record: 0.

## Blockers

| Blocker | Action that clears it |
|---|---|
| Audit NOT_RUN | The operator chose Grok as the governing audit and AGY as corroboration, both on the frozen head. They run next. |
| Signing, steward release phrase, merge | The operator's, after the audit. |

If any commit that changes code or tests lands after this record, this freeze is
void and a new one is needed.

## Files written

- `proof/MACRO-DMX-GUARD-FILE-REPO-001/G02_RETURN.md` (this file)

Rollback: `git revert` of this file's commit restores the first freeze record.
Closing the PR unmerged and deleting the remote branch is the operator's.

Authority: NONE. This return grants nothing.
