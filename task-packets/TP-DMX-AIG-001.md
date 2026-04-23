---
id: TP-DMX-AIG-001
title: Tp Dmx Aig 001
type: explanation
owner: '@codex'
author: '@codex'
date: '2026-04-22'
status: ready
last_review: '2026-04-22'
next_review: '2026-07-21'
prelude: TP-DMX-AIG-001 establishes the repo-truth service census and ingress map for the adaptive ingress plane program without implementing gateway code or collapsing backend authorities.
---
# TP-DMX-AIG-001

## Governing Decision Artifacts

This packet is governed by these repo-stable decision artifact paths first:

- `docs/03-reference/architecture/dopemux-multi-agent-ingress-architecture.md`
- `docs/03-reference/governance/adr-dopemux-adaptive-ingress-plane.md`
- `docs/03-reference/architecture/codex-tp-revision-notes.md`

Applied revisions from the TP notes:

- Internalize non-authoritative adapters behind a gateway only where parity, ownership clarity, and rollback exist.
- Proposed gateway file paths are advisory only and are not adopted in this packet.
- Gateway success is not authoritative success.
- The gateway may coordinate execution handoff but does not own dopetask runtime truth.
- Serena-facing surfaces are not consolidated here because runtime authority is not frozen.

## Scope

In scope:

- Repo-wide service census for ingress-relevant and authority-relevant systems
- Ingress/control surface map across operator CLI, MCP/proxy config, HTTP, stdio, wrappers, and shims
- Keep / candidate-for-internalization / registry-only / deprecate matrix for currently visible surfaces
- First-safe-slice confirmation for the next implementation packet boundary
- Evidence ledger with exact file paths

Out of scope:

- Gateway implementation
- Route rewrites
- Service consolidation
- Serena de-duplication
- Existing TP series edits beyond creating this packet and indexing it

## Invariants

- Canonical backend authorities remain separate from the proposed ingress plane.
- Unresolved authority is marked `UNKNOWN`, not normalized away.
- Gateway coordination is not treated as authoritative success.
- Dopetask runtime truth remains at the observed wrapper/runtime boundary, not in any gateway.
- Dopecon-bridge, mcp-proxy configs, wrappers, aliases, and shims are not upgraded to authority by exposure alone.

## 1. Service Census

