# Implementation Roadmap

## Roadmap posture

- **PROPOSED:** This roadmap sequences the smallest safe Universal Router from contracts to a future narrowly certified automatic lane.
- **PROPOSED:** Steps 1 through 9 define the first release. They stop at `ROUTE_RECOMMENDED` or explicit `OPERATOR_ACCEPTED` and cannot execute work.
- **PROPOSED:** Steps 10 through 12 require new approvals, current evidence, and separate architecture acceptance before enabling execution or automatic selection.
- **PROPOSED:** Every repo-changing step is executed from a dedicated branch/worktree under a task packet with exact allowlists, commands, validation, proof, rollback, stop conditions, embedded audit, and PR Steward intake when a PR is opened.

## Allocation model

| Role | Claim label | Default allocation |
|---|---|---|
| Architecture supervisor | **PROPOSED** | GPT-5.6 Pro for architecture, macro packets, conflict resolution, and high-risk escalation |
| Primary bounded implementer | **PROPOSED** | Codex in a dedicated worktree from a precise packet |
| Implementation fallback | **PROPOSED** | Claude Code Sonnet when Codex capability, capacity, or fit is insufficient |
| High-complexity implementation/refactor fallback | **PROPOSED** | Claude Code Opus after bounded Sonnet/Codex failure or for explicitly justified depth |
| Preferred embedded auditor | **PROPOSED** | AGY/Sonnet only when capability, containment, identity, and safe invocation are current and proven |
| Embedded-audit fallback | **PROPOSED** | Claude Code CLI Sonnet, then Opus for depth/capacity failure |
| Broad-context contradiction auditor | **PROPOSED** | Gemini CLI for large-surface comparisons and cross-artifact contradiction hunts |
| Evidence spine | **PROPOSED** | Git commits, PRs, checks, artifacts, current head SHA, and PR Steward readiness |

- **PROPOSED:** No packet uses multiple implementers on the same slice by default.
- **PROPOSED:** No first-release packet enables subagent fanout.
- **PROPOSED:** Auditor output is captured in proof with tool, model, invocation, exit code when available, verdict, findings, fixes, remaining risks, and skip reason.

## Release map

| Release | Claim label | Included steps | Maximum state reached |
|---|---|---|---|
| R0 architecture | **PROPOSED** | Independent audit of this package | No repo change |
| R1 advisory foundation | **PROPOSED** | 1 through 7 | `ROUTE_RECOMMENDED` |
| R1 shadow and acceptance | **PROPOSED** | 8 through 9 | `OPERATOR_ACCEPTED` |
| R2 bounded execution | **PROPOSED** | 10 | Future `EXECUTION_ACCEPTED` and later states for one adapter only |
| R3 bounded escalation | **PROPOSED** | 11 | Multiple attempts within explicit budgets |
| R4 certified automatic selection | **PROPOSED** | 12 | Narrow automatic lane, separately promoted |

## Step 1: Contract definitions

### Objective

- **PROPOSED:** Establish strict, versioned contracts for all Universal Router-owned records and typed references to existing subsystem records.

### Deliverables

- **PROPOSED:** `src/dopemux/universal_router/models.py`.
- **PROPOSED:** `schemas/universal-router/route-policy.schema.json` and contract schemas or generated-schema tests.
- **PROPOSED:** TaskEnvelope, DCPClassificationRef, RiskPrivacyClassification, RunnerCapabilitySnapshot, ProviderHealthSnapshot, ModelCapabilityRecord, RoutePolicy, RouteCandidate, UniversalRouteDecision, SubsystemDecisionRef, ExecutionRecommendation, ExecutionRequest, RunnerResult, ModelIdentityObservation, UsageObservation, ContainmentDeclaration, NetworkPosture, ValidationResult, EscalationDecision, AuditAssignment, AuditResultRef, HumanApprovalRef, BenchmarkCertification, ProofBundleRef, DopetaskHandoffRef, and PRStewardReadinessRef.
- **PROPOSED:** Contract fixtures for valid, invalid, unknown, and conflicting states.

