---
id: 07-cross-system-synthesis
title: 07 Cross System Synthesis
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-07'
last_review: '2026-05-07'
next_review: '2026-08-05'
prelude: 07 Cross System Synthesis (explanation) for dopemux documentation and developer
  workflows.
---
# DR Pack 07: Cross-System Dopemux Customization Synthesis

Access date: 2026-04-28

## Objective

Synthesize Deep Research outputs for ConPort, Task Orchestrator, Serena, Claude Context, Claude-Mem, and Mem0 into a Dopemux customization strategy that preserves strict authority boundaries.

## Source Seeds

- `dr-upload/00-dopemux-context-boundaries.md`
- `dr-upload/01-conport.md`
- `dr-upload/02-task-orchestrator.md`
- `dr-upload/03-serena.md`
- `dr-upload/04-claude-context.md`
- `dr-upload/05-claude-mem.md`
- `dr-upload/06-mem0.md`
- `data/upstream-source-manifest.json`
- `data/upstream-surface-inventory.json`
- `data/dopemux-authority-map.json`
- `data/responsibility-collision-matrix.md`

## Required Extraction Fields

- upstream feature
- upstream server
- Dopemux target system
- authority domain
- disposition
- collision risk
- source evidence
- implementation slice
- validation command/test
- residual UNKNOWN

## Dopemux Boundary Constraints

- Keep PM metadata, workflow, decisions/progress, chronicle history, retrieval, bridge routing, code intelligence, and execution separate.
- Preferred active Task Orchestrator upstream is `jpicklyk/task-orchestrator`.
- EchoingVesper/iflow task-orchestrator sources are lineage evidence only unless Deep Research proves otherwise.
- Claude-Mem customable and thedotmack lineage must remain separate until provenance is proven.
- Mem0 external memory must remain hidden/deferred by default unless privacy and audit gates are explicit.


## Full Boundary Baseline

Every server-specific answer must preserve all of these Dopemux boundaries: dopemux is operator/control only; dopetask is external execution after wrapper handoff; Leantime owns passive PM metadata and snapshots; task-orchestrator owns workflow transitions and workflow views; ConPort owns structured decisions, progress, project context, custom data, and relationships; dope-memory owns chronicle receipts and evidence history; dope-context owns derived code/docs retrieval; dopecon-bridge is adapter/proxy/event transport only; Serena is support/code-intelligence unless runtime authority is proven.

## Authority Conflict Checks

- Duplicate memory capture/search/update/delete.
- Duplicate code search or symbol search.
- Duplicate task planning/workflow status.
- Duplicate decision/progress logging.
- Context injection replacing evidence.
- Bridge proxy routes claiming truth.
- External hosted services receiving private memory.

## Output Contract

Return exactly:

- `items`: Top-3 actionable findings.
- `more_count`
- `next_token`
- evidence matrix.
- fact vs inference separation.
- UNKNOWN list.
- blocker list.
- responsibility collision matrix.
- implementation slices with validation.

## UNKNOWN / Blocker Handling

Any final strategy must carry unresolved source lineage, package drift, runtime drift, and missing schema validation forward as explicit blockers or provisional assumptions.

## Adopt / Adapt / Reject / Hide / Defer Table Requirements

Produce a cross-system table:

| Feature | Source server | Dopemux target | Authority domain | Disposition | Reason | Validation |
| --- | --- | --- | --- | --- | --- | --- |

## Validation Requirements

- Verify every recommendation traces to a current source URL or repo path.
- Verify every proposed write has one canonical writer.
- Verify every mirror has receipt semantics.
- Verify retrieval outputs remain derived.
- Verify hidden/default-visible MCP tool lists for Codex and other hosts.
- Generate follow-up task packets only with fields allowed by the available dopetask schema; if schema remains missing, mark task-packet generation blocked.