| Service / Surface | Tier | Role | Authority Slice | Merge Policy | Agent-Facing Relevance | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `src/dopemux` / `dopemux` CLI | Tier 0 operator control | Operator entrypoint, config, launch, MCP wiring | Control-plane only; not PM/memory/retrieval/execution authority | `keep` | High | `pyproject.toml`, `src/dopemux/cli.py`, `PROJECT.md`, `TRUTH_CANONICALS.md` |
| `scripts/dopetask` | Tier 0 execution handoff | Canonical local wrapper into external `dopetask` runtime | Execution handoff/runtime truth in repo-owned path | `keep` | High | `scripts/dopetask`, `TRUTH_CANONICALS.md` |
| `scripts/taskx` | Tier 0 compatibility alias | Shim alias to `scripts/dopetask` | No independent authority | `registry-only` | Medium | `scripts/taskx`, `TRUTH_CANONICALS.md`, `TRUTH_GAPS.md` |
| `services/task-orchestrator/app/main.py` | Tier 1 canonical backend candidate | Workflow coordination, PM transition serving, MCP tools | Workflow-significant transitions; HTTP/MCP runtime candidate | `keep` | High | `services/task-orchestrator/app/main.py`, `services/task-orchestrator/Dockerfile`, `services/task-orchestrator/task_orchestrator/app.py`, `src/dopemux/pm/writes.py`, `TRUTH_CANONICALS.md` |
| `services/task-orchestrator/task_orchestrator/app.py` | Tier 3 blocked legacy surface | Hard-failing legacy runtime path | Explicitly non-authoritative | `deprecate` | Low | `services/task-orchestrator/task_orchestrator/app.py`, `TRUTH_GAPS.md` |
| `Leantime` via adapters/bridge | Tier 1 canonical backend | PM metadata and project/ticket snapshot surface | Passive PM metadata authority | `keep` | Medium | `src/dopemux/pm/writes.py`, `PROJECT.md`, `TRUTH_SYSTEMS.md`, `services/dopecon-bridge/README.md` |
| `src/conport/memory_server.py` | Tier 1 canonical backend | Structured context, decisions, progress, graph retrieval | Structured decision/progress/context authority | `keep` | High | `src/conport/memory_server.py`, `TRUTH_CANONICALS.md`, `TRUTH_SYSTEMS.md` |
| `services/working-memory-assistant/dope_memory_main.py` | Tier 1 canonical backend | Chronicle/evidence sink over HTTP tools | Durable chronicle/evidence authority | `keep` | High | `services/working-memory-assistant/dope_memory_main.py`, `services/working-memory-assistant/Dockerfile.dope-memory`, `TRUTH_CANONICALS.md` |
| `services/working-memory-assistant/main.py` | Tier 2 adjacent runtime | Additional WMA app surface | `UNKNOWN` for same authority slice; not canonical in this pass | `registry-only` | Medium | `services/working-memory-assistant/main.py`, `TRUTH_GAPS.md` |
| `services/working-memory-assistant/mcp/server.py` | Tier 2 adjacent logic surface | Tool logic / MCP-adjacent implementation | Not proven as runnable canonical transport | `registry-only` | Medium | `services/working-memory-assistant/mcp/server.py`, `TRUTH_CANONICALS.md`, `TRUTH_GAPS.md` |
| `services/dope-context/src/mcp/server.py` | Tier 1 canonical backend | Deterministic code/docs retrieval and indexing | Retrieval/index authority for derived search surfaces | `keep` | High | `services/dope-context/src/mcp/server.py`, `services/dope-context/tests/test_mcp_server.py`, `services/dope-context/README.md`, `TRUTH_SYSTEMS.md` |
| `services/dopecon-bridge/dopecon_bridge` | Tier 2 adapter/bridge | PM-safe routing, event transport, ConPort proxy, compatibility layer | Non-authoritative adapter only | `internalize-if-proven` for eligible proxy logic where parity, ownership clarity, and rollback exist; authority stays separate | High | `services/dopecon-bridge/dopecon_bridge/routes.py`, `services/dopecon-bridge/README.md`, `TRUTH_SYSTEMS.md`, `TRUTH_GAPS.md` |
| `services/dope-memory/mcp_stdio_adapter.py` | Tier 3 stale shim | Thin stdio-to-HTTP adapter for dope-memory | No authority; likely stale port assumption | `deprecate` | Low | `services/dope-memory/mcp_stdio_adapter.py`, `services/registry.yaml`, `compose.yml`, `TRUTH_GAPS.md` |
| `services/serena` | Tier 2 unresolved runtime family | In-repo Serena implementation family | `UNKNOWN` canonical runtime authority | `registry-only` | High | `services/serena`, `TRUTH_CANONICALS.md`, `TRUTH_GAPS.md` |
| `docker/mcp-servers-source/serena` | Tier 2 deployment wrapper family | Deployed Serena wrapper image | Deployment/runtime authority leans here; dev authority still `UNKNOWN` | `registry-only` | High | `docker/mcp-servers-source/serena/Dockerfile`, `compose.yml`, `services/registry.yaml`, `TRUTH_CANONICALS.md` |
| `mcp-proxy-config*.{json,yaml}` | Tier 2 ingress registry/config | Agent-visible MCP launch and proxy definitions | No service authority; config only | `registry-only` | High | `mcp-proxy-config.json`, `mcp-proxy-config.yaml`, `mcp-proxy-config.copilot.yaml`, `TRUTH_GAPS.md` |
| `services/repo-truth-extractor/run_extraction_v5.py` | Tier 1 canonical backend | Extraction/audit runtime | Repo-truth extraction authority | `keep` | Medium | `services/repo-truth-extractor/run_extraction_v5.py`, `services/repo-truth-extractor/README.md`, `TRUTH_CANONICALS.md` |
| `services/agents` | Tier 2 agent family | Infrastructure-agent surfaces | Not authority for PM truth or ingress truth | `registry-only` | Medium | `services/agents/README.md`, `TRUTH_CANONICALS.md`, `AGENTS.md` |
| `src/dopemux/agent_orchestrator.py` | Tier 2 agent family | Alternate orchestrator family | `UNKNOWN` agent authority | `registry-only` | Medium | `TRUTH_CANONICALS.md`, `TRUTH_GAPS.md` |
| `services/task-orchestrator/task_orchestrator/agents` | Tier 2 agent family | Task-orchestrator-local agent family | `UNKNOWN` agent authority | `registry-only` | Medium | `TRUTH_CANONICALS.md`, `TRUTH_GAPS.md` |
| `services/adhd_engine` | Tier 1 domain backend | ADHD/cognitive support API and MCP surfaces | ADHD/operator support authority slice only | `keep` | Medium | `services/registry.yaml`, `compose.yml`, `TRUTH_SYSTEMS.md` |

