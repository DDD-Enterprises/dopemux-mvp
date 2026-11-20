# MACRO-DMX-GUARD-FILE-REPO-001 - Amendment 11: one set of spellings per real folder; a walk that cannot finish blocks

## Operator words (verbatim, AskUserQuestion answer, 2026-11-20T03:01:12.205Z)

Question put after both audits of frozen head `e95187bb2` returned FAIL:

> Both audits of frozen head e95187bb2 (content head dc5aac697) returned FAIL,
> the third failed freeze. AGY: two more symlink shapes get a red-lane edit
> through (a two-level link target followed by '..', and a link beside a
> symlinked red-lane folder); I reproduced both. Grok: the guard allows the edit
> when its spelling walk aborts (loops, readlink errors); in practice the kernel
> refuses chains over 32 links, so I could not reach that with a path that
> opens, but the principle is right. Both: the audit prompt lacked the
> commit-range proof Amendment 02 required, which I missed in the last two
> rounds. The 40-hop sentence in the freeze record is wrong. How should PR 1513
> proceed?

Answer: **"Amendment 11, one more round (Recommended)"**. The option read:
"Same one-off writer exception as 02-10. Keep one set of spellings per real
folder and use it at every step, not just after '..' (the root cause AGY
found); block when the walk aborts; fix the 40-hop sentence; put the
commit-range proof in the next audit prompt; re-freeze, then Grok and AGY. If
that round FAILs on another symlink shape, I stop and bring you the descope
choice instead of an Amendment 12."

Recorded by the team lead (Control Tower supervisor session
`c311455f-f4c3-4513-b995-82ff91a5ca87`).

**Stop rule from that ruling:** if the audits of the next frozen head FAIL on
another symlink shape, there is no Amendment 12. The supervisor stops and brings
the operator the descope choice.

## Why

The two audits of frozen head `e95187bb2` (content head `dc5aac697`) are saved in
`~/.local/share/dopemux/evidence/pr1513/r3/` (`GROK_VERDICT.json`,
`AGY_VERDICT.json`). Both returned FAIL.

