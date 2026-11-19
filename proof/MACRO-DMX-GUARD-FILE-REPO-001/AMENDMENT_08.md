# MACRO-DMX-GUARD-FILE-REPO-001 - Amendment 08: symlinks are followed one hop at a time

**Operator words** (verbatim, AskUserQuestion answer, 2026-11-19T20:43:26.811Z):

> Question put after both audits of frozen head `ee43f9914` returned: "Both audits of
> frozen head ee43f9914 returned FAIL, and I reproduced the code findings. The guard
> resolves a symlink chain in one jump, so a red-lane name that appears only in the
> middle of a chain is never checked (found by both Grok and AGY); and two symlinks
> around a '..' can still drop the blocked spelling (AGY only). How should PR 1513
> proceed?"
>
> Answer: "Fix as Amendment 08 (Recommended)"

Recorded by the team lead (Control Tower supervisor session
`c311455f-f4c3-4513-b995-82ff91a5ca87`).

## Why

The contained Grok audit and the contained AGY second look both ran on frozen head
`ee43f99140c09ef30e596873fef8da776e0c87ac` and both returned FAIL. Their raw output
is kept under `~/.local/share/dopemux/evidence/pr1513/r2/`. The supervisor
reproduced three shapes with a standalone probe (`r2/repro/agy_f1_f2_probe.py`)
before any edit. Each one was allowed although it writes the same file as a path the
guard blocks:

1. **Chain through a red-lane name.** `docs/innocent.py` is a symlink to
   `services/task-orchestrator/x.py`, which is itself a symlink to a file outside.
   The Amendment 07 walk called `os.path.realpath` at the first link, which jumps to
   the end of the chain, so the red-lane name in the middle was never read.
2. **Target spelled through a symlinked red-lane directory.** `docs/link` points at
   `<sibling>/services/task-orchestrator`, and that directory is a symlink to an
   outside directory. Same cause: only the final target was kept.
3. **`..` out of a second symlink.** In
   `far/link/../<sibling>/services/task-orchestrator/sym2/../x.py` the red-lane
   directory is a symlink to `outside` and `sym2` points to `outside/sub`. At
   `sym2/..` the walk stepped to `outside` and dropped every spelling that ended in a
   symlink name, including `<sibling>/services/task-orchestrator`, which is another
   spelling of `outside`.

## What changed

`.claude/hooks/dcp_surface_guard.py`:

- `_alias_forms` now delegates to a new `_walk_alias_forms`. At a symlink the walk
  reads one hop with `os.readlink` and walks the target path as written, so every
  link in a chain and every symlink inside a target path contributes its own
  spelling (shapes 1 and 2). Relative targets are joined to the directory the link
  really sits in.
- The walk remembers every spelling it has seen for each resolved directory. When
  `..` leaves a symlink's target, the spellings already seen for the directory it
  lands in are picked up again (shape 3).
- A chain longer than 40 hops (`_MAX_SYMLINK_HOPS`), including a loop, yields no
  alias forms. The other readings of the path are unchanged, and the function still
  never raises.
- The `_MAX_ALIAS_FORMS` limit of 64 spellings per path is unchanged and is now
  applied at every step. A path with more spellings than that keeps the first 64,
  the fully resolved one first. This limit is a known residual, not a new one.

Nothing that was blocked or warned before is now allowed: the walk only adds
spellings.

`tests/unit/dcp_surface_guard/test_file_repo_root.py` gains five tests:

- `test_symlink_chain_through_red_lane_name_is_blocked` (shape 1)
- `test_symlink_target_spelled_through_symlinked_red_lane_is_blocked` (shape 2)
- `test_relative_symlink_target_through_symlinked_red_lane_is_blocked` (shape 2,
  relative target)
- `test_dotdot_out_of_second_symlink_keeps_red_lane_spelling` (shape 3)
- `test_symlink_loop_does_not_raise`

The first four failed against `ee43f9914` and pass after the change. The loop test
passed before and after; it guards the new recursion.

## Who made the edit

The supervisor session wrote the code directly, with no child dispatch and no
subagent, under the same one-off writer exception as Amendments 02-07. G01's packet
names `G01-implementer` as the only canonical writer of these two files; the
exception covers this one edit only and changes no `canonical_writers` in the issued
packets, which keep their hashes. This file is in no workstream allowlist; it follows
the Amendment 01-07 precedent.

## Local validation at the edit

Clean env (`env -i`, `HOME`, `PATH=/usr/bin:/bin`, `PYTHONPATH=<worktree>/src`), repo
`.venv` Python, on top of `ee43f9914`:

- PASS - `tests/unit/dcp_surface_guard`: 40 passed.
- PASS - guard, `tests/dcp`, `runner_memory_2a_r2_w09` and native-hooks suites: 502
  passed, 1 failed. The failure is
  `tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`,
  which fails the same way on `main` and on every earlier head of this branch (it
  flags `.github/workflows/` changes from main's history); this PR touches no
  workflow file.
- PASS - `flake8 --select=E9,F` on both files: 0 findings.
- PASS - reproduction probe: all three shapes are now blocked
  (`r2/repro/agy_f1_f2_probe.after_a08.out`); the saved before-output shows
  `F1_far_link_variant_blocked`, `F2a_chain_via_innocent_blocked` and
  `F2b_outside_link_chain_blocked` as false.
- NOT_RUN - full `make test`.
- NOT_RUN - CI on the new head, Copilot review of the new head, Grok audit, AGY
  corroboration. No audit has been run on any head that contains Amendment 08.

## Effect on the freeze

Frozen head `ee43f9914` and its freeze record are superseded. Both audits of that
head stand as FAIL and are not reused. Next: push, CI and a fresh Copilot review on
the new head, rewrite the freeze record (`G02_RETURN.md`) for the head that is
actually frozen, then run the governing Grok audit and the AGY corroboration on that
head.
