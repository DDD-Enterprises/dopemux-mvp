# dopemux-qa: Automated QA Harness

Deterministic, isolated, backlog-oracle QA for the dopemux development platform.

---

## Purpose

This harness validates the dopemux stack against its [BETA-* backlog](../claudedocs/beta-readiness-2026-05-29/) before releases and after significant changes. It runs against an isolated Docker Compose project (`dopemux-qa`) to ensure the live A–E stacks are never touched.

### Design principles

- **Deterministic-first**: Scenarios that call real LLMs are gated behind `DPMX_LIVE_OK=1`. Default runs produce consistent, reproducible results without API spend.
- **Backlog/baseline oracle**: Every scenario is mapped to one or more BETA-* backlog items (`backlog-map.yaml`). The baseline (`baseline/baseline.json`) captures signals from a known-good HEAD for regression comparison.
- **Interruption-resilient**: Each scenario emits results atomically (JSON line) as it completes. A partial run can be resumed with `--resume <run-id>`. The EXIT trap always runs teardown.
- **Isolated by design**: Offset ports (+40), separate compose project name, separate Docker network, separate volumes. `guard_qa_project()` enforces this in every scenario.

---

## Architecture

The harness is organized into four layers:

### L0 — Environment
Scenarios `00` and `99`. Bring up and tear down the QA Docker Compose stack. All other layers depend on L0 succeeding.

### L1 — Deterministic checks
Scenarios `01`, `10`, `20`, `30`, `40`, `50`, `60`, `70`, `80`. Scripted assertions with no randomness and no live LLM calls. These produce stable `PASS/FAIL/NOT_RUN` results on every run at the same HEAD.

- **Entrypoint probing** (`01`): CLI reachable, subcommands present
- **Install gauntlet** (`10`): network creation, service boot, secrets wiring, post-install health
- **CLI sweep** (`20`): all subcommands, output formats, JSON flags
- **MCP round-trips** (`30`): ConPort and PAL MCP health
- **Multi-instance collision** (`40`): Redis port isolation across instances A–E + QA
- **Hooks lifecycle** (`50`): SessionStart and PostToolUse hooks fire
- **RTE routing safety** (`60`): SP fail-close at execution time, injection guards
- **pytest lanes** (`70`): unit, integration, provider-modes, series-gate test suites
- **Docs drift** (`80`): CLI help text matches docs, MCP manifest matches runtime shape

### L2 — Perceptual checks
Scenarios `61` and `90`, plus Claude Desktop tool calls after scenario scripts complete.

- **Live LLM lane** (`61`): a real end-to-end LLM call through the RTE (gated by `DPMX_LIVE_OK`)
- **TUI renders** (`90`): Ink/React dashboard renders without tracebacks; dx-clobber regression absent
- **Web dashboard**: Claude-in-Chrome opens `http://localhost:8120`, checks for JS errors, verifies core UI elements

### L3 — Synthesis
After all scenarios complete, `qa_common.py synthesize_report` generates `report.md`. For deep trend analysis across multiple runs, hand `results.jsonl` to a stronger model.

---

## Quick start

### Using the qa-run skill (Claude Desktop)

```
qa-run --surface all
```

See `SKILL.md` for full parameter reference.

### Manual (bash)

```bash
cd /path/to/worktree

export ROOT=$(pwd)
export RUN_ID=$(date +%Y%m%d-%H%M%S)
export RESULTS_DIR="$ROOT/qa/results/$RUN_ID"
export RESULTS_FILE="$RESULTS_DIR/results.jsonl"
export QA_ENV_FILE="$ROOT/qa/.env"
export QA_NETWORK="dopemux-qa-network"
export COMPOSE_PROJECT_NAME="dopemux-qa"

# QA port offsets
export QA_POSTGRES_PORT=5472    QA_REDIS_EVENTS_PORT=6419  QA_REDIS_PRIMARY_PORT=6420
export QA_CONPORT_HTTP_PORT=3044 QA_CONPORT_MCP_PORT=3045
export QA_PAL_PORT=3043         QA_LITELLM_PORT=4040       QA_DOPE_CONTEXT_PORT=3050
export QA_QDRANT_PORT=6373      QA_QDRANT_GRPC_PORT=6374   QA_LEANTIME_PORT=8120

mkdir -p "$RESULTS_DIR"
cp qa/.env.example qa/.env  # fill in API keys

trap 'bash "$ROOT/qa/scenarios/99_env_down.sh"' EXIT

for script in qa/scenarios/[0-9]*.sh; do
    timeout 300 bash "$script" || true
done
python3 qa/scenarios/20_cli_sweep.py
python3 qa/scenarios/80_docs_drift.py
```

See `runbook.md` for the full operator guide, troubleshooting, and safety rules.

---

## Scenario catalog

