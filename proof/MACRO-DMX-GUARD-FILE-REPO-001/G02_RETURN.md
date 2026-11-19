# G02 return — PR 1513 reviews settled, head frozen (third freeze)

**Status**: READY_FOR_AUDIT (the team lead's word; acceptance belongs to the
auditor and the operator).

**Subject (frozen content head)**: `dc5aac697bbbc4c752e685fbb93baee7b11cfd50` on
`fix/guard-file-repo-root`, PR
https://github.com/DDD-Enterprises/dopemux-mvp/pull/1513, base `main` at
`ba5c3e07b01ad46cae0d55cefdfbb9f9b3b647d7` (merge base; `origin/main` unchanged
at freeze, so the PR is 0 commits behind).

**Audit**: NOT_RUN on this head. No audit has been run on any head that contains
Amendments 08-10.

The commit that adds this version of the file changes only this file, so it sits
on top of the frozen head as a proof-only commit.

## This record replaces the first two freezes

| Freeze | Content head | Record commit | Audit result |
|---|---|---|---|
| first | `6212c8db4ac325c86e55c040fbefd3234c7ea83d` | `0dfc7220a` | Grok: NEEDS_SUPERVISOR |
| second | `7a469cb21d185b45d8e10fe0013e7f5d860b68f6` | `ee43f9914` | Grok: FAIL; AGY: FAIL |
| third (this file) | `dc5aac697bbbc4c752e685fbb93baee7b11cfd50` | the commit that adds this version | NOT_RUN |

The first audit's findings led to Amendment 02, and Copilot's reviews of each
later head led to Amendments 03-07. Both audits of the second freeze found that
the Amendment 07 walk resolved a symlink chain in one jump, so a red-lane name in
the middle of a chain was never checked. The supervisor reproduced those findings
before changing code; they led to Amendment 08. Copilot's reviews of the two
heads after that led to Amendments 09 and 10.

The first two freezes and their audit attempts are spent. They are kept in git
history and in the evidence folder
(`~/.local/share/dopemux/evidence/pr1513/r1` and `r2`); they say nothing about
the head named above.

## What changed since the second frozen head

`7a469cb21..dc5aac697`, in order:

| Commit | What |
|---|---|
| `ee43f9914` | second freeze record (this file, earlier version) |
| `29f77aa0c` | Amendment 08: follow symlinks one hop at a time |
| `07ab70d2d` | Amendment 09: block when a path has more spellings than the limit |
| `dc5aac697` | Amendment 10: spelling-limit message and new-`PROOF.json` check |

Each amendment has its own record (`AMENDMENT_08.md` to `AMENDMENT_10.md`) with
the operator's words, the reason, and the validation at that edit. Amendments
02-10 were written by the supervisor session directly under a one-off writer
exception the operator granted for each; no child was dispatched for them.

Against `main`, the PR changes 23 files: `.claude/hooks/dcp_surface_guard.py`,
`tests/unit/dcp_surface_guard/__init__.py`,
`tests/unit/dcp_surface_guard/test_file_repo_root.py`, and 20 files under
`proof/MACRO-DMX-GUARD-FILE-REPO-001/`. It touches no workflow file.

SHA-256 of the three non-proof files at the frozen head:

