# MACRO-DMX-GUARD-FILE-REPO-001 — Amendment 07: one filesystem walk yields every alias spelling of a path

## Operator words (verbatim, AskUserQuestion answer)

Question put after Copilot's review of merge head
`79dded62ae72be10588ca285411435fc86ff5fd4`: "Copilot reviewed merge head 79dded62a
and raised 2 new high-severity findings; I reproduced both. (1) A path with two
symlink hops (far/link/../sibling/services/task-orchestrator/dir/../x.py) is
allowed although it reaches the same file as the blocked plain sibling path. (2) A
cwd-relative path (link/../sibling/services/task-orchestrator/x.py) is allowed
because the guard collapses '..' before following the symlink. This is the fifth
round of the same family of gap. How should PR 1513 proceed?"

Answer, recorded in the session transcript
(`c311455f-f4c3-4513-b995-82ff91a5ca87`) at 2026-11-19T12:02:54Z:
**"Structural fix (Recommended)"** — the option that read "Amendment 07, same
one-off writer exception. Replace the per-case readings with one
component-by-component walk that follows symlinks at every step and keeps every
intermediate form, for both root discovery and matching. Covers both findings and
the family behind them. Then CI, fresh Copilot review, freeze, Grok and AGY."

## Why

Amendments 04, 05 and 06 each added one more reading of a path that contains `..`
after a symlink. Each closed the case Copilot had named and left the next variant
open. The supervisor reproduced both new findings with a standalone probe against
`79dded62a` before any edit:

1. `far/link/../<sibling>/services/task-orchestrator/dir/../x.py` was allowed. The
   Amendment 05/06 helper resolved the path only up to its last `..`, so a second
   `..` further along moved the split point past the part that had to keep its
   symlink name.
2. `link/../<sibling>/services/task-orchestrator/x.py`, given relative to the
   process cwd, was allowed. The cwd-relative reading was collapsed lexically
   before the symlink was followed.

Both paths reach the same file as the plain sibling path, which is blocked.

## What changed

`.claude/hooks/dcp_surface_guard.py`

- New `_alias_forms(path)` replaces `_hop_resolved`. It walks an absolute path one
  component at a time, the way the filesystem resolves it. At a symlink it carries
  on two spellings: the link's resolved target, and the link's own name. At `..` it
  steps to the parent of where the walk really is, and drops any spelling whose
  last component is a symlink name, because that spelling's lexical parent is a
  different directory. Components that do not exist yet are kept as typed.
- New `_absolute_bases(file_path, project_root)` gives the absolute forms a path is
  read from: the path itself if absolute, otherwise joined to `project_root` and to
  the process cwd.
- `_repo_relative_candidates`, `_guard_starts` and `_guard_readings` now take their
  forms from `_alias_forms`, so path matching and root discovery read the same set
  of spellings. The cwd-relative reading goes through the same walk.
- Readings are still only added. Nothing that was blocked or warned before is
  allowed now. The control-character check, the red-lane patterns, the
  contract-surface list and the warn cache are unchanged.

Known limit: `_alias_forms` keeps at most 64 spellings per path
(`_MAX_ALIAS_FORMS`). The fully resolved spelling and the spelling that keeps only
the most recent symlink name are first in the list and are always kept. A path
with more than six symlink components can lose some of the spellings that keep
several earlier symlink names at once. No test covers that case.

`tests/unit/dcp_surface_guard/test_file_repo_root.py` — one helper
(`_far_link_to_sibling_parent`) and four tests:

- `test_second_dotdot_after_symlinked_sibling_red_lane_is_blocked` (finding 1)
- `test_cwd_relative_dotdot_after_symlink_reaches_sibling_red_lane_is_blocked`
  (finding 2)
- `test_cwd_relative_dotdot_after_symlink_reaches_sibling_contract_surface_is_warned`
  (finding 2, advisory side)
- `test_symlink_below_symlinked_sibling_red_lane_is_blocked`

The first three fail against the guard at `79dded62a` and pass after the change.
The fourth passes on both; it is a regression test for the Amendment 05 case under
the new walk.

## Who made the edit

The supervisor session wrote the code directly, with no child dispatch and no
subagent counters, under the same one-off writer exception as Amendments 02-06.
G01's packet names `G01-implementer` as the only canonical writer of these two
files; the exception covers this one edit only and changes no `canonical_writers`
in the issued packets, which keep their hashes. This file is in no workstream
allowlist; it follows the Amendment 01-06 precedent.

## Local validation at the edit

Clean env (`env -i`, `HOME`, `PATH=/usr/bin:/bin`, `PYTHONPATH=<worktree>/src`),
repo `.venv` Python, on top of `79dded62a`:

- PASS — `tests/unit/dcp_surface_guard/test_file_repo_root.py`: 35 passed.
- PASS — the same test file against the guard at `79dded62a`: 3 failed, 32 passed
  (the three tests named above).
- PASS — every test file under `tests/` that mentions `dcp_surface_guard`,
  `native_hooks` or `red_lane`: 1025 passed, 1 failed. The failure is
  `tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`,
  which fails the same way on `main` and on every earlier head of this branch (it
  flags `.github/workflows/` changes from `main`'s history); this PR touches no
  workflow file.
- PASS — `flake8 --select=E9,F,W` on both files: 0 findings.
- PASS — reproduction probe: both Copilot cases are now blocked, and the plain
  sibling path and the real red-lane path are still blocked.
- NOT_RUN — full `make test`.
- NOT_RUN — CI on the new head, Copilot review of the new head, Grok audit, AGY
  corroboration. No audit has been run on any head that contains Amendments 02-07.

## Next

Push, then CI and a fresh Copilot review on the new head. Rewrite the freeze
record (`G02_RETURN.md`) for the head that is actually frozen, then run the
governing Grok audit and the AGY corroboration on that head.
