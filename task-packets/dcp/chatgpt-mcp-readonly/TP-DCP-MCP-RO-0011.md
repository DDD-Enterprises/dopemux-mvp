---
id: TP-DCP-MCP-RO-0011
title: Read-Only Runtime Registry And Catalog Join
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-07-11'
last_review: '2026-07-11'
next_review: '2026-10-09'
prelude: Join TP-0010 resolved exposure targets with operational MCP runtime and catalog evidence without making any backend callable.
---

# TP-DCP-MCP-RO-0011 — Read-Only Runtime Registry And Catalog Join

Objective: Add the smallest runtime-aware DCP slice after TP-0010. The join consumes a resolved target, the canonical catalog, and operational runtime records through explicit inputs, then returns internal non-callable candidate state.

Scope: explicit nine-family mapping, exact project/worktree scope matching for per-worktree services, catalog contract validation, ambiguity blocking, missing-input `UNKNOWN`, blocked-family handling, and public redaction.

Out of scope: sockets, TCP/MCP/REST probes, Docker/container inspection, port leases, ownership adjudication, mount evidence, backend calls, adapter rewiring, tunnel/authentication, caching, receipts, and Task Orchestrator exposure.

The exposure policy registry remains consent authority. The runtime registry and catalog are operational/advisory evidence only. `to_mcp_wrapper` and `to_compose_rest` remain blocked.

See the JSON packet for invariants, allowlist, validation commands, and proof obligations.
