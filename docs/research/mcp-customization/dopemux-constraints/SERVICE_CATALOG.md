---
id: SERVICE_CATALOG
title: Service Catalog
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-07'
last_review: '2026-05-07'
next_review: '2026-08-05'
prelude: Service Catalog (explanation) for dopemux documentation and developer workflows.
---
# SERVICE_CATALOG

## 1. Purpose

This is a repo-truth catalog of service surfaces in this repository.

It is broader than the `SYSTEM_*` layer.

It does not promote every service to canonical architectural status.

## 2. Classification Model

Service tiers used in this catalog:

- Tier 1: Canonical system docs already exist
- Tier 2: Active operational/support services that matter but do not deserve full SYSTEM docs yet
- Tier 3: Adapters, wrappers, or compatibility surfaces
- Tier 4: Experimental, duplicate, drifted, or legacy surfaces

Service status labels used here:

- `active`
- `active-but-drifted`
- `support`
- `proxy/adapter`
- `duplicate`
- `legacy`
- `unknown`

Tiering is based on current runtime evidence from `compose.yml`, `docker/compose.core.yml`, `services/registry.yaml`, current runtime entrypoints, and the accepted system docs. Directory presence alone is not enough.

Tier 2 may include external systems that are operationally important to the repo, even if their runtime is not primarily implemented in this repository.

## 3. Tier 1 Services

- `dopemux`
  - Role: operator CLI and control surface for startup, routing, MCP coordination, and downstream delegation.
  - Canonical doc path: `/Users/hue/code/dopemux-mvp/docs/03-reference/systems/dopemux/system-dopemux.md`
- `dopetask`
  - Role: external execution runtime reached through `scripts/dopetask`; `scripts/taskx` is only a compatibility shim.
  - Canonical doc path: `/Users/hue/code/dopemux-mvp/docs/03-reference/systems/dopetask/system-dopetask.md`
- `task-orchestrator`
  - Role: workflow coordination and workflow-significant PM transition surface.
  - Canonical doc path: `/Users/hue/code/dopemux-mvp/docs/03-reference/systems/task-orchestrator/system-taskorchestrator.md`
- `ConPort`
  - Role: structured context, decision, progress, and semantic retrieval surface.
  - Canonical doc path: `/Users/hue/code/dopemux-mvp/docs/03-reference/systems/conport/system-conport.md`
- `dope-memory`
  - Role: durable chronicle and evidence-preserving memory sink.
  - Canonical doc path: `/Users/hue/code/dopemux-mvp/docs/03-reference/systems/dope-memory/system-dopememory.md`
- `dope-context`
  - Role: deterministic code/docs indexing and retrieval surface.
  - Canonical doc path: `/Users/hue/code/dopemux-mvp/docs/03-reference/systems/dope-context/system-dopecontext.md`
- `dopecon-bridge`
  - Role: bridge, proxy, event transport, and compatibility routing surface.
  - Canonical doc path: `/Users/hue/code/dopemux-mvp/docs/03-reference/systems/dopecon-bridge/system-dopeconbridge.md`
- `ADHD Engine`
  - Role: operator-support and cognitive-state service with HTTP, MCP, and event surfaces.
  - Canonical doc path: `/Users/hue/code/dopemux-mvp/docs/03-reference/systems/adhd-engine/system-adhdengine.md`
- `Repo Truth Extractor`
  - Role: canonical extraction and audit runtime for repo-truth artifacts.
  - Canonical doc path: `/Users/hue/code/dopemux-mvp/docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md`

## 4. Tier 2 Services

- `Leantime`
  - Path: `/Users/hue/code/dopemux-mvp/compose.yml` and `/Users/hue/code/dopemux-mvp/docker/leantime/`
  - Short role: PM application used for passive PM metadata and project/ticket snapshot surfaces.
  - Why Tier 2 and not Tier 1: it is operationally important and repeatedly referenced in the PM plane, but it is an external PM application wired into the stack rather than a repo-owned architectural runtime with a dedicated current `SYSTEM_*` doc.
  - Status label: `active`

- `working-memory-assistant`
  - Path: `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/main.py`
  - Short role: snapshot/recovery and ADHD-adjacent memory support runtime separate from the canonical `dope-memory` HTTP entrypoint.
  - Why Tier 2 and not Tier 1: runtime code exists and truth docs treat it as a real support surface, but current authority docs do not prove it as canonical durable memory authority.
  - Status label: `support`