### Gate

- **PROPOSED:** Strict schema validation, semantic invariants, no forked proof/handoff fields, and independent review of authority boundaries.

### Stop conditions

- **PROPOSED:** Stop if a referenced canonical contract cannot be located at the implementation commit or if the proposed model requires duplicating its schema.

## Step 2: Read-only CLI recommendations

### Objective

- **PROPOSED:** Expose deterministic `dopemux route explain`, `recommend`, `inspect`, and `validate` through an in-process package.

### Deliverables

- **PROPOSED:** `src/dopemux/universal_router/{__init__,engine,policy,cli}.py`.
- **PROPOSED:** Registration from `src/dopemux/cli.py`.
- **PROPOSED:** ADHD-friendly list output with `items`, `more_count`, and `next_token`, plus versioned JSON output.
- **PROPOSED:** Static policy and fixture-backed decisions only.

### Gate

- **PROPOSED:** No provider/runner invocation, no network call, no subprocess, no upstream mutation, and deterministic output for frozen input.

### Stop conditions

- **PROPOSED:** Stop if CLI registration requires rewriting current `routing` behavior or if any code path can cross `ROUTE_RECOMMENDED`.

## Step 3: Append-only decision journal

### Objective

- **PROPOSED:** Persist the router's own decision history, snapshot imports, corrections, and acceptance events without taking ownership of upstream state.

### Deliverables

- **PROPOSED:** `src/dopemux/universal_router/journal.py`.
- **PROPOSED:** SQLite schema, migration ledger, update/delete abort triggers, WAL configuration, idempotency keys, replay API, and retention/redaction hooks.
- **PROPOSED:** Workspace path `<repo_root>/.dopemux/universal-router/router.sqlite3`.

### Gate

- **PROPOSED:** Deterministic replay, concurrency tests, corruption/migration failure behavior, no raw secret storage, and disablement independence.

### Stop conditions

- **PROPOSED:** Stop if the journal begins storing quota, RTE run state, workflow state, proof bodies, approvals, or release readiness as router authority.

## Step 4: Capability-snapshot ingestion

### Objective

- **PROPOSED:** Import locally acquired runner capability and provider-health evidence with source, confidence, scope, and expiry.

### Deliverables

- **PROPOSED:** `src/dopemux/universal_router/snapshots.py`.
- **PROPOSED:** Snapshot import/validate/inspect CLI paths.
- **PROPOSED:** TTL and invalidation rules for versions, auth, health, containment, vendor catalogs, and benchmark certifications.
- **PROPOSED:** Fixtures based on UR-INV-003 limitations without promoting them to verified status.

### Gate

- **PROPOSED:** Stale, cross-environment, conflicted, and unverifiable snapshots behave according to policy; sandbox denial is not provider outage.

### Stop conditions

- **PROPOSED:** Stop if acquisition requires broad credentials, destructive permissions, or unapproved live provider research.

## Step 5: Existing-subsystem adapters

### Objective

- **PROPOSED:** Normalize read-only references and observations from DCP, Freeflow, LiteLLM, RTE, proof, handoff, audit, and PR Steward sources.

### Deliverables

- **PROPOSED:** `src/dopemux/universal_router/adapters.py` with independently versioned adapter identities.
- **PROPOSED:** Artifact-first fallback for sources without a stable runtime read API.
- **PROPOSED:** Contract tests proving no mutation and no authority absorption.

### Gate

- **PROPOSED:** Each adapter declares source authority, supported operations, unavailable fields, freshness semantics, and failure mapping.

### Stop conditions

- **PROPOSED:** Stop an adapter if the only available interface requires writes, exposes secrets, or cannot distinguish canonical source from proxy/derived output.

## Step 6: Codex advisory adapter

