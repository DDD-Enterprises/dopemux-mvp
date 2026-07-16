# Security and Failure Model

## Security posture

- **PROPOSED:** The Universal Router is a policy and evidence decision point, not a provider credential broker, network proxy, shell executor, workflow writer, or release authority.
- **PROPOSED:** Release one is read-only and advisory, with append-only writes limited to its own workspace journal.
- **PROPOSED:** The primary security objective is to prevent a recommendation or evidence claim from silently weakening privacy, containment, identity, cost, audit, authority, or approval controls.
- **UNKNOWN:** Local runner containment and provider identity evidence are uneven across Codex, Claude Code, Gemini CLI, AGY, LiteLLM, and OpenRouter. Candidate eligibility must reflect the actual evidence level.

## Protected assets

| Asset | Claim label | Required protection |
|---|---|---|
| Repository source and uncommitted changes | **PROPOSED** | Read/write scope, worktree isolation, redaction, path validation |
| Secrets, credentials, tokens, private keys, cookies | **PROPOSED** | Never journal raw values; deny unauthorized network exposure |
| Task and client data | **PROPOSED** | Privacy classification, network policy, retention, access control |
| Executable route policy | **PROPOSED** | Tracked history, schema validation, content hash, reviewed promotion, rollback |
| Capability and health snapshots | **PROPOSED** | Source provenance, expiry, environment scope, integrity hash |
| Universal route decisions | **PROPOSED** | Append-only history, deterministic replay, correction events |
| Model identity evidence | **PROPOSED** | Trust-tier separation, conflict preservation, request linkage |
| Usage, credit, and cost evidence | **PROPOSED** | Source/confidence labels and no unsupported derivation |
| Proof, handoff, audit, approval, PR readiness refs | **PROPOSED** | Integrity, freshness, head/decision linkage, no schema forks |
| Operator intent and overrides | **PROPOSED** | Explicit scope, expiry, provenance, no silent promotion |

## Trust boundaries

1. **PROPOSED:** Operator input to Dopemux CLI.
2. **PROPOSED:** Router package to tracked policy and schema files.
3. **PROPOSED:** Router to workspace SQLite journal.
4. **PROPOSED:** Router to imported capability/provider-health artifacts.
5. **PROPOSED:** Router adapters to DCP, Freeflow, LiteLLM, RTE, proof, handoff, audit, and PR Steward sources.
6. **PROPOSED:** Future router handoff boundary to dopetask.
7. **PROPOSED:** Provider/proxy/runner outputs to identity and usage normalization.
8. **PROPOSED:** Repository and external documents to the decision engine. These are data, not authority.

## Threat model

### T1: Authority capture

- **Threat:** A bridge, proxy, dormant agent, DCP component, or router adapter is promoted into canonical workflow, execution, proof, quota, or release authority.
- **Control:** Hard-coded authority invariants, explicit `SubsystemDecisionRef` types, no write adapter in release one, and forbidden-boundary fixtures.
- **Failure result:** `BLOCKED` with `AUTHORITY_CONFLICT` or `NEEDS_SUPERVISOR` when evidence conflicts.

### T2: Policy tampering or shadow policy

- **Threat:** An untracked file, environment value, stale advisory policy, or workspace overlay broadens routes without review.
- **Control:** Tracked active pointer, immutable versioned policy, content hash, strict schema, precedence checks, tightening-only overlay, and promotion evidence.
- **Failure result:** `BLOCKED`; `explain` may diagnose but `recommend` cannot select a route.

### T3: Snapshot poisoning or stale capability

- **Threat:** Fabricated, copied, cross-host, or expired capability/health evidence makes an unsafe route appear eligible.
- **Control:** Acquisition method, host/environment scope, source hash, adapter version, TTL, confidence, and contradiction retention.
- **Failure result:** Candidate ineligible, `UNKNOWN`, or explicit stale-evidence operator override where policy permits low risk.

### T4: Prompt injection and untrusted evidence

- **Threat:** A task, PR comment, web page, model response, or artifact instructs the router to ignore policy or claim authority.
- **Control:** Treat content as data; only validated contracts and tracked policy affect decisions; sanitize rendered output; never execute embedded commands.
- **Failure result:** Ignore instruction, record evidence conflict if material, and block on unresolved authority impact.

