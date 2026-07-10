---
id: TP-DCP-MCP-RO-0010
title: Exposure Target Registry V2 And Pure Resolver Core
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-09'
last_review: '2026-07-09'
next_review: '2026-10-07'
prelude: Implement exposure-target registry v2 parsing and a pure deterministic filesystem/repository identity resolver core for the DCP read-only facade.
---

# TP-DCP-MCP-RO-0010 — Exposure Target Registry V2 And Pure Resolver Core

Objective: Implement pure target loading and filesystem/repository identity resolution for the DCP read-only facade per `ADR-DCP-MCP-RO-0009`.

Scope: parse registry v2, validate approved roots, resolve workspace realpaths, validate init/identity markers, derive project and worktree roots, bind per-service-family policies, expose the opaque `target_id` as the only caller handle, and report configured capability separately from live capability.

Out of scope: runtime instance registry join, canonical MCP catalog join, candidate discovery, Docker inspection, port leases, TCP/MCP/REST probes, ownership adjudication, backend calls, tunnel, and authentication. All behavior is deterministic and testable without any running service.

See the JSON load packet for validation commands, invariants, and step detail.