Notes:

- `task-orchestrator` runtime authority is partially unresolved because `app/main.py` is the observed runtime target while historical docs and extracted gaps show conflicting paths. The Dockerfile now points at `app.main:app`, which reduces but does not eliminate drift because old docs and configs still cite other ports/paths.
- Serena runtime authority remains `UNKNOWN`. The deployed wrapper and the in-repo implementation must stay distinct until runtime authority is frozen.

## 2. Ingress / Control Surface Map

### Operator ingress

- `src/dopemux/cli.py`
  - Control-plane ingress for operator commands, profile/config orchestration, and MCP-facing configuration generation.
- `scripts/dopetask`
  - Execution ingress to the external `dopetask` binary after repo-local pin/venv enforcement.
- `scripts/taskx`
  - Compatibility ingress only; forwards directly to `scripts/dopetask`.

### Agent-visible MCP / proxy registry ingress

- `mcp-proxy-config.json`
  - Declares agent-facing servers for `task-orchestrator`, `conport`, `serena`, `dope-context`, `gpt-researcher`, `pal`, `leantime-bridge`, and others.
- `mcp-proxy-config.yaml`
  - Alternate registry with conflicting task-orchestrator port (`3017`) and launch assumptions.
- `mcp-proxy-config.copilot.yaml`
  - Copilot-specific registry view of the same surface family.

### HTTP ingress surfaces

- `services/dopecon-bridge/dopecon_bridge/routes.py`
  - `/auth/*`, `/events*`, `/route/pm`, `/kg/*`, `/ddg/*`, `/health`
  - Bridge/router/proxy surfaces only; not canonical truth.
- `services/task-orchestrator/app/main.py`
  - FastAPI runtime plus MCP object; serves workflow and PM routers.
- `services/working-memory-assistant/dope_memory_main.py`
  - HTTP tools and `/health` on port `3020`; canonical dope-memory entry point.
- `services/dope-context/src/mcp/server.py`
  - MCP + HTTP runtime for retrieval/indexing.
- `src/conport/memory_server.py`
  - MCP plus HTTP mode for structured memory/graph interfaces.

### Deployment and wrapper ingress

- `docker/mcp-servers-source/serena/Dockerfile`
  - Deployment wrapper exposing Serena over port `3006`.
- `services/dope-memory/mcp_stdio_adapter.py`
  - Stdio wrapper targeting a stale local port; not trustworthy as active ingress.

### Control edges observed