### T5: Secret or sensitive-data leakage

- **Threat:** Task text, environment values, diffs, logs, or proof refs expose secrets through the journal, CLI, provider route, or evaluation corpus.
- **Control:** Redaction before storage, path/field allowlists, secret-pattern scanning, network posture gates, hash/external-ref storage, and minimal retention.
- **Failure result:** `BLOCKED`, security incident record outside router authority, and route/certification revocation where applicable.

### T6: Model identity spoofing

- **Threat:** Requested/configured model, model-generated text, proxy metadata, or request ID is treated as provider attestation.
- **Control:** Separate all identity fields, require provider-controlled served-model metadata tied to request for attestation, retain conflicts, and cap confidence by source.
- **Failure result:** `attested_actual_model=UNKNOWN`; pinned-model, independent-audit, benchmark, and release-sensitive claims blocked.

### T7: Cost or credit laundering

- **Threat:** Estimated cost is called actual, plan credits are inferred from tokens, runner overhead is guessed by subtraction, or missing telemetry is treated as zero.
- **Control:** Separate usage fields, measurement source/confidence, pricing version, exact/estimated/session/unavailable states, and Freeflow authority refs.
- **Failure result:** Candidate ranked conservatively or blocked where a hard ceiling requires exact/admitted evidence.

### T8: Quota or admission bypass

- **Threat:** Router recommends a path that Freeflow rejects or constructs its own quota interpretation.
- **Control:** Freeflow decision remains separate and authoritative for admission; router references it and cannot mutate it in release one.
- **Failure result:** Route recommendation is `BLOCKED` or marked not admitted, without selecting a bypass path that weakens policy.

### T9: Containment theatre

- **Threat:** Prompt text such as “do not write” is represented as filesystem, command, network, MCP, environment, or session enforcement.
- **Control:** Every control records enforcement source; only runner/OS/wrapper/operator evidence may satisfy corresponding requirements.
- **Failure result:** Candidate ineligible for tasks requiring unproven enforcement.

### T10: Environment failure misclassification

- **Threat:** Sandbox DNS/network denial, missing credentials, filesystem policy, wrapper failure, or unavailable local binary is interpreted as model incapability or provider outage.
- **Control:** Failure taxonomy separates environment, auth, provider, policy, and model behavior; snapshot scope records where the probe ran.
- **Failure result:** Repair/defer/same-tier alternate/block. Never automatic premium-model promotion.

### T11: Audit collusion or self-certification

- **Threat:** Same runner/session challenge or skipped audit is presented as independent pass.
- **Control:** Audit assignment records runner, provider path, model identity confidence, session, independence dimensions, verdict, and skip reason.
- **Failure result:** `REQUIRED_NOT_RUN`, `SKIPPED_WITH_REASON`, or `NEEDS_SUPERVISOR`; never `PASS`.

### T12: Proof or PR freshness confusion

- **Threat:** Old proof, audit, checks, or readiness is linked to a newer head or decision.
- **Control:** Immutable refs, head SHA, decision ID, timestamps, content hashes, and PR Steward current-head requirement.
- **Failure result:** Stale-ref block. Router cannot recertify or override PR Steward.

### T13: Journal tampering and rollback erasure

- **Threat:** Updates/deletes rewrite history, rollback hides prior decisions, or sequence ordering is ambiguous.
- **Control:** SQLite update/delete abort triggers, WAL, foreign keys, migration ledger, monotonic sequence IDs, hashes, backups, and append-only correction/rollback events.
- **Failure result:** Enter `READ_ONLY_DEGRADED`, stop recommendations requiring persistence, preserve recoverable database.

### T14: Concurrent writer race

- **Threat:** Two CLI processes create inconsistent decisions, snapshot imports, or operator acceptance events.
- **Control:** SQLite transactions, bounded busy timeout, unique idempotency keys, expected-parent checks, and single-event append semantics.
- **Failure result:** One write succeeds; the other returns a conflict and must re-read. No silent last-writer-wins mutation.

### T15: Path traversal, symlink, or output-location escape