### Objective

- **PROPOSED:** Represent Codex runner capabilities, containment declarations, usage observations, and execution-request shape without invoking it.

### Deliverables

- **PROPOSED:** Codex-specific adapter normalization and fixtures.
- **PROPOSED:** Mapping for `--model`, JSONL, output schema, sandbox, ephemeral mode, usage fields, and unknown cost/credits/actual identity.
- **PROPOSED:** Recommendation explanations that expose unproven tool denial or model identity.

### Gate

- **PROPOSED:** No claim that Codex model text identifies the served model; no token-to-credit conversion; no runner invocation.

### Stop conditions

- **PROPOSED:** Stop if current Codex CLI behavior materially differs from the capability snapshot and cannot be reacquired safely.

## Step 7: Proof references

### Objective

- **PROPOSED:** Link recommendations and future attempts to canonical proof, handoff, validation, audit, human approval, and PR Steward records by immutable refs.

### Deliverables

- **PROPOSED:** Ref validation, content/head hashes, freshness checks, and broken-ref diagnostics.
- **PROPOSED:** No duplicate proof or handoff schema.
- **PROPOSED:** Decision rendering that distinguishes missing, stale, partial, failed, and conflicting evidence.

### Gate

- **PROPOSED:** Current-head and chain-of-custody tests pass; upstream verdicts are never rewritten.

### Stop conditions

- **PROPOSED:** Stop if a canonical schema is ambiguous, stale, or unavailable and the router would need to invent fields.

## Step 8: Shadow evaluation

### Objective

- **PROPOSED:** Evaluate historical and live advisory recommendations without affecting execution.

### Deliverables

- **PROPOSED:** Versioned historical corpus, gold-label tooling, replay runner, hard-negative fixtures, metrics, and certification report.
- **PROPOSED:** Silent and visible shadow protocols from the evaluation plan.
- **PROPOSED:** Decision-diff and operator-correction artifacts.

### Gate

- **PROPOSED:** Advisory certification thresholds, independent audit, current proof, and PR Steward `READY`.

### Stop conditions

- **PROPOSED:** Stop promotion on any severe failure, hard-boundary failure, data leak, or unresolved evaluator contradiction.

## Step 9: Manual operator acceptance

### Objective

- **PROPOSED:** Record explicit acceptance, alternate selection, rejection, or correction without executing the recommendation.

### Deliverables

- **PROPOSED:** Acceptance CLI and append-only events with decision hash, operator ref, selected candidate, reason, scope, and expiry.
- **PROPOSED:** Override and correction reports.
- **PROPOSED:** No handoff write or runner invocation.

### Gate

- **PROPOSED:** Acceptance cannot change original decision evidence, cannot fabricate approval, and cannot bypass hard invariants.

### Stop conditions

- **PROPOSED:** Stop if operator acceptance becomes implicit, defaulted, or coupled to execution.

## Step 10: One execution adapter at a time

### Objective

- **PROPOSED:** Future phase. Add exactly one bounded execution adapter after separate approval and per-adapter certification.

### Initial candidate

- **INFERRED:** Codex is the leading first candidate because the local evidence includes a successful contained smoke, JSONL, output-schema, sandbox, and ephemeral surfaces.
- **UNKNOWN:** Actual model attestation, plan-credit telemetry, hard tool denial, current auth mode, and target-environment behavior remain insufficient for an execution decision today.

### Deliverables

- **PROPOSED:** Dedicated `runner_adapters/codex.py` only after the adapter split is justified.
- **PROPOSED:** Explicit `ExecutionRequest`, wrapper-enforced worktree/file/command/network controls, proof capture, idempotency, cancellation, and rollback.
- **PROPOSED:** Task classes initially limited to reviewed low-risk implementation packets.

### Gate

- **PROPOSED:** Per-adapter certification, independent containment audit, current identity/usage posture, zero severe failures in bounded trial, and explicit human enablement.

