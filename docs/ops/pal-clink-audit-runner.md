---
id: pal-clink-audit-runner
title: Pal Clink Audit Runner
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-27'
last_review: '2026-05-27'
next_review: '2026-08-25'
prelude: Pal Clink Audit Runner (explanation) for dopemux documentation and developer
  workflows.
---
# PAL Clink Audit Runner

**Module**: `scripts/audit/pal_clink_runner.py`
**Schema**: `schemas/audit/pal_clink_audit_output.schema.json`
**Tests**: `tests/audit/test_pal_clink_runner.py`

## Overview

The PAL clink audit runner executes an audit by invoking the selected clink CLI (`claude-audit` or `gemini-audit`) as a subprocess.  It reuses the existing PAL clink configs from `docker/mcp-servers-source/pal/pal-mcp-server/conf/cli_clients/` — it does **not** create or modify configs.

The audit prompt is delivered via **stdin** so that both claude and gemini CLIs receive it through the same channel regardless of their individual argument parsers.

## Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Prompt delivery | stdin | Both `claude` and `gemini` CLIs accept prompts via stdin; uniform across auditors |
| Timeout handling | Return output with `timed_out=True` | Caller decides how to log and retry; no exception propagation |
| `exit_code` type | `int \| None` | None on pre-flight failure and timeout; required by `pal_clink_audit_output.schema.json` |
| Env merge | `{**os.environ, **route.env}` | Route env overrides system env; allows per-auditor env injection |
| Codex guard | Defense-in-depth in `run_audit()` | `AuditRoute.__post_init__` already rejects codex, but guard again against serialization bypass |
| Subprocess runner | Injectable `subprocess_run` param | Tests inject a fake; production uses `subprocess.run` |

## Usage

```python
from scripts.audit.auditor_router import default_routes, select_route
from scripts.audit.pal_clink_runner import run_audit

route = select_route(default_routes())
if route is None:
    raise RuntimeError("No audit CLI available on this host")

output = run_audit(route, prompt="Review this diff for correctness and security issues:\n\n...")

if output.timed_out:
    # timed_out=True, exit_code=None
    print(f"Audit timed out after 300s: {output.error}")
elif output.exit_code != 0:
    print(f"Audit exited {output.exit_code}:\n{output.stderr}")
else:
    print(output.stdout)
```

## Output Shape

`PalClinkAuditOutput` fields:

| Field | Type | Description |
|---|---|---|
| `cli_name` | `str` | Logical name from the route (e.g. `claude-audit`) |
| `exit_code` | `int \| None` | Process return code; `None` on timeout or pre-flight failure |
| `stdout` | `str` | Captured stdout (UTF-8, decode errors replaced) |
| `stderr` | `str` | Captured stderr (UTF-8, decode errors replaced) |
| `timed_out` | `bool` | `True` when process was killed after timeout |
| `error` | `str \| None` | Human-readable error for pre-flight failures or timeout |
| `duration_seconds` | `float \| None` | Wall-clock seconds; `None` on pre-flight failure |

Serialized output is validated against `schemas/audit/pal_clink_audit_output.schema.json`.

## Pre-flight Checks

Before invoking the subprocess, `run_audit()` performs:

1. **Codex guard**: raises `ValueError` if `route.cli_name` is in `FORBIDDEN_CLI_NAMES` (`{"codex", "codex-audit"}`).  This is defense-in-depth; `AuditRoute.__post_init__` already rejects these names.
2. **Capability probe**: calls `which_fn(route.command)`.  If the command is not found on PATH, returns `PalClinkAuditOutput` with `error="command ... not found on PATH"`, `exit_code=None`, `duration_seconds=None`.

## Env Override Semantics

The subprocess environment is `{**os.environ, **route.env}`.  Keys in `route.env` **shadow** matching system env keys for the duration of the subprocess.  If `route.env` contains `PATH`, the subprocess sees that value instead of the system `PATH`.

**Remaining risk**: PATH at audit invocation time may differ from `shutil.which` probe time if the environment changes between probe and invocation.

## Timeout

Default: 300 seconds.  On timeout:

- `timed_out = True`
- `exit_code = None`
- `stdout = ""`, `stderr = ""`
- `error = "timed out after {timeout_seconds}s"`
- `duration_seconds` is set (wall time until kill)

The `TimeoutExpired` exception from `subprocess.run` is caught internally and converted to output.  All other subprocess exceptions propagate.

## Forbidden CLIs

`codex` and `codex-audit` are **never permitted** as runner targets.  This matches the `embedded_audit.schema.json` `auditor_tool` enum (which does not include Codex) and the operator-level prohibition on adding Codex as a formal auditor without schema approval.

Enforcement layers:
1. `AuditRoute.__post_init__` (cannot construct a forbidden AuditRoute)
2. `run_audit()` codex guard (defense-in-depth for serialization bypass)
3. `audit_route.schema.json` `cli_name` and `command` constraints

## Related Files

- `scripts/audit/auditor_router.py` — route registry and CLI selection
- `scripts/audit/route_schema.py` — `AuditRoute` dataclass and `FORBIDDEN_CLI_NAMES`
- `schemas/audit/audit_route.schema.json` — route validation schema
- `docker/mcp-servers-source/pal/pal-mcp-server/conf/cli_clients/` — PAL clink configs (read-only)
