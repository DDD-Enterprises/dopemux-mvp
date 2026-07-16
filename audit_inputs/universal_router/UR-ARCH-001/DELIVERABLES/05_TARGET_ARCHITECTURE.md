# Target Architecture

## Architectural thesis

- **PROPOSED:** The Universal Router is a small, deterministic orchestration library inside Dopemux. It is a decision synthesizer, not a provider gateway, execution runtime, workflow system, or governance authority.
- **PROPOSED:** The design follows a reference architecture: each universal record points to the authoritative subsystem record that produced the underlying fact.
- **PROPOSED:** Every recommendation is reproducible from a TaskEnvelope, DCP ref, policy version, capability/provider-health snapshots, and subsystem decision refs.

## Package layout

```text
src/dopemux/universal_router/
  __init__.py
  models.py
  engine.py
  policy.py
  journal.py
  snapshots.py
  adapters.py
  cli.py

schemas/universal-router/
  route-policy.schema.json
  task-envelope.schema.json
  universal-route-decision.schema.json
  capability-snapshot.schema.json

config/universal-router/
  active-policy.json
  policies/
    ur-policy-<semver>.yaml

tests/universal_router/
  test_models.py
  test_policy.py
  test_engine.py
  test_journal.py
  test_snapshots.py
  test_adapters.py
  test_state_machine.py
  test_cli.py
```

- **PROPOSED:** The exact first implementation may use fewer schema files if Pydantic/dataclass validation is already the repo norm, but it must not use more authority-bearing contracts than the catalog in `07_CONTRACT_CATALOG.md`.
- **PROPOSED:** The package name is intentionally explicit. It avoids collision with existing `routing_config.py`, `routing_cli.py`, Freeflow, and RTE route code.

## Logical components

| Label | Component | Responsibility | Forbidden responsibility |
|---|---|---|---|
| **PROPOSED** | CLI facade | Parse operator input, call engine, render ADHD-friendly top results, request explicit recording | Provider calls, execution, policy promotion |
| **PROPOSED** | Task-envelope builder | Normalize task text, repo binding, constraints, privacy assertions, and evidence refs | Replacing dopetask packet schema |
| **PROPOSED** | DCP adapter | Obtain or import immutable DCP result | Recomputing DCP semantics |
| **PROPOSED** | Snapshot resolver | Resolve fresh runner/model/provider capabilities | Treating stale or vendor-only facts as live health |
| **PROPOSED** | Policy evaluator | Enforce hard invariants, candidate eligibility, precedence, and fail-closed rules | Quota mutation, provider dispatch |
| **PROPOSED** | Candidate generator | Build ranked route candidates from certified registry entries and snapshots | Inventing unsupported runner/model capabilities |
| **PROPOSED** | Decision engine | Select recommendation, alternatives, validation route, audit route, escalation/demotion posture | Execution authorization |
| **PROPOSED** | Journal | Append intake, classification refs, snapshots refs, decisions, state transitions, and operator acceptance | Storing proof bodies, approvals, provider secrets, or Freeflow/RTE state |
| **PROPOSED** | Read-only subsystem adapters | Import Freeflow, LiteLLM, RTE, proof, handoff, audit, and PR refs | Becoming a second writer for any subsystem |
| **PROPOSED** | Validator | Validate policies, contracts, stale snapshots, references, and legal transitions | Claiming external artifact correctness beyond available evidence |

## Authority boundary diagram

```text
Operator
   |
   v
Dopemux CLI: dopemux route
   |
   +--> TaskEnvelope -------------------------------+
   |                                                |
   +--> DCP adapter --> DCPClassificationRef        |
   |                                                v
   +--> Snapshot resolver --> capability/health --> Policy evaluator
   |                                                |
   |                                                v
   |                                      RouteCandidate[]
   |                                                |
   |                                                v
   +--------------------------------------> UniversalRouteDecision
                                                    |
                +-----------------------------------+------------------+
                |                                   |                  |
                v                                   v                  v
        Freeflow admission ref             RTE route ref       LiteLLM observation ref
                |                                   |                  |
                +-----------------------------------+------------------+
                                                    |
                                                    v
                                       ExecutionRecommendation
                                                    |
                                     release one stops here
                                                    |
                               future: operator accepted handoff
                                                    |
                                                    v
                                              dopetask execution
                                                    |
                     validation -> audit -> proof -> PR Steward readiness
```

## First-release execution model

- **PROPOSED:** The engine is deterministic and performs no model call to choose a model.
- **PROPOSED:** Candidate ranking uses policy rules, evidence confidence, certification, freshness, cost/credit observability, containment support, network posture, and route history.
- **PROPOSED:** The CLI may explain why a candidate was selected without invoking any external model.
- **PROPOSED:** `recommend` returns at most three candidates, a primary recommendation, blockers, evidence freshness, and a next action.
- **PROPOSED:** The CLI output includes `items`, `more_count`, and `next_token` where a list is returned, aligning with the repository operator-output contract.

## State-store design

### Canonical state

- **PROPOSED:** Canonical router state is SQLite at `<repo_root>/.dopemux/universal-router/router.sqlite3`.
- **PROPOSED:** Tables:
  - `schema_migrations`
  - `journal_events`
  - `route_decisions`
  - `capability_snapshots`
  - `provider_health_snapshots`
  - `policy_activations`
  - `reference_index`
