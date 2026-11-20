# MACRO-DMX-GUARD-FILE-REPO-001 - Amendment 03: cwd-relative and symlinked sibling paths; per-path warn cache

**Operator words (verbatim, AskUserQuestion answer, 2026-11-18T13:38:45.307Z):** "Fix both (Recommended)"

**In answer to (verbatim):** "Copilot reviewed 0faa34d15 and raised 2 new issues; I reproduced both. (1) Hard-deny gap: a relative path that reaches a sibling checkout only via the process cwd is allowed, and so is a red-lane directory in a sibling checkout that is a symlink to outside (both are blocked inside the project root). (2) Advisory gap from my Amendment 02: an already-warned first path hides the warning for a new second path. A fix needs an Amendment 03 and the same writer exception as last time. How should PR 1513 proceed?"

**Recorded by:** the team lead (Control Tower supervisor session), after Copilot's review of head `0faa34d15247430079be4ef6378bf2368b10ea94`.

## Why

Copilot's review of `0faa34d15` raised two issues. Both were reproduced with a
standalone probe before any edit, and both are closed by the same probe after it.

1. **Hard-deny gap (block path).** Root discovery started from one form of the
   path only: the path joined to `project_root`, then resolved with
   `os.path.realpath`.
   - A relative path that reaches a sibling checkout only through the process
     cwd never had that checkout discovered as a root, so
     `sibling/services/task-orchestrator/x.py` was allowed.
   - A red-lane directory inside a sibling checkout that is a symlink to a
     location outside it moved discovery out of the checkout, so the sibling
     was never a root and the edit was allowed. The same two cases were already
     blocked inside the project root.
2. **Advisory gap (warn path), introduced by Amendment 02.** The warn loop
   stopped at the first contract surface it found and only then consulted the
   cache. When that first path had already been warned in the session, the call
   returned no warning even if its second path was a new contract surface.

## What changes

- New `_guard_starts(file_path, project_root)` in
  `.claude/hooks/dcp_surface_guard.py`: the absolute forms root discovery walks
  up from. A relative path yields its `project_root` form and its cwd form; each
  is taken both lexically (`os.path.normpath`) and resolved
  (`os.path.realpath`). An absolute path yields its lexical and resolved forms.
- `_guard_roots` walks up from every start instead of one. Roots are only ever
  added; `project_root` stays first. A failing start is skipped, not fatal.
- `_guard_readings` also reads a relative path in its cwd-absolute lexical
  form, so a symlink on the way cannot leave only its resolved target to match.
- `surface_guard_warnings` checks the warn cache per candidate path and reports
  the first contract surface not yet warned in the session. The cache key
  format (`<session>:<path>`) is unchanged.
- `surface_guard_block`, `file_repo_root`, `tool_edit_path` and
  `tool_edit_paths` keep their definitions and signatures. Readings and roots
  are only added, so nothing that was blocked or warned before is now allowed.

Five tests are added to `tests/unit/dcp_surface_guard/test_file_repo_root.py`:

- `test_cwd_relative_sibling_path_is_blocked_when_project_root_is_elsewhere`
- `test_cwd_relative_sibling_contract_surface_is_warned`
- `test_symlinked_red_lane_dir_in_sibling_checkout_is_blocked`
- `test_symlinked_file_in_sibling_red_lane_is_blocked`
- `test_cached_first_path_does_not_hide_new_second_contract_surface`

All five failed against `0faa34d15` before the guard change and pass after it.

## Write surface and who made the edit

The two code files are already in the packet's allowlist. This file,
`AMENDMENT_03.md`, is in no workstream allowlist; it follows the Amendment 01
and 02 precedent. The issued packet files keep their hashes; this amendment is
read alongside them.

G01's packet names `G01-implementer` as the only canonical writer of
`.claude/hooks/dcp_surface_guard.py` and
`tests/unit/dcp_surface_guard/test_file_repo_root.py`, and G01's one correction
round was spent on Amendment 01. As with Amendment 02, the code for this
amendment was written directly by the supervisor session, with no child
dispatch and no subagent counters. The question put to the operator stated that
the fix "needs an Amendment 03 and the same writer exception as last time", and
the operator answered "Fix both (Recommended)". The exception covers this one
edit only. It does not change `canonical_writers` in the issued packets and
does not carry over to later edits.

## Local validation at the edit

Run in the worktree on top of `0faa34d15247430079be4ef6378bf2368b10ea94`, with
`env -i` and the main checkout's `.venv`:

- `tests/unit/dcp_surface_guard`, `tests/dcp`, `tests/unit/runner_memory_2a_r2_w09`,
  `tests/test_native_hooks_workflow.py`, `tests/unit/test_native_hooks_dispatcher.py`,
  `tests/unit/test_native_hooks_register.py`: **474 passed, 1 failed** (469
  passed, 1 failed before this amendment; the difference is the five new tests).
- The failure is `tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`,
  which fails the same way without this change. It lists `.github/workflows/`
  changes from `main`'s history; this PR touches no workflow file.
- Reproduction probe: both hard-deny cases return the red-lane block; the
  dual-key call after a cached first path returns one warning.
- `flake8 --select=F,E9,W6` on both files: 0 findings before and after.
- `black --check` reports both files as needing reformatting, as it did at
  `0faa34d15`. Not reformatted here, to keep the diff to the fix.

## Next

1. Commit and push. Before pushing, check that the remote head is still
   `0faa34d15247430079be4ef6378bf2368b10ea94`.
2. Wait for CI and bot reviews to settle on the new head, and request a fresh
   Copilot review of it.
3. Record a new freeze by rewriting the freeze record (`G02_RETURN.md`) so it
   names the new content head and its test counts.
4. Run the governing Grok audit, then the AGY corroboration, on the new frozen
   head. No audit has been run on any head that contains Amendment 02 or 03.
5. When building the bundle, record both writers of the audited code in the
   implementer field: G01's child and this supervisor session (Amendments 02
   and 03).
