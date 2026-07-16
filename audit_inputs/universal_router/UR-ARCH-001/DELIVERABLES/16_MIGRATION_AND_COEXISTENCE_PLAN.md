# Migration and Coexistence Plan

## Migration posture

- **PROPOSED:** Add the Universal Router beside existing routing systems. Do not replace, merge, or wrap them behind a new authority facade.
- **PROPOSED:** Release one is a reversible read-only advisory slice inside `dopemux`.
- **OBSERVED:** Current routing responsibilities are distributed across Dopemux configuration/control, Freeflow admission and quota state, LiteLLM provider proxying, RTE specialized extraction routing, Task Orchestrator capability assignment, dopetask execution, proof/handoff contracts, and PR Steward review intake.
- **PROPOSED:** The migration succeeds only when those systems remain independently usable with the router disabled or removed.

## Coexistence invariants

- **PROPOSED:** `dopemux` remains operator control.
- **PROPOSED:** `dopetask` remains execution authority after accepted handoff.
- **PROPOSED:** Task Orchestrator remains workflow-transition and workflow-view authority.
- **PROPOSED:** Freeflow retains quota, cooldown, paid-cap, estimated-cost, and admission state.
- **PROPOSED:** LiteLLM remains provider proxy infrastructure.
- **PROPOSED:** RTE retains extraction-run routing, run state, and spend state.
- **PROPOSED:** DopeconBridge remains adapter, proxy, and event transport only.
- **PROPOSED:** Proof, handoff, audit, and PR Steward contracts are extended by references, not copied.
- **PROPOSED:** Human approval remains external evidence.
- **PROPOSED:** Dormant agent families remain isolated.
- **PROPOSED:** `services/task-router` is not revived.

## Existing-system compatibility matrix

| Existing surface | Claim label | Coexistence behavior | Router must not do |
|---|---|---|---|
| `src/dopemux/routing_config.py` | **OBSERVED** | Read configured aliases/provider paths through an adapter where stable | Redefine provider proxy ownership or RTE model maps |
| `src/dopemux/routing_cli.py` | **OBSERVED** | Continue managing current routing service modes | Replace its start/stop/health behavior |
| Freeflow router and ledger | **OBSERVED** | Request/read an admission decision or snapshot through a bounded adapter | Duplicate ledger, infer quota, mutate admission in release one |
| LiteLLM proxy manager | **OBSERVED** | Import proxy observations and normalized health/usage evidence | Become a second proxy manager or treat proxy identity as provider attestation |
| LiteLLM trace callback | **OBSERVED** | Reference JSONL trace evidence when enabled | Require trace availability where not configured or label estimates actual |
| RTE v3/v5 | **OBSERVED** | Request or reference specialized RTE route decisions | Reproduce model ladders, spend logic, promptset gating, or run orchestration |
| Task Orchestrator AgentCoordinator | **OBSERVED** | Accept capability-family projection only when explicitly needed | Select provider/model inside Task Orchestrator or transfer workflow authority |
| DCP classifier/backend policy | **OBSERVED** | Reuse classification result by immutable ref; adapt policy signals behind contract | Make DCP the universal journal, executor, proof owner, or release gate |
| `scripts/dopetask` | **OBSERVED** | Prepare future handoff references after operator acceptance | Execute or mutate handoff in release one |
| Proof and handoff systems | **OBSERVED** | Link canonical bundle and handoff refs | Fork schemas or synthesize missing proof as true |
| PR Steward | **OBSERVED** | Reference current merge-readiness result | Recompute or override readiness |
| Advisory multi-model policy | **OBSERVED** | Mine rules through a disposition matrix | Treat the file as executable authority |
| Dormant agent families | **OBSERVED** | Leave isolated | Route tasks through them without new runtime evidence |

## Migration phases

### Phase M0: baseline and freeze

- **PROPOSED:** Record repository commit, active routing entrypoints, configured policy files, Freeflow/LiteLLM/RTE paths, and known contradictions.
- **PROPOSED:** Make no runtime routing behavior change.
- **PROPOSED:** Freeze the architecture decision and contract names for independent audit.
- **Exit gate:** Independent audit accepts the authority boundary or returns explicit corrections.

### Phase M1: contract definitions

- **PROPOSED:** Add the minimal Universal Router contract catalog and schemas.
- **PROPOSED:** Represent existing proof/handoff/PR Steward objects only as typed refs.
- **PROPOSED:** Add fixtures for `UNKNOWN`, `CONFLICTING`, stale snapshots, environment failures, identity conflict, and policy conflict.
- **Exit gate:** Schema, semantic validation, and hard-boundary tests pass.

### Phase M2: read-only CLI recommendations

