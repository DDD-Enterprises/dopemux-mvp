---
id: ADHD-STATUS-CLI
title: dopemux adhd status
type: reference
owner: '@hu3mann'
author: 'claude-code'
date: '2026-10-30'
last_review: '2026-10-30'
next_review: '2027-01-28'
prelude: Reference for the read-only dopemux adhd status command, which reports the ADHD engine's energy, attention and health over HTTP. Covers URL resolution, statuses, exit codes, JSON output and known limits.
---
# dopemux adhd status

`dopemux adhd status` reads the state of the ADHD engine and prints one line (or one JSON object). It is read-only: it sends two `GET` requests and changes nothing. Design: [Foundations Wave 1](../91-rfc/rfc-2026-10-30-foundations-wave-1.md). Engine HTTP API: [ADHD Engine API](adhd-engine-api.md).

Source: `src/dopemux/commands/adhd_commands.py`. The group is registered in `src/dopemux/cli.py:3206-3208`. Tests: `tests/unit/test_adhd_commands.py`.

## Usage

```bash
dopemux adhd status                      # one line, human readable
dopemux adhd status --json               # one JSON object, for scripts
dopemux adhd status --url http://127.0.0.1:8095
```

| Option | Meaning |
|---|---|
| `--json` | Print the result as one JSON object instead of a sentence (`adhd_commands.py:183`). |
| `--url URL` | Engine base URL. Overrides every environment variable (`adhd_commands.py:184`). |

Example output:

```text
ADHD engine ok (http://127.0.0.1:3025, registry-default): energy medium, attention focused
ADHD engine degraded (http://127.0.0.1:3025, registry-default): energy medium, attention focused; degraded: engine running on its fallback class
ADHD engine unreachable (http://127.0.0.1:3025, registry-default): ConnectionError: no response
```

## Which engine URL it uses

The first match wins (`adhd_commands.py:47-72`). The `url_source` field and the human line say which step matched.

| Order | Source | `url_source` |
|---|---|---|
| 1 | `--url` | `--url` |
| 2 | `DOPEMUX_ADHD_ENGINE_BASE_URL` | `DOPEMUX_ADHD_ENGINE_BASE_URL` |
| 3 | `DOPEMUX_ADHD_ENGINE_PORT`, as `http://127.0.0.1:<port>` | `DOPEMUX_ADHD_ENGINE_PORT` |
| 4 | `ADHD_ENGINE_PORT` (the variable `compose.yml` uses), as `http://127.0.0.1:<port>` | `ADHD_ENGINE_PORT` |
| 5 | Registry host port `3025` on `127.0.0.1` | `registry-default` |

Notes:

- A port variable that is not an integer from 1 to 65535 is ignored. A warning goes to stderr and resolution continues with the next step (`adhd_commands.py:62-70`).
- There is no socket probing. The default `3025` is the compose host port, matching `services/registry.yaml` (`adhd-engine`, port 3025). The test `tests/arch/test_service_port_drift.py` fails if `DEFAULT_ADHD_ENGINE_PORT` and the registry disagree.
- An engine run directly listens on `API_PORT`, default `8095` (`services/adhd_engine/config.py:65`). Reach it with `--url http://127.0.0.1:8095` or an environment variable.
- The older resolvers in `src/dopemux/ui/service_endpoints.py` and `src/dopemux/profile_detector.py` are not used. They probe `5448` and `8095` and never yield `3025`.

## What it calls

| Call | Used for | Needs an API key |
|---|---|---|
| `GET <url>/api/v1/state` | energy, attention, session minutes | No |
| `GET <url>/health` | whether the engine runs on its fallback class | No |

Each call has a 2 second timeout (`adhd_commands.py:102`). It never calls per-user routes, which need `X-API-Key` when a key is configured.

`/state` is read in both known shapes. The `energy_level` and `attention_state` keys win over `energy` and `attention` when both are present (`adhd_commands.py:130-131`). A response with no energy value is malformed. An attention value is optional.

## Statuses and exit codes

| `status` | Exit code | When |
|---|---|---|
| `ok` | 0 | `/state` answered with an energy value and `/health` did not report the fallback class. |
| `unreachable` | 1 | Connection error, timeout, or `/state` returned a non-2xx status. |
| `malformed` | 1 | `/state` was not JSON, not a JSON object, or had no energy value. |
| `degraded` | 3 | `/state` answered, and `/health` reports `"mode": "fallback"`. |

