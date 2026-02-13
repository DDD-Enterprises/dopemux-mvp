---
id: 00_INDEX
title: 00 Index
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-13'
last_review: '2026-02-13'
next_review: '2026-05-14'
prelude: 00 Index (explanation) for dopemux documentation and developer workflows.
---
# Dopemux Index

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
