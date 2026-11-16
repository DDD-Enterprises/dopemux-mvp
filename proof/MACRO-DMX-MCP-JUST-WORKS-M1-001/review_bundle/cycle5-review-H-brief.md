# Review brief — Task H (cycle 5): automatic reap reaches marker-only runtime dirs on an empty registry

Role: independent task reviewer, read-only (run tests/probes; change nothing). Fail closed.
Subject = the uncommitted `git diff` in /Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1 (saved as cycle5-review-H.diff).
Allowed files: src/dopemux/mcp/reap.py, tests/unit/test_mcp_reap.py, the design doc (one appended bullet), the how-to only if it
stated when automatic reaping skips. Task brief: cycle5-task-H-brief.md; implementer report: cycle5-task-H-report.md.
The finding (Codex connector P2 on 192a84dc3): `maybe_reap` returned early on an empty registry, so marker-only runtime dirs of
removed worktrees (build-only launches) never reached plan_reap's `_dir_only_candidates` on a fresh host.
Check: (1) the early return now falls through only when a launcher-marked runtime dir exists, with a cheap bounded directory check
that mirrors `_dir_only_candidates`' enumeration (same root, same marker, symlinks ignored) — can a huge runtime root make the hook
path slow? (2) nothing else in `maybe_reap` changed: throttle, kill switch, deadline and docker-timeout handling identical; (3) a marked
dir whose worktree still exists is never planned (dir-only = worktree_missing only) and a malformed marker is ignored by the planner;
(4) the new tests fail on the current HEAD (192a84dc3) and the existing maybe_reap tests stay green; (5) the design bullet is accurate
and append-only; (6) no change to locks, registry persistence or `_reap_one`.
Run and paste literally: `.venv/bin/python -m pytest tests/unit/test_mcp_reap.py tests/unit/test_mcp_launcher.py tests/unit/test_mcp_runtime_launcher.py -q`;
`/Users/hue/code/dopemux-mvp/.venv/bin/flake8 --select F,E7,E9,W6 src/dopemux/mcp/reap.py`; `git diff --stat`;
`.venv/bin/python scripts/docs_validator.py claudedocs/mcp-just-works-design-2026-11-05.md`.
Verdict: APPROVED or NEEDS_FIXES (path:line, severity, why, exact fix), then the one-line list of what an auditor might still raise.
