---
id: README_UPLOAD_ORDER
title: Readme Upload Order
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-07'
last_review: '2026-05-07'
next_review: '2026-08-05'
prelude: Readme Upload Order (explanation) for dopemux documentation and developer
  workflows.
---
# MCP Customization Deep Research Upload Order

Access date: 2026-04-28

Upload in this order:

1. `dr-upload/00-dopemux-context-boundaries.md`
2. `dopemux-constraints/upstream-source-manifest.json`
3. `dopemux-constraints/dopemux-authority-map.json`
4. `dopemux-constraints/upstream-surface-inventory.json`
5. `dopemux-constraints/responsibility-collision-matrix.md`
6. `dr-upload/01-conport.md`
7. `dr-upload/02-task-orchestrator.md`
8. `dr-upload/03-serena.md`
9. `dr-upload/04-claude-context.md`
10. `dr-upload/05-claude-mem.md`
11. `dr-upload/06-mem0.md`
12. `dr-upload/07-cross-system-synthesis.md`

Deep Research must preserve the Dopemux authority split:

- dopemux controls operator startup and routing.
- dopetask executes after wrapper handoff.
- Leantime owns passive PM metadata and snapshots.
- task-orchestrator owns workflow-significant transitions and workflow views.
- ConPort owns structured decisions, progress, project context, custom data, and relationships.
- dope-memory owns chronicle receipts and evidence history.
- dope-context owns derived code/docs retrieval.
- dopecon-bridge routes and proxies only.
- Serena is support/code-intelligence unless runtime authority is proven.

Preferred Task Orchestrator upstream candidate: `jpicklyk/task-orchestrator`.

Known blockers to carry forward:

- `dopetask-cannonical-spec.json` was not found in this checkout.
- Task-orchestrator runtime packaging remains conflicted in Dopemux repo truth.
- Serena canonical implementation/deployment remains UNKNOWN.
- Some external docs did not expose stable date/version headers.