- **Threat:** Task/envelope refs or imported artifacts point outside permitted repository/workspace roots or through unsafe links.
- **Control:** Canonical path resolution, allowlisted roots, `lstat`/symlink policy, no implicit file creation outside router-owned directory, and hash validation.
- **Failure result:** Reject artifact/ref and block dependent decision.

### T16: Malformed or oversized input denial

- **Threat:** Huge task text, cyclic refs, deeply nested JSON, giant logs, or repeated CLI calls exhaust memory/disk.
- **Control:** Input and ref limits, streaming hashes, bounded rendering, pagination, SQLite quotas/retention, and no raw transcript ingestion by default.
- **Failure result:** Validation error or partial diagnostic with `BLOCKED`, not process-wide crash where avoidable.

### T17: Dependency or parser compromise

- **Threat:** YAML/JSON parser, SQLite binding, CLI framework, or adapter dependency executes unsafe behavior or changes semantics.
- **Control:** Safe loaders, pinned dependencies under repo policy, schema tests, no object deserialization, SBOM/dependency checks, and least-privilege file access.
- **Failure result:** Disable affected surface and require reviewed dependency update.

### T18: Provider drift and silent fallback

- **Threat:** Proxy/provider serves a different model/path or fallback than configured, changing privacy, cost, identity, or capability.
- **Control:** Requested/configured/proxy/provider/attested fields, fallback observation, policy constraints, and certification bound to route tuple.
- **Failure result:** `CONFLICTING` identity, certification invalidation, and block for pinned, independent, benchmark, security, or release routes.

## Required red-lane controls

- **PROPOSED:** Security, auth, secrets, destructive behavior, CI/release configuration, public behavior, and authority-boundary changes require explicit human approval and independent audit.
- **PROPOSED:** Unknown actual model identity blocks pinned-model certification, audit-independence claims, benchmark certification, and release-sensitive recommendations.
- **PROPOSED:** General network access is not eligible when a narrower approved provider or restricted-domain posture satisfies the task.
- **PROPOSED:** No future execution adapter receives broad destructive permission without packet allowlists, rollback, and proof requirements.

## Failure taxonomy

| Failure class | Claim label | Examples | Required router behavior |
|---|---|---|---|
| `INPUT_INVALID` | **PROPOSED** | Schema error, missing task, bad ref | Reject before classification |
| `CLASSIFICATION_UNKNOWN` | **PROPOSED** | Privacy/risk/task class unresolved | Block or escalate; do not guess |
| `POLICY_INVALID` | **PROPOSED** | Hash mismatch, schema error, cycle, weakening overlay | Block recommendation |
| `POLICY_CONFLICT` | **PROPOSED** | Two applicable rules disagree | Preserve conflict, escalate |
| `CAPABILITY_UNKNOWN` | **PROPOSED** | Feature not locally proven | Ineligible where required; documented-only advisory if policy permits |
| `SNAPSHOT_STALE` | **PROPOSED** | TTL exceeded | Refresh, accept bounded override, alternate, or block |
| `ENVIRONMENT_BLOCKED` | **PROPOSED** | Sandbox network denial, filesystem restriction | Repair/defer/same-tier alternate/block; no premium promotion |
| `AUTH_FAILURE` | **PROPOSED** | Missing/expired credential | Repair credential path or block; do not infer provider outage |
| `PROVIDER_UNAVAILABLE` | **PROPOSED** | Provider-controlled outage evidence | Same-tier eligible alternate, cooldown/admission ref, or defer |
| `RATE_LIMITED` | **PROPOSED** | Provider/Freeflow rate limit | Respect admission/cooldown; no bypass ledger |
| `RUNNER_UNAVAILABLE` | **PROPOSED** | Binary missing/version unsupported | Same-tier eligible runner or block |
| `IDENTITY_UNKNOWN` | **PROPOSED** | No served-model evidence | Block identity-sensitive claim |
| `IDENTITY_CONFLICT` | **PROPOSED** | Config/proxy/provider disagree | Preserve `CONFLICTING`; block sensitive route |
| `COST_UNKNOWN` | **PROPOSED** | No exact/estimated cost | Allow only where policy has no hard cost need; otherwise block/escalate |
| `CREDITS_UNKNOWN` | **PROPOSED** | No published credit observation | Do not convert tokens; apply unknown-credit rule |
| `CONTAINMENT_UNVERIFIED` | **PROPOSED** | Prompt-only read-only claim | Ineligible for enforced-control requirement |
| `NETWORK_POSTURE_UNKNOWN` | **PROPOSED** | Egress not proven | Ineligible for sensitive route |
| `ADMISSION_DENIED` | **PROPOSED** | Freeflow decision denies | Block that candidate |
| `RTE_ROUTE_BLOCKED` | **PROPOSED** | RTE specialized gate refuses | Preserve RTE authority; do not reproduce route |
| `VALIDATION_FAILED` | **PROPOSED** | Test/schema/check failure | Future execution attempt may repair within budget or escalate |
| `AUDIT_FAILED` | **PROPOSED** | `FAIL` | Escalate or block; no completion |
| `AUDIT_SKIPPED` | **PROPOSED** | Tool unavailable/capacity | Preserve skip reason; never pass |
| `PROOF_STALE_OR_MISSING` | **PROPOSED** | Broken ref or wrong head | Block proof-dependent claim |
| `PR_STEWARD_BLOCKED` | **PROPOSED** | Unknown review, failed checks, unresolved thread | Preserve readiness block |
| `JOURNAL_FAILURE` | **PROPOSED** | Lock, corruption, migration failure | Read-only degraded mode or fail closed |
| `OPERATOR_REJECTED` | **PROPOSED** | Recommendation rejected | Append correction/rejection; no execution |

