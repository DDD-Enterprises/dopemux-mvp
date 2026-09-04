---
id: adr-dmx-mcp-multiproject-identity-sharing-contract-001
title: Adr Dmx Mcp Multiproject Identity Sharing Contract 001
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-09-03'
last_review: '2026-09-03'
next_review: '2026-12-02'
prelude: Adr Dmx Mcp Multiproject Identity Sharing Contract 001 (adr) for dopemux
  documentation and developer workflows.
status: proposed
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# P0 Identity + Sharing Contract Specification

**Program:** DMX-MCP-MULTIPROJECT
**Packet:** `TP-DMX-MCP-MULTIPROJECT-P0-IDENTITY-SHARING-CONTRACT-001`
**Risk lane:** L2 material contract freeze
**Runtime effect:** none
**Governing R2 package SHA-256:** `fa78556b2d51cd3b22d8c42ff36bd6c3964172ddee6a75662cde61db438e3996`

## 1. Purpose

P0 freezes the semantic contracts that P1 and service tranches must implement. It does not convert the
running fleet to those contracts. The live v1 catalog, path-derived identity resolver, port-lease
implementation, launchers, compose files, services, databases, Redis state, and runner-global
configuration remain unchanged.

This separation is deliberate. P0 answers **what must be true**. P1 and later tranches answer **how the
runtime becomes true**.

## 2. Canonical identity contract

Canonical identity is registry-issued:

```text
project_id   = stable registry identity for one project/repository/product boundary
workspace_id = durable registered logical partition under project_id
instance_id  = registered temporary execution scope such as a worktree/run
```

The following are always non-authoritative evidence or locators:

```text
filesystem path
git common-dir
repository display name
origin URL
CWD
environment variables
port
container name/id
compose project
MCP connection/session identity
MCP clientInfo
runner process identity
```

A trusted resolution result has:

```yaml
schema_version: dopemux.mcp.resolved-execution-identity.v1
resolution_status: VERIFIED
project_id: <non-empty registry id>
workspace_id: <non-empty registry id>
instance_id: <non-empty registry id>
actor_id: <non-empty principal>
client_id: <non-empty client identity>
registry_generation: <integer >= 0>
mutable_routing_allowed: true
aliases:
  - kind: git_common_dir
    value: /locator/example
    role: EVIDENCE_ONLY
```

If `resolution_status` is `UNKNOWN` or `CONFLICTING`, `mutable_routing_allowed` must be `false`.

P0 deliberately does not require UUID syntax. The accepted authority requires stable registry-issued
identifiers, while no current registry schema in this packet proves one exact lexical format.

## 3. Sharing-class contract

Exactly four topology classes exist:

```text
HOST_SINGLETON
PROJECT_SCOPED
WORKTREE_SCOPED
RETIRED
```

A design-only fleet catalog v2 server record declares:

```yaml
sharing_class: WORKTREE_SCOPED
target_class: PROJECT_SCOPED
identity_scope: per-instance
state_authority: canonical
mutation_class: scoped
endpoint_policy: leased
probe: mcp
idle_policy: instance_idle
flip_gate:
  - explicit identity binding passes
  - wrong-project negative tests pass
```

The v2 schema must reject legacy `scope`, `state_scope`, `port_policy`, and
`multi_project_singleton` semantics. The live v1 catalog and loader stay untouched in P0.

## 4. Frozen service topology

`docs/03-reference/mcp/multiproject-service-topology.json` is copied byte-for-byte from the ratified R2
`02_SERVICE_TOPOLOGY.json` and must retain SHA-256:

```text
df8636983e23c273eeb8eb517ea4019653b4c6bcb50cae344cde2e847214d4c2
```

The topology has exactly 26 service rows and uses only the four sharing classes.

Required ratified outcomes include:

```text
ConPort              -> PROJECT_SCOPED, gated by explicit Wave 2 + storage wall
dope-memory V1       -> PROJECT_SCOPED, host-singleton deferred
Task Orchestrator    -> PROJECT_SCOPED, one workflow writer/process per project
redis-events logical -> PROJECT_SCOPED before dope-memory consolidation
Serena V1            -> WORKTREE_SCOPED, host sharing deferred
dope-context         -> HOST_SINGLETON subject to explicit per-call project isolation
```

## 5. Endpoint lease v2 contract

A service lease is **operational endpoint authority**, not domain truth.

Minimum fields:

```yaml
schema_version: dopemux.mcp.service-lease.v2
lease_id: <non-empty>
service_id: <non-empty>
sharing_class: PROJECT_SCOPED
project_id: <non-empty>
workspace_id: null
instance_id: null
registry_generation: 42
owner_epoch: 7
endpoint:
  transport: http
  host: 127.0.0.1
  port: 45678
owner_runtime_identity:
  runtime_kind: container
  runtime_id: <non-empty>
status: active
created_at: <date-time>
updated_at: <date-time>
last_verified_at: <date-time-or-null>
evidence_refs: []
```