- **PROPOSED:** Register `dopemux route explain`, `recommend`, `inspect`, and `validate` as an in-process command group.
- **PROPOSED:** Use static fixtures and tracked policy first. Do not invoke providers, runners, Freeflow writes, RTE runs, or dopetask.
- **Exit gate:** CLI produces deterministic, side-effect-free results and cannot cross `ROUTE_RECOMMENDED`.

### Phase M3: append-only decision journal

- **PROPOSED:** Add workspace-local SQLite journal at `<repo_root>/.dopemux/universal-router/router.sqlite3`.
- **PROPOSED:** Store decisions, refs, snapshots, corrections, and operator acceptance events as append-only records.
- **Exit gate:** Update/delete attempts fail, replay is deterministic, migrations are rollback-safe, and disabling the router leaves existing systems untouched.

### Phase M4: capability-snapshot ingestion

- **PROPOSED:** Ingest signed/hashed local probe artifacts and provider-health observations without executing work.
- **PROPOSED:** Preserve source, acquisition method, timestamps, TTL, confidence, adapter version, and environment boundary.
- **Exit gate:** Stale, conflicted, unverifiable, and environment-blocked snapshots produce the required route behavior.

### Phase M5: existing-subsystem adapters

- **PROPOSED:** Add bounded read adapters for DCP refs, Freeflow admission snapshots, LiteLLM observations, RTE route refs, proof refs, handoff refs, audit refs, and PR Steward refs.
- **PROPOSED:** Start with artifact/file adapters where runtime APIs are not stable or not proven.
- **Exit gate:** Contract tests prove each adapter cannot mutate or absorb upstream state.

### Phase M6: Codex advisory adapter

- **PROPOSED:** Add a capability/telemetry adapter for Codex because UR-INV-003 contains the strongest contained local-runner probe.
- **PROPOSED:** The adapter reports capabilities and constructs an `ExecutionRecommendation`; it does not invoke Codex.
- **Exit gate:** Model identity remains `UNKNOWN` without stronger evidence, usage fields preserve source/confidence, and missing credit/cost stays unavailable.

### Phase M7: proof linkage

- **PROPOSED:** Link route decisions to canonical proof bundle refs, validation refs, audit refs, dopetask handoff refs, and PR Steward readiness refs.
- **PROPOSED:** Do not alter upstream schemas.
- **Exit gate:** Broken, stale, cross-head, or mismatched refs block claims that require them.

### Phase M8: shadow evaluation

- **PROPOSED:** Replay historical tasks and run silent/visible advisory shadow modes under the certification plan.
- **PROPOSED:** Existing operator route selection remains authoritative for actual work.
- **Exit gate:** Advisory certification thresholds are met and independent audit accepts the evidence.

### Phase M9: manual operator acceptance

- **PROPOSED:** Permit an explicit `OPERATOR_ACCEPTED` journal event linked to one recommendation and its exact evidence versions.
- **PROPOSED:** Acceptance does not execute, submit handoff, modify policy, or attest model identity.
- **Exit gate:** Manual acceptance semantics, expiry, corrections, and override evidence are proven.

### Phase M10: one execution adapter at a time

- **PROPOSED:** Future phase. Select one low-risk adapter only after a new packet and certification.
- **PROPOSED:** The initial candidate should be Codex because its contained execution/JSONL/schema surfaces have local evidence, but actual selection remains subject to renewed capability and identity review.
- **PROPOSED:** Every adapter receives its own kill switch, allowlists, rollback, proof mapping, and bounded task classes.
- **Exit gate:** Per-adapter certification and independent audit pass.

### Phase M11: bounded escalation

- **PROPOSED:** Future phase. Add explicit retry/escalation attempts with budgets and deterministic stop rules.
- **PROPOSED:** Environment failures can repair, defer, retry same tier, choose an eligible same/lower-cost alternate, or block. They cannot automatically promote cost/model tier.
- **Exit gate:** Escalation trial meets the certification plan with zero severe failures.

### Phase M12: automatic routing after certification

- **PROPOSED:** Future phase. Enable only a narrowly certified task lane through a separately promoted policy.
- **PROPOSED:** Automatic execution is not implied by automatic route selection.
- **Exit gate:** Exact route tuple, human policy approval, current certification, audit, proof, and rollback are all present.

## First-release boundary

- **PROPOSED:** First release comprises M1 through M9.
- **PROPOSED:** Legal terminal states are `ROUTE_RECOMMENDED`, `OPERATOR_ACCEPTED`, `BLOCKED`, or `ESCALATED`.
- **PROPOSED:** `HANDOFF_PREPARED`, `EXECUTION_ACCEPTED`, `EXECUTING`, `VALIDATING`, `AUDITING`, and `COMPLETED` are modeled but not entered by release-one code.
- **PROPOSED:** Any code path capable of invoking a runner, calling a provider for task work, mutating Freeflow, triggering an RTE run, writing a handoff, or changing workflow state violates release-one scope.

