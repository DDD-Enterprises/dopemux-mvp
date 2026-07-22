---
id: ADR-DCP-MCP-RO-0009
title: ChatGPT MCP Exposure Targets, Runtime Resolution, and Ownership Evidence
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-09'
last_review: '2026-07-10'
next_review: '2026-10-08'
prelude: Accepted DCP read-only facade contract for opaque ChatGPT target IDs, scope-aware runtime resolution, live ownership evidence, and fail-closed backend exposure.
status: accepted
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - dcp-mcp-readonly-architecture
    - dcp-mcp-readonly-registry-contract
    - dcp-mcp-readonly-decisions
    - adr-memory-trinity-authority-and-interaction-model
---

# ADR-DCP-MCP-RO-0009: ChatGPT MCP Exposure Targets, Runtime Resolution, and Ownership Evidence

## Status

**ACCEPTED FOR CONTRACT IMPLEMENTATION.**

Runtime-dependent implementation remains blocked on this branch until the MCP runtime stack through PR #1031 is present on the target implementation base. Live GitHub state observed PR #1031 as merged on 2026-07-10 UTC, but the current `origin/main` used for this docs slice does not contain the PR #1031 merge commit or PR branch head by ancestry. Runtime code, config, tests, live process state, and current PR/base-branch state outrank this ADR.

## Context

ChatGPT Web can connect to one remotely reachable HTTPS MCP endpoint. It must not connect directly to local backend MCP servers because backend surfaces differ, some contain mutations, ports can drift, multiple repositories and worktrees coexist, and a listening port is not proof of service identity or ownership.

The existing DCP read-only facade already establishes a bounded local evidence projection layer. This ADR tightens the contract for ChatGPT-facing identity, runtime resolution, ownership adjudication, and public response redaction before broader remote MCP exposure.

## Decision

The facade shall resolve every ChatGPT backend read through this gate sequence:

```text
ChatGPT target_id
  -> Exposure Policy Registry
  -> Target Identity Validation
  -> Service Policy and Scope Resolution
  -> Operational Runtime Registry and Canonical MCP Catalog
  -> Candidate Discovery
  -> Live Protocol Verification
  -> Ownership Evidence Adjudication
  -> Read-Only Backend Adapter
```

Every required gate must pass before a backend call is made. No tunnel, remote transport, runtime registry record, catalog declaration, container, port, lease, or heuristic discovery result is itself a trust boundary.

## Public Identity Contract

The only ChatGPT-facing infrastructure identity is an opaque `target_id`.

An exposure target is an operator-approved consent and policy binding between a stable opaque identifier and exactly one repository or worktree evidence context. It is not a filesystem path, worktree hash, runtime instance ID, Task Orchestrator state ID, Docker identity, port, URL, backend workspace ID, or discovered MCP server.

ChatGPT may provide:

```json
{
  "target_id": "dopemux-main"
}
```

ChatGPT must never provide workspace paths, project roots, worktree roots, backend URLs, hosts, ports, container identifiers, workspace IDs, instance IDs, state IDs, compose projects, mount paths, raw backend routes, runtime selectors, or lease selectors.

Unknown or disabled targets fail closed.

## Default Worktree Exposure Policy

The default exposure binding mode is `PRIMARY_CHECKOUT_ONLY`.

A target binds to exactly one operator-approved workspace. Additional worktrees require distinct operator-created targets such as `dopemux-main`, `dopemux-pr-1031`, or `dopemux-release-candidate`.

The system must never automatically select the newest worktree, most recently active worktree, first healthy endpoint, first runtime-registry match, current facade branch, prompt-inferred path, Docker-reported worktree, `.mcp.json` inventory item, or port-lease-inferred worktree. An `.mcp.json` census is inventory evidence only; it does not represent consent.

## Identity Layers

The implementation must keep these identities distinct:

| Identity | Purpose | Client Visible |
| --- | --- | --- |
| `target_id` | Exposure consent and public handle | Yes |
| repository identity | Git and marker validation | No |
| exposure workspace | Filesystem evidence context | No |
| project root | Repository-level state resolution | No |
| worktree root | Worktree-level state resolution | No |
| runtime instance ID | Operational process record | No |
| backend workspace ID | Backend data partition | No |
| Task Orchestrator state ID | Task Orchestrator persistence key | No |
| container identity | Runtime ownership evidence | No |
| port | Transport detail | No |
| lease ID | Port allocator state | No |

Path-derived hashes must not become public target IDs.

## Registry Authority Split

