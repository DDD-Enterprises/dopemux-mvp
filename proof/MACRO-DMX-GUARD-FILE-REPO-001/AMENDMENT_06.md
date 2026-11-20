# MACRO-DMX-GUARD-FILE-REPO-001 — Amendment 06: root discovery reads the filesystem-resolved `..` spelling

## Operator words (verbatim, AskUserQuestion answer)

Question put after Copilot's review of `9795635cabbf5ee68906fb8adf0860f8dc25180a`:
"How should PR 1513 proceed?"

Answer: **"Fix here (Recommended)"** — the option that read "Amendment 06, same
one-off writer exception. Root discovery gets the same filesystem-resolved `..`
reading that Amendment 05 gave the path matcher (one shared helper), plus a test.
Then CI, another Copilot round, freeze, Grok and AGY."

The exact answer timestamp is in the session transcript
(`c311455f-f4c3-4513-b995-82ff91a5ca87`); it is not restated here.

## Why

Copilot's review of `9795635ca` listed no open issues and marked the Amendment 05
finding resolved, but its summary asked for one more look at root discovery. The
supervisor reproduced a gap with a standalone probe before any edit:

`<x>/link/../<sibling>/services/task-orchestrator/x.py` was allowed when all three
held: `link` is a symlink (so `..` is the parent of its target, not of `link`),
the target is a sibling checkout, and that checkout's red-lane directory is a
symlink to somewhere outside it.

`_guard_starts` walked up from two forms only. The lexical form collapses `link/..`
to `<x>`, which is not where the file is. The resolved form follows the inner
symlink out of the sibling. Neither start found the sibling's `.git`, so the
sibling was never read as a root.

Not a regression: `origin/main` allows this path and also the plain spelling. The
same path with a real (non-symlink) red-lane directory was already blocked.

## What changed

- `.claude/hooks/dcp_surface_guard.py`
  - New `_hop_resolved(path)`: the part up to the last `..` resolved through the
    filesystem, the rest kept as typed. Returns None without a `..`. Never raises.
  - `_repo_relative_candidates` uses it in place of the inline Amendment 05 block.
    Behaviour unchanged.
  - `_guard_starts` adds that form as a third start per base. Starts are only ever
    added.
- `tests/unit/dcp_surface_guard/test_file_repo_root.py`
  - `test_dotdot_after_symlink_reaches_sibling_symlinked_red_lane_is_blocked`
  - `test_dotdot_after_symlink_reaches_sibling_contract_surface_is_warned`
  - Both failed before the change (2 failed) and pass after it.

## Who made the edit

Written directly in the supervisor session, with no child dispatch and no subagent
counters, under the same one-off writer exception as Amendments 02–05. G01's packet
names `G01-implementer` as the only canonical writer of these two files; the
exception covers this one edit only and changes no `canonical_writers` in the
issued packets, which keep their hashes. This file is in no workstream allowlist;
it follows the Amendment 01–05 precedent.

## Local validation at the edit

- Guard, DCP red-lane, native-hooks, orchestrator-hook and W09 suites
  (clean env, repo `.venv`): **PASS**, 418 passed.
- `flake8 --select=E9,F` on both files: **PASS**, 0 findings.
- Reproduction probe: the three-condition path is now blocked; the plain spelling
  and the real-directory variant stay blocked.
- Full `make test`: **NOT_RUN**.

## Next

Push, then CI and a fresh Copilot review on the new head. Rewrite the freeze
record (`G02_RETURN.md`) for the head that is actually frozen, then run the
governing Grok audit and the AGY corroboration on that head. No audit has been run
on any head that contains Amendments 02–06.