- **PROPOSED:** `journal_events` is the replay spine. Domain tables are append-only projections for indexed reads.
- **PROPOSED:** No raw prompts, responses, credentials, secret-bearing environment values, proof bodies, or full diffs are stored by default.

### Replay and locking

- **PROPOSED:** WAL mode supports one writer and concurrent readers without introducing a service.
- **PROPOSED:** A workspace-scoped advisory lock prevents concurrent recommendation writes from interleaving one decision attempt.
- **PROPOSED:** Replay order is deterministic by integer `sequence_id`; timestamps are evidence, not ordering authority.
- **PROPOSED:** Every event includes schema version, event type, decision ID, parent event, policy hash, and redacted payload hash.

### Migration

- **PROPOSED:** Forward-only migrations are tracked in `schema_migrations` with checksum.
- **PROPOSED:** Migration failure leaves the existing database untouched and places the CLI in `READ_ONLY_DEGRADED` mode.
- **PROPOSED:** No automatic destructive migration is permitted.

### Retention

- **PROPOSED:** Route decisions and policy activation records default to 365 days in workspace storage, subject to repository governance.
- **PROPOSED:** Provider-health snapshots default to 30 days because their operational value decays quickly.
- **PROPOSED:** Capability snapshots default to 180 days for audit history, although only fresh snapshots participate in decisions.
- **PROPOSED:** Retention is enforced by explicit operator maintenance, not silent background deletion in release one.
- **UNKNOWN:** Final retention durations require governance confirmation before implementation.

### Redaction

- **PROPOSED:** Store only secret presence classifications, key names when safe, hashes, and refs. Never store secret values.
- **PROPOSED:** Task text is stored only when operator policy permits; otherwise store a content hash plus external ref.
- **PROPOSED:** Paths may be repo-relative; absolute home paths are redacted from portable exports.

### Rollback

- **PROPOSED:** Disable router with `DOPEMUX_UNIVERSAL_ROUTER_DISABLED=1` or an equivalent CLI config switch.
- **PROPOSED:** Roll back active policy by reverting `config/universal-router/active-policy.json` to a prior certified hash.
- **PROPOSED:** Preserve the append-only database during rollback. It is evidence, not executable state.
- **PROPOSED:** If the package must be removed, existing Dopemux routing commands, Freeflow, LiteLLM, RTE, Task Orchestrator, and dopetask continue unchanged.

## Capability registry

- **PROPOSED:** The tracked registry contains `ModelCapabilityRecord` entries, not claims of current availability.
- **PROPOSED:** Each entry is keyed by provider path, runner, model identifier or alias, adapter version, and policy-compatible capability flags.
- **PROPOSED:** A candidate can be eligible only when registry capability and a fresh local snapshot agree or the policy explicitly permits documented-only advisory use.
- **PROPOSED:** Registry entries may refer to vendor documentation, local help, smoke evidence, benchmark certification, and known limitations separately.

## Snapshot lifecycle

| Label | Snapshot class | Default freshness | Expiry trigger |
|---|---|---:|---|
| **PROPOSED** | Local executable version/help | 7 days | executable version/hash change |
| **PROPOSED** | Runner containment capabilities | 7 days | version/config change |
| **PROPOSED** | Authentication presence/status | 15 minutes | auth-state change or explicit logout |
| **PROPOSED** | Positive provider health | 5 minutes | timeout, auth failure, cooldown, config change |
| **PROPOSED** | Transient environment/network failure | 60 seconds | fresh probe in the same network posture |
| **PROPOSED** | Freeflow cooldown/admission | subsystem-defined | Freeflow record expiry/change |
| **PROPOSED** | Vendor model catalog | 24 hours for automated imports | source/version change |
| **PROPOSED** | Benchmark certification | max 30 days | any route tuple component or adapter/policy version changes |

- **PROPOSED:** TTLs are policy defaults and must be visible in decisions.
- **PROPOSED:** Stale positive health does not become negative health. It becomes `STALE`.
- **PROPOSED:** Negative sandbox reachability is scoped to `SANDBOX_NETWORK_DENIED` and must not poison host-level provider health.

## Policy precedence

1. **PROPOSED:** Hard-coded non-overridable safety invariants.
2. **PROPOSED:** Schema-valid active certified policy.
3. **PROPOSED:** Repository-local tightening-only overlay.
4. **PROPOSED:** Task-packet/operator constraints.
5. **PROPOSED:** DCP classification and route-specific risk/privacy composite.
6. **PROPOSED:** Candidate registry and fresh snapshots.
7. **PROPOSED:** Freeflow/RTE subsystem decisions within their authority slices.
8. **PROPOSED:** Operator preference hints that do not weaken higher layers.

## Future execution phases

- **PROPOSED:** Phase E1 adds exactly one execution adapter, initially Codex if its packet proves containment, identity/usage capture, and dopetask handoff compatibility.
- **PROPOSED:** Phase E2 may add Claude Code Sonnet as fallback, then Opus only for explicit high-complexity cases.
- **PROPOSED:** AGY/Sonnet audit integration remains preferred only after safe availability and containment are proven.
- **PROPOSED:** Gemini CLI remains a broad-context contradiction auditor, not a default implementer, until local containment and subagent behavior are proven.
- **PROPOSED:** Each adapter has independent certification and can be revoked without disabling the advisory router.
