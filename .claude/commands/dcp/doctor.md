---
description: "DCP read-only facade preflight: registry contract, backend probes, ConPort auto-fork hazard, facade test suite"
arguments: "[--live] [--project <id>]"
allowed-tools: ["Bash", "Read", "Grep", "Glob"]
model: "claude-sonnet-4-5"
---

# /dcp:doctor — DCP Facade Preflight

Four-phase preflight for the DCP read-only facade. Automates the manual checks
documented in `docs/03-reference/dcp/chatgpt-mcp-readonly/FACADE_LOCAL_RUN.md`
that every facade/tunnel session repeats.

Use before starting a ChatGPT tunnel session, or to diagnose unexpected tool failures.

---

## Phase 1 — Registry Validation

**1a — Locate registry.** Check `$DCP_FACADE_REGISTRY` first, then
`~/.dopemux/dcp-facade-registry.yaml`. If missing:
```
❌ Registry not found.
Fix: cp services/dcp-readonly-facade/registry.example.yaml ~/.dopemux/dcp-facade-registry.yaml
     then fill in your workspace_path and project details.
```
The facade fail-closes without a valid registry (expected, not a bug).

**1b — Validate contract fields.** Read the registry. Check per-project against
`docs/03-reference/dcp/chatgpt-mcp-readonly/MULTI_PROJECT_REGISTRY_CONTRACT.md`:
- `workspace_path`: present, absolute, and the directory exists on disk
- `enabled`: boolean present
- `service_profiles.*.base_url`: present for each profile
- `identity.project`: present

**1c — Loopback enforcement** (security invariant):
Every `base_url` host must be `127.0.0.1` or `localhost`. Any other host → ❌ FAIL:
```
Security model violation: base_url host must be loopback-only.
```
No exceptions — the DCP facade is a read-only local projection; external hosts break
the security model.

**IMPORTANT: Never print the registry file wholesale.** It is user-private and outside
the repo. Quote only field names and failing values (hosts/ports), never token values
or secrets. The registry should hold no secrets, but fail safe.

---

## Phase 2 — ConPort Auto-Fork Hazard Check

This is the single misconfiguration that silently turns the read-only facade into a writer.

For each project where `service_profiles.conport.progress_readonly_safe: true`:

1. Find the ConPort container:
   ```bash
   docker ps --format '{{.Names}}' | grep -i conport
   ```

2. Inspect its `DOPEMUX_AUTO_FORK_PROGRESS` env var:
   ```bash
   docker inspect <name> --format '{{range .Config.Env}}{{println .}}{{end}}' \
     | grep DOPEMUX_AUTO_FORK_PROGRESS
   ```

3. Anything other than an explicit `DOPEMUX_AUTO_FORK_PROGRESS=0` → ❌ **LOUD FAIL**:
   ```
   ❌ HAZARD: Registry declares progress_readonly_safe=true for project <id>
      but ConPort container has DOPEMUX_AUTO_FORK_PROGRESS=1 (or unset, defaults to 1).
      GET /api/progress will auto-fork (WRITE) on every read.
      Fix: set DOPEMUX_AUTO_FORK_PROGRESS=0 in the ConPort container environment,
           OR set progress_readonly_safe: false in the registry.
   ```

If `progress_readonly_safe` is false or absent → ✅ PASS with note:
"search_progress will report BLOCKED — by design for Phase-1 safety."

---

## Phase 3 — Backend Probes

For each configured service profile, bounded curl (--max-time 2) to the base_url:
```bash
curl -s -o /dev/null -w '%{http_code}' --max-time 2 <base_url>
```

Apply the **expected-limitations table** — do not misreport known Phase-1 states as faults:

| Service | Expected Phase-1 state | Report as |
|---------|------------------------|-----------|
| dope-context | BLOCKED — MCP JSON-RPC vs REST transport gap; Phase-2 bridge pending | ✅ (expected-blocked) |
| conport `search_decisions` | PARTIAL — backend 500s on UUID serialization | ⚠️ known-degraded |
| conport `search_progress` | BLOCKED unless auto-fork hazard check passed | depends on Phase 2 |
| task-orchestrator | needs `task_orchestrator_project_id` set explicitly | ⚠️ WARN if unset |

---

## Phase 4 — Test Suite

**Always** (static tests):
```bash
python -m pytest -q services/dcp-readonly-facade/tests \
  --ignore=services/dcp-readonly-facade/tests/test_live_optional.py
```
Report pass/fail counts.

**`--live` only** (hits real local backends — never default):
```bash
DCP_FACADE_LIVE_TESTS=1 DCP_FACADE_REGISTRY=<path> \
  python -m pytest -q services/dcp-readonly-facade/tests/test_live_optional.py
```

---

## Phase 5 — Report

PASS/FAIL/WARN/NOT_RUN table + the registry path used + max 3 fixes.

End with **tunnel-readiness verdict**:
- `✅ READY` — all phases PASS or expected (dope-context blocked, etc.)
- `⚠️ READY WITH WARNINGS` — non-blocking issues (known-degraded services)
- `❌ NOT READY` — any FAIL in Phases 1 or 2

---

## Error Handling

- Registry file is invalid YAML → FAIL with parse error, proceed to Phase 4
- `docker` unavailable → skip Phase 2 container checks with NOT_RUN note
- `pytest` unavailable → NOT_RUN for Phase 4

---

## Notes for Claude

- **Never print registry contents beyond failing field names/values** — it's user-private.
- The dope-context BLOCKED state is intentional (Phase-1 architectural decision, not a bug).
  Report it as expected-blocked, not as a failure.
- This command is read-only — it never modifies the registry, containers, or tests.
- Model: `claude-sonnet-4-5` per routing policy.
