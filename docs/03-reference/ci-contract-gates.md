---
id: CI-CONTRACT-GATES
title: CI Contract Gates and Port Drift Test
type: reference
owner: '@hu3mann'
author: 'claude-code'
date: '2026-10-30'
last_review: '2026-10-30'
next_review: '2027-01-28'
prelude: What the tests/arch contract tests check, how CI now runs them, how to run them locally, the service port drift rules, and how to add a documented exception.
---
# CI Contract Gates and Port Drift Test

`tests/arch/` holds static contract tests: they read repo files and check that the files agree with each other. Nothing in them starts a service. Until Foundations Wave 1, no CI job ran them. Design: [Foundations Wave 1](../91-rfc/rfc-2026-10-30-foundations-wave-1.md).

## What CI runs

The `🧪 Unit Tests` job in `.github/workflows/ci-complete.yml` has a step named `▶️ Run arch contract gate`:

```bash
uv run --frozen pytest tests/arch -n auto --maxfail=1 --disable-warnings --no-cov
```

- It is a separate pytest process from the `tests/unit` step. `tests/arch` imports service packages whose module names could shadow modules that `tests/unit` imports if both were collected together (the same reason as the dope-memory step above it).
- It inherits the required-check status of the `🧪 Unit Tests` job.
- CI uses Python 3.11 and `uv sync --frozen --extra test --extra services`. The repo venv is 3.12. Every test in `tests/arch` must pass in the CI environment without skips.
- The job stops at the first failure (`--maxfail=1`), so one red test hides the others until it is fixed.

## What `tests/arch` checks

| File | Checks |
|---|---|
| `test_registry_compose_alignment.py` | `services/registry.yaml` against `compose.yml` for services marked `enabled_in_smoke`. |
| `test_service_port_drift.py` | Port agreement between the registry, the MCP catalog, compose, scripts and defaults (next section). |
| `test_service_env_contract.py` | Service environment variable contract. |
| `test_compose_guard.py` | Compose guard drift checks. |
| `test_mcp_fleet_catalog_contract.py`, `test_mcp_multiproject_contracts.py` | MCP fleet catalog and multi-project contracts. |
| `test_pal_model_catalog_contract.py` | PAL model catalog. |
| `test_persona_fleet_contract.py` | Packaged personas are a generated subset of the canonical ones. |
| `test_task_orchestrator_conport_persistence_contract.py` | Static boundary for task-orchestrator workflow persistence. |
| `test_dopetask_submodule_contract.py` | dopetask is pinned, not a git submodule (`.gitmodules`, the CI workflow, the wrapper). |
| `test_adhd_engine_mcp_parity.py` | Every `engine.<method>()` call in an `@mcp.tool()` function of `services/adhd_engine/main.py` exists on both the real engine class and the fallback class; the four methods return the documented shapes. |

Run `pytest tests/arch` before you push a change to the service registry, compose, the MCP catalog or fleet, personas, or any service port.

## Run it locally

From the repo root, with the repo venv (Python 3.12):

```bash
.venv/bin/python -m pytest tests/arch -q
.venv/bin/python -m pytest tests/arch/test_service_port_drift.py -q
```

To match CI more closely:

```bash
uv run --frozen --extra test --extra services pytest tests/arch -n auto --no-cov
```

Pytest markers are strict (`pytest.ini`).

## Service port drift

`tests/arch/test_service_port_drift.py` treats `services/registry.yaml` as the source of truth for ports. It compares host ports only: a compose mapping `"127.0.0.1:${VAR:-N}:M"` has host port `N`, and `${VAR:-default}` resolves to its default. Container ports are not compared.

### The rules

| Test | Rule |
|---|---|
| `test_registry_matches_catalog` | For a service in both the registry and `mcp_catalog.yaml`, the registry port equals the catalog's `reserved_port`, else `default_port_base`, else the port in `url` / `url_template`. |
| `test_registry_matches_compose_for_non_smoke` | For a registry service not marked `enabled_in_smoke`, the registry port is among the host ports its compose service publishes. Smoke services are covered by `test_registry_compose_alignment.py`. A compose service with no host `ports:` or with `network_mode`, or a missing one, is "not comparable": it is printed (`not comparable: ...`) and does not fail. |
| `test_no_unknown_port_literals` | A `localhost:N` or `127.0.0.1:N` literal in the scanned files must be a port in the registry or the catalog. |
| `test_named_defaults_match_registry` | In `src/dopemux/config/manager.py`, `adhd_engine_url`, `leantime_url`, `serena_url` and `litellm_url` use the registry port of `adhd-engine`, `leantime`, `serena` and `litellm`. The test also fails if it finds no such line, so a rename cannot hide drift. |
| `test_cli_default_port_matches_registry` | `DEFAULT_ADHD_ENGINE_PORT` in `dopemux.commands.adhd_commands` equals the registry port of `adhd-engine` (3025). |

