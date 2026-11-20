# MACRO-DMX-GUARD-FILE-REPO-001 - Amendment 11: one set of spellings per real folder; a walk that cannot finish blocks

## Operator words (verbatim, AskUserQuestion answer, 2026-11-20T03:01:12.205Z)

Question put after both audits of frozen head `e95187bb2` returned FAIL:

> Both audits of frozen head e95187bb2 (content head dc5aac697) returned FAIL, the third failed freeze. AGY: two more symlink shapes get a red-lane edit through (a two-level link target followed by '..', and a link beside a symlinked red-lane folder); I reproduced both. Grok: the guard allows the edit when its spelling walk aborts (loops, readlink errors); in practice the kernel refuses chains over 32 links, so I could not reach that with a path that opens, but the principle is right. Both: the audit prompt lacked the commit-range proof Amendment 02 required, which I missed in the last two rounds. The 40-hop sentence in the freeze record is wrong. How should PR 1513 proceed?

Answer: **"Amendment 11, one more round (Recommended)"**. The option read: "Same one-off writer exception as 02-10. Keep one set of spellings per real folder and use it at every step, not just after '..' (the root cause AGY found); block when the walk aborts; fix the 40-hop sentence; put the commit-range proof in the next audit prompt; re-freeze, then Grok and AGY. If that round FAILs on another symlink shape, I stop and bring you the descope choice instead of an Amendment 12."

Recorded by the team lead (supervisor session `c311455f-f4c3-4513-b995-82ff91a5ca87`). **Stop rule:** if the audits of the next frozen head FAIL on another symlink shape, there is no Amendment 12; the supervisor brings the operator the descope choice.

## Why

Verdicts: `~/.local/share/dopemux/evidence/pr1513/r3/` (`GROK_VERDICT.json`, `AGY_VERDICT.json`); probes in `r3/repro/`.

1. **AGY F1 (high), reproduced.** The plain spelling of a red-lane file was blocked and another spelling of the same file was allowed, in two shapes: a link inside a symlinked red-lane folder pointing two levels deep, then `..`; and a link beside a symlinked red-lane ancestor (relative or absolute target). Cause: Amendment 08 merged the spellings already known for a folder only after `..`, while the nested walk of a link target starts from the folder's real name alone.
2. **Grok F2 (high), principle accepted.** When the walk aborts (loop, chain past 40 links, unreadable link, `ValueError`, `RecursionError`) it returned no spellings and let the path through. On this machine the kernel refuses 33 links (errno 62), so no path that opens reached it, but the guard was inconsistent with its own 64-spelling rule.
3. **Grok F1, AGY R2 (process miss).** The prompts of the second and third freezes lacked the commit-range proof Amendment 02 step 4 required in the trusted section. The new builder (`r4/build_audit_input.py`) adds it.
4. **AGY F2 (low), my error.** The third freeze record said chains over 40 links were blocked. They were not. Now they are.
5. **AGY F3 (medium), accurate.** Amendments 02-11 were written by this session under one-off operator exceptions outside the packet's named writer; each records the operator's words.

## What changed

`.claude/hooks/dcp_surface_guard.py`: `_walk_alias_forms` merges the spellings known for the current real folder at every step. `_alias_limit_exceeded` returns true on any abort (more than 64 spellings, loop or chain past `_MAX_SYMLINK_HOPS`, unreadable link, `ValueError`, `RecursionError`); the block message names these causes and still advises no other path. Nothing blocked or warned before is now allowed; the 64-spelling threshold did not move (five stacked links give 33 spellings, six trip the limit).

`tests/unit/dcp_surface_guard/test_file_repo_root.py`: new tests for the two-level target (absolute, relative), the link below a link to the red lane, the link beside the ancestor (absolute, relative), the chain past the hop limit, the unreadable link and the message; controls `test_chain_just_under_the_hop_limit_is_allowed` and `test_ordinary_symlinked_path_is_still_allowed`. **One existing expectation changed:** `test_symlink_loop_does_not_raise` asserted a loop is allowed; it is now `test_symlink_loop_is_blocked_and_does_not_raise` and asserts it is blocked (the kernel cannot open a loop). Against the guard at `e95187bb2`, 9 new cases fail and the 2 controls pass.

Writer: the supervisor session, no child, no subagent, same one-off exception as 02-10; changes no `canonical_writers` in the issued packets.

## Validation at the edit (clean env, repo `.venv`, on `e95187bb2`)

- PASS: guard tests, 59 passed. 32 related test files: 1049 passed, 1 failed (`test_16_no_forbidden_files_modified`, which fails the same way on `main`). `flake8 --select=E9,F,W`: 0 findings.
- PASS: saved probes (`*.after_a11.out`) block every red-lane shape; 14 ordinary paths on this machine (`/tmp`, `/var/folders`, repo, `~/.claude`, sibling projects) are not blocked.
- FAIL, unchanged: `black --check`. NOT_RUN: full `make test`, CI, Copilot, Grok, AGY on the new head.

## Known limits (not fixed here)

- A sibling red-lane folder that is a symlink to a folder outside every repo can still be edited by that folder's own path; `main` allows it too. Needs a design decision.
- `file_repo_root` still returns the first `.git` above the realpath; the guard does not use it.
- Past 64 spellings or 40 links the edit is blocked, ordinary files included.

## Effect on the freeze

The third freeze (`e95187bb2`) is superseded; its two FAIL verdicts stand. The fourth freeze record names content head `72aa9c902`.

**Condensed after `72aa9c902`.** This record was shortened in a proof-only commit so the sealed audit prompt fits AGY's message limit (about 192 KB). The operator's words above are unchanged. The longer text is in git at `72aa9c902`.
