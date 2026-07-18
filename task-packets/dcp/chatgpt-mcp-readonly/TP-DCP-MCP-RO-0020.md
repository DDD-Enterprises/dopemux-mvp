---
id: TP-DCP-MCP-RO-0020
title: Wire Safe Adapters Into Public Facade Tools
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-17'
last_review: '2026-07-17'
next_review: '2026-10-15'
prelude: Expose release-one ConPort and dope-memory safe adapters as public target_id tools behind ownership and connector authorization.
---

# TP-DCP-MCP-RO-0020 - Wire Safe Adapters Into Public Facade Tools

Objective: Wire the TP-0015 release-one safe adapters (ConPort decision list/read; dope-memory chronicle search/replay) into the public FastMCP surface (services/dcp-readonly-facade/src/mcp/server.py + tools_v2) behind ownership verification and connector-policy target/tool authorization, extending the acceptance harness; hermetic tests only, no live backend required.

Depends on: TP-DCP-MCP-RO-0018. Executor: codex.

See the JSON load packet for invariants, validation commands, and step detail.
