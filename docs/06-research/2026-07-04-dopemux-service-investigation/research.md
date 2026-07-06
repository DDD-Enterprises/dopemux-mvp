---
id: research
title: Research
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Research (reference) for dopemux documentation and developer workflows.
---
# Exhaustive Dopemux Service Investigation

Date: 2026-07-04
Task Packet: `TP-DMX-SERVICE-INVESTIGATION-20260704`
Worktree: `<repo-root>/.worktrees/dopemux-service-investigation-20260704` (see `git worktree list`)
Branch: `codex/dopemux-service-investigation-20260704`

## Executive Summary

This audit inspected the live repo shape, not only the curated service catalog. The observed service surface is larger than the Tier 1-4 catalog summary:

- OBSERVED: `42` tracked top-level `services/*` directories exist in git (`git ls-tree -d --name-only HEAD services/`), including non-service artifacts such as `services/.claude`.
- OBSERVED: `24` services are declared in `compose.yml`.
- OBSERVED: `21` service rows exist in `services/registry.yaml`.
- OBSERVED: `SERVICE_CATALOG.md` already separates canonical systems from support, adapter, duplicate, legacy, drifted, and unknown surfaces.

The strongest current architecture remains a multi-plane control stack, not a unified platform. `dopemux` is the operator control surface, Task Orchestrator owns workflow transitions, ConPort owns structured decisions/progress/context, dope-memory owns chronicle receipts, dope-context owns code/docs retrieval, dopecon-bridge is transport/proxy, ADHD Engine is operator support, and Serena is code-intelligence/F001 detection support.

## Authority Used

- OBSERVED: `AGENTS.md` defines repo truth order, worktree/Task Packet requirements, PAL chain expectations, proof requirements, and the rule that ADHD Engine is support only.
- OBSERVED: `PROJECT.md`, `ARCHITECTURE.md`, `PM_PLANE.md`, and `SERVICE_CATALOG.md` describe the current split architecture and known drift.
- OBSERVED: `compose.yml` is marked the canonical Docker Compose entrypoint and declares the active service stack.
- OBSERVED: `services/registry.yaml` lists service health and port metadata for the registered operational set.
- OBSERVED: `services/serena/mcp_server.py`, `services/serena/untracked_work_detector.py`, `services/adhd_engine/main.py`, `services/adhd_engine/api/routes.py`, `src/dopemux/commands/mcp_commands.py`, and `src/dopemux/ui/cockpit/*` are runtime/code evidence for the key deep-dive flows.

## Inventory Counts

OBSERVED from live tree/config:

```text
top-level services directories: 42
compose services: 24
registry services: 21
```

Top-level `services/*` candidates observed:

```text
.claude, activity-capture, adhd-dashboard, adhd-engine,
adhd-notifier, adhd_engine, adhd_notifier, agents, claude_brain,
complexity_coordinator, conport_kg, conport_kg_ui, copilot_transcript_ingester,
dcp-readonly-facade, dddpg, dope-context, dope-memory, dope-query,
dopecon-bridge, dopemux-gpt-researcher, intelligence, mcp-capture,
mcp-client, mcp-integration-bridge, ml-predictions, ml-risk-assessment,
monitoring, monitoring-dashboard, repo-truth-extractor, router, serena,
session-intelligence, session-manager, session_intelligence, shared,
slack-integration, task-orchestrator, task-router, voice-commands,
webhook_receiver, working-memory-assistant, workspace-watcher
```

Compose services observed:

```text
adhd-engine, conport, desktop-commander, dope-context, dope-memory,
dopecon-bridge, exa, gptr-mcp, leantime, leantime-bridge, litellm,
mcp-qdrant, mysql_leantime, pal, pal-stdio, postgres, redis-events,
redis-primary, redis-ui, redis_leantime, serena, task-orchestrator,
webhook-poller, webhook-receiver
```

Registry services observed:

```text
postgres, redis-events, redis-primary, qdrant, dopecon-bridge,
dopecon-bridge-alt, pal, conport-http, conport-mcp, serena, gpt-researcher,
dope-context, exa, desktop-commander, task-orchestrator, leantime-bridge,
dope-memory, adhd-engine, leantime, webhook-receiver, litellm
```

## Key Findings

### 1. The service surface is broad, but the active spine is narrower.

OBSERVED: `compose.yml` wires 24 active runtime/container services. `services/registry.yaml` registers 21 health/port rows. Many `services/*` directories are implementation libraries, duplicates, old experiments, support services, or unwired adjacent surfaces.

INFERRED: Operational UX should not show every directory as an equally actionable service. It should show a layered inventory: active stack, registered but indirect services, source-only support surfaces, and drift/unknown candidates.

### 2. Serena F001 Enhanced exists in code but is not exposed as an MCP tool.

OBSERVED: `services/serena/mcp_server.py` implements `detect_untracked_work_enhanced_tool()` around lines where the method is defined.

OBSERVED: The MCP `list_tools()` registration includes `detect_untracked_work`, `track_untracked_work`, `snooze_untracked_work`, `ignore_untracked_work`, config tools, and analytics tools, but no `detect_untracked_work_enhanced` tool name.

OBSERVED: The `call_tool()` dispatch chain routes `detect_untracked_work` but does not route `detect_untracked_work_enhanced`.

CONCLUSION: The enhanced E1-E4 detection path is present but not currently callable through Serena MCP by name. The current callable path is the base `detect_untracked_work` tool.

### 3. Serena F001 storage/action paths are ConPort-shaped but need contract hardening.

