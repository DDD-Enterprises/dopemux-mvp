---
id: multiproject-control-plane
title: Multiproject Control Plane
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-09-04'
last_review: '2026-09-04'
next_review: '2026-12-04'
prelude: Multiproject Control Plane (reference) for dopemux documentation and
  developer workflows.
---
# P1 Fleet Control Plane

**Program:** DMX-MCP-MULTIPROJECT
**Packet:** `TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001`
**Parent:** `TP-DMX-MCP-MULTIPROJECT-P0-IDENTITY-SHARING-CONTRACT-001` (merged, frozen)

## What this is

P1 implements the control-plane mechanics the ratified P0 contracts describe:
a registry-issued identity resolver, a catalog-v2 compiler and compatibility
projection, service-lease-v2, ownership evidence, generic atomic
materialization, and read-only reconcile/control-plane composition.

**Merging this packet does not activate any service topology change.** No
service is started, stopped, adopted, or migrated by anything P1 adds. The
live v1 catalog (`mcp_catalog.yaml`), the v1 identity resolver
(`project_identity.py`), the v1 port-lease registry (`port_leases.py`), and
every existing `dopemux mcp *` command behave exactly as before. P1's new
modules are dormant, additive code paths that nothing in the live system
calls.

## New modules (all dormant/default-off)

| Module | Purpose |
|---|---|
| `identity_registry.py` / `identity.py` | Registry-issued `project_id`/`workspace_id`/`instance_id`; fail-closed `resolve_execution_identity` |
| `fleet_catalog.py` (catalog-v2 section) | `compile_catalog_v2`, `legacy_client_projection`, `catalog_semantic_fingerprint` |
| `service_leases.py` | Service-lease-v2 endpoint authority, `lease_verdict`, read-only legacy migration preview |
| `ownership.py` | Closed OWNED/FOREIGN/AMBIGUOUS/UNKNOWN evidence evaluator |
| `materialization.py` | Generic atomic session file materialization + PROVENANCE_ONLY receipts |
| `reconcile.py` / `control_plane.py` | Read-only reconcile classification and plan composition (no executor) |

## Canonical vs. evidence identity

Canonical `project_id`/`workspace_id`/`instance_id` are issued **only** by
`IdentityRegistry.register_project`/`register_workspace`/`register_instance`.
Filesystem path, git common-dir, origin, cwd, environment, port, container,
MCP session/process identity, and clientInfo are always locator/evidence
only, recorded as `EVIDENCE_ONLY` aliases -- never authority, never
auto-registering a record. `UNKNOWN` or `CONFLICTING` resolution always
forces `mutable_routing_allowed=false`. See
`docs/90-adr/adr-dmx-mcp-multiproject-identity-sharing-contract-001.md` S2
and `schemas/mcp/resolved-execution-identity.schema.json`.

## Registry/lease paths and test isolation

Production paths (created only on first explicit registration/lease
acquisition, never bootstrapped from path/env evidence):

| Store | Default path | Env override |
|---|---|---|
| Identity registry | `~/.dopemux/mcp/registry/identity.json` | `DOPEMUX_MCP_IDENTITY_REGISTRY` |
| Service leases | `~/.dopemux/mcp/registry/service-leases.json` | `DOPEMUX_MCP_SERVICE_LEASE_REGISTRY` |

`IdentityRegistry.load()`/`ServiceLeaseRegistry.load()` default to
`create_missing=False` -- reading either store when absent returns an empty,
present=False registry, not a bootstrap. **All P1 tests inject `tmp_path`
explicitly and never touch either home-scoped path.** The two `dopemux mcp
control-plane identity|reconcile` preview commands (see below) also load
with `create_missing=False`, so running them on a machine with no registry
yet prints `UNKNOWN`/a blocked plan rather than creating one.

No implementation or validation step in this packet wrote to either home
path, started/stopped a container, or mutated live Docker/Redis/database
state. Any observed instance of that would be `FAIL_P1_UNAUTHORIZED_RUNTIME_MUTATION`.

## Catalog-v2 compatibility gate

`compile_catalog_v2` joins every v1 catalog server to its
`docs/03-reference/mcp/multiproject-service-topology.json` row (by identity,
or the three documented aliases -- see `CATALOG_TO_TOPOLOGY_ALIAS` in
`fleet_catalog.py`) and derives the v2-only governance fields. Before any
catalog file would be written, `catalog_semantic_fingerprint` compares the
v1 catalog against `legacy_client_projection(compiled_v2)` across profile
membership, client placement, endpoints, commands/args, environment key
names, and tool/admin/aux metadata. Any difference stops before touching
`mcp_catalog.yaml`/`default_catalog.yaml`.

**`CATALOG_V2_CUTOVER=BLOCKED_NOT_APPLIED` in this packet, even though the
compiler proves zero drift against the real catalog** (see
`tests/mcp/test_fleet_catalog_v2_runtime.py::test_fingerprint_equal_between_real_v1_and_legacy_projected_v2`).
`fleet_catalog.load_root_catalog` and `mcp_commands._load_catalog` both
hard-raise on `version != 1`, and the latter backs every `dopemux mcp *`
command. Flipping the live file to `version: 2` without first making both
loaders version-tolerant would be an immediate fleet-wide CLI outage, not a
dormant change -- and widening `_load_catalog` is outside this packet's
`mcp_commands.py` grant (read-only preview surfaces only; that loader also
backs `start`/`stop`/`up`/`down`). The follow-on that unblocks cutover: make
both loaders accept v2 and internally apply `legacy_client_projection`, then
the file flip becomes a one-line, truly dormant change.

## Activation boundary

Read-only P1 inspection/preview (`dopemux mcp control-plane identity`,
`dopemux mcp control-plane reconcile`) is live and usable today. Everything
that would *mutate* toward the v2 model -- acquiring a real lease against a
live service, adopting a foreign container, migrating a legacy port lease,
cutting the catalog over -- remains code that exists but that nothing calls.
Later tranches (P2-P8) and an explicit operator activation gate own turning
any of it on. This packet makes no claim about ConPort Wave 2, dope-memory
migration, Task Orchestrator project-scope migration, redis-events
isolation, Serena host sharing, MCP SDK upgrade, merge, or activation --
those all remain exactly as ratified in P0.

## Rollback

Before any later activation, rollback is:

```bash
git revert <P1-merge-commit>
```

No runtime cleanup is expected: P1 implementation and validation performed
no live registry/lease/Docker/service/database mutation, so there is no live
state for a revert to need to unwind.
