---
id: TRUTH_SCOPE
title: Truth Scope
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-07-01'
prelude: Truth Scope (reference) for dopemux documentation and developer workflows.
---
# TRUTH_SCOPE

Task packet: `DMX-CHATGPT-PROJECT-TRUTH-EXTRACTION-002`

Method:
- Repository truth only.
- Directly observed paths are cited explicitly.
- Inference is labeled.
- Unknown canonicality remains `UNKNOWN`.

## Classification Inventory

| System | Repo path(s) | Classification | Why in scope or not | Key evidence | Nearby related systems excluded or deprioritized |
| --- | --- | --- | --- | --- | --- |
| `dopemux core` | `/Users/hue/code/dopemux-mvp/src/dopemux`, `/Users/hue/code/dopemux-mvp/pyproject.toml` | Core Architectural Authority | Primary CLI/runtime package and operator entrypoint. | `pyproject.toml` declares `dopemux = "dopemux.cli:main"`. `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` is the active CLI surface. | `/Users/hue/code/dopemux-mvp/dopemux/__init__.py` is not sufficient evidence of active runtime authority. |
| `dopetask integration surface` | `/Users/hue/code/dopemux-mvp/scripts/dopetask`, `/Users/hue/code/dopemux-mvp/scripts/taskx`, `/Users/hue/code/dopemux-mvp/src/dopemux/commands/kernel_commands.py`, `/Users/hue/code/dopemux-mvp/.dopetask-pin` | Essential Operational Support | This is the actual task-runner bridge used by `dopemux kernel`. It affects runtime development workflow directly. | `scripts/dopetask` enforces `.dopetaskroot` and `.dopetask-pin`, installs pinned `dopetask`, and execs it. `scripts/taskx` is only a shim to `scripts/dopetask`. | `/Users/hue/code/dopemux-mvp/.taskxroot` and TaskX naming are deprioritized as legacy compatibility surfaces. |
| `dope-memory` | `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py`, `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/canonical_ledger.py`, `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/chronicle/store.py`, `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/chronicle/schema.sql` | Core Architectural Authority | Canonical durable work-log and memory retrieval surface for this repo slice. | `dope_memory_main.py` states it is the canonical entry point for Dope-Memory. `compose.yml` builds `dope-memory` from `services/working-memory-assistant/Dockerfile.dope-memory`. | `/Users/hue/code/dopemux-mvp/services/dope-memory/mcp_stdio_adapter.py` is deprioritized as stale adapter drift. |
| `working-memory-assistant` | `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/main.py`, `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/mcp/server.py` | Essential Operational Support | Distinct runtime from `dope-memory`; carries snapshot/recover and ADHD-facing support surfaces. Relevant to operational state, but not proven canonical for durable dope-memory writes. | `main.py` exposes `/snapshot`, `/recover`, `/adhd-*`, `/health`. `mcp/server.py` contains tool logic but no confirmed runnable MCP bootstrap. | `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py` remains the stronger authority for the `dope-memory` system itself. |
| `conport` | `/Users/hue/code/dopemux-mvp/src/conport/memory_server.py` | Core Architectural Authority | Active structured truth / knowledge graph / semantic memory surface. | `memory_server.py` instantiates `Server("conport-memory")`, registers MCP tools, and exposes HTTP endpoints in HTTP mode. | `/Users/hue/code/dopemux-mvp/services/dope-query` is deprioritized because it does not show an equivalent active runtime. |
| `dope-query` | `/Users/hue/code/dopemux-mvp/services/dope-query` | Drifted / Dead / Unclear | Evaluated because requested, but no active service/runtime authority was found. | Observed files are sparse, mainly `/Users/hue/code/dopemux-mvp/services/dope-query/auth/models.py` plus limited tests. No clear entrypoint or compose registration was found. | `/Users/hue/code/dopemux-mvp/src/conport` appears to have absorbed the active structured retrieval role. |
| `dope-context` | `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py`, `/Users/hue/code/dopemux-mvp/services/dope-context/Dockerfile`, `/Users/hue/code/dopemux-mvp/services/dope-context/tests` | Core Architectural Authority | Active code intelligence and hybrid search surface. | `Dockerfile` runs `python -m src.mcp.server`. `src/mcp/server.py` creates `FastMCP("dope-context")`. Tests assert deterministic hybrid ranking and contract schemas. | `/Users/hue/code/dopemux-mvp/mcp-proxy-config*.{json,yaml}` are support/config layers, not runtime authority. |
| `task-orchestrator` | `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app`, `/Users/hue/code/dopemux-mvp/services/task-orchestrator/mcp_stdio.py` | Core Architectural Authority | Active orchestration, workflow, coordination, and PM write surface. | `app/main.py` creates the FastAPI app and `FastMCP("Task-Orchestrator")`. `mcp_stdio.py` imports `mcp` from `app.main`. | `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py` is deprioritized as conflicting runtime drift. |
| `dopecon-bridge` | `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/main.py`, `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge` | Core Architectural Authority | Central proxy/coordination bridge between PM, ConPort, and event surfaces. | `routes.py` states the active bridge is adapter/proxy only and must not be canonical authority. `main.py` loads modular routers. | Older top-level endpoint files under `/Users/hue/code/dopemux-mvp/services/dopecon-bridge` are deprioritized where duplicated by `dopecon_bridge/routes.py`. |
| `ADHD engine / ADHD services` | `/Users/hue/code/dopemux-mvp/services/adhd_engine`, `/Users/hue/code/dopemux-mvp/services/adhd_engine/api/routes.py` | Essential Operational Support | Relevant to orchestration/context state and explicitly integrated with ConPort progress retrieval. | `main.py` provides FastAPI plus MCP tool fallback. `api/routes.py` exposes extensive `/api/v1/*` behavior. `activity_tracker.py` references `ConPortMCPClient.get_progress`. | `/Users/hue/code/dopemux-mvp/services/adhd-engine` is deprioritized as duplicate residue. Domain subapps under `/Users/hue/code/dopemux-mvp/services/adhd_engine/domains` are secondary unless directly invoked by current workflows. |
| `Serena surfaces` | `/Users/hue/code/dopemux-mvp/services/serena`, `/Users/hue/code/dopemux-mvp/docker/mcp-servers-source/serena`, `/Users/hue/code/dopemux-mvp/mcp-proxy-config*.{json,yaml}`, `/Users/hue/code/dopemux-mvp/src/dopemux/claude_config.py` | Essential Operational Support | Relevant code-intelligence/runtime-development surface, but canonical runtime is unresolved between in-repo implementation and Docker wrapper around external Serena. | `compose.yml` builds Serena from `/Users/hue/code/dopemux-mvp/docker/mcp-servers-source/serena`. `claude_config.py` maps `serena-v2`, `serena`, and `dopemux-serena` aliases. | `/Users/hue/code/dopemux-mvp/services/serena` is not excluded, but is not currently preferred as deployment authority. |
| `agents` | `/Users/hue/code/dopemux-mvp/services/agents`, `/Users/hue/code/dopemux-mvp/src/dopemux/agent_orchestrator.py`, `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/agents` | Secondary / Optional | Multiple agent families exist, but none show a single canonical operational authority for this packet. | `services/agents/README.md` says only MemoryAgent is implemented and multiple agents are pending. Separate orchestration code exists in `src/dopemux/agent_orchestrator.py` and task-orchestrator agent pool code. | No single agent family is excluded entirely, but this cluster should not be treated as stable authority without a separate canonicality pass. |
| `repo-truth-extractor` | `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor`, `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py`, `/Users/hue/code/dopemux-mvp/src/dopemux/commands/extractor_commands.py` | Core Architectural Authority | This is the active extraction/audit system the packet directly targets. | `src/dopemux/cli.py` registers `dopemux rte` as the canonical operator command family and labels `dopemux upgrades` as a legacy compatibility alias. `extractor_commands.py` resolves and executes `run_extraction_v5.py` through the shared command implementation. | `/Users/hue/code/dopemux-mvp/src/dopemux/extractor/runner.py`, `dopemux truth`, and `dopemux extractor` are deprioritized as legacy/refusal path drift. |
| `MCP / routing / model-provider surfaces` | `/Users/hue/code/dopemux-mvp/src/dopemux/routing_config.py`, `/Users/hue/code/dopemux-mvp/src/dopemux/litellm_proxy.py`, `/Users/hue/code/dopemux-mvp/src/dopemux/profile_models.py`, `/Users/hue/code/dopemux-mvp/src/dopemux/claude_config.py`, `/Users/hue/code/dopemux-mvp/mcp-proxy-config.json`, `/Users/hue/code/dopemux-mvp/mcp-proxy-config.yaml`, `/Users/hue/code/dopemux-mvp/mcp-proxy-config.copilot.yaml` | Essential Operational Support | These files determine effective tool/runtime routing for developer workflows and extractor execution. | `routing_config.py` validates provider/model/slot/fallback config. `mcp-proxy-config*` files enumerate MCP launch routes. | Profile files under `/Users/hue/code/dopemux-mvp/config/profiles` are related but secondary to the direct routing and proxy definitions above. |

