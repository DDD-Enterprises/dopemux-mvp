---
id: orchestrator-context-refresh
title: Context Status & Refresh Flow
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-28'
prelude: Reference explaining modified file cache checks and gated context freshness nudging.
related_packets:
  - TP-DMX-ORCH-008
---

# Context Status & Refresh Workflow

The context refresh workflow ensures that the agent's context window stays fresh relative to recent upstream code mutations.

## Workflow Mechanics
1.  **Freshness Check**: Audits modified file times and ConPort decisions against the active local cache.
2.  **Nudge Notification**: Prompts the operator or agent with a context refresh plan if key files have mutated mid-flight.