The exposure policy registry is operator-authored, stored outside the repository, read-only to the facade, authoritative for ChatGPT access consent, and unable to start, stop, repair, adopt, or expose runtimes automatically.

The operational runtime registry is machine-generated, owned by `dopemux mcp`, operational state only, never an exposure-consent source, and read-only to the facade.

The canonical MCP catalog declares service families, process and state scope, transport, port variables, port policy, management model, and expected identity scope. The facade may consume catalog semantics but must not treat the catalog as proof that a runtime is live.

Port leases are allocator records, never ownership proof. For reserved singleton services, including Task Orchestrator MCP port `7890`, project or worktree leases are invalid operational residue. The facade may report the residue but must not mutate or reconcile it and must not use it to prove ownership.

## Required Service Families

The unqualified name `task-orchestrator` is forbidden in new facade contracts.

Required service-family identifiers are:

- `conport`
- `dope_memory`
- `to_compose_rest`
- `to_mcp_wrapper`
- `dope_context`
- `serena`
- `pal`
- `docker_mcp_gateway`
- `desktop_commander`

## Required Resolution Classes

Required resolution classes are:

- `per_worktree_runtime`
- `per_repo_runtime`
- `host_singleton_single_active_project`
- `host_singleton_project_routed`
- `singleton_per_call_workspace`
- `host_singleton`
- `blocked`

Current ChatGPT exposure posture:

| Service Family | Resolution Class | ChatGPT Posture |
| --- | --- | --- |
| `conport` | `per_worktree_runtime` | Conditional read-only |
| `dope_memory` | `per_worktree_runtime` | Conditional read-only |
| `to_compose_rest` | `host_singleton_project_routed` | Conditional GET-only |
| `to_mcp_wrapper` | `host_singleton_single_active_project` | Blocked |
| `dope_context` | `singleton_per_call_workspace` | Blocked until read bridge |
| `serena` | `singleton_per_call_workspace` | Blocked until inventory |
| `pal` | `host_singleton` | Blocked |
| `docker_mcp_gateway` | `host_singleton` | Blocked |
| `desktop_commander` | `host_singleton` | Blocked |

## Task Orchestrator Runtime Semantics

`to_mcp_wrapper` is a host-level runtime endpoint on reserved port `7890`. It can serve one active project at a time, is backed by project-specific persistent state selected by the active runtime, is declared from multiple repositories/worktrees but not concurrently routable across projects, and is write-capable.

`to_mcp_wrapper` remains blocked from ChatGPT Phase 1.

Its runtime semantics are:

```text
runtime_scope = host_singleton
state_scope = single_active_project
port_policy = reserved_singleton
reserved_port = 7890
```

A live listener on `7890` proves only that some Task Orchestrator MCP runtime is active. It does not prove which project is active. A port lease must never determine the active project.

`to_compose_rest` is a separate host-singleton process and contract. It is project-routed through request parameters or path segments, may expose reads and mutations, and is permitted only through explicit GET-only facade adapters after route-level project isolation is proven independently of global workspace state, process working directory, current active MCP-wrapper project, caller-controlled paths, and implicit process-global context.

Only `queue`, `blockers`, and `state` may eventually be exposed for `to_compose_rest`. Transition, update, progress-write, coordination-write, and arbitrary proxy behavior remain blocked.

## Ownership Evidence Model

Candidate discovery and ownership authorization are separate stages.

Tier A explicit identity evidence may authorize routing when all other gates pass. Examples include trusted runtime-registry identity, supported server identity endpoints, wrapper identity metadata from a trusted launcher, exact target workspace bind mounts with matching runtime identity, or exact project roots with matching deterministic project IDs from trusted metadata.

Tier B strong derived evidence may authorize only when evidence sources are independent, no conflicting explicit evidence exists, service policy permits Tier B, and final confidence reaches the required threshold.

Tier C discovery heuristics may locate candidates but must never make a backend callable. Compose project names, service substrings, container slugs, published port matches, path substrings, and slug-derived project roots are discovery only.

When explicit and heuristic evidence disagree, explicit evidence wins or resolution blocks. The system must never let heuristic evidence overwrite explicit conflicting identity.

## Mandatory Routing Gates

Every backend call must pass:

