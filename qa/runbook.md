# dopemux-qa Runbook

Human operator guide for running the automated QA harness. This document is also safe to paste as a prompt to Claude Desktop — it is self-contained.

---

## Prerequisites

Before running any QA scenarios, verify the following:

1. **Docker Desktop is running.**
   ```bash
   docker info >/dev/null 2>&1 && echo "OK" || echo "Docker not running"
   ```

2. **dopemux CLI is installed.**
   ```bash
   dopemux --version
   ```
   Expected: a version string such as `dopemux 0.x.y`. If this fails, run `pip install -e .` from the repo root.

3. **qa/.env is populated.**
   ```bash
   cp qa/.env.example qa/.env
   # Then edit qa/.env and fill in the required API keys.
   ```
   The minimum required keys for non-live runs:
   - `ANTHROPIC_API_KEY` (for ConPort / PAL health checks)
   - `LITELLM_MASTER_KEY` (any string for QA stack)

   For live LLM lane (scenario 61) also set:
   - `DPMX_LIVE_OK=1`
   - `DPMX_QA_SPEND_CAP_USD=0.50` (hard cap in USD; set to your budget)

4. **No port conflicts on QA ports.**
   QA uses ports offset by +40 from defaults. Verify none are in use:
   ```bash
   for port in 5472 6419 6420 3044 3045 3043 4040 3050 6373 6374 8120; do
       lsof -i ":$port" -t 2>/dev/null && echo "PORT $port IN USE" || true
   done
   ```
   All should return empty. If a port is occupied, find and stop the conflicting process.

---

## Quick smoke run (no live LLM, ~5 min)

This runs environment setup, CLI probing, and MCP round-trips. No real LLM calls are made.

```bash
cd /Users/hue/code/dopemux-mvp/.claude/worktrees/hopeful-shirley-656b07

# Set run context
export ROOT=$(pwd)
export RUN_ID=$(date +%Y%m%d-%H%M%S)
export RESULTS_DIR="$ROOT/qa/results/$RUN_ID"
export RESULTS_FILE="$RESULTS_DIR/results.jsonl"
export QA_ENV_FILE="$ROOT/qa/.env"
export QA_NETWORK="dopemux-qa-network"
export COMPOSE_PROJECT_NAME="dopemux-qa"
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

mkdir -p "$RESULTS_DIR"

# Register teardown (fires even if you Ctrl-C)
trap 'bash "$ROOT/qa/scenarios/99_env_down.sh"' EXIT

# Run smoke scenarios
for script in 00_env_up.sh 01_probe_entrypoints.sh 30_mcp_roundtrips.sh 99_env_down.sh; do
    echo "--- $script ---"
    timeout 300 bash "$ROOT/qa/scenarios/$script" || true
done

echo ""
echo "Results written to: $RESULTS_FILE"
cat "$RESULTS_FILE" | python3 -c "
import sys, json
lines = [json.loads(l) for l in sys.stdin if l.strip()]
for r in lines:
    icon = {'PASS': '✓', 'FAIL': '✗', 'NOT_RUN': '–'}[r['status']]
    print(f\"{icon} {r['scenario']:40s} {r['message'][:60]}\")
"
```

**Expected output** for a healthy stack:
```
✓ env_up                           QA network and services healthy
✓ probe_entrypoints                dopemux --version and subcommands OK
✓ mcp_roundtrips                   ConPort and PAL MCP respond
✓ env_down                         QA stack torn down cleanly
```

---

## Full run with surface selection

### Run all surfaces

```bash
# Using the qa-run skill (Claude Desktop)
qa-run --surface all

# Or manually:
for script in qa/scenarios/[0-9]*.sh; do
    timeout 300 bash "$script" || true
done
python3 qa/scenarios/20_cli_sweep.py
python3 qa/scenarios/80_docs_drift.py
```

### Run only CLI scenarios

```bash
qa-run --surface cli

# Manual equivalent:
bash qa/scenarios/01_probe_entrypoints.sh
python3 qa/scenarios/20_cli_sweep.py
```

