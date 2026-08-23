---
id: dcp-mcp-readonly-tool-contract
title: DCP Read-Only MCP Facade - Public Tool Contract
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Registry-v2 public tool contract for the local, read-only DCP MCP evidence facade.
---
# Public Tool Contract

## Status

`TP-DCP-MCP-RO-0012` implements this public server surface. It is local-only:
no public ingress, tunnel, connector, credential, lifecycle operation, or
backend service call is enabled by this contract.

The earlier v1 `project_id` tool and direct-service-profile modules remain
historical implementation artifacts only. `mcp.server` does not import them.
They are not part of the public MCP tool manifest.

## Target Contract

Every target-scoped tool requires a bounded opaque `target_id`. It is the only
caller-provided target handle. Caller values that resemble a path, URL, port,
route, workspace ID, SQL fragment, or shell input are blocked without being
reflected in the response.

The server loads registry v2 through `DCP_FACADE_REGISTRY_V2`. An enabled
target must resolve inside an approved root, pass Dopemux workspace validation,
and match its declared `.repo_id` identity. Resolution is fail-closed.

## Public Tools

| Tool | `target_id` | Evidence | Authority | Behavior |
| --- | --- | --- | --- | --- |
| `list_targets` | no | registry-v2 policy | facade | Lists enabled opaque target IDs only. |
| `get_target_capabilities` | required | static policy table | facade | Reports configured state; `live` remains `UNKNOWN` and `callable` is always `false`. |
| `get_target_repo_state_snapshot` | required | local git | OBSERVED/git | Returns branch, head SHA, and dirty state. |
| `list_target_proof_bundles` | required | local `proof/` | OBSERVED/fs | Literal bounded filter, cap 20, no traversal. |
| `fetch_target_proof_bundle` | required | local `proof/` | OBSERVED/fs | Containment- and symlink-checked bounded file reads. |
| `get_target_runtime_receipt` | required | local catalog and runtime registry | DERIVED | Returns a redacted, non-callable candidate receipt. |

`get_target_runtime_receipt` reads only local files: the resolved project's
`mcp_catalog.yaml` (or operator-set `DCP_FACADE_MCP_CATALOG`) and the local
runtime registry (or operator-set `DOPEMUX_MCP_RUNTIME_REGISTRY`). Missing or
malformed evidence yields `PARTIAL`; a matching candidate remains `UNKNOWN`
and `callable: false`. No endpoint, URL, port, container, or operational name
is exposed.

## Explicitly Absent

The public manifest contains no backend adapter, generic fetch, endpoint
selection, task transition, PM mutation, tunnel, ingress, connector, or
runtime lifecycle tool. Existing adapter modules are deferred to a later
authorized child packet with ownership and live-read evidence.

Every response uses the v2 [`RESPONSE_ENVELOPE_SCHEMA.md`](RESPONSE_ENVELOPE_SCHEMA.md).
Paths and recognized secret patterns are redacted before a response leaves the
facade.
