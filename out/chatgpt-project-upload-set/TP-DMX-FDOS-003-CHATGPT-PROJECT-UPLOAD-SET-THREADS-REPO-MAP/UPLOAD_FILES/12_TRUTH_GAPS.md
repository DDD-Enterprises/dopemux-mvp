---
id: TRUTH_GAPS
title: Truth Gaps
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-07-01'
prelude: Truth Gaps (reference) for dopemux documentation and developer workflows.
---
# TRUTH_GAPS

Method:
- Drift and risk items are grouped by category.
- Each item cites exact repo paths.
- No destructive commands were used in this pass.

## Boundary Violations

- `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/routes.py`
  - Observed contract says bridge must not be canonical task, workflow, decision, or progress authority.
  - Risk:
    - downstream operators may still treat bridge endpoints as authoritative because they expose `/kg/*`, `/ddg/*`, and PM routing surfaces.
- `/Users/hue/code/dopemux-mvp/src/dopemux/pm/writes.py`
  - Observed authority split across Leantime, task-orchestrator, ConPort, and dope-memory mirror receipts.
  - Risk:
    - any service that begins owning more than its declared slice will create silent contract drift.

## Duplicate Responsibilities

- `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py`
- `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/main.py`
- `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/mcp/server.py`
  - Multiple memory-related surfaces exist with overlapping names but different transport/runtime status.
- `/Users/hue/code/dopemux-mvp/services/serena`
- `/Users/hue/code/dopemux-mvp/docker/mcp-servers-source/serena`
  - Serena implementation and deployment surfaces overlap without a single declared canonical writer/runtime.
- `/Users/hue/code/dopemux-mvp/services/agents`
- `/Users/hue/code/dopemux-mvp/src/dopemux/agent_orchestrator.py`
- `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/agents`
  - Agent responsibilities are duplicated across at least three families.

## Unresolved Canonicality

- `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py`
- `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py`
- `/Users/hue/code/dopemux-mvp/services/task-orchestrator/Dockerfile`
  - Runtime authority points in conflicting directions.
- `/Users/hue/code/dopemux-mvp/services/serena`
- `/Users/hue/code/dopemux-mvp/docker/mcp-servers-source/serena`
  - Canonical Serena surface remains `UNKNOWN`.
- `/Users/hue/code/dopemux-mvp/services/dope-query`
- `/Users/hue/code/dopemux-mvp/src/conport/memory_server.py`
  - Naming suggests related retrieval families, but only ConPort shows active authority.

## Naming Ambiguity

- `/Users/hue/code/dopemux-mvp/scripts/dopetask`
- `/Users/hue/code/dopemux-mvp/scripts/taskx`
- `/Users/hue/code/dopemux-mvp/src/dopemux/commands/kernel_commands.py`
- `/Users/hue/code/dopemux-mvp/tests/unit/test_cli_kernel_commands.py`
  - Runtime is `dopetask`; operator language still says TaskX in code and tests.
- `/Users/hue/code/dopemux-mvp/services/adhd_engine`
- `/Users/hue/code/dopemux-mvp/services/adhd-engine`
  - Hyphen/underscore duplicate family.
- `/Users/hue/code/dopemux-mvp/src/dopemux/claude_config.py`
  - Maps `serena-v2`, `serena`, and `dopemux-serena`, indicating ongoing alias sprawl.

## Interface Inconsistency

- `/Users/hue/code/dopemux-mvp/mcp-proxy-config.json`
- `/Users/hue/code/dopemux-mvp/mcp-proxy-config.yaml`
- `/Users/hue/code/dopemux-mvp/mcp-proxy-config.copilot.yaml`
  - Observed inconsistent launch methods and endpoint assumptions for Serena and Dope-Context.
- `/Users/hue/code/dopemux-mvp/services/dope-memory/mcp_stdio_adapter.py`
- `/Users/hue/code/dopemux-mvp/services/registry.yaml`
- `/Users/hue/code/dopemux-mvp/compose.yml`
  - Dope-memory adapter uses `8096`, while registry and compose use `3020`.
- `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py`
- `/Users/hue/code/dopemux-mvp/src/dopemux/commands/extractor_commands.py`
  - `truth` shortcut and `extractor/upgrades` commands lead to different extraction engines.

## Dead / Stub / Hard-Failing Paths

- `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py`
  - Hard-fails and says not to use it as runtime authority.
- `/Users/hue/code/dopemux-mvp/services/dope-memory/mcp_stdio_adapter.py`
  - Likely stale because its target port does not match observed runtime config.
- `/Users/hue/code/dopemux-mvp/services/dope-query`
  - No active runtime entrypoint found in this pass.
- `/Users/hue/code/dopemux-mvp/mcp-proxy-config*.{json,yaml}`
  - Refer to missing `/Users/hue/code/dopemux-mvp/services/dope-context/run_mcp.sh`.

## Docs vs Repo Risk

- `/Users/hue/code/dopemux-mvp/README.md`
- `/Users/hue/code/dopemux-mvp/.dopetask-pin`
- `/Users/hue/code/dopemux-mvp/pyproject.toml`
  - README mentions `dopetask==0.2.0`; repo pin and dependency declarations show `0.5.1`.
- `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py`
  - `dopemux rte` is the canonical operator command family, `dopemux upgrades` is a legacy compatibility alias, and `dopemux truth` now refuses with guidance to use `dopemux rte`.
- RTE operator docs
  - Older docs may still carry stale command examples; current docs should classify `dopemux upgrades`, `dopemux extractor`, `dopemux truth`, direct runner calls, and legacy scan paths according to runtime evidence.
- `/Users/hue/code/dopemux-mvp/services/registry.yaml`
- `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py`
  - Registry and runtime module disagree on task-orchestrator port.

## Drift in Operator / Dev Workflow Surfaces

- `/Users/hue/code/dopemux-mvp/src/dopemux/commands/kernel_commands.py`
- `/Users/hue/code/dopemux-mvp/scripts/taskx`
- `/Users/hue/code/dopemux-mvp/scripts/dopetask`
  - Developer workflow branding and actual runtime diverge.
- `/Users/hue/code/dopemux-mvp/mcp-proxy-config*.{json,yaml}`
- `/Users/hue/code/dopemux-mvp/compose.yml`
- `/Users/hue/code/dopemux-mvp/services/registry.yaml`
  - MCP/operator launch surfaces are not aligned on actual service entrypoints.
- `/Users/hue/code/dopemux-mvp/src/dopemux/routing_config.py`
- `/Users/hue/code/dopemux-mvp/src/dopemux/profile_models.py`
- `/Users/hue/code/dopemux-mvp/src/dopemux/claude_config.py`
  - Provider/model/server naming and aliasing appear broader than the currently consistent runtime set.

## Commands Used

- `pwd`
- `find . -maxdepth 2 -type d | sort`
- `rg --files ...`
- `rg -n ...`
- `sed -n 'start,endp' ...`
- `ls -la ...`
- `ls -l scripts/taskx scripts/dopetask .dopetaskroot .taskxroot`
- `cat .dopetask-pin`
- `find services/dope-query -maxdepth 3 -type f | sort`
- `mkdir -p /Users/hue/code/dopemux-mvp/tmp/dmx-chatgpt-project-truth-extraction-002`

Validation note:
- This pass validated by repository inspection and artifact review only.
- No destructive commands were run.
- No commits were created.
