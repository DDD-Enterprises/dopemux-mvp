---
id: SYSTEM_BOUNDARIES
title: System Boundaries
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-31'
last_review: '2026-03-31'
next_review: '2026-06-29'
prelude: System Boundaries (reference) for dopemux documentation and developer workflows.
---
# SYSTEM_BOUNDARIES

This document is derived only from the tracked truth references in `docs/03-reference/truth/`: `truth-systems.md`, `truth-interfaces.md`, `truth-data-events.md`, `truth-canonicals.md`, and `truth-gaps.md`. It does not normalize contradictions. It preserves `UNKNOWN`, `ambiguous`, and `split` where the truth packet does not establish a single authority. No public APIs, interfaces, or types are introduced or changed here.

## Authority Model Overview

The planes below are documentation planes, not services.

- Planes are NOT services.
- Services can span planes.
- Authority is per-domain, not per-service.

### PM Plane

Owns the PM domain only as a split-authority description:
- metadata
- workflow transitions
- progress
- decisions

Observed state from the truth packet: PM authority is `split`, not unified.

### Memory Plane

Owns memory-domain surfaces:
- durable chronicle memory
- work-log and raw-event storage
- snapshot and recovery support surfaces

Observed state from the truth packet: durable ledger authority and snapshot/recovery support are not the same thing.

### Retrieval Plane

Owns retrieval-domain surfaces:
- deterministic code and docs retrieval
- semantic retrieval
- graph retrieval

Observed state from the truth packet: retrieval authority is split across deterministic context retrieval and semantic/graph retrieval.

### Orchestration Plane

Owns orchestration-domain surfaces:
- workflow coordination
- cross-plane operations
- operator control surfaces

Observed state from the truth packet: workflow coordination authority exists, but runtime packaging and deployment authority are not fully aligned.

### Adapter / Bridge Plane

Owns adapter-domain surfaces:
- routing
- compatibility
- proxying
- event-bus transport

Observed state from the truth packet: this plane mediates between authorities; it does not become the authority by exposing their routes.

## System Boundaries Table

| System | Owns | Must NOT Own | Notes |
| --- | --- | --- | --- |
| `dopemux core` | Primary CLI/runtime package, kernel integration, extractor command wiring, routing/provider config loading, operator control surface. | Canonical repo-truth extraction runtime for v5. | `dopemux truth` is legacy `PipelineRunner` drift relative to the extractor v5 path. |
| `dope-memory` | Canonical SQLite chronicle ledger, work-log/raw-event storage, `/tools/*` memory routes, fail-closed ledger resolution. | Canonical PM status authority. | Canonical runtime is the dope-memory HTTP surface in working-memory-assistant; stdio adapter port assumptions contradict registry/compose. |
| `working-memory-assistant` | Snapshot/recovery, contexts/preferences, ADHD-adjacent support routes, operational memory support. | Canonical durable dope-memory authority unless further authority is established; runnable MCP transport is not confirmed. | Persistent writers for this surface remain `UNKNOWN`. |
| `conport` | Structured memory, semantic retrieval, graph-link surfaces, and PM decision/progress logging per the split authority mapping. | Implied equivalence with `services/dope-query`. | Exact retrieval tie-break behavior beyond observed Milvus-to-PostgreSQL flow remains `UNKNOWN`. |
| `dope-context` | Workspace/docs indexing and deterministic hybrid retrieval. | Authoritative runtime definition via `mcp-proxy-config*` or the missing `run_mcp.sh` path. | Exact backing index writer/reader remains `UNKNOWN`. |
| `task-orchestrator` | Workflow coordination, workflow APIs, cross-plane operations, workflow transitions, coordination WebSocket events, and workflow idea/epic/audit writes via bridge custom-data categories. | All PM state; metadata and decision/progress have other canonical writers. Legacy `task_orchestrator/app.py` launch authority. | Active Docker/compose/registry/app runtime points to `app.main:app` on `8000`; legacy `3014` references and the absent `docker/compose.core.yml` remain drift. |
| `dopecon-bridge` | Adapter/proxy/auth/event-bus/compatibility surfaces and upstream routing. | Canonical task, workflow, decision, or progress authority. | It appears authoritative because it exposes `/kg/*`, `/ddg/*`, and `/route/pm`, which is exactly the boundary risk called out in the truth packet. |
| `ADHD engine` | Cognitive-state, workload, break, context-state operational APIs and MCP tools. | Canonical identity through the duplicate `services/adhd-engine` path; broader persistence authority is not established. | It reads ConPort progress; exact persistence backends for several ADHD surfaces remain `UNKNOWN`. |
| `repo-truth-extractor` | Canonical multi-phase repo-truth extraction, v4 compatibility wrapper, and extraction artifacts. | Representation through the legacy `dopemux truth` / `PipelineRunner` path. | Canonical CLI path is extractor/upgrades -> `run_extraction_v5.py`. |
| `serena (ambiguous)` | Only an observed code-intelligence / MCP assistance surface. | A single declared canonical implementation and deployment authority, because the truth packet does not establish one. | Deployment/runtime authority leans toward the Docker wrapper; in-repo implementation authority remains `UNKNOWN`. |

## Critical Boundary Violations

- `dopecon-bridge` appearing authoritative is dangerous because operators can mistake proxy endpoints for source truth. The truth packet explicitly says the bridge must not be canonical task, workflow, decision, or progress authority while also exposing `/kg/*`, `/ddg/*`, and `/route/pm`.
- Duplicate memory systems are dangerous because overlapping names and transports obscure the canonical writer and persistence path. The truth packet shows `dope_memory_main.py`, `main.py`, and `mcp/server.py` under working-memory-assistant with different runtime status.
- Agent system duplication is dangerous because three families can drift independently with no declared operator-facing authority. The truth packet leaves canonical agent ownership `UNKNOWN`.
- PM authority fragmentation is dangerous because metadata, workflow, progress, decisions, and mirror receipts already split across different writers. Any extra ownership claims would create silent contract drift.

## Canonical Authority Mapping

- PM state -> `split`, must be clarified. Observed split: Leantime metadata, task-orchestrator workflow transitions, ConPort progress/decision logging, and dope-memory mirror receipts.
- Workflow -> `task-orchestrator`. Active runtime packaging points to `app.main:app` on `8000`, but this mapping remains incomplete because legacy `3014` references remain outside the active path and `docker/compose.core.yml` is absent in this checkout.
- Decisions -> `ConPort`. `dopecon-bridge` decision routes are proxy surfaces only, not decision authority.
- Memory -> `dope-memory (ledger)`. This mapping is incomplete because working-memory-assistant overlaps operationally and its non-ledger persistence remains `UNKNOWN`.
- Retrieval -> `dope-context + ConPort`. This mapping is incomplete because dope-context backend details remain `UNKNOWN` and `dope-query` status is unresolved.
- Extraction -> `repo-truth-extractor`. Legacy `dopemux truth` remains drift because it routes through `PipelineRunner` instead of the canonical extractor v5 path.

## Forbidden Patterns

- Do not treat a bridge as source of truth.
- Do not allow multiple writers for the same domain.
- Do not allow silent mirroring without receipts.
- Do not leave ownership undeclared.

A mirror is acceptable only when the canonical writer is named and the mirror is explicitly labeled as a receipt/mirror, not source truth.

## Required Future Resolutions

- Serena canonical authority
- agent system ownership
- PM plane unification
- `dope-query` status
- legacy truth runner removal