| From | To | Edge Type | Authority Meaning |
| --- | --- | --- | --- |
| `src/dopemux/cli.py` | MCP config / downstream services | Operator control | Control only |
| `scripts/taskx` | `scripts/dopetask` | Compatibility handoff | No new authority |
| `scripts/dopetask` | external `dopetask` binary | Execution handoff | Execution truth boundary |
| `services/dopecon-bridge` | Leantime / ConPort / selected upstreams | Adapter/proxy | Non-authoritative |
| `src/dopemux/pm/writes.py` | Leantime / task-orchestrator / ConPort / dope-memory | Canonical write routing model | Shows split authority, not gateway ownership |
| agent runtimes via `mcp-proxy-config*` | Serena / dope-context / conport / task-orchestrator / pal / bridge-adjacent surfaces | Agent ingress exposure | Exposure only, not authority proof |

## 3. Keep / Candidate-for-Internalization / Registry-Only / Deprecate Matrix

Disposition legend:

- `keep`: observed runtime/control surface remains in place as currently classified
- `registry-only`: keep visible in the census/registry without consolidation or authority promotion
- `internalize-if-proven`: only eligible for gateway internalization where parity, ownership clarity, and rollback exist
- `deprecate`: stale, blocked, or explicitly non-authoritative surface targeted for retirement

| Surface | Disposition | Why |
| --- | --- | --- |
| `src/dopemux/cli.py` | `keep` | Existing operator ingress; already repo-consistent and authoritative only for control. |
| `scripts/dopetask` | `keep` | Observed runtime wrapper and explicit dopetask handoff authority. |
| `services/task-orchestrator/app/main.py` | `keep` | Canonical backend candidate for workflow-significant transitions. |
| `src/conport/memory_server.py` | `keep` | Canonical structured context/decision/progress surface. |
| `services/working-memory-assistant/dope_memory_main.py` | `keep` | Canonical chronicle/evidence runtime. |
| `services/dope-context/src/mcp/server.py` | `keep` | Canonical retrieval/index runtime. |
| `services/repo-truth-extractor/run_extraction_v5.py` | `keep` | Canonical extraction runtime. |
| `services/adhd_engine` | `keep` | Separate backend authority slice for cognitive/operator support. |
| `services/dopecon-bridge/dopecon_bridge/routes.py` | `internalize-if-proven` | Eligible control-plane translation/proxy logic can move behind a gateway later only where parity, ownership clarity, and rollback exist, but the gateway must not inherit authority. |
| selected launch/projection logic from `mcp-proxy-config*` | `internalize-if-proven` | Gateway registry may absorb deterministic catalog projection later only where parity, ownership clarity, and rollback exist; config files themselves are not authoritative. |
| `scripts/taskx` | `registry-only` | Preserve as alias until explicit operator naming decision; not a target for gateway ownership. |
| `services/serena` | `registry-only` | Runtime authority unresolved. Do not consolidate. |
| `docker/mcp-servers-source/serena` | `registry-only` | Deployment wrapper is relevant to exposure but not enough to collapse the family. |
| `services/working-memory-assistant/main.py` | `registry-only` | Overlapping memory surface; not proven canonical. |
| `services/working-memory-assistant/mcp/server.py` | `registry-only` | Logic surface without proven canonical transport bootstrap. |
| `services/agents`, `src/dopemux/agent_orchestrator.py`, `services/task-orchestrator/task_orchestrator/agents` | `registry-only` | Agent families remain duplicated; no ingress consolidation yet. |
| `services/dope-memory/mcp_stdio_adapter.py` | `deprecate` | Port drift and stale wrapper semantics make it unsafe as an ingress contract. |
| `services/task-orchestrator/task_orchestrator/app.py` | `deprecate` | Explicitly hard-failing legacy runtime. |

## 4. First-Safe-Slice Confirmation

First safe slice confirmed:

