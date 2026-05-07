---
id: ARCHITECTURE
title: Architecture
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-07'
last_review: '2026-05-07'
next_review: '2026-08-05'
prelude: Architecture (explanation) for dopemux documentation and developer workflows.
---
# ARCHITECTURE

## 1. Purpose

This document describes the repository architecture as observed in current runtime code, config, compose wiring, service registry entries, and truth-aligned reference docs in this checkout.

It is not a target-state diagram and not a unification brief. Where the repository shows split authority, overlapping systems, or runtime drift, this document preserves that reality.

## 2. Architectural Shape

The repository is a composed multi-system workspace, not a single application and not a single clean platform core.

The strongest observable repo-level patterns are:

- `dopemux` is the operator control surface
- `dopetask` is the external execution runtime reached through local wrapper scripts
- PM authority is split across Leantime, task-orchestrator, ConPort, and dope-memory mirror receipts
- memory and retrieval remain split across dope-memory, ConPort, and dope-context
- dopecon-bridge is a routing/proxy layer, not a domain authority
- ADHD Engine is an operator-support service, not a PM or memory authority
- repo-truth-extractor is a separate extraction/audit subsystem

This is a multi-plane architecture with real cross-system coupling, not a unified monolith.

## 3. Major Planes And Authorities

### 3.1 Operator / Control Plane

`dopemux` is the main operator-facing control layer. It owns CLI entrypoints, startup behavior, MCP/server coordination, routing mode management, and local environment shaping.

It does not own canonical PM truth, memory truth, retrieval truth, or the external execution runtime after handoff.

### 3.2 Execution Plane

Execution handoff runs through:

`dopemux` -> `scripts/taskx` -> `scripts/dopetask` -> external `dopetask`

This repo owns the wrapper/bootstrap path, not the full external `dopetask` implementation.

### 3.3 PM Plane

PM authority is split by concern, not unified:

- Leantime: passive PM metadata and project/ticket snapshot authority
- task-orchestrator: workflow-significant transitions and workflow-serving APIs
- ConPort: structured decision/progress/project-context authority
- dope-memory: mirrored historical PM receipts, not primary PM state
- dopemux: PM routing/normalization layer, not the PM system of record

The repo does not prove one single canonical PM authority surface.

### 3.4 Memory Plane

Memory is also split:

- dope-memory: chronicle and evidence-preserving history
- ConPort: structured context, decisions, progress, custom data
- working-memory-assistant: operational snapshot/recovery and support surfaces

These are adjacent but not interchangeable.

### 3.5 Retrieval Plane

Retrieval is split across:

- dope-context: deterministic code/docs indexing and retrieval
- ConPort: structured/semantic retrieval and relationship-query surfaces

Retrieval outputs are derived views, not automatically source truth.

### 3.6 Adapter / Bridge Plane

dopecon-bridge is the active bridge plane. It owns routing, proxying, compatibility surfaces, event transport, and health aggregation. It does not become the authority for PM, workflow, decisions, or progress by exposing those routes.

### 3.7 Cognitive / Operator-Support Plane

ADHD Engine is an operator-support and cognitive-state service. It exposes HTTP, MCP, WebSocket, and event/hook-facing surfaces for ADHD support, recommendations, and current service state.

It does not own PM truth, chronicle truth, ConPort authority, or retrieval authority.

### 3.8 Extraction / Audit Plane

Repo Truth Extractor is the extraction and audit subsystem. `services/repo-truth-extractor/run_extraction_v5.py` is the strongest extraction runtime authority in this checkout. It produces analysis/proof artifacts about the repo; it does not replace runtime truth.

## 4. System Interaction Model

The current architecture is best understood as cooperating systems with explicit boundaries:

- `dopemux` coordinates startup, routing, and operator commands
- `task-orchestrator` serves workflow views and workflow-significant PM transitions
- `dopecon-bridge` mediates safe PM routing, ConPort proxy calls, and event transport
- `ConPort` stores structured context/decision/progress/custom data
- `dope-memory` stores historical chronicle receipts and evidence
- `dope-context` indexes and retrieves code/docs
- `ADHD Engine` serves operator-support state and projections
- `repo-truth-extractor` inspects the repo and emits truth artifacts