Exit code 2 is left to click for usage errors (`adhd_commands.py:21`). The exit codes are in `EXIT_CODES`; the message says which case applied.

### What `degraded` means

The engine's `main.py` starts a stand-in engine class if the real one fails to start. That stand-in answers `/health` with `"mode": "fallback"` and a `startup_error` (`services/adhd_engine/main.py:176-181`). The command then reports `degraded` and exits 3, and the detail adds the startup error when there is one. The energy and attention shown in that case come from the stand-in, not from real tracking.

`engine_mode` in the JSON output:

| Value | Meaning |
|---|---|
| `normal` | `/health` answered 2xx with a JSON object that is not fallback and has no `error` key. |
| `fallback` | `/health` has `"mode": "fallback"`. |
| `unknown` | `/state` failed, or `/health` was unreachable, non-2xx, not JSON, not an object, or carried an `error` key (`adhd_commands.py:84-99`). |

An `ok` result can still have `engine_mode: "unknown"`: when `/state` answers and `/health` cannot be classified, the status stays `ok` (`adhd_commands.py:141-149`). A `/health` body for an engine that is still starting (`"overall_status": "Starting"`, no `mode`, no `error`) counts as `normal`.

## JSON output

`--json` prints one object with these keys (the `StatusResult` fields, `adhd_commands.py:27-36`), then exits with the code above:

| Key | Value |
|---|---|
| `status` | `ok`, `degraded`, `unreachable` or `malformed` |
| `url` | the base URL used |
| `url_source` | the resolution step that supplied it |
| `engine_mode` | `normal`, `fallback` or `unknown` |
| `energy` | string, or `null` when no value was read |
| `attention` | string, or `null` |
| `session_minutes` | integer as the engine reported it, or `null` |
| `detail` | empty for `ok`; the reason otherwise |

`session_minutes` in the JSON is the engine's raw value, including `0`. The human line shows session minutes only when the value is greater than 0 (`adhd_commands.py:169`).

## Known limits

- **A failing `/state` still looks healthy.** If `/state` hits an internal error it answers 200 with `medium`, `focused` and `0` (`services/adhd_engine/api/routes.py:1594-1602`). That is the same body as a healthy engine with default values. The CLI cannot tell the two apart. Fixing it means changing `routes.py`, which this wave does not touch.
- **Session minutes are always 0 today.** Nothing in the engine sets `_session_start_times` (`routes.py:1582` only reads it), so `/state` reports `session_minutes: 0`. The human line hides that value for this reason.
- **The energy value is a label.** It is the engine's tracked state for the operator user (defaults to `medium` when nothing was recorded), not a measurement.
- **One user only.** There are no per-user routes and no `--user` option.
- **Read-only.** There are no `break`, `focus` or `ack` verbs. A break-writer endpoint and those verbs wait for PR #1472 (Pulse) to merge.
- **Not in the MCP manifest.** The engine's MCP server is mounted at `/mcp` but is not registered in `.mcp.json` or `mcp_catalog.yaml`.
- **The engine's own tests are not in CI.** `services/adhd_engine/tests/` is not run by CI and is unhealthy (88 passed, 28 failed, 4 files fail to import on 2026-10-30). A CI-run test, `tests/arch/test_adhd_engine_mcp_parity.py`, covers only the MCP-to-engine method parity (see [CI contract gates](ci-contract-gates.md)).

## Related engine change in this wave

The real engine class gained the four methods its MCP tools call: `get_energy_level`, `get_attention_state`, `get_cognitive_load` and `assess_task` (`services/adhd_engine/core/engine.py:423-452`). Before, they existed only on the fallback class, so the MCP tools failed on a healthy engine.

- `get_energy_level` returns `EnergySnapshot(level, score)`. `score` comes from the fixed `ENERGY_SCORE` table (`engine.py:114-120`): very_low 0.1, low 0.3, medium 0.5, high 0.7, hyperfocus 0.9. It is a label mapped to a number, not a measurement.
- `get_attention_state` returns `AttentionSnapshot(state)`.
- `assess_task` uses a complexity of 0.5 and 30 minutes as placeholders and lists them in the result as `defaults_used`, so a caller can tell placeholders from measurements.

Follow-ups for this command and its engine are listed in section 10 of the [design](../91-rfc/rfc-2026-10-30-foundations-wave-1.md).
