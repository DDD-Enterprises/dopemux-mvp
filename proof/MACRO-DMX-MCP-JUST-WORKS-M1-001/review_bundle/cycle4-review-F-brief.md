# Review brief — Task F (cycle 4): doctor port findings re-evaluated after allocation

Role: independent task reviewer, read-only (run tests/probes; change nothing). Fail closed.
Worktree /Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1; subject = the uncommitted `git diff` (saved as
cycle4-review-F.diff). Allowed files: src/dopemux/mcp/lifecycle.py, tests/unit/test_mcp_lifecycle_ports_from_leases.py (new tests),
tests/unit/test_mcp_lifecycle.py (controller ruling: ONLY `test_start_blocks_unlabeled_port_owner` replaced by a
no-free-port BLOCKED variant and a re-lease PLANNED variant — it asserted BLOCKED solely from the stale doctor finding),
the design doc (one appended bullet). Any other path is a finding. Task brief: cycle4-task-F-brief.md; implementer report: cycle4-task-F-report.md.

The finding (Codex connector P2 on 83b468e71): the doctor preflight runs against the envrc ports before `_resolve_ports`
may lease replacements; its DOCKER_CONTAINER_WRONG_PROJECT for a stale envrc port held by another project's container was
copied into the immutable `blocking` prefix and survived a successful re-lease, blocking CLI and launcher cold starts.
Required fix: for start/restart only, the six port-dependent doctor codes are not carried as blockers but recorded as INFO
DOCTOR_PORT_FINDING_REEVALUATED; `_collision_checks` against the resolved ports (+ PORT_ALLOCATION_BLOCKED) decide; other
ops unchanged; `_collision_checks`, `_resolve_ports`, `_mutable_facts` and the locks untouched; one design bullet.

Check adversarially — the central question: is there ANY case one of the six dropped doctor codes would have blocked that
the lifecycle's post-allocation checks do NOT recompute? Read `_collision_checks` (~555-720: by expected container name,
then by resolved-port owner), `_resolve_ports` (~372; when does it keep an envrc port, when does it allocate, when does it
raise PortAllocationBlocked), the reserved-singleton handling in `_mutable_facts`, and the doctor module's producers of
those six codes (src/dopemux/mcp/doctor*.py or wherever run_mcp_doctor lives). Cases to try: a foreign container on the
RESOLVED port (must still block); the same-project wrong-service container on our port; an unlabeled container on the
resolved port; envrc port equal to the reserved :7890; two services configured on the same envrc port; the stale-port
scenario itself (must not block); the launcher's cold start path (ensure_backend → run_lifecycle start) sees the same
behaviour; the re-check under the instance lock (second `_mutable_facts` call) is consistent with the preflight.
Also: the INFO entries are visible only on blocked results and in the preflight facts — a successful start's output
lists no preflight warnings (`_start_services` returns warnings=[], pre-existing; the bullet must say so). Is that
acceptable, and does the bullet state it truthfully? Does `stop`
still carry them? Do the new tests fail on the old code (not tautological)? Is the design bullet accurate and append-only?
Run and paste literally: `.venv/bin/python -m pytest tests/unit/test_mcp_lifecycle.py tests/unit/test_mcp_lifecycle_ports_from_leases.py tests/unit/test_mcp_launcher.py tests/unit/test_mcp_doctor_repo_aware.py -q`;
`/Users/hue/code/dopemux-mvp/.venv/bin/flake8 --select F,E7,E9,W6 src/dopemux/mcp/lifecycle.py`; `git diff --stat`.
Verdict: APPROVED or NEEDS_FIXES (path:line, severity, why, exact fix), then the one-line list of what an auditor might
still raise about this change.
