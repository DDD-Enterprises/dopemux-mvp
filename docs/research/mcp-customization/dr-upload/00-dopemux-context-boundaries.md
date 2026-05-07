---
id: 00-dopemux-context-boundaries
title: 00 Dopemux Context Boundaries
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-07'
last_review: '2026-05-07'
next_review: '2026-08-05'
prelude: 00 Dopemux Context Boundaries (explanation) for dopemux documentation and
  developer workflows.
---
# DR Pack 00: Dopemux Context Boundaries

Access date: 2026-04-28

## Objective

Establish Dopemux authority boundaries before evaluating upstream MCP/server families. Use this pack as the first upload for every server-specific Deep Research pass.

## Source Seeds

- `PROJECT.md`
- `ARCHITECTURE.md`
- `PM_PLANE.md`
- `docs/03-reference/truth/truth-canonicals.md`
- `docs/03-reference/truth/truth-gaps.md`
- `docs/03-reference/truth/truth-interfaces.md`
- `docs/03-reference/systems/system-boundaries.md`
- `docs/research/mcp-customization/data/dopemux-authority-map.json`
- `docs/research/mcp-customization/data/responsibility-collision-matrix.md`

## Required Extraction Fields

- system
- observed authority
- canonical writer
- readers/consumers
- derived/cache/advisory surfaces
- forbidden ownership
- runtime evidence
- docs evidence
- UNKNOWNs
- drift
- confidence

## Dopemux Boundary Constraints

- dopemux is operator/control plane only.
- dopetask is the external execution runtime reached through `scripts/taskx -> scripts/dopetask`.
- PM authority is split: Leantime metadata, task-orchestrator workflow, ConPort decisions/progress/context/custom data, dope-memory chronicle receipts.
- Memory is split: dope-memory chronology, ConPort structured context, working-memory-assistant support unless proven otherwise.
- Retrieval is split: dope-context code/docs indexing, ConPort structured/semantic/graph retrieval.
- dopecon-bridge is adapter/proxy/event transport only.
- Serena is support/code-intelligence unless runtime authority is proven.
- Never collapse planes.


## Full Boundary Baseline

Every server-specific answer must preserve all of these Dopemux boundaries: dopemux is operator/control only; dopetask is external execution after wrapper handoff; Leantime owns passive PM metadata and snapshots; task-orchestrator owns workflow transitions and workflow views; ConPort owns structured decisions, progress, project context, custom data, and relationships; dope-memory owns chronicle receipts and evidence history; dope-context owns derived code/docs retrieval; dopecon-bridge is adapter/proxy/event transport only; Serena is support/code-intelligence unless runtime authority is proven.

## Authority Conflict Checks

- Does any bridge/proxy claim source truth?
- Does any retrieval index claim source truth?
- Does any memory package claim PM status authority?
- Does any task package claim Leantime metadata authority?
- Does any support/code-intelligence package bypass worktree and task-packet gates?
- Does any mirror omit canonical writer and receipt status?

## Output Contract

Return:

- `items`: exactly Top-3 actionable findings.
- `more_count`: count of additional findings not shown.
- `next_token`: stable drilldown token.
- evidence matrix with title, URL/path, access date, version/commit/release, source type, confidence.
- fact vs inference separation.
- UNKNOWN list.
- blocker list.
- responsibility collision matrix.
- adopt/adapt/reject/hide/defer table.
- implementation slices with validation.

## UNKNOWN / Blocker Handling

Mark `UNKNOWN` when runtime ownership, current upstream state, or canonical writer cannot be proven. Do not infer authority from names, docs, routes, wrappers, or package branding.

## Adopt / Adapt / Reject / Hide / Defer Requirements

Every recommendation must include:

| Candidate | Domain | Disposition | Reason | Authority preserved | Validation |
| --- | --- | --- | --- | --- | --- |

## Validation Requirements

- Cite runtime code/config/tests before docs where available.
- Preserve doc-vs-runtime drift instead of smoothing it over.
- Identify canonical writer and likely readers for every shared artifact or state domain.
- State residual risk for each unresolved authority.