- Scope the next implementation packet to a non-authoritative ingress inventory layer only.
- Limit changes to:
  - deterministic service registry normalization for ingress-relevant surfaces
  - explicit runtime capability cataloging
  - authority annotations for known services and `UNKNOWN` markers for unresolved ones
  - feature-flagged hiding of duplicate agent-visible proxy surfaces where parity is already proven
- Do not:
  - write gateway request handlers
  - rewrite backend service APIs
  - move dopetask execution logic
  - collapse Serena surfaces
  - treat bridge/gateway responses as committed state events

Why this is the first safe slice:

- The governing ADR allows an agent-facing ingress plane for control concerns only.
- The revised TP notes explicitly forbid turning gateway work into authority work.
- Repo truth still contains unresolved runtime authority for Serena and residual ingress drift across `mcp-proxy-config*`, bridge surfaces, and task-orchestrator path history.

Blocked until after this slice:

- Any packet that internalizes bridge/proxy logic without parity proof
- Any packet that changes dopetask handoff semantics
- Any Serena consolidation packet
- Any packet that claims one unified agent runtime authority

## 5. Evidence Ledger

### Governing external artifacts

- `/Users/hue/Downloads/codex_tp_revision_notes_revised.md`
- `/Users/hue/Downloads/adr_dopemux_adaptive_ingress_plane_revised.md`
- `/Users/hue/Downloads/dopemux_multi_agent_ingress_architecture_revised_full.md`
- `/Users/hue/Downloads/codex_54_synthesis/RULES.md`
- `/Users/hue/Downloads/codex_54_synthesis/PROJECT.md`
- `/Users/hue/Downloads/codex_54_synthesis/TRUTH_SYSTEMS.md`
- `/Users/hue/Downloads/codex_54_synthesis/TRUTH_CANONICALS.md`
- `/Users/hue/Downloads/codex_54_synthesis/TRUTH_GAPS.md`

### Repo runtime and config evidence

- `/Users/hue/code/dopemux-mvp/compose.yml`
- `/Users/hue/code/dopemux-mvp/services/registry.yaml`
- `/Users/hue/code/dopemux-mvp/mcp-proxy-config.json`
- `/Users/hue/code/dopemux-mvp/mcp-proxy-config.yaml`
- `/Users/hue/code/dopemux-mvp/mcp-proxy-config.copilot.yaml`
- `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py`
- `/Users/hue/code/dopemux-mvp/src/dopemux/pm/writes.py`
- `/Users/hue/code/dopemux-mvp/scripts/dopetask`
- `/Users/hue/code/dopemux-mvp/scripts/taskx`
- `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/routes.py`
- `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/README.md`
- `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py`
- `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py`
- `/Users/hue/code/dopemux-mvp/services/task-orchestrator/Dockerfile`
- `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py`
- `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/main.py`
- `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/mcp/server.py`
- `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/Dockerfile.dope-memory`
- `/Users/hue/code/dopemux-mvp/services/dope-memory/mcp_stdio_adapter.py`
- `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py`
- `/Users/hue/code/dopemux-mvp/services/dope-context/README.md`
- `/Users/hue/code/dopemux-mvp/src/conport/memory_server.py`
- `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/run_extraction_v5.py`
- `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/README.md`
- `/Users/hue/code/dopemux-mvp/docker/mcp-servers-source/serena/Dockerfile`
- `/Users/hue/code/dopemux-mvp/src/dopemux/claude_config.py`
- `/Users/hue/code/dopemux-mvp/services/agents/README.md`

### Proof statements

- Service classification in this packet is based on directly inspected runtime code/config plus the cited truth-pack artifacts.
- `UNKNOWN` was preserved for Serena runtime authority and duplicated agent-family authority because the inspected repo does not prove a single canonical writer/runtime there.
- No gateway code was implemented.
- No follow-on packet work is authorized by this document.

## Stop Condition

Stop after this packet. Do not proceed to TP-DMX-AIG-002 or any gateway implementation packet without a new instruction.
