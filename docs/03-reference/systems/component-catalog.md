---
id: component-catalog
title: Component Catalog
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Compact component catalog for Dopemux systems, authorities, and drift markers.
---
# Component Catalog

This catalog is a compact operator reference. The per-system docs under
[`docs/03-reference/systems/`](.) (`system-<name>.md`) remain the richer
source for tiering and detailed evidence.

> **Task Orchestrator dual-surface note**: two distinct runtimes share the "Task Orchestrator" name — the in-repo FastAPI workflow service AND the upstream stdio MCP container that holds workflow-state authority per the accepted ADR. See [`task-orchestrator/system-taskorchestrator.md`](task-orchestrator/system-taskorchestrator.md) §9 for the canonical disambiguation.

| Component | Role | Authority | Drift / UNKNOWN |
| --- | --- | --- | --- |
| `dopemux` | Operator CLI and control surface | startup, routing, MCP/server coordination | Does not own downstream PM, memory, retrieval, or execution truth. |
| `dopetask` | External execution runtime | execution after `scripts/dopetask` handoff | TaskX naming remains in some code/tests as compatibility drift. |
| Leantime | PM application | passive metadata and project/ticket snapshots | Mostly accessed through adapters/bridge tooling. |
| Task Orchestrator | Workflow surfaces (dual) | **upstream stdio MCP** (canonical workflow authority per accepted ADR): work-item state machine, schema-driven gates, proof-bundle complete-gate, claims; **in-repo FastAPI service**: idea/epic CRUD, project workflow views, PM-plane write routing | Two distinct runtimes share the name — see `task-orchestrator/system-taskorchestrator.md` §9. FastAPI runtime path + port `8000` vs `3014` drift remains. |
| ConPort | Structured context system | decisions, progress, context, custom data | Access is split across `3004`, `3005`, and caller assumptions. |
| dope-memory | Chronicle service | historical receipts and chronicle ledger | Lives under working-memory-assistant tree; do not treat as all memory. |
| working-memory-assistant | Memory support surface | snapshot/recovery support where implemented | Non-ledger persistence authority remains `UNKNOWN`. |
| dope-context | Code/docs retrieval | derived indexing and search | Retrieval output is derived, not source truth. |
| dopecon-bridge | Adapter/proxy/event layer | proxying, compatibility routing, event transport | Must not own PM, workflow, decision, progress, memory, or retrieval. |
| ADHD Engine | Operator-support service | cognitive-state and recommendation surfaces | Persistence backends for some surfaces remain `UNKNOWN`. |
| Repo Truth Extractor | Audit/extraction runtime | repo-truth evidence artifacts | Artifacts do not outrank runtime code/config/tests. |
| Serena | Code-intelligence support | operational support only | Deployment/runtime authority remains `UNKNOWN`. |
| LiteLLM | Model routing support | routing proxy infrastructure | Support component, not a repo truth authority. |
| leantime-bridge | PM adapter | proxy to Leantime | Not PM authority itself. |
| agent families | Agent implementations | `UNKNOWN` | Multiple families exist; no single repo-wide agent authority is proven. |

## Port Orientation

Observed compose/registry defaults:

| Service | Host port |
| --- | ---: |
| dopecon-bridge | `3016` |
| ConPort HTTP | `3004` |
| ConPort MCP/SSE | `3005` |
| dope-context | `3010` |
| dope-memory | `3020` |
| task-orchestrator | `8000` |
| ADHD Engine | `3025` |
| Leantime | `8080` |

Local `.env` overrides can change these. Packet 003 did not run a live compose
startup, so live service health is `NOT_RUN`.

## Use Rule

Before depending on a component, classify whether you need:

- authority: a canonical writer or owner
- proxy: an operational route to another authority
- derived context: retrieval/report output
- support: useful runtime help with no domain authority
- unresolved ownership: `UNKNOWN`
