---
id: dopemux-architecture
title: Dopemux Architecture
type: explanation
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Architecture explanation for Dopemux split-authority service and control planes.
---
# Dopemux Architecture

Dopemux is a split-authority operator workspace. The architecture is not a
single service and not a single assistant. It is a set of cooperating systems
with domain-specific authority and known drift.

## Planes

| Plane | Primary systems | Authority shape |
| --- | --- | --- |
| Operator/control | `dopemux` | CLI, startup coordination, routing, MCP/server coordination |
| Execution | `dopetask` via `scripts/dopetask` | External execution after handoff |
| PM metadata | Leantime | Passive work-item metadata and project/ticket snapshots |
| Workflow | Task Orchestrator | Workflow transitions, queue, blockers |
| Structured context | ConPort | Decisions, progress, project context, custom data |
| Chronicle memory | dope-memory | Historical receipts and evidence-preserving ledger |
| Retrieval | dope-context and ConPort retrieval | Derived search/retrieval over code/docs and structured records |
| Bridge/adapter | dopecon-bridge | Proxying, compatibility routing, event transport |
| Operator support | ADHD Engine | Cognitive-state and support surfaces |
| Extraction/audit | Repo Truth Extractor | Evidence artifacts about the repo |

## Runtime Spine

`pyproject.toml` exposes `dopemux = "dopemux.cli:main"`, so `src/dopemux/cli.py`
is the operator CLI entrypoint. The `dopemux start` path handles cockpit,
routing, validation, and coordination behavior. It should not be documented as
owning every downstream domain.

Execution handoff flows through:

```text
dopemux -> scripts/taskx -> scripts/dopetask -> external dopetask binary
```

`scripts/taskx` is a compatibility shim. `scripts/dopetask` enforces
`.dopetaskroot`, reads `.dopetask-pin`, installs the pinned external
`dopetask`, and executes it.

## PM Architecture

`src/dopemux/pm/writes.py` is the clearest PM write-boundary evidence:

- metadata updates go to Leantime
- workflow transitions go to task-orchestrator
- progress and decision logs go to ConPort
- historical receipt mirrors go to dope-memory

Task Orchestrator is therefore workflow authority, not all PM authority.
Leantime is metadata authority, not workflow legality authority. ConPort is
decision/progress/context authority, not passive PM metadata authority.
dope-memory is a receipt/chronicle sink, not current PM state authority.

## Bridge Architecture

`services/dopecon-bridge/dopecon_bridge/routes.py` states the bridge is an
adapter and proxy layer only. It exposes PM, KG, decision, progress, and event
routes, but those routes do not make it source truth.

Bridge-mediated writes must name the upstream canonical writer. Bridge-mediated
reads must be labeled as proxy or derived views.

## Retrieval And Extraction

dope-context indexes and retrieves code/docs. ConPort also supports structured
and semantic retrieval. These outputs are derived and can help an operator find
evidence, but the retrieved source file, runtime code, or config remains the
actual authority.

Repo Truth Extractor runs repo analysis and emits artifacts. Its outputs are
evidence artifacts, not runtime truth. The current canonical operator command
family is `dopemux rte`; `dopemux upgrades` is compatibility, and older
`dopemux truth` style paths are drift/refusal surfaces.

## Known Architecture Drift

- Task Orchestrator has historical conflict across runtime app paths and port
  references. Current compose and registry use `8000`; legacy references to
  `3014` remain in older surfaces.
- ConPort is split across HTTP `3004`, MCP/SSE `3005`, and info `4004`.
- dope-memory runs as the canonical chronicle service under the
  working-memory-assistant tree, while other working-memory-assistant surfaces
  remain adjacent support surfaces.
- Serena and agent systems remain unresolved or drifted in this packet's
  evidence set.

## Must Not Own

| System | Must Not Own |
| --- | --- |
| dopemux | Canonical PM entity truth, chronicle truth, dope-context retrieval truth, external execution after handoff |
| Task Orchestrator | Passive PM metadata, all PM state, ConPort structured authority, dope-memory chronicle |
| ConPort | All memory, passive PM metadata, workflow legality, dope-context source truth |
| dope-memory | Current PM state, workflow legality, all memory |
| dope-context | Source truth for code/docs, PM truth, chronicle truth |
| dopecon-bridge | Canonical PM, workflow, decision, progress, memory, or retrieval authority |
| ADHD Engine | PM truth, ConPort authority, dope-memory authority |
| Repo Truth Extractor | Runtime truth, PM authority, memory authority, retrieval authority |

Where ownership is not proven, preserve `UNKNOWN`.