## Escalation and demotion safety

- **PROPOSED:** Model/reasoning escalation is driven by task complexity, validation/audit evidence, or policy, not by environment failure.
- **PROPOSED:** One reasoning increase and one model-tier increase are the default future attempt budgets unless a task policy is stricter.
- **PROPOSED:** Demotion is permitted only when all hard requirements remain satisfied and the route is certified for the task class.
- **PROPOSED:** Cost pressure may demote or block. It may not remove containment, privacy, identity, validation, or audit requirements.
- **PROPOSED:** Provider/runner unavailability may select an equivalent same-tier route. If equivalence is unproven, return `BLOCKED` or `ESCALATED`.

## Incident response boundary

- **PROPOSED:** The router may emit an evidence record and disable an affected route/policy through an operator action, but it is not the incident-management system.
- **PROPOSED:** Security incidents, leaked credentials, provider abuse, and release rollback follow existing repository and organizational procedures.
- **PROPOSED:** Do not store raw leaked material in the router journal. Store classification, hashes, protected refs, and response status.

## Security validation suite

- **PROPOSED:** Policy tamper/hash mismatch tests.
- **PROPOSED:** Weakening-overlay rejection tests.
- **PROPOSED:** Path traversal and symlink tests.
- **PROPOSED:** SQLite append-only and concurrent-writer tests.
- **PROPOSED:** Secret redaction and no-raw-environment tests.
- **PROPOSED:** Prompt-injection and untrusted-model-claim fixtures.
- **PROPOSED:** Identity conflict and request-ID-only tests.
- **PROPOSED:** Prompt-requested versus enforced containment tests.
- **PROPOSED:** Sandbox denial versus provider outage tests.
- **PROPOSED:** Environment failure cannot promote cost/model tier tests.
- **PROPOSED:** Same-runner, same-session, and skipped-audit tests.
- **PROPOSED:** Stale proof/current-head mismatch tests.
- **PROPOSED:** Freeflow denial and RTE blocked-decision preservation tests.
- **PROPOSED:** Fuzz/property tests for contracts and state transitions.

## Residual unknowns

- **UNKNOWN:** Whether each runner can emit provider-controlled served-model metadata sufficient for attestation.
- **UNKNOWN:** Whether AGY and Gemini CLI can satisfy required containment and session-persistence controls in the target operator environment.
- **UNKNOWN:** Exact stable read interfaces for every Freeflow, LiteLLM, RTE, proof, audit, and PR Steward adapter at the implementation commit.
- **UNKNOWN:** Organizational retention and access requirements for task text, decision journals, and evaluation corpora.
- **UNKNOWN:** Whether policy signatures beyond Git history/content hashes are required.
- **PROPOSED:** These unknowns block affected adapter or phase certification, not independent audit of this architecture.