1. `TARGET_KNOWN`
2. `TARGET_ENABLED`
3. `WORKSPACE_EXISTS`
4. `APPROVED_ROOT_MATCH`
5. `REPOSITORY_MARKER_MATCH`
6. `SERVICE_POLICY_ENABLED`
7. `SERVICE_FAMILY_EXPLICIT`
8. `RESOLUTION_CLASS_SUPPORTED`
9. `PORT_POLICY_VALID`
10. `RUNTIME_CANDIDATE_FOUND`
11. `RUNTIME_CANDIDATE_UNAMBIGUOUS`
12. `LOOPBACK_ENDPOINT_ONLY`
13. `TCP_LISTENER_PRESENT`
14. `PROTOCOL_FINGERPRINT_MATCH`
15. `OWNERSHIP_EVIDENCE_SUFFICIENT`
16. `PROJECT_IDENTITY_MATCH`
17. `WORKTREE_OR_STATE_SCOPE_MATCH`
18. `MOUNT_OR_DATA_SCOPE_MATCH`
19. `RUNTIME_FRESHNESS_ACCEPTABLE`
20. `READ_ONLY_OPERATION_ALLOWLISTED`
21. `REDACTION_GATE_PASS`

Failure at any gate blocks the call. The facade must not start, stop, restart, repair, reconcile, relabel, or adopt any runtime.

## Capability Reporting

Capability states must distinguish configured, discovered, ownership-verified, live, and callable. Configured, discovered, or listening must never imply callable.

Supported states are:

- `AVAILABLE`
- `BLOCKED`
- `UNAVAILABLE`
- `UNKNOWN`
- `DEGRADED`

## Public Response Rules

Allowed public response fields include opaque target ID, service-family name, authority label, capability state, blocked reason, branch, head SHA, dirty-state boolean, redacted proof metadata, redacted search results, verification timestamp, and explicit limitations.

Forbidden public response fields include absolute paths, ports, backend URLs, hostnames, container names or IDs, environment values, mount source paths, backend credentials, backend workspace IDs, runtime hashes, lease IDs, database connection strings, and home-directory paths.

## Caching and Resolution Receipts

Resolution results may be cached for no more than 10 seconds. Cache keys include target ID, service family, operation, exposure registry generation, runtime registry update timestamp, and catalog generation. Contradictory live evidence invalidates the cache immediately. Reserved-singleton active-project changes invalidate all cached `to_mcp_wrapper` resolutions.

Every resolution attempt emits a local receipt containing request ID, target ID, service family, operation, registry/catalog generations, candidate count, selected candidate digest, ownership evidence tier, gates evaluated, result state, blocked reason, and verification timestamp. Receipts must not expose infrastructure details to ChatGPT.

## Rejected Alternatives

Rejected alternatives:

- Static URLs as canonical routing.
- Runtime registry as exposure authority.
- Port leases as ownership authority.
- One connector per worktree.
- Direct backend tunnels.
- Runtime container as public target.
- Implicit active target.
- Automatic `.mcp.json` import.
- Compose match as final ownership proof.
- Raw Task Orchestrator MCP concurrency as a prerequisite.

## Security Invariant

No remote MCP transport or tunnel may be enabled until registry v2 exists, runtime joining exists, live protocol fingerprints exist, ownership evidence tiers are enforced, heuristic discovery cannot authorize routing, ambiguity blocks, mount isolation checks exist, service-family allowlists exist, redaction tests pass, and multi-repository live tests pass.

## Consequences

Positive consequences:

- One ChatGPT connector can safely expose approved repositories and worktrees.
- Per-worktree memory remains aligned with git evidence.
- Reserved-singleton semantics are modeled accurately.
- Wrong-project port reuse fails closed.
- Cross-repo chronicle mounts fail closed.
- Runtime churn does not require changing the ChatGPT connector.
- Operator consent remains explicit.

Costs:

- Resolver complexity increases.
- Live checks add latency.
- Ownership evidence needs provenance.
- Existing runtime doctor classifications may be too weak for facade authorization.
- A fully live per-worktree dope-memory exemplar is still required.
- Some capabilities remain blocked.

These costs are preferable to cross-project data leakage or wrong-worktree evidence.

## Proposed ConPort CRS v2 resolution amendment

ConPort resolves to one centralized logical `ConPort CRS v2` service through a trusted project/workspace/instance gateway. Worktree path is alias evidence for `instance_id`, not service authority. Every DCP read includes a resolved identity envelope. DCP receives an allowlisted redacted read-only contract through an adapter backed by the same policy engine and has no direct database, raw admin, write, or sensitive export route.

A DCP ConPort read fails closed when identity is unresolved, ambiguous, stale, unauthorized, or mismatched. Configuration reachability and runtime discovery do not grant access.
