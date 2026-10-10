---
id: serena-deployment-alignment
title: Serena Deployment Alignment and Sanctioned Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-20'
last_review: '2026-03-20'
next_review: '2026-06-18'
prelude: Aligns Serena's documented role with the repo-proven deployed runtime and narrows the PM-plane contract to supported technical-context behavior.
---
# Serena Deployment Alignment and Sanctioned Contract

## Runtime alignment result

Repo-proven deployment points to the dockerized Serena wrapper, not the larger local `services/serena/` implementation tree.

Evidence used:

- `docker/compose.core.yml`
- `docker/mcp-servers-source/serena/Dockerfile`
- `docker/mcp-servers-source/serena/wrapper.py`
- `docker/mcp-servers-source/serena/info_server.py`

## Drift summary

The repo currently contains two materially different Serena surfaces:

1. deployed/runtime candidate: lightweight wrapper around upstream Serena
2. local implementation candidate: larger service tree with additional tools and ConPort integrations

PM-plane integration must follow the deployed/runtime candidate until proven otherwise.

## ConPort write boundary

Repo-proven active runtime path does not show ConPort writes.

Local non-deployed candidate code does include ConPort-writing behavior. That behavior is not sanctioned for PM-plane dependency because the packet did not prove it is deployed.

Authority rule:

- Serena is technical context only
- any Serena-produced ConPort writes, if ever activated, are bounded producer behavior only
- Serena does not become canonical for PM, workflow, decision, or progress truth

## Sanctioned PM-plane contract

Allowed now:

- `pm_get_technical_context`

This contract is:

- read-oriented
- technical-context only
- provenance-preserving
- non-authoritative for PM/workflow/decision/progress objects

Blocked pending live proof:

- `pm_get_implementation_context`
- `pm_get_code_impact_context`
- `pm_get_technical_risks`

## Excluded from PM-plane dependency

Until deployment proof changes, the PM plane must not depend on:

- local `services/serena/` MCP tool inventory
- local `services/serena/` HTTP endpoints
- local Serena → ConPort write paths
