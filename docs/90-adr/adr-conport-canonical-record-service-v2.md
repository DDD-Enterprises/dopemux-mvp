---
id: adr-conport-canonical-record-service-v2
title: ADR - ConPort Canonical Record Service v2
type: adr
owner: "@hu3mann"
author: "Wave 0 documentation packet"
date: 2026-07-21
last_review: 2026-07-21
next_review: 2026-08-21
status: accepted
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-conport-as-decision-progress-and-context-authority
    - adr-memory-trinity-authority-and-interaction-model
supersedes:
  - adr-conport-as-decision-progress-and-context-authority
relates_to:
  - adr-memory-trinity-authority-and-interaction-model
  - adr-dope-memory-as-chronicle-memory-authority
  - adr-dope-context-as-search-and-retrieval-plane
  - adr-task-orchestrator-as-workflow-authority
  - adr-pm-plane-authority-boundaries
  - adr-mcpint-001
  - adr-mcpint-002
  - adr-mcpint-004
  - adr-conport-migration-foundation-gate
prelude: Defines one normalized Dopemux ConPort canonical record service with registry-backed identity, bounded authority, durable events, derived projections, and ADR-gated rollout.
---

# ADR: ConPort Canonical Record Service v2

## Status and authority

**Accepted (2026-07-21).** Independent Wave 1 review accepted the exact ADR digest under the [Wave 1 acceptance record](../../proof/conport-crs-v2/wave1/WAVE1-ACCEPTANCE.json). Acceptance does not itself authorize code, migration, deployment, cleanup, cutover, merge, or Wave 2.

## Context

Current evidence identifies two healthy ConPort-like containers sharing one PostgreSQL store while exposing incompatible custom JSON-RPC, SSE/stdio, admin, and upstream-wrapper stories. The store contains multiple project names, absolute-path aliases, packet scopes, `_system`, foreign-project data, pytest paths, and records with missing instance provenance. No evidence-based rule makes either container canonical. One container was globally bound, package launch included unpinned `uvx --from context-portal-mcp`, and live MCP lifecycle behavior was not established across the advertised surfaces.

The accepted ConPort authority ADR makes ConPort broadly canonical for decisions, progress, and context and temporarily tolerates multiple surfaces. That decision is too broad and too weakly enforced for the observed deployment. Existing Memory Trinity, PM, workflow, DCP, MCP integration, migration, and event ADRs do not fully specify stable project/workspace/instance identity, per-call authorization, atomic outbox behavior, promotion provenance, projection consistency, or a single canonical runtime identity.

## Decision

### 1. Canonical service identity

Dopemux will use one logical canonical service named **Dopemux ConPort Canonical Record Service v2** (`ConPort CRS v2`). It is a newly normalized Dopemux custom runtime in `DDD-Enterprises/dopemux-mvp`.

The current custom containers, the upstream package, and any wrappers remain evidence or compatibility fixtures until a target build is independently accepted. Upstream `context-portal-mcp` may be pinned as a protocol/tool reference but may not run as a parallel canonical service.

Before runtime activation, the target identity must bind exact values for:

- full git commit SHA;
- dependency lock SHA-256;
- OCI image digest;
- SBOM digest;
- generated configuration SHA-256;
- policy bundle SHA-256;
- normalized tool contract SHA-256;
- schema and migration bundle SHA-256.

Floating package versions, image tags, branches, or unpinned `uvx` are prohibited in the target.

### 2. Canonical storage

Canonical records will live in a dedicated PostgreSQL database or explicitly isolated database boundary, with canonical schema `conport_v2`, least-privilege roles, row-level security, immutable revisions, deterministic idempotency, audit records, quarantine, projection checkpoints, and a transaction outbox.

The legacy shared `public` schema is not declared canonical merely because it is currently populated. Existing data must be exported, classified, quarantined where necessary, and imported through an explicit migration plan. No provenance may be invented.

### 3. Identity boundary

Every canonical record is scoped by stable registry-issued identifiers:

- `project_id`: stable project/product/repository identity;
- `workspace_id`: durable canonical logical data partition under a project;
- `instance_id`: temporary execution scope such as a worktree, branch, task packet, agent session, or supervised run.

Paths, names, ports, containers, compose projects, current working directories, and ambient environment variables are aliases or evidence only. They never authorize a call by themselves.

A trusted gateway resolves client claims against authenticated actor/client identity, registry state, repository markers, aliases, grants, commit/branch/worktree lineage, task-packet references, and registry generation. Alias collision, wrong project, wrong workspace, wrong instance, stale registry generation, forged actor/client, stale or unrelated commit, and test namespace use fail closed.

