# Task G (cycle 5) — narrow the Task F drop to one checkable invariant (Codex audit F1/F2 at fc591cba1)

Workspace: /Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1 (HEAD fc591cba1). Shared workspace; preserve others'
edits. No git commit/add/stash/push. Files you may change: src/dopemux/mcp/lifecycle.py ·
tests/unit/test_mcp_lifecycle_ports_from_leases.py · tests/unit/test_mcp_lifecycle.py (only if an existing test asserts
behaviour this change restores — report which) · claudedocs/mcp-just-works-design-2026-11-05.md (ONE appended bullet).
Anything else → STOP and report. RED first. Do not reformat untouched lines. Added lines ≤ 88 chars.
Interpreter .venv/bin/python; tools /Users/hue/code/dopemux-mvp/.venv/bin/{black,isort,flake8}.

## Why (independent audit at fc591cba1, two mediums, both regressions of Task F vs HEAD/main)
Task F dropped six port-dependent doctor codes from the start/restart blockers. Two guards went with them:
F1 lifecycle.py:~1469 — `_resolve_ports` can RETAIN existing leases without allocating (~437-469), `_collision_checks` checks
   docker ownership only, and the reserved-port check at ~1059 is INFO; so two services' leases retained on one port, or a
   lease retained on reserved :7890, now start with zero blockers (the doctor's PORT_INTRA_CONFIG_COLLISION /
   PORT_RESERVED_COLLISION blocked that before).
F2 lifecycle.py:~702 — rule (2) needs a truthy owner hash; a managed same-project container with a contradictory workspace
   label and NO `dopemux.worktree_hash` on a retained port passes (classification WRONG_PROJECT; the launcher refuses it at
   launcher.py:~630); the doctor's DOCKER_CONTAINER_WRONG_PROJECT blocked that before.

## The invariant to implement (one sentence an auditor can check)
For start/restart, every doctor blocker is carried except a DOCKER_CONTAINER_* finding whose container publishes no port
in the RESOLVED port map; and the resolved port map itself is validated for duplicate and reserved ports.

## Changes
1. Preflight (~1462-1483): replace the PORT_DEPENDENT_DOCTOR_CODES split. For `op in {"start","restart"}`: every doctor
   blocker whose code does NOT start with "DOCKER_CONTAINER_" → `blocking` as on main (this restores PORT_RESERVED_COLLISION,
   PORT_INTRA_CONFIG_COLLISION, PORT_OWNED_BY_OTHER_PROJECT); DOCKER_CONTAINER_* findings → a list `deferred_doctor`
   (NOT yet INFO). Other ops: unchanged (everything → blocking). Remove the now-unused PORT_DEPENDENT_DOCTOR_CODES constant
   (or shrink it to the three DOCKER_CONTAINER_* codes and rename, e.g. DEFERRED_DOCTOR_CONTAINER_CODES).
2. `_mutable_facts` gains a keyword `deferred_doctor: Sequence[Dict[str, Any]] = ()` (pass it through `facts_kw` so all
   three call sites — preflight ~1554, stop re-check ~1662, start/restart re-check ~1717 — behave identically). After
   `ports` and `docker` are known and after `_collision_checks` (~1166): for `op in {"start","restart"}`:
   `kept, dropped = _split_deferred_doctor(deferred_doctor, docker, ports)`; `blocking.extend(kept)`; for each dropped
   finding append the INFO `DOCTOR_PORT_FINDING_REEVALUATED` entry (same message format as today). Helper:
     def _split_deferred_doctor(findings, docker, ports): a finding is KEPT when docker is unavailable (fail closed) or when
     its container — evidence[0] is the container name in all three doctor producers (doctor.py ~1035/1077/1110) — matches a
     snapshot container (`c.name == name or c.name.endswith(name)`, the tolerance used elsewhere in lifecycle.py) whose
     `published_ports` intersects the resolved port values; otherwise DROPPED. Dedupe against findings already in blocking
     (same code+service+message; the existing dedupe at the end of `_mutable_facts` also covers it).
