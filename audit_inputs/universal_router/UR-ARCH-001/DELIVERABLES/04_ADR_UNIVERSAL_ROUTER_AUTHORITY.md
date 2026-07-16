# ADR: Universal Router Authority and First-Release Boundary

- **PROPOSED:** ADR identifier: `ADR-UR-001`.
- **PROPOSED:** Status: `PROPOSED_FOR_INDEPENDENT_AUDIT`.
- **PROPOSED:** Decision date: `2026-07-11`.

## Context

- **OBSERVED:** Dopemux already contains separate operator, classification, quota/admission, provider proxy, extraction routing, workflow, execution, proof, audit, and release-readiness authorities.
- **OBSERVED:** No active universal router exists, and `services/task-router` has no tracked runtime source or caller.
- **OBSERVED:** Prior proposals are advisory and sometimes promote DCP or proof schemas beyond their proven authority.
- **OBSERVED:** UR-REV-004 requires an exact in-process location, exact CLI, exact state location, executable policy ownership, and isolation of dormant agent families.

## Decision

### Package and module location

- **PROPOSED:** Canonical package: `src/dopemux/universal_router/`.
- **PROPOSED:** Canonical modules for the first release:
  - `models.py` for Universal Router-owned contracts only.
  - `engine.py` for deterministic classification-to-recommendation orchestration.
  - `policy.py` for policy loading, precedence, validation, and hard invariants.
  - `journal.py` for append-only SQLite records and replay.
  - `snapshots.py` for capability and provider-health snapshot ingestion/expiry.
  - `adapters.py` for read-only interfaces to DCP, Freeflow, LiteLLM observations, RTE, dopetask references, proof references, and PR Steward references.
  - `cli.py` for the `dopemux route` command group.
- **PROPOSED:** A package may later split `adapters.py` into a subpackage only when the number of independently versioned adapters justifies it. The first packet should not pre-create empty architecture furniture.

### CLI surface

- **PROPOSED:** Register `route` from `src/dopemux/cli.py`.
- **PROPOSED:** Exact first-release commands:

```text
dopemux route explain --task <text-or-file> [--policy <id>] [--json]
dopemux route recommend --task <text-or-file> [--dcp-ref <id>] [--json]
dopemux route inspect decision <decision-id> [--json]
dopemux route inspect capabilities [--runner <id>] [--json]
dopemux route inspect health [--provider <id>] [--json]
dopemux route validate policy [--policy <id>] [--json]
dopemux route validate decision <decision-id> [--json]
dopemux route validate snapshots [--json]
```

- **PROPOSED:** `explain` is side-effect free except optional append-only evidence when `--record` is explicitly supplied.
- **PROPOSED:** `recommend` writes one append-only decision attempt by default, because the first-release posture requires evidence of operator-invoked recommendations.
- **PROPOSED:** `inspect` and `validate` never contact providers unless a future explicit `--refresh` capability is separately authorized and implemented.

### Service decision

- **PROPOSED:** No network service or daemon is needed.
- **INFERRED:** All first-release behavior is local, deterministic, operator-invoked, and can reuse existing in-process libraries and filesystem state.
- **PROPOSED:** A service may be reconsidered only if evidence later proves a need for multi-process concurrent callers, remote clients, or durable cross-workspace coordination that cannot be met safely by the CLI/library.

### Authority owned by Universal Router

- **PROPOSED:** Cross-subsystem orchestration decision.
- **PROPOSED:** Minimal append-only route decision/state journal.
- **PROPOSED:** Imported runner capability and provider-health snapshots.
- **PROPOSED:** Executable universal route policy contract and deterministic candidate ranking.

### Authority explicitly not owned

- **PROPOSED:** DCP classification semantics.
- **PROPOSED:** Freeflow quota, cooldown, paid-cap, admission, and estimated-cost state.
- **PROPOSED:** LiteLLM provider proxying or process lifecycle.
- **PROPOSED:** RTE extraction ladders, preflight, strict-schema, provider lock, spend, and run state.
- **PROPOSED:** Task Orchestrator workflow legality or workflow views.
- **PROPOSED:** Dopetask execution and accepted handoff.
- **PROPOSED:** Proof, handoff, audit, human approval, or PR readiness authority.
- **PROPOSED:** Provider billing truth or plan-credit conversion.

### Journal and state location

- **PROPOSED:** Workspace database: `<repo_root>/.dopemux/universal-router/router.sqlite3`.
- **PROPOSED:** Router state is workspace-bound to avoid cross-repository privacy and authority leakage.
- **PROPOSED:** SQLite tables are append-only through application rules plus `BEFORE UPDATE` and `BEFORE DELETE` triggers that abort mutation.
- **PROPOSED:** SQLite uses WAL mode, foreign keys, a schema migration ledger, and deterministic replay order `(created_at, sequence_id)`.
- **PROPOSED:** Proof bundles and handoff artifacts stay in their existing stores. The router stores refs and hashes only.

### DCP reuse boundary

- **PROPOSED:** The engine calls or imports DCP through an adapter that returns `DCPClassificationRef`.
- **PROPOSED:** DCP fields are immutable inputs to the universal decision. Any router-derived interpretation is recorded separately as `RiskPrivacyClassification` and cannot rewrite DCP output.
- **PROPOSED:** DCP `backend_kind` or recommendation fields never authorize runner execution.

### Privacy and risk ownership

- **PROPOSED:** DCP remains canonical for its existing risk/authority classification fields.
- **PROPOSED:** The TaskEnvelope carries operator/task-packet privacy assertions and secret-scan references.
- **PROPOSED:** Universal Router owns only the route-specific composite record that validates privacy inputs, references DCP risk, computes route constraints, and preserves `UNKNOWN` or `CONFLICTING`.
- **PROPOSED:** The router does not claim universal privacy truth outside the route decision.

