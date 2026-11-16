# Task F (cycle 4) — doctor port findings are re-evaluated after port allocation (Codex connector P2 on 83b468e71)

Workspace: /Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1 (HEAD 83b468e71). Shared workspace; preserve others' edits.
No git commit/add/stash/push. Files you may change: src/dopemux/mcp/lifecycle.py ·
tests/unit/test_mcp_lifecycle_ports_from_leases.py (or tests/unit/test_mcp_lifecycle.py if its fixtures fit better) ·
claudedocs/mcp-just-works-design-2026-11-05.md (ONE appended bullet in "## Implementation amendments (2026-11-07)").
Anything else → STOP and report. RED first. Do not reformat untouched lines. Added lines ≤ 88 chars.
Interpreter .venv/bin/python; tools /Users/hue/code/dopemux-mvp/.venv/bin/{black,isort,flake8}.

## The finding (Codex connector, PR #1503 review of 83b468e71, P2, lifecycle.py:1409)
After `init` then `stop` (or reap), the port leases are released but `.envrc.dopemux-mcp` keeps the old port. If another
project's container now holds that port, the doctor preflight (`run_mcp_doctor(..., process_env=doctor_env)`, ~line 1304)
reports DOCKER_CONTAINER_WRONG_PROJECT for the STALE envrc port, and `_doctor_blocking_findings(...)` (~line 1407-1412)
copies it into `blocking`, the immutable prefix that `_mutable_facts()` carries. `_resolve_ports(allocate=True)` then
leases a different free port and `_collision_checks(ports=<resolved>)` (~1105-1115) finds nothing — but the stale doctor
finding still blocks the start (Codex reproduced: BLOCKED with replacement port 3020 because a foreign container held the
old envrc port 3040). CLI starts and launcher cold starts cannot recover although rebinding succeeded.

## Fix (Codex's second option: replace carried port findings with the fresh post-allocation checks)
1. Module constant next to BLOCKING_FINDING_CODES:
   `PORT_DEPENDENT_DOCTOR_CODES = frozenset({"PORT_RESERVED_COLLISION", "PORT_INTRA_CONFIG_COLLISION",
   "PORT_OWNED_BY_OTHER_PROJECT", "DOCKER_CONTAINER_WRONG_PROJECT", "DOCKER_CONTAINER_UNLABELED_UNKNOWN",
   "DOCKER_CONTAINER_PORT_COLLISION"})` with a comment: these doctor findings are computed against the envrc ports before
   allocation; for start/restart the lifecycle recomputes them against the RESOLVED ports (`_collision_checks`, and
   `_resolve_ports` raises PortAllocationBlocked when no free port exists), so they are not carried as blockers.
2. In the preflight where `blocking.extend(_doctor_blocking_findings(...))` runs (~1407): when `op in {"start", "restart"}`,
   split the result — findings whose code is NOT in the set → `blocking` (unchanged); findings whose code IS in the set →
   one INFO entry each appended to `warnings`: `{"code": "DOCTOR_PORT_FINDING_REEVALUATED", "severity": "INFO",
   "service": f.get("service"), "message": f"doctor {code} (computed against the envrc port before allocation) is
   re-evaluated against the resolved ports: {original message}"}`. For every other op the behaviour is unchanged.
   Keep the existing `for f in doctor.findings: if WARN → warnings` loop as is.
3. Do NOT change `_collision_checks`, `_resolve_ports`, `_mutable_facts` or the lock structure. Confirm by reading that
   `_collision_checks` runs against the resolved ports for start/restart and is extended into `blocking` there (1105-1115)
   and that the re-check under the instance lock (`_mutable_facts(...)` second call) receives the same carried `blocking`.
4. Design amendment (append ONE bullet at the end of "## Implementation amendments (2026-11-07)", same style):
   "**Doctor port findings are re-evaluated after allocation (cycle 4, Codex connector review of `83b468e71`).** The doctor
   preflight inspects the envrc ports before `_resolve_ports` may lease replacements, so for `start`/`restart` its
   port-dependent findings (`PORT_RESERVED_COLLISION`, `PORT_INTRA_CONFIG_COLLISION`, `PORT_OWNED_BY_OTHER_PROJECT`,
   `DOCKER_CONTAINER_WRONG_PROJECT`, `DOCKER_CONTAINER_UNLABELED_UNKNOWN`, `DOCKER_CONTAINER_PORT_COLLISION`) are no
   longer carried as blockers; they are recorded as `DOCTOR_PORT_FINDING_REEVALUATED` INFO entries and the lifecycle's own
   collision checks against the resolved ports (plus `PORT_ALLOCATION_BLOCKED` when no free port exists) decide. After
   `init` → `stop` a foreign container on the stale envrc port no longer blocks a start that re-leased a free port.
   `stop`/`status` keep the doctor findings as before."

## Tests (RED first; keep the failing output). Use the fixture style of
## tests/unit/test_mcp_lifecycle_ports_from_leases.py::test_a_start_after_init_and_stop_re_leases_the_envrc_ports (~524)
1. `test_start_after_init_and_stop_is_not_blocked_by_a_foreign_container_on_the_stale_envrc_port`: envrc holds the old
   conport port (e.g. 3040), no active lease for it; the docker snapshot contains a managed container with labels
   dopemux.managed=true, dopemux.project_id=<another project>, dopemux.service=conport publishing 3040 (and the real
   doctor must see it — if the doctor reads docker through the same `docker_runner`, feed it there; otherwise explain how
   the finding is produced in the test). `run_lifecycle("start", dry_run=True, ...)` → status not BLOCKED, resolved conport
   port != 3040, `blocking` has no DOCKER_CONTAINER_WRONG_PROJECT, `warnings` has one DOCTOR_PORT_FINDING_REEVALUATED
   naming conport. Must FAIL on the current code (BLOCKED).
2. A port-independent doctor blocker is still carried for start (e.g. the existing TRANSPORT_MISMATCH or MCP_JSON
   parse path — reuse an existing test's fixture): unchanged behaviour, passes before and after (control).
3. `op="stop"` with the same foreign-container setup still carries DOCKER_CONTAINER_WRONG_PROJECT as before (control
   for "other ops unchanged") — only if a stop fixture is cheap; otherwise state why not.
4. Existing tests in both lifecycle test files and tests/unit/test_mcp_launcher.py pass unchanged.

## Validation you run and paste literally
  .venv/bin/python -m pytest tests/unit/test_mcp_lifecycle.py tests/unit/test_mcp_lifecycle_ports_from_leases.py tests/unit/test_mcp_launcher.py tests/unit/test_mcp_doctor_repo_aware.py -q
  /Users/hue/code/dopemux-mvp/.venv/bin/black --check src/dopemux/mcp/lifecycle.py <test file>   (untouched-line hunks expected)
  /Users/hue/code/dopemux-mvp/.venv/bin/isort --check-only <same files>
  /Users/hue/code/dopemux-mvp/.venv/bin/flake8 --select F,E7,E9,W6 src/dopemux/mcp/lifecycle.py
  .venv/bin/python scripts/docs_validator.py claudedocs/mcp-just-works-design-2026-11-05.md
  git -C /Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1 diff --stat
Report: RED output · the lifecycle.py diff · GREEN · tool outputs · deviations/STOP · one-line list of what an auditor
might still raise (e.g. a port-dependent doctor code that the lifecycle's own checks do NOT recompute).
