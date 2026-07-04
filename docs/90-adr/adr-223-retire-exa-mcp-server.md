---
id: adr-223
title: ADR-223 - Retire the exa MCP Server
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-08-04'
status: accepted
prelude: Architecture Decision Record for decommissioning the exa (neural web search) MCP server from the fleet catalog, compose stack, and source tree.
graph_metadata:
  node_type: ADR
  impact: low
  relates_to: []
---

# ADR-223: Retire the exa MCP Server

**Status**: Accepted
**Date**: 2026-07-04
**Owners**: @hu3mann

## Context

The `exa` MCP server (neural web search, container `mcp-exa`, port 3011) was pinned in the fleet catalog with `lifecycle: decision-required` and `follow_on_decision: wire-or-retire` (see `REQUIRED_SERVER_PERSONALITIES["exa"]` in `src/dopemux/mcp/fleet_catalog.py` and the matching entry in `src/dopemux/mcp/default_catalog.yaml` / `mcp_catalog.yaml`). That lifecycle state meant the fleet-audit tooling would keep flagging it until an operator made an explicit wire-or-retire call.

PR #1002's MCP fleet audit established the following facts:

- **Zero client consumers**: `exa` is not present in the repo's `.mcp.json` (per-worktree generated config), and no committed Claude or Codex configuration in this repository wires it in. It was never promoted out of `decision-required` quarantine into any startable generated output (`local/.mcp.json`, `claude/mcpServers.json`, `codex/config.toml`), by design of the decision-required quarantine gate.
- **Broken exec target**: the catalog's `docker exec` command (`docker exec -i -e MCP_RUN_MODE=stdio mcp-exa python /app/exa_server.py`) targets a container that, in at least one drifted config surface, pointed at the wrong container entirely (`mcp-litellm` instead of `mcp-exa`), and in the canonical catalog was never exercised end-to-end by any consumer.
- **Fallback already exists**: doctrine (`~/.claude/MCP_Exa.md`, `MODE_DeepResearch.md`) already documents `WebSearch` as the fallback when Exa is absent, so no capability gap opens by retiring it.

Given zero consumers, a broken/unverified exec path, and an existing fallback, the wire-or-retire decision resolves to **retire**.

## Decision

Fully decommission `exa` from the MCP fleet:

1. Remove the `exa:` server block from both `src/dopemux/mcp/default_catalog.yaml` and `mcp_catalog.yaml` (kept byte-identical).
2. Remove the `"exa"` entry from `REQUIRED_SERVER_PERSONALITIES` in `src/dopemux/mcp/fleet_catalog.py` — the personality contract errors on drift *or absence* of pinned servers, so the pin must be removed in the same change that removes the catalog entry.
3. Remove the `exa:` service block from `compose.yml`.
4. Delete the server source directory `docker/mcp-servers-source/exa/` (Dockerfile, README, `exa_server.py`, `requirements.txt`); `docker/mcp-servers/exa` is a symlink into that source tree and resolves away automatically.
5. Remove the orphaned `exa` entry from `services/registry.yaml` (marked `enabled_in_smoke: false`, so its removal does not affect smoke-stack alignment checks, but leaving it would point at a compose service that no longer exists).
6. Update the fleet-catalog test suite's real-catalog assertions (`tests/unit/test_mcp_fleet_catalog.py`, `tests/arch/test_mcp_fleet_catalog_contract.py`) to no longer expect `exa` as a decision-required server, and add non-startability lock assertions confirming `exa`/`mcp-exa` is not a compose service and `docker/mcp-servers-source/exa` does not exist.

Synthetic test fixtures that merely use the string `"exa"` to name a server in a self-contained test catalog (not the real one) are left unchanged — they test mechanisms (docker-exec drift detection, sync-globals dry-run/apply/prune behavior), not the real `exa` server.

## Consequences

- Exa-brand neural web search is no longer available via MCP in this repository. `WebSearch` remains the documented fallback for web lookups when a dedicated search MCP is absent.
- The fleet-audit "decision-required" backlog shrinks by one; only `desktop-commander` remains pending its own wire-or-retire decision.
- Re-introducing Exa (or any neural-search MCP) in the future requires: a fresh catalog entry with a verified (not just declared) docker-exec or HTTP target, a personality-contract pin if it should be tracked, compose wiring with a working healthcheck, and this ADR should be marked superseded by the new one.
- Several documentation and archived-audit surfaces still mention Exa (e.g. `INSTALL.md`, `TASK_ORCH_MCP_PLUGIN_SURFACE.md`, `docker/mcp-servers-source/*.md`, `.claude/commands/docs/find.md`, `.claude/commands/web/triage.md`, `mcp-proxy-config.*`). These are historical/dormant references, not live fleet wiring, and are left for a follow-up documentation pass rather than blocking this retirement.

## Alternatives Considered

**Wire it natively** at `http://localhost:3011/mcp` (the compose service already exposed this port) instead of retiring. Rejected: there was no consumer demand driving the wire decision, and wiring it would add a new external-API-key dependency (`EXA_API_KEY`) plus recurring cost surface for a capability that `WebSearch` already covers as a fallback. Retiring is the minimal-blast-radius choice consistent with "no consumer, no reason to keep."