### Existing subsystem interactions

- **PROPOSED:** Freeflow interaction is a request for candidate admission or an imported admission reference. The router cannot mutate Freeflow tables directly.
- **PROPOSED:** LiteLLM interaction is a provider-path recommendation plus later read-only observation import. The router never starts or configures the proxy in release one.
- **PROPOSED:** RTE coexistence uses a specialized route candidate whose execution and spending remain entirely inside RTE.
- **PROPOSED:** Task Orchestrator receives only an optional read-only projection/ref after operator acceptance. It does not select the provider/model.
- **PROPOSED:** Dopetask handoff is future-phase and occurs only after a separate accepted handoff record. Router recommendation is not acceptance.

### First-release scope

- **PROPOSED:** First release ends at `ROUTE_RECOMMENDED` or `OPERATOR_ACCEPTED`.
- **PROPOSED:** No runner invocation, provider call, worktree mutation, handoff submission, workflow transition, policy promotion, subagent fanout, or release judgment is automated.

## Decision matrix for the required architecture questions

| # | Label | Decision |
|---:|---|---|
| 1 | **PROPOSED** | Package `src/dopemux/universal_router/`. |
| 2 | **PROPOSED** | CLI `dopemux route explain/recommend/inspect/validate`. |
| 3 | **PROPOSED** | No service or daemon. |
| 4 | **PROPOSED** | Router owns workspace-local append-only SQLite journal. |
| 5 | **PROPOSED** | TaskEnvelope is a router intake contract, not a task packet replacement. |
| 6 | **PROPOSED** | DCP output is referenced and immutable. |
| 7 | **PROPOSED** | Full canonical privacy/risk ownership remains `UNKNOWN`; DCP supplies risk input, task/operator/scan sources supply privacy evidence, and the router owns only route-specific fail-closed synthesis. |
| 8 | **PROPOSED** | Freeflow remains sole admission/quota/cooldown/cap writer. |
| 9 | **PROPOSED** | LiteLLM remains proxy/observation infrastructure. |
| 10 | **PROPOSED** | RTE remains specialized extraction router. |
| 11 | **PROPOSED** | Task Orchestrator receives projections only. |
| 12 | **PROPOSED** | Dopetask accepts execution only through existing handoff boundary. |
| 13 | **PROPOSED** | Router owns a versioned capability registry projection. |
| 14 | **PROPOSED** | Snapshots are operator/import acquired, append-only, and TTL-bound. |
| 15 | **PROPOSED** | Provider health is time, network, posture, and source scoped. |
| 16 | **PROPOSED** | Identity trust uses separate requested/configured/claimed/proxy/provider/attested fields. |
| 17 | **PROPOSED** | Usage normalization preserves exact, estimated, session, and unavailable values. |
| 18 | **PROPOSED** | Reasoning is an abstract requested tier resolved by adapter. |
| 19 | **PROPOSED** | Network posture is explicit and fail-closed when unknown. |
| 20 | **PROPOSED** | Containment controls carry enforcement-source evidence. |
| 21 | **PROPOSED** | Release one has no subagent fanout; future delegation is sequential and bounded. |
| 22 | **PROPOSED** | Escalation is quality/capability driven; demotion is certification/cost driven. |
| 23 | **PROPOSED** | Environment failure never triggers premium escalation. |
| 24 | **PROPOSED** | Audit assignment is separate and must prove independence. |
| 25 | **PROPOSED** | Proof linkage uses refs/hashes only. |
| 26 | **PROPOSED** | Certification is route-tuple and version specific. |
| 27 | **PROPOSED** | Dopemux Universal Router owns executable policy parsing and invariants. |
| 28 | **PROPOSED** | Immutable versioned policies plus tracked active pointer and tightening-only local overlay. |
| 29 | **PROPOSED** | Promotion requires independent certification, review, and PR evidence; never self-promoted. |
| 30 | **PROPOSED** | Human override is external, scoped, expiring, and referenced. |
| 31 | **PROPOSED** | Disable through CLI/env kill switch and active-policy rollback. |
| 32 | **PROPOSED** | First release is read-only advisory with append-only evidence. |
| 33 | **PROPOSED** | Advisory policy is mined, mapped, tested, then selectively migrated. |
| 34 | **PROPOSED** | Existing routing systems remain authoritative for their slices. |

## Alternatives rejected

- **PROPOSED:** Reject a new network service because no first-release requirement needs remote access or independent process lifecycle.
- **PROPOSED:** Reject extending Freeflow as the universal journal because its schema and authority are admission-specific.
- **PROPOSED:** Reject extending RTE as the universal journal because its state is extraction-specific.
- **PROPOSED:** Reject reviving `services/task-router` because current runtime evidence proves no active source or caller.
- **PROPOSED:** Reject building on dormant agent families because active dispatch, state, identity, usage, and authority are unproven.
- **PROPOSED:** Reject promoting the current advisory policy directly because no executable owner, certification, precedence, or rollback contract exists.

## Consequences

- **PROPOSED:** Positive: minimal blast radius, clear ownership, deterministic replay, safe shadow evaluation, and low operator drag.
- **PROPOSED:** Positive: no duplicate quota, proxy, proof, handoff, workflow, execution, or release systems.
- **PROPOSED:** Negative: the first release cannot execute recommendations and may return `UNKNOWN`, `BLOCKED`, or `ESCALATED` frequently.
- **PROPOSED:** Negative: provider-specific identity and usage adapters remain required before certification.
- **PROPOSED:** Risk: a broad `models.py` can become a schema magnet. Contract review must reject fields that belong to existing systems.
