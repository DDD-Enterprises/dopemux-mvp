---
id: responsibility-collision-matrix
title: Responsibility Collision Matrix
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-01'
last_review: '2026-05-01'
next_review: '2026-07-30'
prelude: Responsibility Collision Matrix (explanation) for dopemux documentation and
  developer workflows.
---
# Responsibility Collision Matrix

Access date: 2026-04-28

| Responsibility | Dopemux authority | Upstream pressure | Collision risk | Required disposition |
| --- | --- | --- | --- | --- |
| PM metadata | Leantime | Task orchestration packages may expose task CRUD | Workflow tools can mutate metadata without Leantime receipts | Adapt only through PM write router; reject direct metadata ownership |
| Workflow transitions | task-orchestrator | jpicklyk/task-orchestrator and EchoingVesper lineage both model tasks/gates | Transition authority can drift into Leantime, bridge, or memory packages | Adapt jpicklyk concepts into task-orchestrator only |
| Decisions/progress | ConPort | ConPort, task tools, and memory tools all log state | Multiple decision/progress writers create split truth | Adopt ConPort as canonical; mirror receipts only |
| Chronicle history | dope-memory | Claude-Mem and Mem0 store/update memories | Summaries or mutable memory can replace evidence history | Adapt hook ingestion; reject destructive canonical chronology |
| Code/docs retrieval | dope-context | claude-context and Serena both search code | Semantic ranking can become untraceable source truth | Adapt with deterministic ranking/provenance gates |
| Symbol/code intelligence | Serena support surface | Serena provides read, write, shell, refactor tools | Edit tools bypass worktree/task-packet gates | Adopt read-only support; hide write/shell by default |
| Bridge routing | dopecon-bridge | Many systems expose proxy/adapter endpoints | Proxy paths look authoritative | Keep bridge operational only; never source truth |
| External hosted memory | none by default | Mem0 hosted MCP | Private repo memory leaves local evidence plane | Defer or hide unless explicit operator approval and audit semantics exist |

## Drift To Preserve

- Task Orchestrator preferred active upstream is `jpicklyk/task-orchestrator`.
- `EchoingVesper/mcp-task-orchestrator` is archived and remains lineage evidence.
- `iflow-mcp/echoingvesper-mcp-task-orchestrator` is a fork/repackage lineage, not a separate proven canonical base.
- `claude-mem` seed and package lineage are split between `customable/claude-mem` and `thedotmack/claude-mem`.
- `mem0-mcp-server` PyPI metadata points to a repository URL that returned 404 through GitHub API during this pass.