Scanned files for the literal rule (`SCANNED_FILES`): `src/dopemux/config/manager.py`, `scripts/dopemux_dashboard.py`, `.claude/statusline.sh`, `mcp_server_health_report.sh`, `scripts/mcp_health_check.sh`, `src/dopemux/ui/service_endpoints.py`, `src/dopemux/profile_detector.py`. A missing file fails the test, so update the list when you move one.

### Limits of the literal rule

- It only sees text of the form `localhost:N` or `127.0.0.1:N`. A bare number such as the `5448` and `8095` probes in `service_endpoints.py` and `profile_detector.py`, or a port built from a variable, is invisible to it.
- It flags a port only if the port is unknown. A port that is valid for a different service passes. For example `.claude/statusline.sh` probes `localhost:3009` as task-orchestrator, but `3009` is `gptr-mcp`, so the test does not flag it.
- It checks ports, not paths. `mcp_server_health_report.sh` probes pal at `/mcp` where the catalog's health URL is `/health`; the test does not see that.

### Fixed in this wave

`src/dopemux/config/manager.py` carried stale defaults for the Dope layout (class defaults and the layout dict). They now use the registry ports: `adhd_engine_url` 3025 (was 3008), `leantime_url` 8080 (was 3007), `serena_url` 3006 (was 3010, which is dope-context). Two other defaults, `conport_url` (3009, which is gpt-researcher) and `activity_capture_url`, have no unambiguous registry service and were left alone (follow-up below).

### Add an exception

Known, accepted differences live in the `EXCEPTIONS` table at the top of the test file. The key says which rule it excuses:

| Key | Excuses |
|---|---|
| `("catalog", service_name)` | a registry/catalog difference for that service |
| `("compose", service_name)` | a registry/compose difference for that service |
| `("literal", (file, port))` | an unknown `localhost:port` literal in that file |

Each entry needs two non-empty fields: `reason` (why the difference is correct or accepted) and `follow_up` (what will resolve it, or why nothing will). `test_exceptions_are_documented` fails on an entry missing either.

A stale entry also fails. `test_no_stale_exceptions` computes the differences that are live now and fails on any `EXCEPTIONS` key that matches none. When you fix a difference, delete its entry in the same change. When you add one, do not use it for a difference you can fix.

Current entries:

| Key | Reason | Follow-up |
|---|---|---|
| `("catalog", "task-orchestrator")` | Two processes share the name: the Python orchestrator on 8000 (registry) and the Kotlin MCP server on 7890 (catalog). | Map item S2 (identity split). |
| `("compose", "dopecon-bridge-alt")` | The registry alt entry says 3000; its compose service `dopecon-bridge` publishes only 3016. | Retire the alt entry or give it a compose mapping. |
| `("literal", ("scripts/dopemux_dashboard.py", 8095 / 8005 / 8003))` | Stale script: the adhd-engine container port, and two ports in no registry or compose entry. | Retire or repair the script. |

## Not covered

- The engine's own test suite, `services/adhd_engine/tests/`, is not run by CI and is unhealthy (88 passed, 28 failed, 4 files fail to import on 2026-10-30). Wiring it in would turn CI red.
- The engine's MCP server is mounted at `/mcp` but is not registered in `.mcp.json` or `mcp_catalog.yaml`.

## Follow-ups this wave creates

From section 10 of the [design](../91-rfc/rfc-2026-10-30-foundations-wave-1.md). None is done here.

- Break-writer endpoint and `dopemux adhd break|focus|ack`, after PR #1472 merges.
- Register the engine's MCP server in the catalog and `.mcp.json`.
- Triage `services/adhd_engine/tests/` and wire it into CI.
- Fix the task-orchestrator probe in `.claude/statusline.sh`.
- Retire `services/adhd_engine/cli/adhd.py`.
- Resolve the task-orchestrator name collision (S2).
- Proof-only closure mode for clean merges of `main` (operator decision).
- Retire or repair `scripts/dopemux_dashboard.py`.
- Resolver defaults `5448` / `8095` in `service_endpoints.py` and `profile_detector.py`; the `manager.py` defaults `conport_url` and `activity_capture_url`; the pal health path in `mcp_server_health_report.sh`.

See also: [dopemux adhd status](adhd-status-cli.md).