## Advisory-policy migration

### Source treatment

- **OBSERVED:** The existing multi-model routing proposals and `config/ai/model-routing.policy.yaml` are advisory evidence, not executable authority.
- **PROPOSED:** Preserve source file, source line/ref, date, and original claim label for each candidate rule.

### Rule disposition process

| Disposition | Claim label | Meaning |
|---|---|---|
| `MIGRATE` | **PROPOSED** | Rule is supported and maps cleanly to the new contract |
| `REWRITE` | **PROPOSED** | Goal is useful but authority, identity, usage, containment, or route semantics must change |
| `DEFER` | **PROPOSED** | Insufficient evidence or future execution-phase behavior |
| `REJECT` | **PROPOSED** | Contradicts current boundaries or creates duplicate authority |

- **PROPOSED:** Reject rules that make DCP a universal authority, treat OpenRouter/proxy metadata as attestation, derive plan credits from tokens, treat prompt instructions as containment, use same-runner audit as independent, or create proof/release authority inside the router.
- **PROPOSED:** A migrated rule requires schema field mapping, rationale refs, fixtures, historical replay, and policy-promotion evidence.

## Data migration

- **PROPOSED:** There is no migration of Freeflow, LiteLLM, RTE, workflow, proof, handoff, or PR Steward state into the router database.
- **PROPOSED:** Import only snapshots or refs with source hashes and acquisition metadata.
- **PROPOSED:** Existing advisory route logs, if imported, are marked `IMPORTED_ADVISORY` and cannot be treated as canonical decisions.
- **PROPOSED:** No inferred model identity, cost, credit, containment, or approval data is backfilled as observed fact.

## CLI compatibility

- **PROPOSED:** Existing `dopemux routing ...`, `dopemux kernel ...`, `dopemux upgrades ...`, and subsystem CLIs remain unchanged.
- **PROPOSED:** The new noun is `route`, while existing service-management commands retain `routing` to avoid accidental semantic replacement.
- **PROPOSED:** `dopemux route` does not alias or redirect legacy commands.
- **PROPOSED:** Machine output is versioned and opt-in with `--json`.

## Storage coexistence

- **PROPOSED:** Router SQLite is a local orchestration journal only.
- **PROPOSED:** Freeflow SQLite remains canonical for its quota/admission slice.
- **PROPOSED:** RTE run/spend artifacts remain in RTE-owned locations.
- **PROPOSED:** Proof and handoff artifacts remain in their canonical stores.
- **PROPOSED:** Human approval refs point outward and are not rewritten into router-owned approval state.
- **PROPOSED:** Cross-store consistency is by immutable IDs, hashes, and timestamps, not distributed transactions.

## Rollback

### Release-one rollback

1. **PROPOSED:** Set `DOPEMUX_UNIVERSAL_ROUTER_DISABLED=1` or create the workspace disable marker.
2. **PROPOSED:** Revert the CLI registration and active-policy pointer in Git.
3. **PROPOSED:** Leave the append-only journal intact for audit or archive it under repository retention policy.
4. **PROPOSED:** Continue using existing routing, Freeflow, LiteLLM, RTE, Task Orchestrator, dopetask, proof, and PR Steward flows.

### Policy rollback

- **PROPOSED:** Revert only to a previously certified immutable policy hash.
- **PROPOSED:** Record a rollback event and reason. Do not rewrite prior decisions.
- **PROPOSED:** If schema compatibility prevents loading the prior policy, disable recommendations until an explicit migration packet resolves it.

### Adapter rollback

- **PROPOSED:** Disable a single adapter or certification without disabling the whole router.
- **PROPOSED:** Candidate routes requiring that adapter become ineligible or `UNKNOWN`; no implicit alternate may weaken controls.

## Decommissioning conditions

- **PROPOSED:** Remove the router rather than preserve it if it becomes a second proxy, quota ledger, execution engine, workflow engine, proof store, or release gate.
- **PROPOSED:** Reconsider a network service only after measured evidence shows the in-process library cannot support required concurrency, remote clients, or isolation.
- **PROPOSED:** Any future service proposal requires a new ADR and proof that it does not duplicate DopeconBridge, LiteLLM, Freeflow, Task Orchestrator, or dopetask.

## Migration stop conditions

- **PROPOSED:** Stop when an adapter requires unapproved writes, a source contract is unstable, an authority contradiction is unresolved, a required root authority file is absent and no tracked runtime evidence resolves it, or first-release code can cross into execution.
- **PROPOSED:** Stop policy promotion on failed hard-boundary tests, stale proof, unknown reviewer/bot, failed checks, or PR Steward status other than `READY`.
