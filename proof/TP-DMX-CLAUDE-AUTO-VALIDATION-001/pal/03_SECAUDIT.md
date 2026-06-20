# 03 — Secaudit · TP-DMX-CLAUDE-AUTO-VALIDATION-001

**focus_on:** secrets, auth, MCP exposure

## Audit strategy

OWASP-aligned review of hook fail-closed paths, env file handling, MCP port binding, and proof/secret leakage.

## Findings

### Pass

1. **dcp_surface_guard** — PreToolUse hard-block via `surface_guard_block` → exit 2 + `permissionDecision: deny` (`native_hooks.py`).
2. **proof_tracking_guard** — Prevents silent proof drop; force-add policy aligned with TP-DMX-PROOF-TRACKING-POLICY-001.
3. **Per-worktree MCP ports** — `mcp_catalog.yaml` uses `${CONPORT_MCP_PORT}`, `${DOPE_MEMORY_PORT}`, `${TASK_ORCHESTRATOR_HTTP_PORT}` — isolation by worktree hash.
4. **task-orchestrator HTTP bind** — Singleton script binds `127.0.0.1:7890` only (not 0.0.0.0).
5. **mcp_health_probe** — SessionStart advisory; does not expose secrets in output (read doctor CLI only).

### Concerns

| ID | Severity | Finding | Recommendation |
|----|----------|---------|----------------|
| S1 | high | `.env` exists at repo root with live secrets | Child-template PreToolUse hook: block Edit/Write to `.env`, `.env.*`, `uv.lock` |
| S2 | medium | conport `DOPEMUX_AUTO_FORK_PROGRESS` hazard (design doc §0) | Document in child template; no automation bypass |
| S3 | low | Proposed auto-pytest hook could run tests with network fixtures | Scope to `pytest --disable-socket` matching adOps `pyproject.toml` |
| S4 | medium | GitHub MCP tools can push files | User-only skills with `disable-model-invocation: true` for deploy/push |

### Child-repo auth (adOps reference)

- `src/adops/api/auth.py` — security-reviewer subagent template should cite API key boundaries.
- Not in dopemux-mvp scope for implementation this phase.

## Conclusion

**PASS** for platform security posture. **CONDITIONAL** for child-repo secret-blocking hook (recommended MVP template item).