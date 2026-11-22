# MACRO-DMX-GUARD-FILE-REPO-001 - Amendment 10: spelling-limit message and the new-PROOF.json check

## Operator words (verbatim, AskUserQuestion answer, 2026-11-19T21:43:43.697Z)

Question put after Copilot's review of the Amendment 09 head:

> Copilot's fresh review of the Amendment 09 head raised 2 new findings; I
> reproduced both. (1) The Amendment 09 block message says "Use the file's
> real path instead". When a sibling's red-lane directory is a symlink to a
> folder outside every repo, that real path is allowed, so the message points
> at a way round the block. The guard cannot see that such a real path is
> red-lane (main allows it too); only the advice is new. (2) Advisory tier
> only: for a relative path, the "new PROOF.json" exemption checks existence
> against the process cwd only, so an existing schemas/proof/.../PROOF.json
> gets no warning when cwd is elsewhere. Main does the same for the repo's own
> relative paths. How should PR 1513 proceed?

Answer: **"Fix both as Amendment 10 (Recommended)"**

Recorded by the team lead (Control Tower supervisor session
`c311455f-f4c3-4513-b995-82ff91a5ca87`).

## Why

Copilot reviewed head `07ab70d2dbbdf89de564e6e1ca32225d0a929693` (Amendment 09)
and raised two findings. The supervisor reproduced both with a standalone
probe (`~/.local/share/dopemux/evidence/pr1513/r2/repro/copilot_a09_probe.py`)
before any edit.

1. **The block message pointed at a way round the block.** Amendment 09 blocks
   a path that has more than 64 spellings and told the caller to "Use the
   file's real path instead". Take a sibling checkout whose
   `services/task-orchestrator` is a symlink to a folder outside every repo.
   The real path of a file in it is `<outside>/x.py`, which matches no
   red-lane pattern, so the guard allows it. The message therefore named a
   spelling that gets the same edit through.
2. **An existing PROOF.json could be treated as new.** The warning tier skips a
   `PROOF.json` that does not exist yet (the scaffold flow). The existence
   check used the path as given, so a relative path was looked up under the
   process cwd only. With cwd elsewhere, an existing
   `schemas/proof/TP/PROOF.json` under the project root looked new and got no
   contract-surface warning.

## What changed

`.claude/hooks/dcp_surface_guard.py`:

- The spelling-limit block message no longer names another path to try. It now
  ends: "Do not retry it under a different spelling: ask the operator to
  review where the path leads first." The block itself is unchanged.
- `_proof_json_is_new` takes `project_root` and looks a relative path up under
  the same bases the rest of the guard reads (`project_root` and the process
  cwd, from `_absolute_bases`). The file counts as new only when neither base
  has it. `os.path.lexists` is used, so a dangling symlink named `PROOF.json`
  counts as existing and is warned. Absolute paths behave as before.
- `surface_guard_warnings` passes `project_root` to the helper. It is the only
  caller.

Nothing that was blocked or warned before is now allowed. The change adds one
warning case (finding 2) and changes one message (finding 1).

`tests/unit/dcp_surface_guard/test_file_repo_root.py` gains four tests:

- `test_spelling_limit_block_does_not_advise_another_path`
- `test_existing_relative_proof_json_is_warned_when_cwd_is_elsewhere`
- `test_existing_relative_proof_json_is_warned_when_only_cwd_has_it`
- `test_new_relative_proof_json_is_not_warned`

The first two failed against `07ab70d2d` and pass after the change. The other
two passed before and after; they pin the cwd lookup and the scaffold-flow
exemption so the fix cannot remove either.

## Who made the edit

The supervisor session wrote the code directly, with no child dispatch and no
subagent, under the same one-off writer exception as Amendments 02-09. G01's
packet names `G01-implementer` as the only canonical writer of these two
files; the exception covers this one edit only and changes no
`canonical_writers` in the issued packets, which keep their hashes. This file
is in no workstream allowlist; it follows the Amendment 01-09 precedent.

## Local validation at the edit

Clean env (`env -i`, `HOME`, `PATH=/usr/bin:/bin`, `PYTHONPATH=<worktree>/src`),
repo `.venv` Python, on top of `07ab70d2d`:

- PASS - `tests/unit/dcp_surface_guard/test_file_repo_root.py`: 49 passed
  (45 before, plus the 4 new tests).
- PASS, with one known failure - the 32 test files under `tests/` that mention
  `dcp_surface_guard`, `native_hooks` or `red_lane`: 1,039 passed, 1 failed.
  The failure is
  `tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`,
  which fails the same way on `main` and on every earlier head of this branch
  (it flags `.github/workflows/` changes from main's history); this PR touches
  no workflow file.
- PASS - `flake8 --select=E9,F` on both files: 0 findings.
- PASS - reproduction probe (`r2/repro/copilot_a09_probe_a10.py`, a copy of
  the Amendment 09 probe with the helper call given its new second argument;
  output in `r2/repro/copilot_a09_probe.after_a10.out`):
  `f1_block_message_says_use_real_path` true -> false,
  `f2_relative_is_treated_as_new` true -> false,
  `f2_relative_warned_cwd_elsewhere` false -> true,
  `f2_own_repo_relative_warned_cwd_elsewhere` false -> true. The path is still
  blocked past the limit.
- PASS - the Amendment 08 cap probe and the AGY F1/F2 probe give the same
  output as after Amendment 09 (`*.after_a10.out`).
- FAIL (same before and after) - `black --check` on both files. Both already
  fail at `07ab70d2d`. Not reformatted, to keep the diff to the fix.
- NOT_RUN - full `make test`.
- NOT_RUN - CI on the new head, Copilot review of the new head, Grok audit,
  AGY corroboration. No audit has been run on any head that contains
  Amendments 08, 09 or 10.

## Known limit (not fixed here)

`f1_real_path_blocked` is false before and after this amendment. When a
sibling's red-lane directory is a symlink to a folder outside every repo, an
edit addressed by that folder's own path is allowed, because nothing in that
path names a red-lane location and the guard does not search other checkouts
for links that point at it. `main` allows the same edit. Amendment 10 only
stops the guard's own message from suggesting it. Closing the gap needs a
design decision (for example a reverse lookup of red-lane links) and belongs
in a follow-up, not in this PR.

## Effect on the freeze record

`G02_RETURN.md` still describes superseded head `ee43f9914`; both audits of
that head stand as FAIL and are not reused. Next: push, CI and a fresh Copilot
review on the new head, rewrite the freeze record for the head that is
actually frozen, then run the governing Grok audit and the AGY corroboration
on that head.
