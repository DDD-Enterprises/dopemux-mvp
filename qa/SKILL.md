---
name: qa-run
description: Run the dopemux automated QA harness against the QA stack
version: 1.0.0
tools:
  - desktop-commander
  - mcp__Claude_in_Chrome__*
  - Bash
  - Read
---

# qa-run — dopemux QA Harness

**One-line**: Run the dopemux automated QA harness against the QA stack.

## When to invoke

- Regression testing after a code change or merge
- Verifying a fix resolves the targeted BETA-* backlog item
- Pre-merge smoke check on a PR branch
- Populating or refreshing the golden baseline after a known-good HEAD
- Confirming QA isolation (live A–E stacks must be untouched)

---

## Parameters

All parameters are optional.

| Flag | Values | Default | Purpose |
|------|--------|---------|---------|
| `--surface` | `install` `cli` `mcp` `multiinstance` `hooks` `rte` `tui` `web` `docs` `all` | `all` | Run only scenarios matching this surface tag |
| `--baseline` | (flag) | off | After a successful run, overwrite `qa/baseline/baseline.json` with signals from this run |
| `--resume <run-id>` | e.g. `20260529-143201` | (new run) | Resume a partial run — skip scenarios that already have a result in that run's `results.jsonl` |
| `--live` | (flag) | off | Enable the live LLM lane (scenario `61_live_lane.sh`). Requires `DPMX_LIVE_OK=1` and `DPMX_QA_SPEND_CAP_USD` to be set in `qa/.env` |

Surface tags map to scenario prefixes:

| `--surface` | Scenarios included |
|-------------|-------------------|
| `install`   | 00, 10 |
| `cli`       | 01, 20 |
| `mcp`       | 30 |
| `multiinstance` | 40 |
| `hooks`     | 50 |
| `rte`       | 60, 61 |
| `tui`       | 90 |
| `web`       | 90 (web dashboard) |
| `docs`      | 80 |
| `all`       | 00–99 |

---

## Safety Rails (read before proceeding)

1. **COMPOSE_PROJECT_NAME must be `dopemux-qa`** for every docker command. The lib guard (`guard_qa_project`) enforces this in each scenario. Verify before any `docker compose` call.
2. **Never pass `--rm -v` to the live `dopemux` project.** The QA harness only touches `dopemux-qa` containers and volumes.
3. **Never modify ports in the live range** (5432, 6379, 6380, 3004, 3005). QA uses offset ports (+40).
4. **Teardown runs on EXIT** (trap). Even if a scenario aborts, `99_env_down.sh` fires to avoid leaving QA containers running.
5. **Spend cap required for live lane**: do not set `DPMX_LIVE_OK=1` without also setting `DPMX_QA_SPEND_CAP_USD` to a positive number.

---

## Driver Procedure

Claude should follow these steps in order. Do not parallelize scenario scripts — they are sequential by design.

### Step 1 — Initialize run

```bash
ROOT=$(git rev-parse --show-toplevel)
RUN_ID=$(date +%Y%m%d-%H%M%S)
RESULTS_DIR="$ROOT/qa/results/$RUN_ID"
RESULTS_FILE="$RESULTS_DIR/results.jsonl"
mkdir -p "$RESULTS_DIR"
echo "[qa-run] RUN_ID=$RUN_ID"
```

### Step 2 — Prepare qa/.env

```bash
if [[ ! -f "$ROOT/qa/.env" ]]; then
    cp "$ROOT/qa/.env.example" "$ROOT/qa/.env"
    echo "[WARN] qa/.env created from .env.example — fill in API keys before live lane runs"
fi
```

### Step 3 — Register teardown trap

Register `99_env_down.sh` to execute on EXIT so the QA stack is torn down even if a scenario fails or Claude's turn ends early:

```bash
trap 'bash "$ROOT/qa/scenarios/99_env_down.sh"' EXIT
```

### Step 4 — Export shared environment

These vars must be set for every scenario script:

```bash
export ROOT RUN_ID RESULTS_DIR RESULTS_FILE
export QA_ENV_FILE="$ROOT/qa/.env"
export QA_NETWORK="dopemux-qa-network"
export COMPOSE_PROJECT_NAME="dopemux-qa"

# QA port offsets
export QA_POSTGRES_PORT=5472
export QA_REDIS_EVENTS_PORT=6419
export QA_REDIS_PRIMARY_PORT=6420
export QA_CONPORT_HTTP_PORT=3044
export QA_CONPORT_MCP_PORT=3045
export QA_PAL_PORT=3043
export QA_LITELLM_PORT=4040
export QA_DOPE_CONTEXT_PORT=3050
export QA_QDRANT_PORT=6373
export QA_QDRANT_GRPC_PORT=6374
export QA_LEANTIME_PORT=8120
```

If `--live` was passed, also set:

```bash
export DPMX_LIVE_OK=1
# DPMX_QA_SPEND_CAP_USD must already be present in qa/.env
```