### Run only MCP scenarios

```bash
qa-run --surface mcp

# Manual:
bash qa/scenarios/30_mcp_roundtrips.sh
```

### Run RTE routing safety (no live calls)

```bash
qa-run --surface rte

# Manual:
bash qa/scenarios/60_rte_routing_safety.sh
# Note: 61_live_lane.sh is skipped unless DPMX_LIVE_OK=1
```

### Run with live LLM lane enabled

**Warning: this incurs real API spend.**

```bash
# Add to qa/.env:
#   DPMX_LIVE_OK=1
#   DPMX_QA_SPEND_CAP_USD=0.50

qa-run --surface rte --live

# Manual:
export DPMX_LIVE_OK=1
bash qa/scenarios/61_live_lane.sh
```

---

## Reading results

### Raw results file

Each completed run writes `qa/results/<RUN_ID>/results.jsonl`. Each line is a JSON object:

```json
{"scenario":"env_up","status":"PASS","message":"All QA services healthy","evidence":{},"timestamp":"2026-05-29T14:32:01Z","duration_s":47}
```

Fields:
- `scenario`: scenario name (cross-reference with `qa/backlog-map.yaml`)
- `status`: `PASS`, `FAIL`, or `NOT_RUN`
- `message`: human-readable summary
- `evidence`: structured data for diagnostics (exit codes, HTTP status, etc.)
- `timestamp`: UTC ISO-8601
- `duration_s`: how long the scenario took

### Quick summary

```bash
RUN_ID=20260529-143201   # replace with your run ID
cat qa/results/$RUN_ID/results.jsonl | python3 -c "
import sys, json
lines = [json.loads(l) for l in sys.stdin if l.strip()]
by_status = {'PASS': [], 'FAIL': [], 'NOT_RUN': []}
for r in lines:
    by_status[r['status']].append(r['scenario'])
print(f\"PASS: {len(by_status['PASS'])}\")
print(f\"FAIL: {len(by_status['FAIL'])}\")
print(f\"NOT_RUN: {len(by_status['NOT_RUN'])}\")
if by_status['FAIL']:
    print()
    print('FAILURES:')
    for s in by_status['FAIL']:
        print(f'  {s}')
"
```

### What each status means

| Status | Meaning | Action |
|--------|---------|--------|
| `PASS` | All assertions in the scenario succeeded | No action needed |
| `FAIL` | At least one assertion failed | Read `message` + `evidence`; see Troubleshooting below |
| `NOT_RUN` | Scenario was skipped | Check if `env_up` FAIL caused downstream skips; or surface filter excluded it |

**Important**: `NOT_RUN` is not a pass. A run where `env_up` fails will produce `NOT_RUN` for every downstream scenario. Check `env_up` first.

### Markdown report

If the harness ran `qa_common.py synthesize_report`, a human-readable report is at:
```
qa/results/<RUN_ID>/report.md
```

---

## Populating baseline

The baseline captures signals from a known-good HEAD and is used to detect regressions.

### When to update baseline

- After a clean full run on a freshly merged PR that you know is correct
- After deliberately raising the bar (e.g., more passing tests)
- Never update baseline when there are known failures

### How to populate

```bash
# Via skill (recommended):
qa-run --surface all --baseline

# Manual equivalent (run only after confirming zero FAIL results):
python3 qa/lib/qa_common.py update_baseline \
    qa/results/<RUN_ID>/results.jsonl \
    qa/baseline/baseline.json

# Commit the updated baseline:
git add qa/baseline/baseline.json
git commit -m "qa: update baseline to $(git rev-parse --short HEAD)"
```

The baseline file (`qa/baseline/baseline.json`) stores:
- `head_sha`: the git SHA the baseline was generated from
- `signals`: numeric signals (test pass counts, avg response times, etc.)
- `golden_snapshots`: captured output snippets for perceptual comparison
- `generated_at`: timestamp