These systems are connected, but they are not one canonical "brain" or "cognitive core," and no inspected runtime path proves such a unification layer exists.

## 5. Important Cross-System Flows

### 5.1 Operator Startup And Runtime Control

Observed flow:

- operator enters through `dopemux`
- `dopemux` can start MCP/services, configure routing, and launch local workflows
- downstream systems are then consumed as separate runtimes

Authority remains with `dopemux` only for the control/startup slice.

### 5.2 PM Write Flow

Observed flow from `src/dopemux/pm/writes.py` and PM docs:

- passive metadata -> Leantime
- workflow-significant transition -> task-orchestrator
- structured progress/decision logging -> ConPort
- mirrored historical receipt -> dope-memory

This is an intentionally split authority flow.

### 5.3 Bridge-Mediated Routing

Observed flow from `services/dopecon-bridge/dopecon_bridge/routes.py`:

- safe PM operations -> leantime-bridge
- ConPort-compatible reads/writes -> ConPort HTTP API
- compatibility decision graph reads -> ConPort-backed normalized views
- event publication/subscription -> Redis Streams

The bridge mediates. It does not own the upstream truth.

### 5.4 ADHD Support Flow

Observed ADHD flow:

- ADHD Engine maintains current runtime state and recommendations
- it exposes HTTP/MCP/WebSocket surfaces
- it can project selected data into bridge/ConPort-adjacent storage or event paths
- bridge-side ADHD integrations can publish buffered event traffic

This is an operator-support flow, not PM or memory authority transfer.

### 5.5 Repo-Truth Extraction Flow

Observed extractor flow:

- operator invocation comes through `dopemux upgrades ...` or direct runner execution
- active engine runs through `run_extraction_v5.py`
- compatibility contract rebuilding can occur through `run_extraction_v4.py`
- run/proof/doctor/coverage artifacts are written into extraction trees

These outputs are evidence artifacts about the repo, not the live systems themselves.

## 6. Architectural Constraints

The following constraints are repeatedly proven in code and docs:

- bridges and adapters must not be treated as source truth
- PM authority is per-slice, not per-brand
- memory and retrieval must remain separate from PM authority
- extracted artifacts must not outrun runtime truth
- support systems such as ADHD Engine are real architectural participants, but their presence does not grant authority over PM, memory, or retrieval planes

## 7. Known Architectural Drift

- task-orchestrator runtime authority is conflicted between `app/main.py`, the hard-failing legacy runtime path, and Docker/startup wiring
- dopecon-bridge exposes broad surfaces that look authoritative even though its runtime explicitly denies that role
- dope-memory and working-memory-assistant overlap by tree location and naming
- ConPort access and port assumptions drift across different callers/docs
- ADHD Engine has overlapping support/context surfaces in both `services/adhd_engine/*` and `src/dopemux/adhd/*`
- repo-truth-extractor has active-v5 versus legacy-command/output-root drift
- agent authority remains unresolved across multiple agent families, with no single runtime proving canonical ownership of agent execution or coordination
- the requested `docs/03-reference/SYSTEM_BOUNDARIES.md` path is absent in this checkout; the current boundary reference file is `docs/03-reference/systems/system-boundaries.md`

## 8. What This Architecture Is Not

This repo architecture is not proven to be:

- a single unified PM platform
- a single unified memory platform
- a single unified agent system
- a single cognitive core with ADHD Engine at the center
- a bridge-centric architecture where the bridge owns truth

Those interpretations would overclaim beyond the inspected runtime.

## 9. Working Rules

- Start from runtime entrypoints and current system docs, not from historical architecture prose.
- Keep control, execution, PM, memory, retrieval, bridge, cognitive-support, and extraction planes distinct.
- Name the canonical writer for each slice before making architecture claims.
- Preserve `UNKNOWN` where ownership or runtime packaging is not settled.
- If a system only proxies, routes, mirrors, or indexes data, document that role explicitly instead of upgrading it into authority.
