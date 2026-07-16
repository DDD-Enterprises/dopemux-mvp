---
id: dcp-mcp-readonly-runtime-catalog-join-contract
title: DCP Read-Only MCP Facade - Runtime Registry And Catalog Join Contract
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-07-11'
last_review: '2026-07-11'
next_review: '2026-10-09'
prelude: Internal, read-only join contract for operational MCP catalog and runtime evidence after target identity resolution.
---

# Runtime Registry And Catalog Join Contract

Status: implemented in TP-DCP-MCP-RO-0011 as a pure facade-local join. This contract is intentionally narrower than live runtime authorization.

## Authority boundary

The exposure policy registry is the consent authority. TP-0010 resolves its `target_id` to a validated `ResolvedTarget`. The canonical MCP catalog describes operational service names and static management semantics. The runtime registry records operational instances. The latter two inputs are advisory evidence only and are read-only to this facade.

The join never starts, stops, repairs, adopts, reconciles, probes, or calls a service. A joined candidate remains `callable: false` until later gates independently verify liveness, protocol identity, ownership, project identity, worktree/data scope, freshness, read-only route policy, and redaction.

## Explicit family mapping

The facade accepts only the nine ADR family names from registry v2. The join uses this fixed translation:

| Facade family | Catalog name | TP-0011 posture |
| --- | --- | --- |
| `conport` | `conport` | Candidate join allowed; still non-callable |
| `dope_memory` | `dope-memory` | Candidate join allowed; still non-callable |
| `to_compose_rest` | none | Blocked; route isolation is not proven |
| `to_mcp_wrapper` | `task-orchestrator` | Blocked; reserved singleton and write-capable |
| `dope_context` | `dope-context` | Blocked until read bridge |
| `serena` | `serena` | Blocked until inventory |
| `pal` | `pal` | Blocked |
| `docker_mcp_gateway` | `MCP_DOCKER` | Blocked |
| `desktop_commander` | `desktop-commander` | Blocked |

No hyphen/underscore normalization or caller-supplied operational name is accepted. The bare `task-orchestrator` name remains forbidden as a facade policy family.

## Candidate matching

For `conport` and `dope_memory`, a runtime record is a candidate only when all of these match exactly after local path canonicalization:

1. Runtime `service` equals the explicit catalog name.
2. Runtime `project_id` equals the generated `ProjectIdentity.project_id` derived from the resolved project and worktree roots, matching lifecycle-written runtime records.
3. Runtime `project_root` equals the resolved project root.
4. Runtime `worktree_root` equals the resolved worktree root.

Project name, worktree hash, port, container name, compose name, URL, or lease alone never matches a candidate. One candidate produces internal state `UNKNOWN` because liveness and ownership are not proven. Zero candidates produce `UNAVAILABLE`. Multiple candidates produce `BLOCKED` and no candidate is selected.

The registry `.repo_id` project identity is validated earlier when resolving the
DCP target. It authorizes the target but is intentionally not reused as the
runtime record `project_id`, which follows the shared generated lifecycle
identity.

Missing or malformed catalog/runtime input produces `UNKNOWN`. Catalog policy drift produces `BLOCKED`. Disabled or blocked exposure policy produces `BLOCKED`.

## Public redaction

The public result contains only the facade family, capability state, an opaque reason, and `callable: false`. It does not contain paths, ports, URLs, hostnames, container names or IDs, runtime instance IDs, lease IDs, raw runtime records, or backend workspace IDs.

## Out of scope

TP-0011 does not implement live TCP/MCP/REST verification, Docker or mount inspection, ownership evidence tiers, freshness checks, caching, resolution receipts, adapter rewiring, tunnel/authentication, or remote ChatGPT exposure.