Every canonical read and write requires `project_id`, `workspace_id`, `instance_id`, `actor_id`, `client_id`, and `request_id`. Every write additionally requires `idempotency_key`, `commit_sha`, `branch_ref`, trusted `worktree_ref`, `issued_at`, and `registry_generation`. Optional `task_packet_id`, `session_id`, and `parent_instance_id` carry additional provenance.

Every response, including denial, returns a safe resolved identity envelope with canonical IDs, alias evidence, applied grants, registry generation, commit relation, authenticated principal, and policy decision ID.

### 4. Multi-workspace and multi-instance hosting

One logical service may host multiple workspaces only after RLS, scoped credentials/session settings, query-level scope defense, cross-scope negative tests, projection isolation, audit, and leakage tests pass. Shared database hosting is a conditional topology, not an assumption.

Multiple containers may share the database only as intentional stateless replicas behind one trusted routing authority after image, lock, configuration, policy, schema, tool, authorization, and concurrent-idempotency equivalence is proven. Otherwise use one canonical process.

Test and fixture data use physically separate database/schema/role boundaries. Production identity resolution rejects temporary and test namespace patterns.

### 5. Instance lifecycle

Instance create, fork, handoff, promote, merge, supersede, archive, and delete/purge are explicit operations. Reads never create or auto-fork state.

Promotion and merge create new revisions or grants while preserving original project, workspace, instance, actor, client, commit, request, and source-revision provenance. Promotion never clears identity. Merge requires a deterministic plan, human approval, revision checks, per-record decisions, and an immutable receipt.

Active context is durable but lease-bound, reviewable, and instance-scoped by default. Cross-instance visibility requires an explicit bounded and expiring grant or reviewed promotion.

### 6. Authority classes

ConPort CRS v2 is canonical for:

- architectural and product decisions and their immutable approval/supersession history;
- durable structured product/project context;
- active-context revisions and handoff records;
- typed progress observations and work evidence;
- allowlisted custom structured data;
- typed semantic relationship assertions;
- ConPort audit, provenance, idempotency, and outbox records.

ConPort CRS v2 is not canonical for:

- task status, transition legality, blockers, queue, completion authority, approvals in workflow, or next action, which belong to Task Orchestrator;
- passive PM metadata, which belongs to Leantime;
- chronology, which belongs to dope-memory;
- semantic retrieval and ranking, which belong to dope-context and remain advisory;
- source-code truth, which belongs to source code and repository documentation, with Serena as a technical-context plane;
- adapter routing, DCP views, graph topology, vector neighborhoods, cache entries, or raw scratch notes.

The word `progress` in ConPort contracts means only `progress_observation` or `work_evidence`. A ConPort observation may reference a workflow object but may not transition it.

Scratch notes are local/session state. They enter ConPort only through explicit reviewed conversion into a typed record with provenance. Secrets and large binary artifacts are rejected; large artifacts are stored by content-addressed reference in an approved external store.

### 7. Relationship, graph, FTS, and vector posture

A typed relationship assertion may be a canonical ConPort record. An AGE edge, graph topology, path ranking, FTS index row, embedding, Qdrant point, Redis key, or dope-context result is derived.

Native PostgreSQL FTS may be enabled after create/update/supersede/delete/replay/rebuild consistency tests pass. Vector retrieval remains outside canonical ConPort and may be enabled only through dope-context after privacy, provenance, tenant isolation, deterministic tie-break, update/delete consistency, tombstone, replay, and rebuild gates pass.

All semantic retrieval is advisory. It may surface related records but may not judge conflicts, approve decisions, or authorize writes.

### 8. Tool and transport contract

Agent-facing tools use one normalized versioned contract and one policy engine. Claude Code and Codex receive bounded reads plus policy-gated proposal, active-context, evidence, and structured-data writes. DCP receives a redacted read-only subset. Internal services use exact allowlists and service credentials. Admin tools use a separate operator control plane and are absent from agent discovery.

The target transport is a thin local stdio launcher to authenticated MCP Streamable HTTP or a Unix-domain-socket core. Authenticated private-network service access may be used when necessary. SSE is not part of the target.

MCP annotations are hints only. Identity, authorization, approval, revision checks, idempotency, RLS, and database constraints enforce behavior.

### 9. Decision workflow

Before a material technical proposal, an agent performs a bounded decision conflict check. Retrieval is advisory and the agent must read related decisions and reason.

A decision enters as `proposed`. Acceptance or supersession requires explicit digest-bound human approval verified by the server. Supersession atomically creates/accepts the replacement and marks the old decision superseded with bidirectional references. History is never silently deleted.