| File | SHA-256 |
|---|---|
| `.claude/hooks/dcp_surface_guard.py` | `d6e5554a008b9660782b2950548ac01a53cb5c40a80a9f135b1896e0f489a275` |
| `tests/unit/dcp_surface_guard/test_file_repo_root.py` | `a940b736a52863db6d507dbd9408a611ce8d2fdce8863e73e8b7bacca13046c3` |
| `tests/unit/dcp_surface_guard/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

## State at freeze (observed 2026-11-19, 21:58Z)

| Item | Result | Evidence |
|---|---|---|
| Local head equals remote head | PASS | both `dc5aac697bbbc4c752e685fbb93baee7b11cfd50`; worktree clean |
| PR up to date with `main` | PASS | 0 behind, 19 ahead; merge base `ba5c3e07b` |
| PR out of draft | PASS | `isDraft=false` |
| Review threads | PASS | 0 unresolved of 10 |
| Copilot review of the frozen head | PASS | submitted 2026-11-19T21:55:46Z: "No open issues", both findings from the review of `07ab70d2d` marked resolved, no inline comment raised on this head |
| CI on the frozen head | 20 pass, 2 fail, 3 skipped | see below |

The two failing checks are `independent embedded audit` and
`PR Steward / final readiness`. Both wait for the audit and have failed on every
head of this PR. The three skipped checks are Installer Smoke, Integration Tests
and Scoped Coverage. `mergeStateStatus` is `BLOCKED` for the same reason.

Copilot's review is headed "Needs a closer look" and says the symlink traversal
and path aliasing "have security and performance implications that warrant human
assessment". That assessment is the audit's and the operator's; this record does
not answer it.

## Local validation on the frozen head

Clean env (`env -i`, `HOME`, `PATH=/usr/bin:/bin`, `PYTHONPATH=<worktree>/src`),
repo `.venv` Python. Run on the worktree at `dc5aac697` with a clean tree:

| Check | Result |
|---|---|
| `tests/unit/dcp_surface_guard/test_file_repo_root.py` | PASS — 49 passed |
| Same test file against the guard at `7a469cb21` (second frozen head) | 9 failed, 40 passed (the tests added by Amendments 08-10) |
| Same test file against the guard at `07ab70d2d` | 2 failed, 47 passed (the two Amendment 10 tests) |
| Every test file under `tests/` that mentions `dcp_surface_guard`, `native_hooks` or `red_lane` (32 files) | 1039 passed, 1 failed |
| `flake8 --select=E9,F,W` on the guard and its test file | PASS — 0 findings |
| `black --check` on the guard and its test file | FAIL — both would be reformatted; the guard on `main` fails the same check; not reformatted, to keep the diff to the fix |
| Probe for the two audit findings on the second freeze (`agy_f1_f2_probe.py`) | PASS — all seven shapes blocked |
| Probe for Copilot's finding on `29f77aa0c` (`copilot_a08_cap_probe.py`) | PASS — 2, 5, 6 and 7 stacked links all blocked by plain path and through the link |
| Probe for Copilot's two findings on `07ab70d2d` (`copilot_a09_probe_a10.py`) | PASS on both findings; one known gap stays open, see below |
| Full `make test` | NOT_RUN |

The one test failure is
`tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`.
It fails the same way on `main` and on every earlier head of this branch: it flags
`.github/workflows/` changes that come from `main`'s history.

The probe scripts and their outputs are in
`~/.local/share/dopemux/evidence/pr1513/r2/repro/`, outside the repo.

## Known limits carried into the audit

- **Open gap, same on `main`.** When a sibling checkout's red-lane directory is a
  symlink to a folder outside every repo, an edit addressed by that folder's own
  path is allowed. Nothing in that path names a red-lane location, and the guard
  does not search other checkouts for links that point at it. Amendment 10 only
  stops the guard's own message from suggesting that path. Closing the gap needs a
  design decision and belongs in a follow-up. (Recorded in `AMENDMENT_10.md`;
  probe key `f1_real_path_blocked` is false.)
- **Fail-closed cost.** A path with more than 64 spellings
  (`_MAX_ALIAS_FORMS = 64`; six stacked symlinks are enough) is hard-blocked, and
  so is a symlink chain longer than 40 hops (`_MAX_SYMLINK_HOPS = 40`). This also
  blocks ordinary files that sit behind that many links. (Recorded in
  `AMENDMENT_09.md`.)
- Copilot and the two auditors have repeatedly found new variants of the
  symlink / `..` gap on earlier heads of this PR; Amendments 03-09 each answer
  one. The claim that the walk now closes the family is untested beyond the cases
  in the test file and the three probes.

## Route

- Session model: requested `claude-fable-5-2`. Provider-attested model: UNKNOWN.
- Effort: `$CLAUDE_EFFORT` read `high` when this record was written.
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

Rollback: `git revert` of this file's commit restores the second freeze record.
Closing the PR unmerged and deleting the remote branch is the operator's.

Authority: NONE. This return grants nothing.