OBSERVED: `services/serena/untracked_work_storage.py` stores category `untracked_work` through `conport_client.log_custom_data(...)` and reads via `get_custom_data(...)`.

OBSERVED: `track_untracked_work_tool()` in `services/serena/mcp_server.py` creates progress-like records and links in `untracked_work_links`.

OBSERVED: `FalseStartsAggregator`, `PriorityContextBuilder`, and metrics helpers tolerate missing ConPort clients and return empty/mock-like views.

INFERRED: The fallback behavior is useful for non-blocking UX but currently risks looking healthier than reality unless surfaced as degraded/unknown in Cockpit and dashboard.

### 4. ADHD Engine is active support runtime, not a PM or memory authority.

OBSERVED: `services/adhd_engine/main.py` creates the FastAPI app, mounts FastMCP under `/mcp`, and includes `/api/v1` routes.

OBSERVED: `services/adhd_engine/api/routes.py` exposes state, assessment, break, activity, hook, WebSocket, and trust/customization surfaces.

OBSERVED: Event handling spans Redis stream `dopemux:events`, `event_emitter.py`, `event_listener.py`, `workspace_watcher.py`, dashboard backend, and activity-capture. Startup of some pieces is conditional/degraded.

CONCLUSION: ADHD Engine can produce cognitive state and recommendation signals. It should not directly create PM truth. It should emit support signals, and Task Orchestrator/ConPort should own workflow/progress effects.

### 5. Cockpit currently emphasizes deterministic visibility and guarded actions.

OBSERVED: `src/dopemux/ui/cockpit/render_modes.py` renders PM, Implementer, Overview, Services, and Events modes as deterministic/no-write surfaces.

OBSERVED: `src/dopemux/ui/cockpit/runtime_contract.py` models command palette, safe action gates, settings/admin/runtime, and unknown-drift queues.

OBSERVED: No inspected Cockpit path directly consumes Serena F001 or ADHD Engine live state. Dashboard frontend and ADHD dashboard backend are separate surfaces.

CONCLUSION: Cockpit is the right home for service/F001 visibility, but a separate data-source integration packet is needed before claiming live F001/ADHD surfacing.

### 6. Several service families have naming or deployment drift.

OBSERVED examples:

- `services/adhd_engine` is active; `services/adhd-engine` is duplicate residue.
- `services/adhd-notifier` exists; `services/adhd_notifier` is only a small Python package-like duplicate.
- `services/session-intelligence` and `services/session_intelligence` both exist.
- `services/serena` contains substantial code, while compose builds from `docker/mcp-servers/serena/Dockerfile`.
- `dope-memory` compose runtime points at `services/working-memory-assistant/Dockerfile.dope-memory`, while `services/dope-memory` contains only an MCP stdio adapter.

CONCLUSION: The UX needs a naming reconciliation layer that names canonical runtime, source-only support tree, and duplicates separately.

## Risk List

- HIGH: Showing directory presence as service health would mislead operators.
- HIGH: Exposing F001 Enhanced UX before registering/dispatching the MCP tool would create a false affordance.
- HIGH: Treating ADHD Engine activity/hook state as durable PM truth would violate architecture boundaries.
- MEDIUM: Mock/fallback dashboard behavior can appear healthy unless degraded provenance is visible.
- MEDIUM: Compose and registry do not cover all source-only service families, so "all services" needs a multi-layer inventory model.
- MEDIUM: `docker compose -f compose.yml config` renders sensitive-looking environment values from the local compose configuration. Raw config output should not be copied into reports or UX receipts.
- MEDIUM: Large service test suites may fail for environment/dependency reasons unrelated to this docs-only audit.
- LOW: Some adjacent service docs are stale and may overclaim production readiness compared with current runtime wiring.

## Validation Ledger

PASS:

- `python -m json.tool task-packets/TP-DMX-SERVICE-INVESTIGATION-20260704.json >/dev/null` exited `0`.
- `python - <<'PY' ... jsonschema.validate(...) ... PY` exited `0`.
- `docker compose -f compose.yml config` exited `0`. Raw output is not reproduced because it rendered sensitive-looking environment values from local compose configuration.
- `dopemux mcp status` exited `0`. It reported the already-running Dopemux containers, including healthy ConPort, Serena, dope-context, dope-memory, dopecon-bridge, Task Orchestrator, Leantime, PAL, Exa, desktop-commander, Redis, Postgres, and Qdrant surfaces, plus an unhealthy LiteLLM container.
- `pytest -q tests/mcp tests/unit/dopemux/ui/cockpit` exited `0` with `183` passing tests.

FAIL:

- `pytest -q services/serena/test_f001_enhanced.py services/serena/tests/test_mcp_server_local.py` exited `3` during collection. Key output: `Import failed: No module named 'untracked_work_detector'`, then `SystemExit: 1` from `services/serena/test_f001_enhanced.py`.
- `pytest -q services/adhd_engine/tests tests/unit/test_adhd_*.py` exited `2` during collection. Key output: missing modules including `services.adhd_engine.attention_calibrator`, `ml`, `adhd_engine.feature_flags`, and `services.adhd_engine.voice_assistant`.

NOT_RUN:

- `pnpm --dir ui-dashboard test` was not run because `ui-dashboard/node_modules` is missing in this worktree. The guard command exited `125` with `NOT_RUN: ui-dashboard/node_modules missing`.
- Live health probes beyond the already-running `dopemux mcp status` container view were not run because this audit did not authorize starting stopped services or mutating runtime state.

PENDING:

- `git diff --check` runs at precommit after final report edits.