Deterministic JSONL plus Markdown export is required for portability, review, backup, and human inspection.

### 10. Events, mirrors, and projections

Every canonical revision and lifecycle change writes an outbox event in the same database transaction. If the record or outbox insert fails, the whole transaction fails. After commit, consumer outage does not roll back the record. The durable outbox retries and records consumer receipts; exhausted attempts enter dead letter and alert an operator.

Canonical change events are non-lossy. They are exempt from UI event dropping and from coalescing that could erase decision, supersession, deletion, identity, or revision semantics.

The ConPort-to-dope-memory event carries event, aggregate, revision, operation, identity, actor/client/request/idempotency, source-control provenance, payload digest, redacted summary, supersession/tombstone, sensitivity, policy decision, and schema version fields. dope-memory owns the chronicle receipt. dope-context, AGE, FTS, vector, caches, and rollups use source snapshots and ordered event cursors, propagate tombstones, expose lag/freshness, and can be rebuilt.

### 11. Migration and rollout

Migration is incremental and ADR-gated:

1. Wave 0 documentation proposal;
2. Wave 1 independent acceptance or rejection;
3. freeze, fresh inventory, immutable pins;
4. identity registry and policy engine;
5. isolated canonical schema, RLS, revision, idempotency, audit, quarantine, and outbox;
6. normalized service and adapter;
7. backup, export, row classification, quarantine, validated import, and shadow reads;
8. isolation and lifecycle negative tests;
9. agent policy and client trials;
10. event, mirror, FTS, retrieval, and graph projections;
11. security, observability, backup/restore, and rollback rehearsal;
12. final acceptance, controlled cutover, rollback window, then deprecation and cleanup.

No big-bang rewrite and no dual canonical writes are permitted.

### 12. Rollback

The rollback unit is the last independently accepted epoch binding application, configuration, policy, tool contract, schema, migration bundle, and canonical event cursor. Before rollback, stop target writes. Do not cross an irreversible migration or cleanup boundary without a verified restore. Preserve idempotency and outbox evidence, restore the accepted epoch, and reconcile committed events.

### 13. Security

Canonical routes bind to loopback, Unix socket, or an authenticated private boundary. Global unauthenticated binding is prohibited. The service uses authenticated actor/client identity, least-privilege roles, RLS, deterministic policy, approval verification, secret-safe logs, audit, denial metrics, bounded requests, and independent security review.

No deny may live only in an LLM instruction. Agent guidance is advisory; the policy engine and storage constraints carry the hard boundary.

### 14. Acceptance invariants

The target is not implementation-ready until all required acceptance gates pass, including source/runtime identity, schema, MCP handshakes, multi-project/workspace/instance isolation, wrong-scope negatives, alias collisions, decision conflict/supersession, progress authority, active-context visibility, projection consistency, mirror replay, backup/restore, deterministic export/import, contaminated migration, Claude Code, Codex, DCP, performance, security, and rollback.

An unexecuted test is `NOT_RUN`, never `PASS`.

## Consequences

### Positive

- One named canonical service and policy engine replace shadow authority.
- Stable identity and provenance become enforceable rather than conventional.
- Progress no longer competes with workflow authority.
- Decisions gain server-enforced approval, atomic supersession, and portable export.
- Mirrors and projections become durable, replayable, and explicitly noncanonical.
- Claude Code, Codex, DCP, and internal services share one normalized contract with audience-specific exposure.

### Negative

- The target is a new bounded service, not a configuration-only cleanup.
- Identity registry, RLS, migration classification, outbox, approval, and lifecycle add engineering and operating cost.
- Existing records cannot be blindly relabeled.
- A centralized service creates an operational dependency that requires backup, recovery, observability, and strict network controls.
- Some legacy tools and client assumptions must be broken rather than preserved.

## Alternatives rejected

### Keep current shadow twins

Rejected. Their authority equivalence, authorization, and isolation are not proven.

### Replace directly with upstream per-workspace SQLite

Rejected as a direct target. It improves physical file isolation but does not establish Dopemux project/instance/actor/client/commit authority, cross-plane contracts, DCP routing, shared policy, or migration semantics.

### Upstream core with unrestricted Dopemux extensions

Rejected. Without a single normalized authority and explicit extension boundary, it recreates the overloaded-family problem.

### One service per workspace

Not selected as the default. It can physically isolate data but multiplies lifecycle, discovery, update, backup, DCP, and client-routing burden. It remains a contingency if the shared-service isolation gates cannot pass.

## Non-authorization statement

This accepted ADR authorizes no code, schema, migration, runtime, data, client, deployment, cleanup, merge, or Wave 2 action by itself.
