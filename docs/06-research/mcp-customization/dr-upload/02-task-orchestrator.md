---
id: 02-task-orchestrator
title: 02 Task Orchestrator
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-07'
last_review: '2026-05-07'
next_review: '2026-08-05'
prelude: 02 Task Orchestrator (explanation) for dopemux documentation and developer
  workflows.
---
# DR Pack 02: Task Orchestrator

Access date: 2026-04-28

## Objective

Research current Task Orchestrator candidates with `jpicklyk/task-orchestrator` as the preferred active upstream base, while preserving EchoingVesper, PyPI, and iflow lineage drift as evidence.

## Source Seeds

Preferred active base:

- https://github.com/jpicklyk/task-orchestrator

Lineage and packaging context:

- https://github.com/EchoingVesper/mcp-task-orchestrator
- https://pypi.org/project/mcp-task-orchestrator/
- https://github.com/iflow-mcp/echoingvesper-mcp-task-orchestrator
- https://pypi.org/project/iflow-mcp_echoingvesper_mcp-task-orchestrator/
- `docs/06-research/mcp-customization/data/upstream-source-manifest.json`
- Dopemux runtime seed: `services/task-orchestrator/app/main.py`
- Dopemux workflow seed: `services/task-orchestrator/app/api/project_workflow.py`
- Dopemux PM seed: `src/dopemux/pm/writes.py`

Observed source status:

- `jpicklyk/task-orchestrator`: archived=false, fork=false, latest release v3.3.0 published 2026-04-23T21:09:12Z, latest commit 14023d25636db5e86adee7e7c83c96a39f2ce0ac.
- `EchoingVesper/mcp-task-orchestrator`: archived=true, latest commit db942e70e611afa2fce3a25384e26bc83440ef18, PyPI latest 1.8.0 uploaded 2025-06-08T23:28:20Z.
- `iflow-mcp/echoingvesper-mcp-task-orchestrator`: fork=true, parent EchoingVesper, PyPI latest 2.0.0 uploaded 2026-01-28T05:42:34Z.

## Required Extraction Fields

- MCP tools/resources/prompts
- task/work item model
- workflow state model
- transition/gate model
- specialist/agent roles
- persistence model
- templates
- transports
- package/release lineage
- migration compatibility
- archive/fork/repackage status
- security/auth model

## Dopemux Boundary Constraints

- task-orchestrator owns workflow-significant transitions, queue, blockers, and workflow views.
- It must not own passive Leantime metadata.
- It must not own ConPort decision/progress truth.
- It must not own dope-memory chronicle history.
- It must not rely on bridge persistence as source truth unless canonical writer and receipts are explicit.


## Full Boundary Baseline

Every server-specific answer must preserve all of these Dopemux boundaries: dopemux is operator/control only; dopetask is external execution after wrapper handoff; Leantime owns passive PM metadata and snapshots; task-orchestrator owns workflow transitions and workflow views; ConPort owns structured decisions, progress, project context, custom data, and relationships; dope-memory owns chronicle receipts and evidence history; dope-context owns derived code/docs retrieval; dopecon-bridge is adapter/proxy/event transport only; Serena is support/code-intelligence unless runtime authority is proven.

## Authority Conflict Checks

- Does upstream task CRUD mutate metadata that belongs in Leantime?
- Does upstream memory/persistence overlap with ConPort or dope-memory?
- Does upstream status transition model support fail-closed legality?
- Does upstream include agent delegation that could bypass dopetask execution authority?
- Does any archived/forked lineage get treated as active base without evidence?

## Output Contract

Return exactly:

- `items`: Top-3 actionable findings.
- `more_count`
- `next_token`
- evidence matrix
- fact vs inference separation
- UNKNOWN list
- blocker list
- responsibility collision matrix
- implementation slices with validation

## UNKNOWN / Blocker Handling

If lineage history between jpicklyk, EchoingVesper, iflow, and package registries cannot be proven, keep each candidate separate and mark relationship `UNKNOWN`.

## Adopt / Adapt / Reject / Hide / Defer Table Requirements

Include rows for:

- task creation
- task decomposition
- workflow transition
- gates/quality checks
- specialist roles
- persistence
- memory integration
- templates
- archived EchoingVesper lineage
- iflow repackage lineage

## Validation Requirements

- Treat `jpicklyk/task-orchestrator` as preferred current base.
- Verify current jpicklyk tools and releases directly.
- Compare against Dopemux PM write split and task-orchestrator runtime drift.
- Propose validation for workflow legality, mirror receipts, and no metadata ownership.
