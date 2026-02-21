---
title: Dopemux PM Plane Docs
plane: pm
component: dopemux
status: skeleton
id: 00_INDEX
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Dopemux PM Plane Docs (explanation) for dopemux documentation and developer
  workflows.
---
# Dopemux PM Plane Docs (Canonical)

## What Dopemux is

Dopemux is a runtime fabric for:
- context + memory
- runner/model routing
- MCP lifecycle reliability
- ADHD-centered execution UX
- deterministic execution via TaskX (by boundary contract)

TODO: 1 paragraph “what problems it solves” in plain English.

## The boundary (non-negotiable)

### TaskX is the deterministic engine
TaskX is responsible for deterministic orchestration and artifacts only.

### Dopemux Supervisor is the adaptive control plane
Dopemux is responsible for policies, routing, memory, and MCP management.

TODO: Insert the short boundary bullets from the Brain Dump, verbatim where possible.

## How to navigate these docs

Read order:
1. [01_SYSTEM_ARCHITECTURE.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/01_SYSTEM_ARCHITECTURE.md)
1. [07_TASKX_INTEGRATION.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/07_TASKX_INTEGRATION.md)
1. [02_MEMORY_AND_STATE.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/02_MEMORY_AND_STATE.md)
1. [03_MCP_LIFECYCLE_AND_RELIABILITY.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/03_MCP_LIFECYCLE_AND_RELIABILITY.md)
1. [04_ROUTING_POLICY_AND_COST.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/04_ROUTING_POLICY_AND_COST.md)
1. [05_ADHD_EXECUTION_MODEL.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/05_ADHD_EXECUTION_MODEL.md)
1. [06_INSTANCE_AND_WORKTREE_ISOLATION.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/06_INSTANCE_AND_WORKTREE_ISOLATION.md)
1. [08_SUPERVISOR_PACKET_FORMAT.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/08_SUPERVISOR_PACKET_FORMAT.md)
1. [09_USAGE_LIMITS_AND_RESETS.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/09_USAGE_LIMITS_AND_RESETS.md)
1. [10_PLAYBOOKS.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/10_PLAYBOOKS.md)

## Glossary

TODO: Create a small glossary section with pointers:
- Task Packet
- Runner
- Model
- MCP
- Workspace / worktree / instance
- Artifact
- ConPort
- Promotion

## Doc set index
- [01_SYSTEM_ARCHITECTURE.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/01_SYSTEM_ARCHITECTURE.md)
- [02_MEMORY_AND_STATE.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/02_MEMORY_AND_STATE.md)
- [03_MCP_LIFECYCLE_AND_RELIABILITY.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/03_MCP_LIFECYCLE_AND_RELIABILITY.md)
- [04_ROUTING_POLICY_AND_COST.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/04_ROUTING_POLICY_AND_COST.md)
- [05_ADHD_EXECUTION_MODEL.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/05_ADHD_EXECUTION_MODEL.md)
- [06_INSTANCE_AND_WORKTREE_ISOLATION.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/06_INSTANCE_AND_WORKTREE_ISOLATION.md)
- [07_TASKX_INTEGRATION.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/07_TASKX_INTEGRATION.md)
- [08_SUPERVISOR_PACKET_FORMAT.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/08_SUPERVISOR_PACKET_FORMAT.md)
- [09_USAGE_LIMITS_AND_RESETS.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/09_USAGE_LIMITS_AND_RESETS.md)
- [10_PLAYBOOKS.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/10_PLAYBOOKS.md)
- [DEEP_RESEARCH.md](file:///Users/hue/code/dopemux-mvp/docs/planes/pm/dopemux/DEEP_RESEARCH.md)

## Self-verification
TODO: Link to docs gate script location once implemented.

---

## Doc Gate Checklist

This doc set is treated as a spec harness. If the gate fails, implementation work stops until fixed.

### Required files exist
- [ ] 00_INDEX.md
- [ ] 01_SYSTEM_ARCHITECTURE.md
- [ ] 02_MEMORY_AND_STATE.md
- [ ] 03_MCP_LIFECYCLE_AND_RELIABILITY.md
- [ ] 04_ROUTING_POLICY_AND_COST.md
- [ ] 05_ADHD_EXECUTION_MODEL.md
- [ ] 06_INSTANCE_AND_WORKTREE_ISOLATION.md
- [ ] 07_TASKX_INTEGRATION.md
- [ ] 08_SUPERVISOR_PACKET_FORMAT.md
- [ ] 09_USAGE_LIMITS_AND_RESETS.md
- [ ] 10_PLAYBOOKS.md
- [ ] DEEP_RESEARCH.md

### Required headings exist in every doc
Each doc must contain these headings (exact text):
- [ ] ## Purpose
- [ ] ## Scope
- [ ] ## Non-negotiable invariants
- [ ] ## FACT ANCHORS (Repo-derived)
- [ ] ## Open questions

### Index links resolve
- [ ] All links in this index point to existing files.
- [ ] No duplicate doc titles (single source of truth per concept).

### UNKNOWN discipline
- [ ] No "UNKNOWN" appears outside "FACT ANCHORS" or "Open questions".
- [ ] Every UNKNOWN has a matching bullet in "Open questions" describing:
- [ ] what is unknown
- [ ] what file/command would resolve it

### Boundary enforcement (TaskX vs Supervisor)
- [ ] 07_TASKX_INTEGRATION.md states TaskX is deterministic and does not own:
  policy, memory, MCP lifecycle, cost optimization, routing intelligence.
- [ ] No other doc assigns those responsibilities to TaskX.

### Evidence hygiene
- [ ] FACT ANCHORS bullets include repo pointers in `path:line-range` form when available.
- [ ] Every non-trivial claim outside FACT ANCHORS is backed by a FACT ANCHOR or marked ASSUMPTION.

### Operational readiness
- [ ] 10_PLAYBOOKS.md contains: MCP down, limits low, fatigue/ADHD, and tests-fail RCA loops.

### Research Bundle Hygiene
- [ ] `docs/planes/pm/dopemux/research/` contains only structured bundles.
- [ ] Each bundle contains required files (`BUNDLE_INDEX.json` or lightweight set).
- [ ] `DEEP_RESEARCH.md` rules followed for all claims.