| Scenario | Validates | BETA-* IDs | Mutating? |
|----------|-----------|------------|-----------|
| `00_env_up.sh` | QA network + all services start healthy | BETA-INSTALL-02 | Yes — starts containers |
| `01_probe_entrypoints.sh` | `dopemux` CLI reachable; core subcommands in `--help` | BETA-CLI-01, BETA-CLI-02 | No |
| `10_install_gauntlet.sh` | Full fresh-install flow: network, boot, secrets, health | BETA-INSTALL-01–06 | Yes — installs into QA |
| `20_cli_sweep.py` | All subcommands, output formats, JSON flags | BETA-CLI-01, 02, 04, 05 | No |
| `30_mcp_roundtrips.sh` | ConPort MCP and PAL MCP round-trips | BETA-MCP-01, 02 | No |
| `40_multi_instance_collision.sh` | No Redis port collision across instances A–E + QA | BETA-MCP-03 | No |
| `50_hooks_lifecycle.sh` | SessionStart and PostToolUse hooks fire correctly | BETA-HOOK-01, 02 | No |
| `60_rte_routing_safety.sh` | SP fail-close at execution time; routing injection guards | BETA-RTE-01, 02 | No |
| `61_live_lane.sh` | Real end-to-end LLM call (gated: `DPMX_LIVE_OK=1`) | BETA-RTE-03 | No (read-only) |
| `70_pytest_lanes.sh` | Unit, integration, provider-modes, series-gate suites | BETA-TEST-01–03, 06 | No |
| `80_docs_drift.py` | Docs describe correct product; CLI help matches docs; MCP manifest matches runtime | BETA-DOCS-02, 05, 06 | No |
| `90_tui_renders.sh` | Dashboard renders; dx-clobber regression absent (#720) | BETA-UI-02, 03 | No |
| `99_env_down.sh` | QA stack torn down cleanly | (none) | Yes — stops containers |

**Mutating** means the scenario modifies Docker state (starts/stops containers or installs files). All mutations are scoped to the `dopemux-qa` compose project.

---

## Adding a new scenario

### Naming convention

Use the next available two-digit prefix in the appropriate group:
- `00–09`: environment lifecycle
- `10–19`: install / first-run
- `20–29`: CLI
- `30–39`: MCP
- `40–49`: multi-instance / isolation
- `50–59`: hooks
- `60–69`: RTE
- `70–79`: test suites
- `80–89`: docs / drift
- `90–98`: UI / TUI / web

### Bash scenario template

```bash
#!/usr/bin/env bash
# qa/scenarios/NN_my_scenario.sh
# Validates: <what this tests>
# BETA-* IDs: <backlog items>
set -euo pipefail
source "$(dirname "$0")/../lib/qa_common.sh"

guard_qa_project

scenario_start "my_scenario"

# Your assertions here:
assert_exit0 "dopemux does X" dopemux some-command --flag

emit_result "$CURRENT_SCENARIO" "PASS" "all assertions passed"
```

### Python scenario template

```python
#!/usr/bin/env python3
"""qa/scenarios/NN_my_scenario.py — Validates: <what this tests>"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from qa_common import scenario_start, emit_result, assert_exit0, guard_qa_project

guard_qa_project()
scenario_start("my_scenario")

# Your assertions here:
ok = assert_exit0("dopemux does X", ["dopemux", "some-command", "--flag"])

if ok:
    emit_result("my_scenario", "PASS", "all assertions passed")
```

### Register in backlog-map.yaml

Add an entry in `qa/backlog-map.yaml`:

```yaml
scenarios:
  my_scenario:
    - BETA-AREA-NN   # brief description of what this catches
```

### Checklist

- [ ] Script uses `guard_qa_project()` (or `guard_qa_project` in bash)
- [ ] All docker commands use `qa_docker_compose` wrapper (bash) or `COMPOSE_PROJECT_NAME=dopemux-qa`
- [ ] Every code path calls `emit_result` with `PASS`, `FAIL`, or `NOT_RUN`
- [ ] Script handles its own timeout gracefully (does not hang indefinitely)
- [ ] BETA-* IDs registered in `backlog-map.yaml`
- [ ] Scenario name in `emit_result` matches the key in `backlog-map.yaml`

---

## Baseline

### What it is

`qa/baseline/baseline.json` stores numeric signals and optional golden snapshots captured from a known-good HEAD. It acts as a regression oracle: if a signal degrades significantly relative to baseline, the comparison report flags it.

Signals captured:
- `conport_decision_count` — number of decisions in ConPort DB (should not decrease)
- `dope_context_search_relevance_avg` — average search relevance score
- `pytest_unit_pass_count` — unit tests passing (should not decrease)
- `pytest_unit_skip_count` — skipped tests (increase may indicate scope regression)
- `pytest_integration_pass_count` — integration tests passing
- `mcp_startup_time_s` — time for MCP services to reach healthy state
- `cli_help_commands_count` — number of subcommands in `dopemux --help` (should not decrease)
- `adhd_cognitive_load_avg` — average ADHD cognitive load score from engine

`golden_snapshots` are free-form string captures (e.g., `dopemux --help` output) stored for perceptual comparison.

### When to update

Update baseline:
- After a full clean run on a PR that you have manually verified is correct
- When deliberately raising the bar (e.g., new tests added, performance improved)

Do NOT update baseline:
- When there are known `FAIL` results
- To make a regression "disappear"

### How to update

```bash
# Via skill (safest — refuses to update if FAILs present):
qa-run --surface all --baseline

# Manual:
git rev-parse HEAD
# Verify zero FAIL lines:
grep '"status":"FAIL"' qa/results/<RUN_ID>/results.jsonl | wc -l  # should be 0

python3 qa/lib/qa_common.py update_baseline \
    qa/results/<RUN_ID>/results.jsonl \
    qa/baseline/baseline.json

git add qa/baseline/baseline.json
git commit -m "qa: update baseline to $(git rev-parse --short HEAD)"
```

The `head_sha` field in `baseline.json` records which commit the baseline was generated from. If a run's HEAD SHA differs, the report notes the gap.
