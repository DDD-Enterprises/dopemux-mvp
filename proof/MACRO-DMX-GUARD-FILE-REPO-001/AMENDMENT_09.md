# MACRO-DMX-GUARD-FILE-REPO-001 - Amendment 09: past the spelling limit the guard blocks

**Operator words** (verbatim, AskUserQuestion answer, 2026-11-19T21:22:12.989Z):

> Question put after Copilot's review of the Amendment 08 head: "Copilot reviewed the
> Amendment 08 head 29f77aa0c and raised one new issue, which I reproduced: when a
> path has more than 64 spellings (six stacked symlinks are enough), the guard keeps
> only the first 64 and can throw away the red-lane spelling, so the edit is allowed.
> Everything else is green apart from the two audit-gated checks. How should PR 1513
> proceed?"
>
> Answer: "Fix as Amendment 09 (Recommended)"

Recorded by the team lead (Control Tower supervisor session
`c311455f-f4c3-4513-b995-82ff91a5ca87`).

## Why

Copilot reviewed head `29f77aa0c5c6d72b5439614a3d3ad7c6bc879cf9` and raised one
issue. The supervisor reproduced it with a standalone probe
(`~/.local/share/dopemux/evidence/pr1513/r2/repro/copilot_a08_cap_probe.py`) before
any edit.

Amendment 08 recorded the 64-spelling limit (`_MAX_ALIAS_FORMS`) as a known residual:
a path with more spellings kept the first 64. Each symlink on a path can double the
number of spellings, so the limit is reachable. In the probe, `docs/link` points at
`<sibling>/services/task-orchestrator`, and that directory is a symlink reached
through six or seven stacked links. The red-lane spelling was among those cut, so
writing `docs/link/x` was allowed although it is the same file as the blocked
`<sibling>/services/task-orchestrator/x`. With five stacked links the path has 34
spellings and was already blocked.

## What changed

`.claude/hooks/dcp_surface_guard.py`:

- The spelling list is never cut short. `_walk_alias_forms` raises a new
  `_AliasLimitExceeded` when a step would hold more than 64 spellings (new helper
  `_within_alias_limit`, used at both places that used to slice the list).
- `_block_reason_for_path` calls a new `_alias_limit_exceeded` before it matches any
  pattern. When any absolute form of the path (as typed, or joined to the project
  root or the process cwd) is past the limit, the edit is hard-blocked with a reason
  that names the limit and red lane `DCP-RED-MERGE-SEAM-0001`.
- `_alias_forms` catches the new exception and returns `()`, so root discovery and
  the advisory tier still never raise. The dispatcher
  (`src/dopemux/claude/native_hooks.py`, lines 497-499) denies on the block reason
  before it runs the advisory tier, so no advisory is lost on a path that is past
  the limit.

Nothing that was blocked before is now allowed. The change only adds blocks.

Known cost: an ordinary file that is not in any red lane is also blocked when its
path is past the limit. That takes about six stacked symlinks on one path. The block
reason tells the caller to use the file's real path.

`tests/unit/dcp_surface_guard/test_file_repo_root.py` gains five tests:

- `test_red_lane_behind_more_spellings_than_the_cap_is_blocked`
- `test_relative_path_with_more_spellings_than_the_cap_is_blocked`
- `test_ordinary_file_with_more_spellings_than_the_cap_is_blocked`
- `test_ordinary_file_under_the_cap_is_allowed`
- `test_warnings_do_not_raise_past_the_cap`

The first three failed against `29f77aa0c` and pass after the change. The last two
passed before and after; they guard against over-blocking and against a raise in the
advisory tier.

## Who made the edit

The supervisor session wrote the code directly, with no child dispatch and no
subagent, under the same one-off writer exception as Amendments 02-08. G01's packet
names `G01-implementer` as the only canonical writer of these two files; the
exception covers this one edit only and changes no `canonical_writers` in the issued
packets, which keep their hashes. This file is in no workstream allowlist; it follows
the Amendment 01-08 precedent.

## Local validation at the edit

Clean env (`env -i`, `HOME`, `PATH=/usr/bin:/bin`, `PYTHONPATH=<worktree>/src`), repo
`.venv` Python, on top of `29f77aa0c`:

- PASS - `tests/unit/dcp_surface_guard`: 45 passed.
- PASS - the 32 test files under `tests/` that mention `dcp_surface_guard`,
  `native_hooks` or `red_lane`: 1035 passed, 1 failed. The failure is
  `tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`,
  which fails the same way on `main` and on every earlier head of this branch (it
  flags `.github/workflows/` changes from main's history); this PR touches no
  workflow file.
- PASS - `flake8 --select=E9,F` on both files: 0 findings.
- PASS - Copilot's reproduction probe: the six-link and seven-link cases are now
  blocked (`r2/repro/copilot_a08_cap_probe.after_a09.out`); the saved before-output
  (`copilot_a08_cap_probe.out`) shows `n6_via_docs_link_blocked` and
  `n7_via_docs_link_blocked` as false.
- PASS - the Amendment 08 probe still blocks all of its shapes
  (`r2/repro/agy_f1_f2_probe.after_a09.out`).
- FAIL (same before and after) - `black --check` on both files. Both files already
  fail it at `29f77aa0c`; none of the lines black would change are lines this
  amendment added. Not reformatted, to keep the diff to the fix.
- NOT_RUN - full `make test`.
- NOT_RUN - CI on the new head, Copilot review of the new head, Grok audit, AGY
  corroboration. No audit has been run on any head that contains Amendment 08 or 09.

## Effect on the freeze

No head is frozen. The freeze record (`G02_RETURN.md`) still describes superseded
head `ee43f9914`; both audits of that head stand as FAIL and are not reused. Next:
push, CI and a fresh Copilot review on the new head, rewrite the freeze record for
the head that is actually frozen, then run the governing Grok audit and the AGY
corroboration on that head.
