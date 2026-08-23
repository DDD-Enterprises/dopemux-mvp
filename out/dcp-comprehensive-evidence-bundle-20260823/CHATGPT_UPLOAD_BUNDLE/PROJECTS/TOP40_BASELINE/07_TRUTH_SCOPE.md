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

Authority order note:
- Active Task Packets control scoped execution and allowlists for the current work slice.
- Runtime code, config, compose wiring, tests, and active entrypoints govern behavior claims.
- Truth-scope classifications describe repo truth as observed; they do not override runtime/source truth.
- Generated, advisory, extracted, exploratory, or external artifacts do not become source truth by being cited here.
- Unsupported or unresolved authority remains `UNKNOWN`.

## Classification Inventory

| System | Repo path(s) | Classification | Why in scope or not | Key evidence | Nearby related systems excluded or deprioritized |
| --- | --- | --- | --- | --- | --- |
| `dopemux core` | `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]` | Core Architectural Authority | Primary CLI/runtime package and operator entrypoint. | `pyproject.toml` declares `dopemux = "dopemux.cli:main"`. `[LOCAL_PATH_REDACTED]` is the active CLI surface. | `[LOCAL_PATH_REDACTED]` is not sufficient evidence of active runtime authority. |
| `dopetask integration surface` | `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]` | Essential Operational Support | This is the actual task-runner bridge used by `dopemux kernel`. It affects runtime development workflow directly. | `scripts/dopetask` enforces `.dopetaskroot` and `.dopetask-pin`, installs pinned `dopetask`, and execs it. `scripts/taskx` is only a shim to `scripts/dopetask`. | `[LOCAL_PATH_REDACTED]` and TaskX naming are deprioritized as legacy compatibility surfaces. |
| `dope-memory` | `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]` | Core Architectural Authority | Canonical durable work-log and memory retrieval surface for this repo slice. | `dope_memory_main.py` states it is the canonical entry point for Dope-Memory. `compose.yml` builds `dope-memory` from `services/working-memory-assistant/Dockerfile.dope-memory`. | `[LOCAL_PATH_REDACTED]` is deprioritized as stale adapter drift. |
| `working-memory-assistant` | `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]` | Essential Operational Support | Distinct runtime from `dope-memory`; carries snapshot/recover and ADHD-facing support surfaces. Relevant to operational state, but not proven canonical for durable dope-memory writes. | `main.py` exposes `/snapshot`, `/recover`, `/adhd-*`, `/health`. `mcp/server.py` contains tool logic but no confirmed runnable MCP bootstrap. | `[LOCAL_PATH_REDACTED]` remains the stronger authority for the `dope-memory` system itself. |
| `conport` | `[LOCAL_PATH_REDACTED]` | Core Architectural Authority | Active structured truth / knowledge graph / semantic memory surface. | `memory_server.py` instantiates `Server("conport-memory")`, registers MCP tools, and exposes HTTP endpoints in HTTP mode. | `[LOCAL_PATH_REDACTED]` is deprioritized because it does not show an equivalent active runtime. |
| `dope-query` | `[LOCAL_PATH_REDACTED]` | Drifted / Dead / Unclear | Evaluated because requested, but no active service/runtime authority was found. | Observed files are sparse, mainly `[LOCAL_PATH_REDACTED]` plus limited tests. No clear entrypoint or compose registration was found. | `[LOCAL_PATH_REDACTED]` appears to have absorbed the active structured retrieval role. |
| `dope-context` | `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]` | Core Architectural Authority | Active code intelligence and hybrid search surface. | `Dockerfile` runs `python -m src.mcp.server`. `src/mcp/server.py` creates `FastMCP("dope-context")`. Tests assert deterministic hybrid ranking and contract schemas. | `[LOCAL_PATH_REDACTED]` are support/config layers, not runtime authority. |
| `task-orchestrator` | `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]` | Core Architectural Authority | Active orchestration, workflow, coordination, and PM write surface. | `app/main.py` creates the FastAPI app and `FastMCP("Task-Orchestrator")`. `mcp_stdio.py` imports `mcp` from `app.main`. | `[LOCAL_PATH_REDACTED]` is deprioritized as conflicting runtime drift. |
| `dopecon-bridge` | `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]` | Core Architectural Authority | Central proxy/coordination bridge between PM, ConPort, and event surfaces. | `routes.py` states the active bridge is adapter/proxy only and must not be canonical authority. `main.py` loads modular routers. | Older top-level endpoint files under `[LOCAL_PATH_REDACTED]` are deprioritized where duplicated by `dopecon_bridge/routes.py`. |
| `ADHD engine / ADHD services` | `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]` | Essential Operational Support | Relevant to orchestration/context state and explicitly integrated with ConPort progress retrieval. | `main.py` provides FastAPI plus MCP tool fallback. `api/routes.py` exposes extensive `/api/v1/*` behavior. `activity_tracker.py` references `ConPortMCPClient.get_progress`. | `[LOCAL_PATH_REDACTED]` is deprioritized as duplicate residue. Domain subapps under `[LOCAL_PATH_REDACTED]` are secondary unless directly invoked by current workflows. |
| `Serena surfaces` | `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]` | Essential Operational Support | Relevant code-intelligence/runtime-development surface, but canonical runtime is unresolved between in-repo implementation and Docker wrapper around external Serena. | `compose.yml` builds Serena from `[LOCAL_PATH_REDACTED]`. `claude_config.py` maps `serena-v2`, `serena`, and `dopemux-serena` aliases. | `[LOCAL_PATH_REDACTED]` is not excluded, but is not currently preferred as deployment authority. |
| `agents` | `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]` | Secondary / Optional | Multiple agent families exist, but none show a single canonical operational authority for this packet. | `services/agents/README.md` says only MemoryAgent is implemented and multiple agents are pending. Separate orchestration code exists in `src/dopemux/agent_orchestrator.py` and task-orchestrator agent pool code. | No single agent family is excluded entirely, but this cluster should not be treated as stable authority without a separate canonicality pass. |
| `repo-truth-extractor` | `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]` | Core Architectural Authority | This is the active extraction/audit system the packet directly targets. | `src/dopemux/cli.py` registers `dopemux rte` as the canonical operator command family and labels `dopemux upgrades` as a legacy compatibility alias. `extractor_commands.py` resolves and executes `run_extraction_v5.py` through the shared command implementation. | `[LOCAL_PATH_REDACTED]`, `dopemux truth`, and `dopemux extractor` are deprioritized as legacy/refusal path drift. |
| `MCP / routing / model-provider surfaces` | `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]` | Essential Operational Support | These files determine effective tool/runtime routing for developer workflows and extractor execution. | `routing_config.py` validates provider/model/slot/fallback config. `mcp-proxy-config*` files enumerate MCP launch routes. | Profile files under `[LOCAL_PATH_REDACTED]` are related but secondary to the direct routing and proxy definitions above. |

## Scope Freeze Recommendation

Recommended project scope freeze for the ChatGPT Business Project truth pass:
- Include as authoritative build/runtime focus:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
- Hold as non-canonical until resolved:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`

Reason for freeze:
- These paths contain the strongest observed runtime and contract authority.
- The held paths contain unresolved duplication, stale names, or contradictory entrypoints that would contaminate a canonical architecture document if treated as settled truth.