- `Serena`
  - Path: `/Users/hue/code/dopemux-mvp/compose.yml`, `/Users/hue/code/dopemux-mvp/docker/mcp-servers/serena/`, and `/Users/hue/code/dopemux-mvp/services/serena/`
  - Short role: code-intelligence / MCP support surface used in the broader developer workflow and referenced by PM read paths for technical context.
  - Why Tier 2 and not Tier 1: it matters operationally and is wired in compose and registry, but canonical runtime authority remains unresolved between the Docker wrapper and the in-repo implementation.
  - Status label: `active-but-drifted`

- `LiteLLM`
  - Path: `/Users/hue/code/dopemux-mvp/compose.yml`, `/Users/hue/code/dopemux-mvp/services/registry.yaml`, and `/Users/hue/code/dopemux-mvp/docker/mcp-servers/litellm/`
  - Short role: model-routing proxy for the multi-provider control stack.
  - Why Tier 2 and not Tier 1: it is active infrastructure in the compose stack and affects operator workflows, but it is support infrastructure rather than a repo-owned canonical system of record.
  - Status label: `support`

- `webhook-receiver`
  - Path: `/Users/hue/code/dopemux-mvp/services/webhook_receiver/` and `/Users/hue/code/dopemux-mvp/compose.yml`
  - Short role: OpenAI-first webhook sidecar with provider event ledger and optional poller-based completion harvesting.
  - Why Tier 2 and not Tier 1: current compose wiring and README show a real operational sidecar, but it is an ancillary integration service rather than part of the repo’s architectural spine.
  - Status label: `support`

## 5. Tier 3 Services

- `leantime-bridge`
  - Path: `/Users/hue/code/dopemux-mvp/docker/mcp-servers/leantime-bridge/`
  - Role: MCP and REST compatibility bridge for Leantime task/project operations.
  - What upstream authority it depends on: Leantime for PM metadata and ticket/project truth.
  - Status label: `proxy/adapter`

- `PAL`
  - Path: `/Users/hue/code/dopemux-mvp/docker/mcp-servers/pal/`
  - Role: multi-model reasoning MCP server used as an auxiliary tool surface.
  - What upstream authority it depends on: external model providers and its own MCP tool runtime; it is not a domain authority for repo PM, memory, retrieval, or workflow state.
  - Status label: `proxy/adapter`

- `webhook-poller`
  - Path: `/Users/hue/code/dopemux-mvp/services/webhook_receiver/poller.py` via `/Users/hue/code/dopemux-mvp/compose.yml`
  - Role: background poller for `xai` and `gemini` async job completion events.
  - What upstream authority it depends on: `webhook-receiver` ledger tables and provider APIs.
  - Status label: `proxy/adapter`

- `mcp-client`
  - Path: `/Users/hue/code/dopemux-mvp/services/mcp-client/main.py`
  - Role: utility MCP client that can connect over stdio or HTTP and invoke tools.
  - What upstream authority it depends on: whichever MCP servers it is configured to call; it owns no domain truth.
  - Status label: `proxy/adapter`

## 6. Tier 4 Services

- `services/dope-query`
  - Path: `/Users/hue/code/dopemux-mvp/services/dope-query`
  - Why it is not trustworthy as a primary runtime: current passes found sparse files, no clear runtime entrypoint, and no compose or registry authority, while ConPort shows the active structured retrieval surface.
  - Classification: `legacy`

