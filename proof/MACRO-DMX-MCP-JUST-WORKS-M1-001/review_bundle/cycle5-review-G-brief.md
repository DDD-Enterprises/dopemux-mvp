# Review brief — Task G (cycle 5): one invariant for the doctor re-evaluation + resolved-map validation
(Note: this file was written after the round-0 review; that review worked from the controller's message and the task brief — see the ledger.)

Role: independent task reviewer, read-only (run tests/probes; change nothing). Fail closed.
Subject = the uncommitted `git diff` in /Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1 (saved as cycle5-review-G.diff).
Allowed files: src/dopemux/mcp/lifecycle.py, tests/unit/test_mcp_lifecycle_ports_from_leases.py, tests/unit/test_mcp_lifecycle.py
(only if an existing test asserted behaviour this restores), the design doc (one appended bullet).
Acceptance rule: every start/restart case main blocked must block again, except the stale-port recovery (container on a port no
longer in the resolved map); Codex F1 (retained leases on duplicate/reserved ports) and F2 (same-project container with a contradictory
workspace label and no hash on a retained port) must block; the preflight and both under-lock re-checks must resolve the deferred
findings identically; docker unavailable keeps them; no change to `_resolve_ports` or the locks; new tests fail on fc591cba1.
Commands: the four-file pytest line, flake8 F/E7/E9/W6 on lifecycle.py (4 pre-existing F841), `git diff --stat`, docs validator.
Verdict: APPROVED or NEEDS_FIXES (path:line, severity, why, exact fix), then what an auditor might still raise.
