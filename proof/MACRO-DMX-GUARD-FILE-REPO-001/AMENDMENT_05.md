# MACRO-DMX-GUARD-FILE-REPO-001 - Amendment 05: resolve `..` through the filesystem, not lexically

**Operator words (verbatim, AskUserQuestion answer, 2026-11-19, shortly before 04:25:37Z; exact time not read back from the transcript):** "Fix here (Recommended)"

**In answer to (verbatim):** "Copilot reviewed 19ea99626: the Amendment 04 finding is resolved, 1 new one, reproduced. My Amendment 04 fix over-blocks: when `link` is a symlink to `other/sub`, the path `link/../services/task-orchestrator/x.py` really lands in `other/services/...` (an ordinary file) but is now hard-blocked, and the advisory fires falsely the same way. The previous head allowed it. It is a false block, not a bypass. How should PR 1513 proceed?"

**Recorded by:** the team lead (Control Tower supervisor session), after Copilot's review of head `19ea9962648392e64fe95e7f010cacd2c756b3d7`.

## Why

Amendment 04 added `os.path.normpath(file_path)` as a reading. `normpath`
collapses `..` lexically, but the filesystem resolves `<symlink>/..` to the
parent of the symlink's target. With `<root>/link -> <root>/other/sub`, the
path `<root>/link/../services/task-orchestrator/x.py` is the ordinary file
`<root>/other/services/task-orchestrator/x.py`, yet the lexical reading named
the red-lane file and the edit was hard-blocked. The advisory fired falsely in
the same way.

Reproduced with a standalone probe before any edit: blocked and warned at
`19ea99626`, allowed and not warned at `e2bc70673`. This was a regression
introduced by Amendment 04. It failed closed (a false block, not a bypass).

## What changes

In `_repo_relative_candidates` in `.claude/hooks/dcp_surface_guard.py`, the
`normpath` reading is replaced. When the path contains `..`, the part up to and
including the last `..` is resolved with `os.path.realpath`, and the part after
it is appended as typed (symlinks kept). Paths without `..` get no extra
reading, as before Amendment 04.

- The Amendment 04 case still blocks: `<x>/../<checkout>/services/<symlink>/f`
  becomes `<checkout>/services/<symlink>/f`.
- The false block is gone: `<root>/link/../services/...` becomes
  `<root>/other/services/...`.
- Compared with `e2bc70673` this only adds a candidate. Compared with
  `19ea99626` it removes the lexical one, which is the intended correction.

Three tests are added to `tests/unit/dcp_surface_guard/test_file_repo_root.py`:

- `test_dotdot_after_symlink_to_ordinary_file_is_allowed` (failed before the fix)
- `test_dotdot_after_symlink_to_ordinary_file_is_not_warned` (failed before the fix)
- `test_dotdot_after_symlink_into_red_lane_is_blocked` (passed before and after;
  it pins the true-positive direction)

The three Amendment 04 tests still pass.

## Write surface and who made the edit

The two code files are already in the packet's allowlist. This file is in no
workstream allowlist; it follows the Amendment 01-04 precedent. The issued
packet files keep their hashes.

As with Amendments 02-04, the code was written directly by the supervisor
session, with no child dispatch, although G01's packet names `G01-implementer`
as the only canonical writer of these two files. The option the operator chose
read: "Amendment 05, same one-off writer exception". The exception covers this
one edit only and does not change `canonical_writers` in the issued packets.

## Local validation at the edit

Run in the worktree on top of `19ea9962648392e64fe95e7f010cacd2c756b3d7`, with
`env -i` and the main checkout's `.venv`:

- `tests/unit/dcp_surface_guard`, `tests/dcp`, `tests/unit/runner_memory_2a_r2_w09`,
  `tests/test_native_hooks_workflow.py`, `tests/unit/test_native_hooks_dispatcher.py`,
  `tests/unit/test_native_hooks_register.py`, `tests/test_dcp_surface_guard.py`,
  `tests/coldstart/test_l0_membership.py`: **534 passed, 1 failed** (531 passed,
  1 failed before this amendment; the difference is the three new tests).
- The failure is `tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`,
  which fails the same way without this change.
- Reproduction probe: the false block and the false advisory are gone; the true
  red-lane path is still blocked.
- `flake8 --select=F,E9,W6` on both files: 0 findings.
- `black --check` reports both files as needing reformatting; it did so before
  this PR's amendments as well, and they were not reformatted here.

## Next

Push after checking the remote head is still
`19ea9962648392e64fe95e7f010cacd2c756b3d7`; wait for CI and a fresh Copilot
review; rewrite the freeze record (`G02_RETURN.md`) for the new head; then the
governing Grok audit and the AGY corroboration on that head. No audit has been
run on any head that contains Amendments 02-05. The bundle's implementer field
names G01's child and this supervisor session (Amendments 02-05).