---

## Troubleshooting

### QA stack fails to start (00_env_up.sh FAIL)

**Symptom**: `env_up` fails; all downstream scenarios are `NOT_RUN`.

**Check 1**: Is `dopemux-network` (the external network for live stacks) present? This is separate from `dopemux-qa-network`.
```bash
docker network ls | grep dopemux
```
If missing, create it:
```bash
docker network create dopemux-network
```
(BETA-INSTALL-02: this network is not auto-created on fresh installs.)

**Check 2**: Port conflicts.
```bash
for port in 5472 6419 6420 3044 3045 3043 4040 3050 6373 6374 8120; do
    pid=$(lsof -i ":$port" -t 2>/dev/null | head -1)
    [[ -n "$pid" ]] && echo "Port $port used by PID $pid ($(ps -p $pid -o comm= 2>/dev/null))"
done
```

**Check 3**: Docker memory. QA stack needs at least 4GB RAM headroom.
```bash
docker system df
docker stats --no-stream
```

### All MCPs NOT_RUN

This almost always means `env_up` failed. Check:
1. `00_env_up.sh` result in `results.jsonl`
2. Docker compose logs: `docker compose -p dopemux-qa logs --tail=50`

### A scenario hangs

Each scenario has a 300-second timeout enforced by the runner. If it fires, the result is written as `FAIL` with `"timed out after 300s"` and execution continues with the next scenario.

If you see a hung terminal manually, Ctrl-C will trigger the EXIT trap and run teardown.

### Live lane not running (61_live_lane.sh NOT_RUN)

Live lane requires both env vars:
```bash
# In qa/.env:
DPMX_LIVE_OK=1
DPMX_QA_SPEND_CAP_USD=0.50
```

Also requires `--live` flag when using the skill.

### TUI perceptual check fails

Check for:
- dx-clobber regression (BETA-UI-03): run `dopemux cockpit` and confirm dx commands are listed
- Raw escape codes in output: indicates Ink rendering failure; check Node.js version

### Docs drift scenario fails (80_docs_drift.py)

This scenario compares CLI `--help` output against documented command lists. Common causes:
- A new subcommand added to CLI but not documented
- A subcommand renamed without updating docs

Read the FAIL message for the specific mismatch.

---

## Safety / isolation

### How the QA stack is isolated

The QA harness runs a separate Docker Compose project (`COMPOSE_PROJECT_NAME=dopemux-qa`) with port offsets (+40 from all default ports). This means:

| Service | Live port | QA port |
|---------|-----------|---------|
| PostgreSQL | 5432 | 5472 |
| Redis Events | 6379 | 6419 |
| Redis Primary | 6380 | 6420 |
| ConPort HTTP | 3004 | 3044 |
| ConPort MCP | 3005 | 3045 |
| PAL | 3003 | 3043 |
| LiteLLM | 4000 | 4040 |
| Dope-Context | 3010 | 3050 |
| Qdrant | 6333 | 6373 |
| Leantime | 8080 | 8120 |

QA containers use Docker volumes named with the `dopemux-qa` prefix and the `dopemux-qa-network` Docker network — entirely separate from the live `dopemux-network`.

### The -v safety rule

**Never** run `docker compose -p dopemux ...` (the live project) with `-v` (remove volumes) from a QA script. The `guard_qa_project()` function in `qa/lib/qa_common.sh` and `qa/lib/qa_common.py` enforces that `COMPOSE_PROJECT_NAME` must equal `dopemux-qa` before any compose command runs.

### Verifying the live stack is untouched

After a QA run, confirm the live stack was not affected:
```bash
# Check live ConPort is still up
curl -sf http://localhost:3004/health && echo "Live ConPort OK"

# Check live Redis
redis-cli -p 6380 ping && echo "Live Redis OK"

# Confirm QA containers are down (after 99_env_down runs)
docker ps --filter "label=com.docker.compose.project=dopemux-qa"
# Should show no running containers
```