### Step 5 — Run scenarios sequentially

Surface filter logic: run a scenario if `--surface all` or if the surface tag matches the scenario's prefix group (see table above). Wrap each script in a per-scenario 300-second timeout.

```bash
SCENARIOS=(
    "00_env_up.sh:install,all"
    "01_probe_entrypoints.sh:cli,all"
    "10_install_gauntlet.sh:install,all"
    "20_cli_sweep.py:cli,all"
    "30_mcp_roundtrips.sh:mcp,all"
    "40_multi_instance_collision.sh:multiinstance,all"
    "50_hooks_lifecycle.sh:hooks,all"
    "60_rte_routing_safety.sh:rte,all"
    "61_live_lane.sh:rte,all"
    "70_pytest_lanes.sh:all"
    "80_docs_drift.py:docs,all"
    "90_tui_renders.sh:tui,web,all"
    "99_env_down.sh:all"
)

SURFACE="${SURFACE_ARG:-all}"

for entry in "${SCENARIOS[@]}"; do
    script="${entry%%:*}"
    tags="${entry##*:}"
    # Check if surface tag matches
    if [[ "$SURFACE" == "all" ]] || echo "$tags" | grep -qw "$SURFACE"; then
        script_path="$ROOT/qa/scenarios/$script"
        if [[ "$script" == *.py ]]; then
            timeout 300 python3 "$script_path" || true
        else
            timeout 300 bash "$script_path" || true
        fi
    fi
done
```

**If `--resume <run-id>` was passed**: before running each scenario, check if `qa/results/<run-id>/results.jsonl` already contains a result for that scenario. If it does, skip (emit NOT_RUN with message "resumed: already recorded"). Copy existing results to the new RUN_ID directory first.

### Step 6 — L2 perceptual: TUI assessment

After `90_tui_renders.sh` completes (if surface includes `tui` or `all`):

Use the desktop-commander screenshot tool to capture the terminal output and assess TUI quality:

```
mcp__desktop-commander__screenshot()
```

Look for:
- No Python tracebacks in the terminal output
- Ink/React components rendered (not raw escape codes)
- dx-clobber regression absent (BETA-UI-03): verify dx commands are present in cockpit output

Record assessment as an additional result line in RESULTS_FILE:

```python
{"scenario":"tui_perceptual_l2","status":"PASS|FAIL","message":"<observation>","evidence":{},...}
```

### Step 7 — L2 perceptual: Web dashboard

If `--surface` includes `web` or `all`:

```python
# Open Claude-in-Chrome
mcp__Claude_in_Chrome__navigate(url="http://localhost:8120")
screenshot = mcp__Claude_in_Chrome__preview_screenshot()
console_errors = mcp__Claude_in_Chrome__read_console_messages()
```

Check for:
- Page loads (HTTP 200, not blank/error page)
- No uncaught JS exceptions in console
- Core UI elements present (navigation, dashboard panels)

Emit result:

```python
{"scenario":"web_dashboard_l2","status":"PASS|FAIL","message":"...","evidence":{"console_errors": [...]},...}
```

### Step 8 — Synthesize report

```bash
python3 "$ROOT/qa/lib/qa_common.py" synthesize_report "$RESULTS_DIR"
# Generates: $RESULTS_DIR/report.md
```

Read and display `$RESULTS_DIR/report.md` to the user.

### Step 9 — Baseline update (if --baseline)

If `--baseline` was passed and the run had no FAIL results:

```bash
python3 "$ROOT/qa/lib/qa_common.py" update_baseline \
    "$RESULTS_DIR/results.jsonl" \
    "$ROOT/qa/baseline/baseline.json"
echo "[qa-run] baseline.json updated from run $RUN_ID"
```

If there were FAIL results, warn the user and do NOT overwrite the baseline.

---

## Model guidance

- **Sonnet (this model)** drives L0–L2: environment setup, scenario execution, perceptual checks.
- For **L3 synthesis** (deep report analysis, trend detection across multiple runs): optionally hand `$RESULTS_DIR/results.jsonl` to Opus via a follow-up invocation with the prompt: "Analyze this QA run for systemic patterns, regression risk, and recommended next actions."
- Keep scenario execution strictly sequential — parallelizing scenarios risks port collisions and produces unreliable results.

---

## Result interpretation

Each line in `results.jsonl` has one of three statuses:

| Status | Meaning |
|--------|---------|
| `PASS` | Scenario assertions all succeeded |
| `FAIL` | At least one assertion failed — see `message` and `evidence` |
| `NOT_RUN` | Scenario was skipped (surface filter, resume skip, or prerequisite failed) |

`NOT_RUN` is **not** the same as `PASS`. A run where all scenarios are `NOT_RUN` provides no signal.

---

## Backlog coverage

After a run, cross-reference `results.jsonl` scenario names against `qa/backlog-map.yaml` to determine which BETA-* items were exercised. Items not covered by any `PASS` scenario remain unverified.
