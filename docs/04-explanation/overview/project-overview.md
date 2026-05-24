---
id: project-overview
title: Project Overview
type: explanation
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Repo-grounded overview of Dopemux as a split-authority operator workspace.
---
# Project Overview

Dopemux is a composed operator workspace for development-control workflows. It
is centered on the `dopemux` CLI, but the repository is not only a CLI package.
It contains operator tooling, service runtimes, bridge/proxy layers, PM
adapters, memory and retrieval systems, compose wiring, and repo-truth
extraction tooling.

The strongest repo-grounded interpretation is that Dopemux coordinates
multiple systems without collapsing their authority:

- `dopemux` owns operator control, startup coordination, routing, and MCP/server
  coordination.
- `dopetask` owns execution after handoff through `scripts/dopetask`; `scripts/taskx`
  is only a compatibility shim.
- Leantime owns passive PM metadata and project/ticket snapshots.
- task-orchestrator owns workflow-significant transitions, queue state, and
  blockers.
- ConPort owns structured decisions, progress, project context, and custom-data
  context.
- dope-memory owns chronicle receipts and historical memory.
- dope-context owns code/docs indexing and derived retrieval.
- dopecon-bridge owns proxying, compatibility routing, and event transport.
- ADHD Engine owns operator-support and cognitive-state surfaces.
- Repo Truth Extractor owns extraction and audit artifacts about the repo.

This is not a monolithic assistant, not one PM system, not one memory system,
and not one agent authority. Repo-wide agent ownership remains `UNKNOWN` across
the inspected agent families.

## Source Basis

This overview is grounded in:

- `PROJECT.md`
- `ARCHITECTURE.md`
- `PM_PLANE.md`
- `SERVICE_CATALOG.md`
- `docs/03-reference/systems/system-boundaries.md`
- `docs/03-reference/governance/dopemux-documentation-source-map.md`
- `src/dopemux/pm/writes.py`
- `compose.yml`
- `services/registry.yaml`

Runtime code, config, compose wiring, tests, and active entrypoints still outrank
this document.

## Operating Shape

The operator enters through `dopemux`. From there, the repo can coordinate
routing, workspace context, local service configuration, and selected command
families such as Repo Truth Extractor. Execution handoff flows through
`scripts/taskx` into `scripts/dopetask`, which installs and runs the pinned
external `dopetask` runtime.

PM behavior is split by concern. Metadata belongs with Leantime, workflow
transitions with task-orchestrator, decision/progress context with ConPort, and
historical receipt mirroring with dope-memory. dopecon-bridge can route or proxy
some PM-adjacent operations, but it is not the PM authority.

Memory and retrieval are also split. ConPort stores structured context and
decisions. dope-memory preserves chronicle receipts. dope-context indexes and
retrieves code/docs. Retrieval results are useful evidence, but source files and
runtime code remain source truth.

## Current Limits

- task-orchestrator runtime packaging has known drift between app code, older
  module paths, and port references.
- ConPort access patterns are split across HTTP and MCP/SSE surfaces.
- dope-memory and working-memory-assistant share a tree and can be confused.
- dopecon-bridge exposes broad routes that can look authoritative but are not.
- Repo Truth Extractor outputs evidence artifacts; they do not replace runtime.
- Agent authority is `UNKNOWN`.

These limits are not closed by documentation. They require targeted runtime
validation or separate implementation work.
