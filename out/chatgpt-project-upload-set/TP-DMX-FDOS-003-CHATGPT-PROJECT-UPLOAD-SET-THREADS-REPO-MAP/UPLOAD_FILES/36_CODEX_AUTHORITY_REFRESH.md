---
id: codex-authority-refresh
title: Codex Authority Refresh
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Codex-facing authority matrix for current dopemux repo work, labels, and proof rules.
---
# Codex Authority Refresh

This matrix is a Codex-facing refresh for repo-changing work in this checkout. It does not replace runtime code, config, tests, compose wiring, active entrypoints, or active Task Packets. It records the authority surfaces Codex should inspect before making claims or edits.

## Labels

- `OBSERVED`: current repo files directly support the claim.
- `CONFLICTING`: current repo files expose more than one authority or path and the conflict must remain visible.
- `UNKNOWN`: current repo files do not prove the authority, runtime owner, or path.
- `RECOMMENDED`: operational instruction for future Codex work, not proof of runtime behavior.

## Codex Control Rules

- `OBSERVED`: `AGENTS.md` is the durable Codex and agent-style instruction surface for this repo.
- `OBSERVED`: the live Task Packet schema is `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`.
- `OBSERVED`: active Task Packets control execution scope, allowlists, validation obligations, and stop conditions.
- `OBSERVED`: runtime code, config, compose wiring, tests, and active entrypoints outrank docs for behavior claims.
- `RECOMMENDED`: validate generated Task Packets against the live schema before implementation.
- `RECOMMENDED`: Codex should not treat GitHub/CI alone as semantic proof of runtime correctness, authority ownership, or replay safety.
- `RECOMMENDED`: Codex work must return proof and PR evidence, including commands, exit codes, changed files, residual risks, UNKNOWNs, commit SHA, and PR URL or exact blocker.

## Authority Matrix

| Surface | Status | Codex Authority Boundary | Evidence Paths |
| --- | --- | --- | --- |
| `dopemux` | `OBSERVED` | Operator control, CLI, startup, routing, MCP/service coordination. It is not PM, memory, retrieval, or external execution authority. | `AGENTS.md`; `PROJECT.md`; `ARCHITECTURE.md`; `pyproject.toml`; `src/dopemux/cli.py` |
| `dopetask` | `OBSERVED` | External execution runtime reached through local wrappers. Repo source owns the wrapper/bootstrap path, not the external engine implementation. | `scripts/dopetask`; `.dopetaskroot`; `.dopetask-pin`; `scripts/taskx` |
| Task Orchestrator | `CONFLICTING` | Workflow-significant transitions and workflow views. `services/task-orchestrator/app/main.py` and the Dockerfile point to the canonical runtime, while `services/task-orchestrator/task_orchestrator/app.py` hard-fails as unsupported. | `services/task-orchestrator/app/main.py`; `services/task-orchestrator/Dockerfile`; `services/task-orchestrator/task_orchestrator/app.py`; `services/task-orchestrator/mcp_stdio.py` |
| Leantime | `OBSERVED` | Passive PM metadata and project/ticket snapshot authority through dopemux PM adapters and bridge-safe routes. It is not workflow legality authority. | `src/dopemux/pm/writes.py`; `src/dopemux/pm/reads.py`; `compose.yml`; `services/dopecon-bridge/dopecon_bridge/routes.py` |
| ConPort | `CONFLICTING` | Structured decisions, progress, project context, and custom data. Current PM code proves use, while docs/runtime notes preserve access-contract drift around ConPort-facing ports and clients. | `src/dopemux/pm/writes.py`; `src/dopemux/pm/reads.py`; `services/dopecon-bridge/dopecon_bridge/routes.py`; `PROJECT.md`; `ARCHITECTURE.md` |
| dope-memory | `CONFLICTING` | Chronicle and evidence-preserving receipts. The strongest observed dope-memory HTTP runtime is under working-memory-assistant, while adjacent memory surfaces remain overlapping. | `services/working-memory-assistant/dope_memory_main.py`; `services/working-memory-assistant/mcp/server.py`; `services/working-memory-assistant/main.py`; `PROJECT.md`; `ARCHITECTURE.md` |
| dope-context | `OBSERVED` | Code/docs indexing and retrieval. Retrieval output is derived evidence and is not source truth by itself. | `services/dope-context/src/mcp/server.py`; `PROJECT.md`; `ARCHITECTURE.md` |
| dopecon-bridge | `OBSERVED` | Adapter, proxy, routing, event transport, and compatibility layer. It must not be promoted into canonical task, workflow, decision, progress, PM, chronicle, or retrieval authority. | `services/dopecon-bridge/dopecon_bridge/routes.py`; `services/dopecon-bridge/dopecon_bridge/app.py`; `services/dopecon-bridge/kg_authority.py` |
| ADHD Engine | `OBSERVED` | Operator-support and cognitive-state service. It supports state, recommendations, hooks, API, MCP, and WebSocket surfaces, but does not own PM, memory, chronicle, ConPort, or retrieval authority. | `services/adhd_engine/main.py`; `services/adhd_engine/mcp_stdio.py`; `PROJECT.md`; `ARCHITECTURE.md` |
| Repo Truth Extractor | `OBSERVED` | Extraction and audit runtime only. Its outputs are evidence artifacts and do not replace runtime/source truth. Live execution requires explicit consent and is out of scope for docs-only Codex refresh work. | `services/repo-truth-extractor/run_extraction_v5.py`; `AGENTS.md`; `PROJECT.md`; `ARCHITECTURE.md` |
| agents | `UNKNOWN` | Repo-wide agent runtime authority is unresolved. Multiple agent families exist, and no inspected path proves a single canonical agent execution or coordination owner. | `services/agents/*`; `src/dopemux/agent_orchestrator.py`; `services/task-orchestrator/task_orchestrator/agents/*`; `AGENTS.md` |
| Cockpit/dopeUI | `CONFLICTING` | Cockpit runtime code is observed as a guarded local UI/runtime-render surface. `dopeUI` was not observed as a current named source/docs authority in the focused search, so Codex must not claim a unified Cockpit/dopeUI authority without new evidence. | `src/dopemux/ui/cockpit/*`; `src/dopemux/commands/cockpit_commands.py`; `tests/unit/dopemux/ui/cockpit/*`; `tests/unit/test_cockpit_cli.py` |

## Current Path Rules

- `OBSERVED`: `compose.yml` presents itself as the canonical Docker Compose entrypoint for normal runtime operation.
- `CONFLICTING`: root authority docs and tracked `docs/03-reference/*` equivalents do not always share identical paths. Preserve exact paths rather than normalizing root and docs authority into one cleaner story.
- `CONFLICTING`: TaskX naming remains in `scripts/taskx`, tests, docs, and older packets, but live wrapper evidence shows `scripts/taskx` is a compatibility shim to `scripts/dopetask`.
- `UNKNOWN`: any authority not backed by runtime code, config, compose wiring, tests, active entrypoints, or the active Task Packet remains unresolved.

## Codex Proof Rule

Codex may cite GitHub checks, CI, PR state, and commits as delivery evidence, but those signals are not enough to prove semantic correctness or authority ownership. For substantial repo work, Codex must return a proof ledger with exact commands, exit codes, changed files, diff scope, validation results, commit SHA, PR URL or exact blocker, residual risks, UNKNOWNs, and cleanup status.
