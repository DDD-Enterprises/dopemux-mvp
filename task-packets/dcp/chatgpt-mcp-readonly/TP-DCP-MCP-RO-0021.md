---
id: TP-DCP-MCP-RO-0021
title: Dope-Memory Fail-Closed Workspace Guard
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-17'
last_review: '2026-07-17'
next_review: '2026-10-15'
prelude: Reject cross-workspace stores at the dope-memory boundary and ship a supervised contamination purge tool.
---

# TP-DCP-MCP-RO-0021 - Dope-Memory Fail-Closed Workspace Guard

Objective: Make dope-memory fail closed on workspace identity: reject store/ingest operations whose workspace_id does not match the configured workspace identity, add a supervised quarantine/purge tool for existing cross-repo rows, and cover both with tests - fixing the active contamination class found 2026-07-17 (dNh_CRM sidecar ledger accepting workspace_id=/Users/hue/code/dopemux-mvp rows).

Depends on: TP-DCP-MCP-RO-0018. Executor: codex.

See the JSON load packet for invariants, validation commands, and step detail.
