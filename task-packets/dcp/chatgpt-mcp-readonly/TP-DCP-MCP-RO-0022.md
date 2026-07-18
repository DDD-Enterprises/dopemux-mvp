---
id: TP-DCP-MCP-RO-0022
title: Gate-0C Live Exemplar And Registry Hygiene
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-17'
last_review: '2026-07-17'
next_review: '2026-10-15'
prelude: Stand up and verify the clean per-worktree dope-memory exemplar; reconcile runtime-registry and lease hygiene.
---

# TP-DCP-MCP-RO-0022 - Gate-0C Live Exemplar And Registry Hygiene

Objective: Stand up and verify the Gate-0C live exemplar set on the operator host: purge the dNh_CRM ledger contamination (using the TP-0021 tool), recreate the mvp dope-memory container with correct identity env (removing the leaked DOPE_MEMORY_WORKSPACE_ID=dNh_CRM), fulfill or release the unfulfilled per-worktree lease (3054) by starting a per-worktree dope-memory sidecar for the active DCP worktree via the proven compose-override path, restore mcp-conport_dnh_crm_8d6d to healthy, and reconcile runtime-registry hygiene (release ~30 stale test leases, register the 5 unregistered live containers, resolve the 6 conflicting task-orchestrator identity claims on port 7890).

Depends on: TP-DCP-MCP-RO-0021. Executor: shell.

See the JSON load packet for invariants, validation commands, and step detail.
