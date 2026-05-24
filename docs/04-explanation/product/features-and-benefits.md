---
id: features-and-benefits
title: Features And Benefits
type: explanation
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Repo-grounded Dopemux features, benefits, evidence, and limitations.
---
# Features And Benefits

This document separates implemented repo evidence from product benefit
language. Benefits are product interpretation; authority and limitations remain
grounded in the repo.

| Feature area | Implemented evidence | Benefit | Limitation |
| --- | --- | --- | --- |
| Operator CLI | `dopemux` entrypoint and command family | Gives the operator a control surface for workspace coordination | Does not own every domain it can reach |
| Execution handoff | `scripts/taskx`, `scripts/dopetask`, `.dopetask-pin` | Keeps execution behind an explicit handoff boundary | External `dopetask` runtime is not implemented in this repo |
| PM metadata | Leantime adapters and PM docs | Keeps passive PM facts in the PM application lane | Does not prove workflow legality |
| Workflow transitions | task-orchestrator service and Task Orchestrator workflow | Centralizes queue, blocker, and transition handling | Does not own all PM state |
| Structured decisions and progress | ConPort PM routes and system docs | Keeps decisions and progress queryable as structured context | Does not replace Leantime metadata or dope-memory chronology |
| Chronicle receipts | dope-memory runtime and chronicle docs | Preserves historical receipts and evidence trails | dope-memory is not all memory |
| Code/docs retrieval | dope-context indexing and retrieval surfaces | Helps operators find relevant source/docs quickly | Retrieval output is derived, not source truth |
| Bridge/proxy routing | dopecon-bridge routes and policy checks | Connects systems through compatibility and event surfaces | dopecon-bridge is not PM, workflow, decision, progress, memory, or retrieval authority |
| Operator support | ADHD Engine service family | Supports workload, cognitive-state, and recommendations | It does not own PM or memory truth |
| Repo audit | Repo Truth Extractor v5 runner and docs | Produces evidence artifacts for repo-truth work | Artifacts do not outrank runtime code/config/tests |
| Documentation governance | Task Packets, source map, gap register, validators | Makes docs changes auditable and replayable | Full-repo docs hygiene still has remaining debt |

## Implemented

- A repo-grounded operator-control surface exists through `dopemux`.
- The execution handoff boundary is explicit.
- The PM plane is documented and implemented as split by concern.
- dopecon-bridge has a clear proxy/adapter role.
- dope-context and ConPort provide retrieval/context surfaces.
- dope-memory provides chronicle receipt authority.
- Repo Truth Extractor provides evidence artifacts.

## Experimental Or Drifted

- Some runtime packaging, port, and launch surfaces remain drifted.
- Some support services are active but not fully promoted to canonical system
  authority.
- Agent-family ownership remains UNKNOWN.

## Vision

The product direction is a smoother operator experience over the split system,
not a hidden unification of authority. Any future claim that a drift area is
closed needs runtime verification.
