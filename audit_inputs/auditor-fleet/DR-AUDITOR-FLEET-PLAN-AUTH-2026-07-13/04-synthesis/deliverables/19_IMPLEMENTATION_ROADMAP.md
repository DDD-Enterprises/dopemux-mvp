# Implementation Roadmap

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `19_IMPLEMENTATION_ROADMAP.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Roadmap posture

`PROPOSED` This is an implementation sequence, not authorization to edit the repository. Every work item requires a future approved Task Packet, dedicated worktree, allowlist, validation, independent audit, and proof.

## Workstreams

### WS-1: Contract freeze

**Disposition:** `CURRENTLY_DESIGNABLE`

Deliverables:

- request envelope schema;
- result envelope schema;
- manual receipt schema;
- adapter registry schema;
- route profile schema;
- typed failure taxonomy;
- proof/handoff mapping to existing contracts.

Gate: independent review confirms no fork of embedded-audit or PR Steward authority.

### WS-2: Mechanical lane hardening

**Disposition:** `CURRENTLY_IMPLEMENTABLE_AFTER_AUTHORIZATION`

Deliverables:

- validator profile registry;
- read-only/no-network worker specification;
- authority statements;
- excluded-command checks;
- deterministic receipt bundle;
- mechanical-only eligibility tests.

Gate: no command mutates, installs, or performs network access.

### WS-3: Local broker core

**Disposition:** `DESIGNABLE_BUT_NOT_IMPLEMENTED`

Deliverables:

- strict request validation;
- exact-head verifier;
- replay store and durable lease;
- classification and recommendation output;
- worker dispatch boundary;
- result validation and sealed spool;
- operator-visible state and recovery queue.

Gate: broker has no provider credential, no GitHub write credential, and no candidate execution path.

### WS-4: Manual receipt path

**Disposition:** `CURRENTLY_DESIGNABLE`

Deliverables:

- manual receipt validator;
- artifact/transcript hashing;
- exact-head display and operator attestation;
- evidence-confidence labels;
- PR Steward handoff mapping.

Gate: manual evidence cannot be mislabeled automated or identity-attested.

### WS-5: Per-tool isolation foundation

**Disposition:** `BLOCKED_PENDING_HOST_DECISION`

Deliverables:

- dedicated OS user or VM profiles;
- separate homes, configs, keychains, logs, temp, and IPC;
- negative checks for shared writable state;
- credential revocation runbook;
- network policy framework.

Gate: selected macOS worker technology and per-tool provider policy are approved.

### WS-6: Codex and Claude conformance

**Disposition:** `BLOCKED_PENDING_AUTHORIZATION`

Deliverables:

- version-pinned static conformance;
- auth route and owner receipt;
- effective config and no-tool evidence;
- output schema and failure mapping;
- identity/usage receipt;
- bounded live probe plan.

Gate: vendor permission, credential lifecycle, privacy, and live-probe authorization.

### WS-7: Gemini, Grok, AGY, and OpenCode research adapters

**Disposition:** `RESEARCH_ONLY_OR_BLOCKED`

Deliverables:

- Gemini account-class and envelope normalizer research;
- Grok `0.2.99` version-matched contract;
- AGY unattended receipt/lifecycle evidence;
- OpenCode upstream permission, fallback, and identity evidence.

Gate: tool-specific unknowns resolved. No shared shortcut.

### WS-8: Evaluation harness

**Disposition:** `BLOCKED_NO_LIVE_ROUTES`

Deliverables:

- corpus manifest;
- gold adjudication schema;
- shadow runner;
- metrics and control limits;
- certification and revocation registry.

Gate: approved routes and evaluation governance.

### WS-9: GitHub trusted request pickup

**Disposition:** `DEFERRED_LATER_AUTOMATION`

Deliverables:

- trusted-main request workflow;
- artifact manifest and digest;
- read-only verifier App;
- replay/freshness/exact-head tests;
- no-checkout and hostile-data tests.

Gate: broker stable and GitHub security review passes.

### WS-10: Separate publisher

**Disposition:** `DEFERRED_LATER_AUTOMATION`

Deliverables:

- least-privilege publisher App;
- broker-seal verification;
- exact-head recheck;
- idempotent check publication;
- branch-protection integration.

Gate: no provider credential or candidate execution in publisher.

### WS-11: API fallback

**Disposition:** `BLOCKED_PENDING_PRIVACY_COST_CERTIFICATION`

Deliverables:

- direct API and OpenRouter profiles;
- key isolation;
- route metadata validation;
- price catalog and reservation ledger;
- privacy/retention approvals;
- shadow certificates.

Gate: exact endpoint approval and route certification.

## Recommended sequence

```text
WS-1
  -> WS-2
  -> WS-3
  -> WS-4
  -> WS-5
  -> WS-6 and WS-7 research
  -> WS-8
  -> WS-9
  -> WS-10
  -> WS-11 as independently approved
```

WS-2 through WS-4 can create value before any model route is activated.

## Program-level acceptance criteria

`PROPOSED`

- Exact-head proof survives request, dispatch, result, and publication.
- No candidate-controlled context can reach persistent provider credentials.
- No model process can write to GitHub.
- Mechanical authority limits are explicit.
- Disabled adapters fail closed.
- Every fallback is approved, pinned, budgeted, and traceable.
- Automatic routing remains off until certified.
- Human and existing governance contracts retain authority.

## Rough prioritization

| Priority | Work | Why |
|---|---|---|
| 1 | Contracts and mechanical lane | High value, lowest uncertainty |
| 2 | Broker exact-head core and manual receipts | Establishes trustworthy transport without provider risk |
| 3 | Isolation foundation | Required before any credentialed adapter |
| 4 | Codex/Claude conformance | Strongest research candidates |
| 5 | Evaluation harness | Required before route use |
| 6 | GitHub ingress and publisher | Automation after the core is proven |
| 7 | Other adapters and API fallback | Higher unknowns and broader privacy/cost surface |
