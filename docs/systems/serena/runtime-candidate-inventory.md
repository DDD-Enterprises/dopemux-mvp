---
id: serena-runtime-candidate-inventory
title: Serena Runtime Candidate Inventory
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-20'
last_review: '2026-03-20'
next_review: '2026-06-18'
prelude: Evidence-backed inventory of Serena runtime candidates, transports, and deployment status.
---
# Serena Runtime Candidate Inventory

## Active runtime candidate

| candidate | status | evidence | transport | ports | auth posture | backing source path |
|---|---|---|---|---|---|---|
| Dockerized Serena wrapper | active runtime candidate | `docker/compose.core.yml` wires service `serena` to `docker/mcp-servers/serena`, which resolves to `docker/mcp-servers-source/serena` | FastAPI info server + MCP-over-SSE proxy | `4006` HTTP info, `3006` SSE proxy by default | no repo-proven auth on health/info; wrapper inherits upstream Serena behavior | `docker/mcp-servers-source/serena/` |

## Non-sanctioned local candidate

| candidate | status | evidence | transport | ports | auth posture | backing source path |
|---|---|---|---|---|---|---|
| Local Serena implementation tree | local implementation candidate, not repo-proven deployed | rich local code under `services/serena`, but compose does not point to it | local MCP server + local FastAPI candidate | repo-local only | includes local write-capable integrations; deployment not proven | `services/serena/` |

## Active runtime decision

The active Serena runtime for PM-plane purposes is the dockerized wrapper path:

- `docker/mcp-servers/serena/`
- resolved source: `docker/mcp-servers-source/serena/`

The local `services/serena/` tree is not sanctioned as an active PM-plane dependency until deployment evidence proves it is the runtime in use.
