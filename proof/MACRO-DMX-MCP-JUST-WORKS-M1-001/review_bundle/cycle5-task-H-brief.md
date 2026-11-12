# Task H (cycle 5) — automatic reap must reach marker-only runtime dirs on an empty registry (Codex connector P2 on 192a84dc3)

Workspace: /Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1 (HEAD 192a84dc3). Shared workspace; preserve others' edits.
No git commit/add/stash/push. Files you may change: src/dopemux/mcp/reap.py · tests/unit/test_mcp_reap.py ·
claudedocs/mcp-just-works-design-2026-11-05.md (ONE appended bullet) · docs/02-how-to/mcp-setup-other-repos.md ONLY if its reap
section states when automatic reaping runs or skips (grep "reap"); otherwise leave it and say so.
Anything else → STOP and report. RED first. Do not reformat untouched lines. Added lines ≤ 88 chars.

## The finding (Codex connector, PR review of 192a84dc3, P2, reap.py:1307)
`maybe_reap()` (reap.py ~1247, the throttled automatic path used by the Stop/SessionEnd hooks and the launcher) returns early when
`registry.instances()` is empty (~1306). On a fresh host where launches only reached LAUNCH_IMAGE_BUILDING, no instance records exist
but the launches left launcher-marked runtime dirs (`instance.json`, build logs). If their worktrees are then removed, every automatic
reap returns before `plan_reap()` and its `_dir_only_candidates()` (~538) recovery path, so those dirs accumulate until an explicit
`dopemux mcp reap` or an unrelated successful start creates a registry entry.

## Fix
1. Replace the early return with: return early ONLY when the registry has no instances AND no launcher-marked runtime dir exists.
   Add a small helper (e.g. `_any_marked_runtime_dir(runtime_root) -> bool`) that enumerates the same runtime root and marker file
   (`INSTANCE_MARKER`) that `_dir_only_candidates` uses (read ~538-600 to reuse its enumeration and ignore rules: symlinked dirs are
   never candidates, malformed markers are ignored by the planner — the pre-check may be a cheap "is there any `<dir>/instance.json`"
   test; the planner keeps the authority on validity). Keep the docker-inspection and deadline/kill-switch logic unchanged.
2. Make sure the pre-check is cheap and bounded (one directory listing; no docker call before the existing inspection step).
3. Design bullet, appended at the end of "## Implementation amendments (2026-11-07)", one line: "**Automatic reap reaches
   marker-only runtime dirs on an empty registry (cycle 5, Codex connector review of `192a84dc3`).** `maybe_reap` returned before
   planning whenever the runtime registry had no instances, so build-only launches (`LAUNCH_IMAGE_BUILDING`) of since-removed worktrees
   left their `instance.json`-marked runtime dirs behind on a fresh host until an explicit `dopemux mcp reap` or an unrelated successful
   start created a registry entry; it now returns early only when there is also no launcher-marked runtime dir, and otherwise proceeds
   to `plan_reap`, whose dir-only candidates (`worktree_missing` only) handle them under the same bounds, kill switch and throttle."
4. How-to: only if a sentence describes when automatic reaping skips; adjust minimally or report "no change needed".

## Tests (tests/unit/test_mcp_reap.py; RED first against the current tree; reuse the maybe_reap fixtures — grep "maybe_reap" there)
  a. Empty registry + one marked runtime dir whose `worktree_root` no longer exists (+ a fake inspector returning an available docker
     snapshot with no containers): `maybe_reap(...)` now plans and finishes that dir-only candidate (assert via the report: reaped /
     finished entry naming the dir, or the dir removed per the dir-only semantics — read what plan_reap/_reap_one do for dir_only and
     assert accordingly); RED today: the report is empty and the inspector is never called.
  b. Control: empty registry + no marked dirs → returns an empty report and the inspector is NOT called (unchanged behaviour).
  c. Control: empty registry + a marked dir whose worktree still exists → nothing planned (dir-only candidates are `worktree_missing`
     only), inspector may be called.
  d. Existing maybe_reap tests (throttle, kill switch, deadline, docker timeout) unchanged and green.

## Validation you run and paste literally
  .venv/bin/python -m pytest tests/unit/test_mcp_reap.py tests/unit/test_mcp_launcher.py tests/unit/test_mcp_runtime_launcher.py -q
  /Users/hue/code/dopemux-mvp/.venv/bin/flake8 --select F,E7,E9,W6 src/dopemux/mcp/reap.py
  black/isort --check on the touched .py files (untouched-line hunks expected; report literally)
  .venv/bin/python scripts/docs_validator.py claudedocs/mcp-just-works-design-2026-11-05.md
  git -C /Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1 diff --stat ; no added line > 88
Report: RED output · the reap.py diff · GREEN · tool outputs · how-to decision · deviations/STOP · one-line list of what an auditor
might still raise (e.g. cost of the pre-check on hosts with many runtime dirs; a marked dir with a live worktree is still never touched).
