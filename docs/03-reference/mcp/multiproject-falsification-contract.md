
# Falsification Contract

```text
PACKET_ID=TP-DMX-MCP-MULTIPROJECT-R2-PRO-ADJUDICATION-001-A1
SAFETY_THRESHOLD=ZERO
BASE_MATRIX=3_PROJECTS_X_4_WORKTREES_PER_PROJECT_X_2_CONCURRENT_RUNNER_FAMILIES
MINIMUM_CONCURRENT_CONTEXTS=24
IMPLEMENTATION=NOT_RUN
```

## Hard properties

1. Canonical project_id never changes solely because a path, checkout location, basename, symlink, branch or port changes.
2. Git common dir, CWD, environment, labels, clientInfo, session IDs, service names and ports never independently authorize a mutable operation.
3. Every mutable call is bound to a verified project and, where required, workspace and instance; UNKNOWN or CONFLICTING denies.
4. No project can read, write, transition, retrieve, replay, consume or promote another project’s data.
5. No service-family probe can prove project ownership.
6. No foreign or ambiguous process/container/volume/lease is mutated automatically.
7. ConPort exposes one project truth across its worktrees and enforces a storage-level wall against other projects.
8. Task Orchestrator has exactly one canonical writer per project and never one shared multi-project authority process.
9. The Python workflow service cannot masquerade as Kotlin Task Orchestrator and is not deleted without consumer evidence.
10. dope-memory accepts no missing/default identity and uses one canonical ledger per project in V1.
11. redis-events uses project-scoped streams, consumer groups, envelopes, replay state and promotion gates; no global managed stream survives activation.
12. Serena remains worktree-scoped unless a host candidate proves concurrent immutable workspace routing.
13. Runner startup never depends on a mutable shared global config rewrite and never loads a stale/wrong-worktree endpoint.
14. MCP protocol statelessness or SDK upgrade never substitutes for application identity, authorization, storage isolation or workflow walls.
15. Derived retrieval, adapters, proxies, labels, receipts and configs never self-promote to canonical authority.
16. Any safety failure count greater than zero blocks the affected service topology or runner profile.

## Matrix construction

Use projects `P-A`, `P-B`, `P-C`; each has worktrees `W-1` through `W-4`. At minimum, run Claude Code and Codex concurrently because both have real renderers and materially different config semantics. Run adapter-specific conformance suites for OpenCode and Copilot using the same in-tree and out-of-tree fixtures. Directory basenames must intentionally collide across projects.

Every test records:

```text
project_id workspace_id instance_id
registry_generation lease_id lease_generation
runner_family profile rendered_config_digest
selected_service_id endpoint owner_runtime_identity
source/storage namespace
expected result actual result
all disclosed IDs/rows/events/tools
```

A zero-row or denied result must be proven by deterministic storage/query/event assertions, not inferred from a model answer.

## Exact adversarial fixtures