### Stop conditions

- **PROPOSED:** Stop on allowlist escape, identity conflict for a pinned task, missing proof, unauthorized network/write, or any attempt to execute a second adapter in parallel.

## Step 11: Bounded escalation

### Objective

- **PROPOSED:** Future phase. Add deterministic retry, reasoning escalation, model-tier escalation, demotion, and alternate-route behavior within hard budgets.

### Deliverables

- **PROPOSED:** Attempt graph, escalation decision records, per-class budgets, validation/audit triggers, cooldown/admission refs, and operator-visible explanations.
- **PROPOSED:** Default maximum of one reasoning increase and one model-tier increase unless a stricter policy applies.
- **PROPOSED:** Environment failures have a separate path that cannot promote cost/model tier.

### Gate

- **PROPOSED:** At least 50 reviewed escalation scenarios, zero severe failures, exact state legality, and independent audit.

### Stop conditions

- **PROPOSED:** Stop on loops, repeated identical failure, cost ceiling breach, stale identity/capability evidence, or guard-weakening fallback.

## Step 12: Automatic routing only after certification

### Objective

- **PROPOSED:** Future phase. Promote a narrowly scoped automatic route-selection policy after sustained evidence.

### Preconditions

- **PROPOSED:** At least 100 certified low-risk executions for the exact lane and route tuple.
- **PROPOSED:** Zero severe failures and no unresolved authority, privacy, identity, containment, audit, or proof defect.
- **PROPOSED:** Current benchmark certification, independent audit, human policy approval, and PR Steward `READY`.
- **PROPOSED:** Route-specific kill switch, rollback, monitoring, and revocation tests.

### Boundary

- **PROPOSED:** Automatic route selection does not automatically grant execution, workflow, release, or human-approval authority.

### Stop conditions

- **PROPOSED:** Revoke or suspend on severe failure, provider drift, stale certification, policy mismatch, unexplained override spike, or proof/PR freshness failure.

## Cross-step validation gates

- **PROPOSED:** `git status` before and after.
- **PROPOSED:** `git diff --stat`, full `git diff`, and `git diff --check`.
- **PROPOSED:** Exact command outputs and exit codes.
- **PROPOSED:** Focused unit/contract tests, then broader affected-suite tests.
- **PROPOSED:** Schema and fixture validation.
- **PROPOSED:** Embedded audit for every non-trivial implementation packet.
- **PROPOSED:** PR Steward readiness for every opened PR.
- **PROPOSED:** Current proof must match the latest head SHA.

## Dependency and critical path

```text
1 Contracts
  -> 2 CLI
  -> 3 Journal
  -> 4 Snapshots
  -> 5 Existing adapters
  -> 6 Codex advisory adapter
  -> 7 Proof refs
  -> 8 Shadow evaluation
  -> 9 Manual acceptance
  -> [new architecture approval]
  -> 10 One execution adapter
  -> 11 Bounded escalation
  -> 12 Certified automatic lane
```

- **PROPOSED:** Steps 4 and 5 may be developed in separate branches only after contracts stabilize, but they should be merged sequentially to keep proof and policy current.
- **PROPOSED:** Step 6 depends on both snapshot and adapter contracts.
- **PROPOSED:** Step 8 cannot certify behavior until all release-one decision inputs and refs are stable.
- **PROPOSED:** Step 10 cannot start merely because step 9 is complete. It requires a new explicit go/no-go review.

## Roadmap completion definition

- **PROPOSED:** A step is complete only when its task packet acceptance criteria are met, embedded audit is captured, proof is current, PR Steward is `READY` when a PR exists, the diff stays inside scope, and remaining risks are explicit.
- **PROPOSED:** A merged PR or green CI check is evidence, not semantic proof by itself.
- **PROPOSED:** Skipped audit, stale proof, unknown reviewer/bot, unresolved blocking thread, or failed check prevents a completion claim.