## Scope Freeze Recommendation

Recommended project scope freeze for the ChatGPT Business Project truth pass:
- Include as authoritative build/runtime focus:
  - `/Users/hue/code/dopemux-mvp/src/dopemux`
  - `/Users/hue/code/dopemux-mvp/scripts/dopetask`
  - `/Users/hue/code/dopemux-mvp/src/conport`
  - `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py`
  - `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/chronicle`
  - `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp`
  - `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge`
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app`
  - `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor`
  - `/Users/hue/code/dopemux-mvp/services/adhd_engine`
  - `/Users/hue/code/dopemux-mvp/services/registry.yaml`
  - `/Users/hue/code/dopemux-mvp/compose.yml`
  - `/Users/hue/code/dopemux-mvp/src/dopemux/routing_config.py`
  - `/Users/hue/code/dopemux-mvp/src/dopemux/claude_config.py`
- Hold as non-canonical until resolved:
  - `/Users/hue/code/dopemux-mvp/services/dope-query`
  - `/Users/hue/code/dopemux-mvp/services/dope-memory/mcp_stdio_adapter.py`
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py`
  - `/Users/hue/code/dopemux-mvp/services/adhd-engine`
  - `/Users/hue/code/dopemux-mvp/services/serena`
  - `/Users/hue/code/dopemux-mvp/src/dopemux/extractor/runner.py`
  - `/Users/hue/code/dopemux-mvp/services/agents`

Reason for freeze:
- These paths contain the strongest observed runtime and contract authority.
- The held paths contain unresolved duplication, stale names, or contradictory entrypoints that would contaminate a canonical architecture document if treated as settled truth.