| Fixture | Scenario | Required result |
|---|---|---|
| `FX-IDENT-01` | Three projects with identical directory basenames | Distinct registry project_id and endpoints; no alias-based selection. |
| `FX-IDENT-02` | Relocate a checkout and each worktree | project_id/workspace_id unchanged; instance_id preserved only with the same verified registry worktree record. |
| `FX-IDENT-03` | Symlink and realpath aliases to the same worktree | Resolve one instance; contradictory alias metadata fails closed. |
| `FX-IDENT-04` | Two aliases/markers claim one path for different project_ids | CONFLICTING; no mutable endpoint or config emitted. |
| `FX-IDENT-05` | Ambient env overrides project/workspace/root | Override is locator input only; mismatch denies and cannot change storage. |
| `FX-LEASE-01` | Stale lease after worktree deletion | No route; explicit stale classification; no automatic port reuse until ownership proof. |
| `FX-LEASE-02` | Foreign process owns the leased port | Service-family probe may pass, but ownership mismatch denies start/adopt/mutate. |
| `FX-LEASE-03` | Correct service family with wrong project labels/lease | WRONG_PROJECT hard failure. |
| `FX-LEASE-04` | Unlabeled compatible service | No automatic adoption; explicit operator adoption proof required. |
| `FX-RUNNER-01` | Claude Code launched simultaneously in four worktrees | No shared/global config write; each receipt and endpoint matches its instance. |
| `FX-RUNNER-02` | Codex worktree .git is a file; main checkout .git is a directory | Observed loaded config must be the exact worktree candidate or strict profile is BLOCKED. |
| `FX-RUNNER-03` | OpenCode in-tree and out-of-tree worktrees with conflicting config | Exact expected config wins; merge cannot import foreign MCPs. |
| `FX-RUNNER-04` | Copilot in-tree and out-of-tree worktrees with project/global conflicts | Worktree/session config and allowlist win; global expansion denied. |
| `FX-RUNNER-05` | Stale rendered config after lease generation changes | Runner launch denies before connection; no stale endpoint use. |
| `FX-RUNNER-06` | Two concurrent materializers target the same worktree | Atomic idempotent identical output or OCC conflict; never partial/interleaved bytes. |
| `FX-CONPORT-01` | Two worktrees in one project write/read structured records | Shared project truth with correct instance provenance. |
| `FX-CONPORT-02` | Second project uses valid-looking instance_id against first endpoint | Denied at endpoint/storage wall; zero rows disclosed or written. |
| `FX-CONPORT-03` | Missing provenance during migration | Quarantine; never default to current project/instance. |
| `FX-TO-01` | Two projects run Kotlin workflow authority concurrently | Distinct leased endpoints/stores; each has exactly one writer. |
| `FX-TO-02` | Python :8000 service answers under Task Orchestrator name | Routing denied due service identity/authority mismatch. |
| `FX-TO-03` | Duplicate transition, stale version, restart and replay | Idempotency/OCC/restart persistence preserve one legal result. |
| `FX-MEM-01` | Write omits workspace_id or instance_id | Rejected; no default/default-A persistence. |
| `FX-MEM-02` | Request identity conflicts with endpoint-bound project | Rejected before storage selection. |
| `FX-MEM-03` | DOPEMUX_CAPTURE_LEDGER_PATH or root env points to foreign ledger | Cannot select tenancy; startup/operation denies mismatch. |
| `FX-MEM-04` | Concurrent writers exceed WAL budget | Bounded backpressure/error, no lost/corrupt/partially committed chronology. |
| `FX-EVENT-01` | Two projects publish same event type concurrently | Distinct streams/groups; each event consumed only by its project. |
| `FX-EVENT-02` | Foreign consumer joins another project group | ACL/namespace/identity denial; no delivery. |
| `FX-EVENT-03` | Legacy unprefixed event and incomplete envelope | Quarantined or rejected; never promoted. |
| `FX-EVENT-04` | Replay cursor or pending entry copied across projects | Rejected; no duplicate/lost foreign promotion. |
| `FX-SERENA-01` | Two clients activate/query different roots concurrently | V1 uses separate worktree processes. Any host candidate must show no shared mutable root. |
| `FX-PROTO-01` | Legacy Mcp-Session-Id and self-reported clientInfo spoof project identity | Ignored as tenancy input; operation uses trusted resolver/endpoint or denies. |
| `FX-PROTO-02` | Connection reuse and reconnect across projects | No context/identity inherited from prior connection/request. |
| `FX-LEAK-01` | Cross-project dope-context retrieval | Zero foreign result metadata/content. |
| `FX-LEAK-02` | Cross-project ConPort decision/progress read/write | Zero disclosure/mutation. |
| `FX-LEAK-03` | Cross-project Task Orchestrator state/transition | Zero disclosure/mutation. |
| `FX-LEAK-04` | Cross-project dope-memory chronology/event promotion | Zero disclosure/mutation/promotion. |
| `FX-FAIL-01` | Shared host service unavailable | Explicit degradation; no weaker source or foreign endpoint substitution. |
| `FX-FAIL-02` | Project canonical service unavailable | Hard block for authority-requiring operation; no wrong-project fallback. |
| `FX-RESTART-01` | Machine restart with stale leases and changed container IDs | Reconcile by registry/lease/labels/probes; no name/port-only adoption. |
| `FX-DELETE-01` | Delete and recreate worktree at same path | New instance_id unless explicit verified lineage adoption; stale instance denied. |

## Gate evaluation

```text
CROSS_PROJECT_DISCLOSURES=0
CROSS_PROJECT_MUTATIONS=0
WRONG_PROJECT_WORKFLOW_RESULTS=0
WRONG_INSTANCE_PROVENANCE_ACCEPTED=0
FOREIGN_RUNTIME_MUTATIONS=0
UNSCOPED_EVENT_PROMOTIONS=0
GLOBAL_CONFIG_REWRITES_DURING_SWITCH=0
STALE_CONFIG_ENDPOINT_SELECTIONS=0
PATH_RELOCATION_IDENTITY_CHANGES=0
PROTOCOL_IDENTITY_LAUNDERING=0
HIDDEN_CONTRADICTIONS=0
```

One nonzero count falsifies the affected candidate. Resource savings are evaluated only after all hard properties pass.

## Utility measurements after safety

Measure process/container count, idle RAM/CPU, open connections, file descriptors, cold start, warm switch, duplicate embedding/index work, WAL contention, config writes, operator touches, stale lease incidents and maintenance burden. Report raw runs and distributions. No resource threshold can waive a hard property.
