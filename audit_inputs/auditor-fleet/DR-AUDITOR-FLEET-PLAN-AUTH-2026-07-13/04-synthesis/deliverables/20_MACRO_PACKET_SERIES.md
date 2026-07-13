# Macro Task-Packet Series

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `20_MACRO_PACKET_SERIES.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Series posture

`PROPOSED` These are future macro packets for planning and sequencing. They are not active Task Packets and do not authorize repository changes.

## Dependency chain

```text
TP-AUD-001 Contract Authority
  -> TP-AUD-002 Mechanical Profiles
  -> TP-AUD-003 Broker Core
  -> TP-AUD-004 Manual Receipts
  -> TP-AUD-005 Worker Isolation
  -> TP-AUD-006 Exact-Head Verification
  -> TP-AUD-007 Codex/Claude Static Conformance
  -> TP-AUD-008 Authorized Live Conformance
  -> TP-AUD-009 Shadow Evaluation
  -> TP-AUD-010 GitHub Pull Pickup
  -> TP-AUD-011 Publisher
  -> TP-AUD-012 API Fallback
  -> TP-AUD-013 Limited Automation Gate
```

## Packet catalogue

### `TP-DMX-AUDIT-001-CONTRACT-AUTHORITY`

- **Disposition:** `CURRENTLY_DESIGNABLE`
- **Objective:** Freeze request, result, manual-receipt, adapter-state, failure, and route-profile contracts.
- **Must preserve:** Embedded-audit and PR Steward authority; no task-router revival.
- **Validation:** Schema examples, unknown-field rejection, exact-head fields, proof/handoff compatibility review.
- **Stop conditions:** Canonical schema conflict or missing governance decision.

### `TP-DMX-AUDIT-002-MECHANICAL-PROFILES`

- **Disposition:** `CURRENTLY_IMPLEMENTABLE_AFTER_AUTHORIZATION`
- **Objective:** Convert accepted validators into versioned, read-only, no-network profiles with authority limits.
- **Validation:** Mutation and network negative tests, deterministic exits, fixture coverage, proof receipts.
- **Stop conditions:** Any install, write, network access, or ambiguous authority.

### `TP-DMX-AUDIT-003-BROKER-CORE`

- **Disposition:** `DESIGNABLE_BUT_NOT_IMPLEMENTED`
- **Objective:** Implement strict local request validation, replay store, durable lease, route recommendation, worker dispatch, result validation, and sealed spool.
- **Validation:** State-machine tests, crash recovery, no-provider-credential check, no-candidate-execution check.
- **Stop conditions:** Broker requires broad GitHub or provider credentials.

### `TP-DMX-AUDIT-004-MANUAL-RECEIPTS`

- **Disposition:** `CURRENTLY_DESIGNABLE`
- **Objective:** Ingest human-operated tool receipts with exact-head and confidence labeling.
- **Validation:** Manual/automated distinction, artifact hashes, missing identity remains `UNKNOWN`.
- **Stop conditions:** Receipt path fabricates provider attestation or plan billing evidence.

### `TP-DMX-AUDIT-005-WORKER-ISOLATION`

- **Disposition:** `BLOCKED_PENDING_HOST_DECISION`
- **Objective:** Establish broker, per-tool, worker, and publisher OS/VM boundaries.
- **Validation:** Cross-user read/write negative tests, shared-directory audit, keychain/secret isolation, cleanup.
- **Stop conditions:** Candidate code can access persistent provider or GitHub credentials.

### `TP-DMX-AUDIT-006-EXACT-HEAD-VERIFICATION`

- **Disposition:** `DESIGNABLE`
- **Objective:** Verify repo/PR/base/head/source/freshness/replay at pickup, dispatch, result, and publication.
- **Validation:** Head-change races, replay, run-attempt mismatch, wrong-repo and wrong-workflow fixtures.
- **Stop conditions:** Any result can bind to a different head.

### `TP-DMX-AUDIT-007-CODEX-CLAUDE-STATIC-CONFORMANCE`

- **Disposition:** `BLOCKED_PENDING_VENDOR_AND_LOCAL_AUTH_EVIDENCE`
- **Objective:** Version-pinned, non-model validation of config isolation and prohibited surfaces.
- **Validation:** Effective settings capture, no-tool negative checks, unsafe-flag rejection, config-root isolation.
- **Stop conditions:** Requires account login, credential inspection, or model invocation without separate authorization.

### `TP-DMX-AUDIT-008-AUTHORIZED-LIVE-CONFORMANCE`

- **Disposition:** `BLOCKED_NOT_AUTHORIZED`
- **Objective:** Collect bounded identity, auth-route, output, network, timeout, and failure receipts for one approved tool at a time.
- **Validation:** Synthetic/public input, no repository secrets, exact route metadata, credential revocation rehearsal.
- **Stop conditions:** Any unknown privacy, terms, or containment gate.

### `TP-DMX-AUDIT-009-SHADOW-EVALUATION`

- **Disposition:** `BLOCKED_NO_CONFORMANT_ROUTE`
- **Objective:** Evaluate routes without affecting merge decisions.
- **Validation:** Gold corpus, severe recall, false positives, unsupported claims, schema validity, environment failures, cost.
- **Stop conditions:** Missing identity, unadjudicated corpus, or route drift.

### `TP-DMX-AUDIT-010-GITHUB-PULL-PICKUP`

- **Disposition:** `DEFERRED`
- **Objective:** Trusted-main workflow emits inert request artifact; broker pulls and verifies with read-only GitHub identity.
- **Validation:** No PR-head checkout, artifact provenance, replay/freshness, exact-head race tests.
- **Stop conditions:** Raw OIDC token stored in artifact or candidate code executes in trusted context.

### `TP-DMX-AUDIT-011-SEPARATE-PUBLISHER`

- **Disposition:** `DEFERRED`
- **Objective:** Publish broker-sealed results through least-privilege GitHub App.
- **Validation:** Exact-head recheck, idempotency, permission audit, provider-secret absence.
- **Stop conditions:** Publisher can execute candidate code or read provider credentials.

### `TP-DMX-AUDIT-012-API-FALLBACK`

- **Disposition:** `BLOCKED_PENDING_PRIVACY_COST_CERTIFICATION`
- **Objective:** Add direct provider and OpenRouter profiles with hard admission and provenance.
- **Validation:** Exact route pinning, fallback denial, retention review, budget reservation/reconciliation, metadata mismatch tests.
- **Stop conditions:** Unknown endpoint, retention, identity, price, or certificate.

### `TP-DMX-AUDIT-013-LIMITED-AUTOMATION-GATE`

- **Disposition:** `BLOCKED_PENDING_PRODUCTION_EVIDENCE`
- **Objective:** Consider automatic execution for narrow certified cohorts.
- **Validation:** Independent audit, sustained shadow metrics, rollback drill, operator approval, no automatic policy promotion.
- **Stop conditions:** Any certification expiry, identity drift, severe miss, or control-limit breach.

## Packet-level universal requirements

Every future packet must include:

- repo binding and fresh dedicated worktree;
- exact file allowlist;
- commit-sized steps;
- smallest relevant validations after each slice;
- codereview before precommit;
- explicit `PASS`, `FAIL`, and `NOT_RUN` buckets;
- proof bundle, warnings/blockers, and handoff when control passes;
- actual tool/model/provider evidence for any model-involved work;
- residual risks and `UNKNOWN`s;
- rollback and cleanup status.

## Packet series verdict

`PROPOSED` Authorize packets only one at a time. The first executable series should end after mechanical lane, broker core, and manual receipts. Credentialed adapter packets remain blocked until their evidence gates are separately approved.