1. **AGY F1 (high), reproduced.** Two shapes where the plain spelling of a
   red-lane file is blocked and another spelling of the same file is allowed.
   Probe: `r3/repro/agy_r3_f1_probe.py`, output before this amendment in
   `agy_r3_f1_probe.out`.
   - A symlink inside a symlinked red-lane folder points two levels deep
     (`outside/a/b`), then the path steps back with `..`. The one-level version
     (Amendment 08's own test) was blocked.
   - `<checkout>/services` is a symlink to an outside folder, and a link in that
     folder points at `task-orchestrator` (relative or absolute target). Editing
     through that link was allowed.
   Cause: Amendment 08 added the spellings already seen for a real folder only
   after a `..`. The nested walk of a link's target starts from the folder's real
   name alone, so it did not pick up the red-lane spelling when it passed through
   a folder it had already met.
2. **Grok F2 (high), principle accepted, not reproduced as an exploit.** When
   the spelling walk aborts (a chain past 40 links, a loop, a link that cannot be
   read, a `ValueError`, a `RecursionError`), `_alias_forms` returns no
   spellings and `_alias_limit_exceeded` let the path through. Probe:
   `r3/repro/grok_r3_f2_probe.py`: on this machine the kernel refuses a chain of
   33 links (errno 62), so no path that opens reaches the 40-link limit, and a
   loop cannot be opened either. The guard still allowed both, which is the
   inconsistency Grok named.
3. **Grok F1 (high) and AGY R2 (low), a process miss.** The audit prompts for the
   second and third freezes did not carry the commit-range proof that
   Amendment 02 step 4 required in the trusted section (`git rev-list` and
   `git diff --name-only <content-head>..<audited-head>`). The prompt builder
   used for both rounds did not add it, and I did not check. For the third
   freeze the range is one commit (`dc5aac697..e95187bb2`) and it changes only
   `G02_RETURN.md`; the next round puts that proof in the trusted section.
4. **AGY F2 (low), my error.** The third freeze record said a chain longer than
   40 links is hard-blocked. The code did not block it. After this amendment it
   does, and the next freeze record states the actual behaviour.
5. **AGY F3 (medium), accurate.** Amendments 02-11 were written by this session
   under one-off operator exceptions, outside the packet's named writer and its
   attempt limits. Every amendment records the operator's words; this one does
   too. The finding stands as a governance observation for the operator.

## What changed

`.claude/hooks/dcp_surface_guard.py`:

- `_walk_alias_forms` now merges the spellings already known for the current real
  folder at every step, not only after `..`. Descending into a folder, following
  a link, and stepping back all use the same set. `known` is still shared across
  the nested walks of link targets.
- `_alias_limit_exceeded` returns true on any abort of the walk: more than 64
  spellings (Amendment 09), a chain past `_MAX_SYMLINK_HOPS` or a loop, a link
  that cannot be read, `ValueError`, `RecursionError`. It used to return true
  only for the 64-spelling case. The block message now names all four causes and
  still does not advise another path (Amendment 10).
- Nothing else changed. `_alias_forms` still returns no spellings on an abort, so
  root discovery and the warning tier never raise.

Nothing that was blocked or warned before is now allowed. The change adds
spellings and adds blocks. The 64-spelling threshold did not move: five stacked
links give 33 spellings and six trip the limit, before and after.

`tests/unit/dcp_surface_guard/test_file_repo_root.py`:

- New: `test_second_link_two_levels_deep_then_dotdot_keeps_red_lane_spelling`
  (absolute and relative target), `test_two_level_link_below_a_link_to_the_red_lane_is_blocked`,
  `test_link_beside_a_symlinked_red_lane_ancestor_is_blocked` (absolute and
  relative), `test_symlink_chain_past_the_hop_limit_is_blocked`,
  `test_unreadable_link_is_blocked_not_allowed`,
  `test_blocked_walk_does_not_advise_another_path`.
- Controls that pass before and after: `test_chain_just_under_the_hop_limit_is_allowed`,
  `test_ordinary_symlinked_path_is_still_allowed`.
- **Changed expectation of an existing test.** `test_symlink_loop_does_not_raise`
  asserted that a symlink loop is allowed (`result is None`). It is renamed
  `test_symlink_loop_is_blocked_and_does_not_raise` and now asserts the path is
  blocked. This follows Grok F2; the kernel cannot open a loop (ELOOP), so no
  working edit is affected.

Against the guard at `e95187bb2`, 9 of the new test cases fail (the renamed loop
test, two for the two-level target, one for the link below a link, two for the
link beside the ancestor, the hop-limit chain, the unreadable link, and the
message test) and the two controls pass.

## Who made the edit

The supervisor session wrote the code directly, with no child dispatch and no
subagent, under the same one-off writer exception as Amendments 02-10. G01's
packet names `G01-implementer` as the only canonical writer of these two files;
the exception covers this one edit only and changes no `canonical_writers` in
the issued packets, which keep their hashes. This file is in no workstream
allowlist; it follows the Amendment 01-10 precedent.

## Local validation at the edit

Clean env (`env -i`, `HOME`, `PATH=/usr/bin:/bin`, `PYTHONPATH=<worktree>/src`),
repo `.venv` Python, on top of `e95187bb2`:

- PASS - `tests/unit/dcp_surface_guard/test_file_repo_root.py`: 59 passed.
- PASS, with one known failure - the 32 test files under `tests/` that mention
  `dcp_surface_guard`, `native_hooks` or `red_lane`: 1049 passed, 1 failed. The
  failure is
  `tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`,
  which fails the same way on `main` and on every earlier head of this branch
  (it flags `.github/workflows/` changes from main's history); this PR touches
  no workflow file.
- PASS - `flake8 --select=E9,F,W` on both files: 0 findings.
- PASS - the saved probes, outputs `*.after_a11.out` beside each:
  `agy_r3_f1_probe` (every shape blocked), `grok_r3_f2_probe` (every chain and the
  loop blocked), `agy_f1_f2_probe` and `copilot_a08_cap_probe` (unchanged).
  `copilot_a09_probe_a10` is unchanged, including its one known gap
  (`f1_real_path_blocked` false, see below).
- PASS - 14 ordinary paths on this machine, including `/tmp`, `/var/folders`,
  the repo, `~/.claude` and sibling projects, are not blocked and their walk does
  not abort.
- FAIL (same before and after) - `black --check` on both files; both already
  fail it at `e95187bb2`. Not reformatted, to keep the diff to the fix.
- NOT_RUN - full `make test`.
- NOT_RUN - CI on the new head, Copilot review of the new head, Grok audit, AGY
  corroboration. No audit has been run on any head that contains Amendment 11.

## Known limits (not fixed here)

- **Outside real path.** When a sibling checkout's red-lane folder is a symlink to
  a folder outside every repo, an edit addressed by that folder's own path is
  allowed. Nothing in that path names a red-lane location and the guard does not
  search other checkouts for links that point at it. `main` allows the same edit.
  Unchanged since Amendment 10; needs a design decision (for example a reverse
  lookup of red-lane links) and belongs in a follow-up.
- **`file_repo_root`.** The exported helper still returns the first `.git` above
  the realpath. The guard does not use it (Amendment 01). A Wave 2B caller that
  blocks from it alone would miss a root the guard keeps. Raised as risk R2 by
  Grok; not changed here.
- **Spelling limit.** 64 spellings (`_MAX_ALIAS_FORMS`) and 40 links
  (`_MAX_SYMLINK_HOPS`) are the guard's own limits. Past either, the edit is
  blocked, including ordinary files behind that many links.

## Effect on the freeze

The third freeze record (`e95187bb2`, content head `dc5aac697`) is superseded.
Both audits of it stand as FAIL and are not reused. Next: push, CI and a fresh
Copilot review on the new head; rewrite the freeze record for the head that is
actually frozen, correcting the 40-link sentence; build the audit prompt with the
commit-range proof in the trusted section; run the governing Grok audit, then the
AGY corroboration.
