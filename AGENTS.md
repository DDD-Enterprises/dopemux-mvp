# AGENTS.md

## 1. Purpose

This is an operator-control document for the current repo state. It is meant to help you act safely without inventing a unified architecture, smoothing over drift, or hiding `UNKNOWN`.

Repo truth beats docs.

## 2. Read This First

- The task packet names `RULES.md`, `PROJECT.md`, `ARCHITECTURE.md`, `SYSTEM_BOUNDARIES.md`, `PM_PLANE.md`, `DOC_TRUST_MAP.md`, and `DOCS_VS_REPO_DIFF.md` as allowed authority.
- In this checkout, those files were not present during this rewrite.
- The repo-truth artifacts present in this pass were:
  - `tmp/dmx-chatgpt-project-truth-extraction-002/TRUTH_SYSTEMS.md`
  - `tmp/dmx-chatgpt-project-truth-extraction-002/TRUTH_CANONICALS.md`
  - `tmp/dmx-chatgpt-project-truth-extraction-002/TRUTH_GAPS.md`
- Do not invent the contents of `RULES.md`, `SYSTEM_BOUNDARIES.md`, `PM_PLANE.md`, or `DOC_TRUST_MAP.md`. If those files are added later, use them, but repo truth beats docs.

## 3. Canonical Operator Surfaces

- `dopemux` CLI is the main operator control plane.
- `services/repo-truth-extractor/run_extraction_v5.py` is the canonical repo-truth extraction path.
- `scripts/dopetask` is the runtime authority for dopetask. `scripts/taskx` is a compatibility shim, not a separate runtime.
- `services/task-orchestrator/app/main.py` is the intended task-orchestrator runtime surface from this pass, but runtime packaging and Docker alignment are unresolved.
- `services/dopecon-bridge/dopecon_bridge/routes.py` exposes important routing and compatibility surfaces, but bridge is not authority.

## 4. PM Plane

- PM truth is split across multiple surfaces. This pass does not support a single-file PM authority claim.
- `services/task-orchestrator` is the workflow coordination and PM write-normalization surface.
- `src/dopemux/pm/writes.py` shows PM writes crossing Leantime, task-orchestrator, ConPort, and dope-memory mirror receipts.
- Agents do not own PM truth.
- Bridge is not authority for PM truth. Treat `/route/pm` as routing, not as canonical state.
- `PM_PLANE.md` is named by the packet but was not present in this checkout. Do not infer it.

## 5. Memory and Retrieval

- `dope-memory` is the durable evidence-preserving memory sink.
- `dope-memory` is not the canonical PM status authority.
- `conport` is the structured memory, graph, and semantic retrieval surface.
- `dope-context` is the deterministic code and docs retrieval surface.
- `working-memory-assistant` overlaps with memory-related responsibilities, but this pass did not prove it is the canonical durable runtime for the same authority slice.

## 6. Agent Systems

- Agent system authority is `UNKNOWN`.
- This repo contains at least three agent families:
  - `services/agents`
  - `src/dopemux/agent_orchestrator.py`
  - `services/task-orchestrator/task_orchestrator/agents`
- Do not assume one unified agent architecture.
- Do not route operator decisions through agent abstractions unless you verify the exact runtime path in code and config.
- Agents do not own PM truth.

## 7. Working Rules

- Start from runtime code, config, and tests. Do not start from hopeful docs.
- Prefer canonical writers over bridges, adapters, aliases, and shims.
- Mark `UNKNOWN` explicitly when canonicality is unresolved.
- Treat `RULES.md` and `SYSTEM_BOUNDARIES.md` as named-but-absent authority docs in this checkout.
- If a doc conflicts with runtime behavior, repo truth beats docs.

## 8. Docs Trust

- For this rewrite pass, the usable truth docs were `TRUTH_SYSTEMS.md`, `TRUTH_CANONICALS.md`, and `TRUTH_GAPS.md`.
- `DOC_TRUST_MAP.md` and `DOCS_VS_REPO_DIFF.md` were named in the packet but not present in this checkout.
- Older docs and README surfaces may drift from runtime reality. Escalate the drift instead of normalizing it away.
- Repo truth beats docs.

## 9. Known Dangers

- `dopecon-bridge` exposes broad surfaces that can look authoritative. It is not canonical task, workflow, decision, or progress authority.
- Task-orchestrator runtime authority is conflicted across `app/main.py`, `task_orchestrator/app.py`, and the Dockerfile.
- Memory-related surfaces overlap across `dope_memory_main.py`, `main.py`, and `mcp/server.py`.
- Agent responsibilities are duplicated across multiple families, and agent authority is `UNKNOWN`.
- `scripts/dopetask` is the observed runtime, but operator naming still drifts through TaskX language.
- MCP and proxy config surfaces are inconsistent in places, including stale port assumptions and missing launch targets.