- `task-orchestrator legacy runtime path`
  - Path: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py`
  - Why it is not trustworthy as a primary runtime: the file hard-fails and says it is no longer the supported runtime, while the Dockerfile and registry/compose still create runtime confusion around it.
  - Classification: `active-but-drifted`

- `services/adhd-engine`
  - Path: `/Users/hue/code/dopemux-mvp/services/adhd-engine`
  - Why it is not trustworthy as a primary runtime: current compose wiring and truth docs point to `/services/adhd_engine`; the hyphenated tree appears to be duplicate residue.
  - Classification: `duplicate`

- `services/serena`
  - Path: `/Users/hue/code/dopemux-mvp/services/serena`
  - Why it is not trustworthy as a primary runtime: there is substantial implementation code here, but current compose runtime leans toward the Docker wrapper, so the in-repo service tree is not proven deployment authority.
  - Classification: `unknown`

- `services/dopemux-gpt-researcher`
  - Path: `/Users/hue/code/dopemux-mvp/services/dopemux-gpt-researcher`
  - Why it is not trustworthy as a primary runtime: the repo contains a research API implementation, but current compose wires `gptr-mcp` from `docker/mcp-servers/gptr-mcp` instead of this service tree.
  - Classification: `active-but-drifted`

- `services/task-router`
  - Path: `/Users/hue/code/dopemux-mvp/services/task-router`
  - Why it is not trustworthy as a primary runtime: the repo contains a named service family, but current compose, registry, and system docs do not establish it as an active runtime authority.
  - Classification: `unknown`

- `services/taskmaster`
  - Path: `/Users/hue/code/dopemux-mvp/services/taskmaster`
  - Why it is not trustworthy as a primary runtime: PM-plane docs reference taskmaster-related surfaces, but it is not part of the current canonical system set and is not wired into current compose or registry authority.
  - Classification: `legacy`

- `services/conport_kg` and `services/conport_kg_ui`
  - Path: `/Users/hue/code/dopemux-mvp/services/conport_kg` and `/Users/hue/code/dopemux-mvp/services/conport_kg_ui`
  - Why they are not trustworthy as primary runtimes: they overlap the ConPort naming family, but current system docs and compose authority point to ConPort itself, not these adjacent trees.
  - Classification: `unknown`

- `activity-capture`
  - Path: `/Users/hue/code/dopemux-mvp/services/activity-capture`
  - Why it is not trustworthy as a primary runtime: executable code exists, but current compose and registry do not place it in the active runtime spine.
  - Classification: `unknown`

- `workspace-watcher`
  - Path: `/Users/hue/code/dopemux-mvp/services/workspace-watcher`
  - Why it is not trustworthy as a primary runtime: it is a real helper service with event emission logic, but current compose and registry do not treat it as part of the active service stack.
  - Classification: `unknown`

- `adhd-dashboard` and `adhd-notifier`
  - Path: `/Users/hue/code/dopemux-mvp/services/adhd-dashboard` and `/Users/hue/code/dopemux-mvp/services/adhd-notifier`
  - Why they are not trustworthy as primary runtimes: they are adjacent to the ADHD family, but current stack authority centers on `services/adhd_engine`, not these side surfaces.
  - Classification: `unknown`

- `session-manager`
  - Path: `/Users/hue/code/dopemux-mvp/services/session-manager`
  - Why it is not trustworthy as a primary runtime: the repo has a substantial local orchestrator/TUI implementation, but current system docs, compose, and registry do not establish it as a live canonical service surface.
  - Classification: `unknown`

## 7. Duplicate / Overlap Hotspots

- `dope-memory` vs `working-memory-assistant`
  - The canonical `dope-memory` runtime lives under the `working-memory-assistant` tree at `services/working-memory-assistant/dope_memory_main.py`, while `services/working-memory-assistant/main.py` is a separate operational support service. The tree layout invites false equivalence.

- ADHD Engine vs dopemux-side ADHD utilities
  - The active service runtime is `services/adhd_engine`, but `src/dopemux/adhd/*` also contains ADHD-related logic. Those dopemux-side utilities are not the ADHD Engine service runtime.

- task-orchestrator runtime path conflicts
  - `services/task-orchestrator/app/main.py` is the intended runtime authority, but `services/task-orchestrator/task_orchestrator/app.py` hard-fails while the Dockerfile still points into the legacy module path. Registry and compose also disagree with older `3014` assumptions.

- ConPort runtime/deployment splits
  - ConPort is canonical, but PM and bridge callers still split across `3004` and `3005` contracts. The runtime surface is active; the access pattern is not cleanly unified.

- Serena implementation vs deployment surface
  - The repo has a substantial `services/serena` tree, while current compose wiring points at the Docker wrapper under `docker/mcp-servers/serena/`. Runtime authority is not settled in one place.

- ADHD service naming family
  - `services/adhd_engine` is the active runtime family. `services/adhd-engine` is duplicate naming drift and should not be treated as a second canonical service.

- agent-family overlap
  - Agent responsibilities remain split across `services/agents`, `src/dopemux/agent_orchestrator.py`, and `services/task-orchestrator/task_orchestrator/agents`. That overlap matters operationally even though it is not a single catalog entry.

## 8. Promotion Rules

A Tier 2, Tier 3, or Tier 4 service should be promoted to a full `SYSTEM_*` doc only when one or more of these conditions is true:

- it becomes canonical for a real authority slice
- it becomes a critical runtime dependency in the default stack
- it becomes a recurring source of operator confusion or drift
- it is repeatedly referenced in `PROJECT.md`, `ARCHITECTURE.md`, `PM_PLANE.md`, or `AGENTS.md`
- its runtime path, contract surface, and deployment wiring are stable enough to describe without major `UNKNOWN`

Do not promote a service only because it exists in the tree, has a Dockerfile, or has old docs.

## 9. Working Rules

- Use `SYSTEM_*` docs first for Tier 1 systems.
- Do not assume all services deserve equal documentation weight.
- Do not confuse adapters with authorities.
- Preserve `UNKNOWN`, `active-but-drifted`, and duplicate classifications where runtime evidence does not settle them.
- Use this catalog to decide whether a service needs deeper documentation or should stay catalog-only.
