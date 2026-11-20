# MACRO-DMX-GUARD-FILE-REPO-001 - Amendment 04: read the `..`-collapsed spelling of a path

**Operator words (verbatim, AskUserQuestion answer, 2026-11-19T03:26:39.521Z):** "Fix here (Recommended)"

**In answer to (verbatim):** "Copilot reviewed e2bc70673: both earlier findings resolved, 1 new one, reproduced. A path with a `..` hop (e.g. `/tmp/transit/../sibling/services/task-orchestrator/x.py`) is allowed when the red-lane directory is a symlink to outside. The same bypass exists on main today inside the project root, so this PR did not introduce it. How should PR 1513 proceed?"

**Recorded by:** the team lead (Control Tower supervisor session), after Copilot's review of head `e2bc70673b329e907ad8d6fa2b56ed9f233e0189`.

## Why

Copilot's review of `e2bc70673` marked both Amendment 03 findings resolved and
raised one "previously missed" issue in code that Amendment 03 did not change.

`_repo_relative_candidates` read a path in two spellings: as given, and resolved
with `os.path.realpath`. For `<x>/../<checkout>/services/task-orchestrator/x.py`
where `services/task-orchestrator` is a symlink to a location outside the
checkout:

- the given spelling does not sit under the checkout lexically, because the
  `..` is not collapsed;
- the resolved spelling follows the symlink out of the checkout.

Neither reading matched a red-lane pattern, so the edit was allowed. The plain
spelling of the same file was blocked.

Reproduced with a standalone probe before any edit:

- against `e2bc70673`: allowed for a sibling checkout, allowed for the project
  root, and no advisory for a symlinked `schemas` directory in a sibling;
- against `origin/main`'s guard: the project-root case is allowed there too.
  The gap predates this PR.

## What changes

- `_repo_relative_candidates` in `.claude/hooks/dcp_surface_guard.py` adds one
  more candidate: `os.path.normpath(file_path)`, the `..`-collapsed lexical
  spelling with symlinks kept. The given spelling is still read (an in-tree
  `..` is kept so the rules' own traversal pattern can match it), and so is the
  resolved one.
- Nothing else changes. The function only gains a candidate, so nothing that
  was blocked or warned before is now allowed. Block and advisory both go
  through this function, so one change covers both.

Three tests are added to `tests/unit/dcp_surface_guard/test_file_repo_root.py`:

- `test_traversal_prefix_to_symlinked_sibling_red_lane_is_blocked`
- `test_traversal_prefix_to_symlinked_project_root_red_lane_is_blocked`
- `test_traversal_prefix_to_symlinked_sibling_contract_surface_is_warned`

All three failed against `e2bc70673` before the guard change and pass after it.

## Write surface and who made the edit

The two code files are already in the packet's allowlist. This file,
`AMENDMENT_04.md`, is in no workstream allowlist; it follows the Amendment
01-03 precedent. The issued packet files keep their hashes.

As with Amendments 02 and 03, the code was written directly by the supervisor
session, with no child dispatch and no subagent counters, although G01's packet
names `G01-implementer` as the only canonical writer of these two files. The
option the operator chose read: "Amendment 04, same one-off writer exception".
The exception covers this one edit only and does not change
`canonical_writers` in the issued packets.

## Local validation at the edit

Run in the worktree on top of `e2bc70673b329e907ad8d6fa2b56ed9f233e0189`, with
`env -i` and the main checkout's `.venv`:

- `tests/unit/dcp_surface_guard`, `tests/dcp`, `tests/unit/runner_memory_2a_r2_w09`,
  `tests/test_native_hooks_workflow.py`, `tests/unit/test_native_hooks_dispatcher.py`,
  `tests/unit/test_native_hooks_register.py`: **477 passed, 1 failed** (474
  passed, 1 failed before this amendment; the difference is the three new tests).
- The failure is `tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`,
  which fails the same way without this change.
- `tests/test_dcp_surface_guard.py` and `tests/coldstart/test_l0_membership.py`
  (the other suites that import the guard): **54 passed**.
- Reproduction probe: all three traversal cases are now blocked or warned.
- `flake8 --select=F,E9,W6` on both files: 0 findings.

## Next

Unchanged from Amendment 03: push after checking the remote head is still
`e2bc70673b329e907ad8d6fa2b56ed9f233e0189`; wait for CI and a fresh Copilot
review; rewrite the freeze record (`G02_RETURN.md`) for the new head; then the
governing Grok audit and the AGY corroboration on that head. No audit has been
run on any head that contains Amendment 02, 03 or 04. The bundle's implementer
field names G01's child and this supervisor session (Amendments 02, 03, 04).