Rules:

- `PROJECT_SCOPED` requires `project_id`.
- `WORKTREE_SCOPED` requires `project_id` and `instance_id`.
- `HOST_SINGLETON` may omit tenant IDs because the lease identifies the host endpoint, not authorization
  for individual requests.
- `RETIRED` cannot own a lease.
- Port formulas, paths, labels, and service-family probes cannot independently prove ownership.
- Unknown/conflicting lease state cannot authorize mutation.

## 6. Ownership evidence contract

Ownership classification is one of:

```text
OWNED
FOREIGN
AMBIGUOUS
UNKNOWN
```

`mutation_eligible=true` is valid only when classification is `OWNED` and the evidence bundle includes:

1. registry identity binding;
2. exact active lease binding;
3. service-family protocol probe;
4. storage/mount or equivalent endpoint corroboration.

Labels are evidence but never sufficient by themselves. A successful service-family probe proves service
family only, not project ownership.

For `FOREIGN`, `AMBIGUOUS`, or `UNKNOWN`:

```text
mutation_eligible=false
```

## 7. Runner materialization receipt

A rendered runner config emits a provenance-only receipt:

```yaml
schema_version: dopemux.mcp.runner-materialization-receipt.v1
authority: PROVENANCE_ONLY
materialization_id: <non-empty>
project_id: <non-empty>
workspace_id: <non-empty>
instance_id: <non-empty>
registry_generation: 42
runner_family: codex
profile: core-code
catalog_digest: <64 lowercase hex>
rendered_config_digest: <64 lowercase hex>
lease_refs: []
generated_at: <date-time>
shared_global_config_mutated: false
strict_mode: true
inherited_surface_status: EXCLUDED
```

`shared_global_config_mutated` is always false.

For `strict_mode=true`, `inherited_surface_status=UNKNOWN` is invalid.

The receipt proves what was rendered. It does not authorize service mutation, task execution, merge, or
activation.

## 8. Project event envelope

The P0 event envelope is a minimum transport identity contract, not a complete Redis implementation:

```yaml
schema_version: dopemux.mcp.project-event-envelope.v1
event_id: <non-empty>
event_type: <non-empty>
emitted_at: <date-time>
source_service_id: <non-empty>
project_id: <non-empty>
workspace_id: <non-empty>
instance_id: <non-empty>
registry_generation: 42
payload_digest: <64 lowercase hex>
stream_namespace: project/<project_id>/<event-type>
sequence: 12
replay_key: <non-empty-or-null>
```

No field may default project/workspace/instance identity from process environment. P5 owns Redis stream,
consumer-group, migration, replay, and promotion implementation.

## 9. Protocol-independence contract

MCP 2026-07-28 and SDK compatibility work runs in PX. P0 freezes only this invariant:

> Protocol connection/session/process/client metadata is never the canonical tenant boundary.

A future protocol upgrade may improve transport. It cannot make path-derived or connection-derived
project identity authoritative.

## 10. P0 no-runtime-effect contract

The following are forbidden P0 mutation domains:

```text
mcp_catalog.yaml
src/dopemux/mcp/**
src/dopemux/commands/mcp_commands.py
services/**
docker/**
compose.yml / compose*.yml
.mcp.json
lockfiles
home/global runner configuration
live lease registry
Docker/container state
Redis/database state
```

The only `src/dopemux/mcp/**` references in P0 are read-only context. P1 owns implementation of the new
identity, endpoint, catalog, and lease semantics.

## 11. Exact frozen falsification reference

`docs/03-reference/mcp/multiproject-falsification-contract.md` is copied byte-for-byte from R2 and must
retain SHA-256:

```text
84b6e68f929e5b3f3ad37e9c2843755cc38a3a119fc87b5af057505d8ed83bcb
```

P0 does not execute the 3-project × 4-worktree × 2-runner matrix. It freezes the contract that P8 must
execute. P0 tests only schema/static negative invariants needed to prevent later tranches from weakening
that matrix.

## 12. Stop conditions

Stop P0 if a proposed contract:

- makes path/CWD/env/port/container/clientInfo/session identity authoritative;
- permits mutable routing with unresolved identity;
- adds a fifth sharing class;
- permits `multi_project_singleton` workflow authority;
- changes live v1 runtime behavior;
- authorizes ConPort Wave 2;
- changes dope-memory V1 target away from project scope;
- moves Serena to host scope in V1;
- permits normal global runner-config rewrite;
- allows an ownership probe or label to independently prove mutation authority;
- creates a new canonical registry/store/gateway/daemon in this tranche;
- weakens the frozen R2 service topology or falsification contract.