3. Resolved-map validation, same place, for start/restart: (a) two SELECTED services whose resolved ports are equal →
   {"code": "PORT_INTRA_CONFIG_COLLISION", "severity": "FAIL", "service": <second service>, "message": "resolved ports collide:
   <var1>=<port> and <var2>=<port>"}; (b) a selected service other than task-orchestrator whose resolved port is in
   `singleton_reserved_ports(catalog)` (plus 7890) → {"code": "PORT_RESERVED_COLLISION", "severity": "FAIL", "service": <svc>,
   "message": "resolved port :<port> (<var>) is a reserved singleton port"}. Keep the existing INFO
   ALLOCATOR_RESERVED_SINGLETON_PORT entry as it is. Do NOT change `_resolve_ports` or the locks.
4. Keep the rounds-2/3 ownership rules in `_collision_checks` (defense in depth); no changes there.
5. Design doc: append ONE bullet at the end of "## Implementation amendments (2026-11-07)": "**Cycle 5 narrows the Task F
   re-evaluation to one invariant (Codex audit at `fc591cba1`).** For `start`/`restart` every doctor blocker is carried except
   a `DOCKER_CONTAINER_*` finding whose container publishes no port in the resolved port map (that one becomes a
   `DOCTOR_PORT_FINDING_REEVALUATED` INFO entry), and the resolved port map is validated: two selected services on one port
   or a sidecar on a reserved singleton port block as `PORT_INTRA_CONFIG_COLLISION` / `PORT_RESERVED_COLLISION` even when
   `_resolve_ports` retained existing leases. The `PORT_*` doctor codes are no longer dropped. Consequently the two
   behaviour changes recorded in the previous bullet — a managed container with only compose labels holding our expected
   name, and a project-scoped task-orchestrator container started from another worktree of the same project — block again
   exactly as on main; the stale-envrc-port recovery (the connector finding) is kept." Keep it one line.

## Tests (RED first; keep the failing output). Fixtures as in tests/unit/test_mcp_lifecycle_ports_from_leases.py.
  a. Codex F1-a: leases for conport and dope-memory both ACTIVE on the same port (write the lease registry so both services
     hold 3005 for this worktree; envrc may carry the same values) → start dry-run BLOCKED with PORT_INTRA_CONFIG_COLLISION
     (RED today: PLANNED).
  b. Codex F1-b: an active conport lease retained on 7890 (envrc CONPORT_MCP_PORT=7890) → BLOCKED with PORT_RESERVED_COLLISION
     (RED today).
  c. Codex F2: managed conport container with our project_id, NO worktree hash, NO scope, and a different
     `dopemux.workspace_id` / `dopemux.project_root`, publishing the port our active lease keeps → BLOCKED (the doctor's
     DOCKER_CONTAINER_WRONG_PROJECT is kept because the container is on a resolved port) (RED today: PLANNED).
  d. The P2 scenario stays fixed: stale envrc port held by a foreign container, probe busy, port moves → not BLOCKED and the
     INFO DOCTOR_PORT_FINDING_REEVALUATED entry is present on a blocked variant (existing tests; must stay green).
  e. Docker unavailable with a deferred finding → the finding is KEPT (fail closed): a small direct test of
     `_split_deferred_doctor` with `docker.available = False`.
  f. Existing tests: if `test_start_re_leases_around_an_unlabeled_container_on_the_configured_port` or any Task F test
     changes outcome, explain why (expected: the unlabeled container on the STALE 3041 is dropped → still PLANNED).
Run before the fix: a, b, c, e must fail; d must pass.

## Validation you run and paste literally
  .venv/bin/python -m pytest tests/unit/test_mcp_lifecycle.py tests/unit/test_mcp_lifecycle_ports_from_leases.py tests/unit/test_mcp_launcher.py tests/unit/test_mcp_doctor_repo_aware.py tests/unit/test_mcp_config_repair.py -q
  /Users/hue/code/dopemux-mvp/.venv/bin/flake8 --select F,E7,E9,W6 src/dopemux/mcp/lifecycle.py   (4 pre-existing F841 expected)
  black/isort --check on the touched files (untouched-line hunks expected; report literally)
  .venv/bin/python scripts/docs_validator.py claudedocs/mcp-just-works-design-2026-11-05.md
  git -C /Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1 diff --stat ; no added line > 88
Report: RED output · the lifecycle.py diff (preflight split, `_mutable_facts` additions, helper) · GREEN · tool outputs ·
deviations/STOP · one-line list of what an auditor might still raise.
