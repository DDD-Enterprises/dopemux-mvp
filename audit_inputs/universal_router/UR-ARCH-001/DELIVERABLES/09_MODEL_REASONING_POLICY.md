# Model and Reasoning Policy

## Policy principle

- **PROPOSED:** Select the least expensive, lowest-overhead route that is certified to meet required quality, containment, identity, validation, and audit constraints.
- **PROPOSED:** Model choice is resolved from a versioned `ModelCapabilityRecord` and fresh snapshots. Marketing names or vendor claims alone do not make a route eligible.
- **PROPOSED:** Model aliases are allowed in policy, but the recommendation records requested and configured identity separately and never claims actual identity without attestation.

## Abstract reasoning levels

```text
NONE
LOW
MEDIUM
HIGH
MAX
AUTO
UNSUPPORTED
UNKNOWN
```

- **PROPOSED:** Policy chooses an abstract level. Runner adapters map it to supported CLI/API values.
- **PROPOSED:** If a runner cannot prove a requested level, the candidate is ineligible for pinned-reasoning certification but may remain advisory with `UNKNOWN` where policy allows.
- **PROPOSED:** `AUTO` is allowed only when policy does not require deterministic effort and the adapter records that the runner may choose.

## Default role allocation

| Label | Role | Preferred route | Fallback | Notes |
|---|---|---|---|---|
| **PROPOSED** | Architecture, macro packets, escalations | GPT-5.6 Pro supervisor path | Claude Code Opus or independently approved frontier route | No bulk low-risk work. |
| **PROPOSED** | Bounded implementation | Codex in dedicated worktree | Claude Code Sonnet | Requires precise packet and proof. |
| **PROPOSED** | Medium/high complexity implementation fallback | Claude Code Sonnet | Codex or Opus based on failure class | No self-audit. |
| **PROPOSED** | High-complexity refactor/debug fallback | Claude Code Opus | GPT-5.6 Pro escalation | Premium route requires reason. |
| **PROPOSED** | Preferred embedded audit | AGY/Sonnet when safe and fresh | Claude Code Sonnet, then Opus | Local AGY safe containment is currently `UNKNOWN`; candidate blocks until proven. |
| **PROPOSED** | Broad-context contradiction audit | Gemini CLI | GPT-5.6 Pro supervisor | Advisory until containment/identity evidence is sufficient. |
| **PROPOSED** | Evidence spine | GitHub/CI | local proof refs | CI is evidence, not semantic proof by itself. |

## Required task-class behavior

### Cheap read

- **PROPOSED:** Runner: cheapest certified read-capable route or local deterministic tooling when no model is needed.
- **PROPOSED:** Provider path: plan-backed or API path only if cost/credit posture is known enough for the operator constraint.
- **PROPOSED:** Model: low-cost model record with adequate context and read quality.
- **PROPOSED:** Reasoning: `LOW`.
- **PROPOSED:** Network: `OFFLINE` for repository-only facts; otherwise explicit `APPROVED_PROVIDER_NETWORK`.
- **PROPOSED:** Containment: read-only, no MCP unless required, no writes, optional ephemeral session.
- **PROPOSED:** Audit: `NOT_REQUIRED` unless authority/security implications appear.

### Repository investigation

- **PROPOSED:** Runner: Codex or Claude Code Sonnet with read-only worktree; Gemini may be a broad-context challenger.
- **PROPOSED:** Model: strong code/repository model record, not premium by default.
- **PROPOSED:** Reasoning: `MEDIUM`, rising to `HIGH` only for unresolved call-flow or cross-system contradiction.
- **PROPOSED:** Validation: evidence ledger, path refs, deterministic searches, no implementation.
- **PROPOSED:** Audit: light independent challenge for architecture-sensitive conclusions.

### Ordinary implementation

- **PROPOSED:** Runner: Codex.
- **PROPOSED:** Fallback: Claude Code Sonnet.
- **PROPOSED:** Model: configured certified implementation model; exact ID resolved from snapshot/registry.
- **PROPOSED:** Reasoning: `MEDIUM`.
- **PROPOSED:** Network: provider network only; general network denied unless packet allows API lookup.
- **PROPOSED:** Containment: dedicated worktree, file allowlist, command allowlist, environment redaction, bounded outputs.
- **PROPOSED:** Validation: targeted tests, diff review, embedded audit.

### Multi-file implementation

- **PROPOSED:** Runner: Codex or Claude Code Sonnet based on certified route quality and context needs.
- **PROPOSED:** Reasoning: `HIGH`.
- **PROPOSED:** Planning: GPT-5.6 Pro macro packet for architecture-sensitive scope.
- **PROPOSED:** Audit: AGY/Sonnet if safely available; otherwise Claude Code Sonnet or Opus using a separate session/provider path where possible.
- **PROPOSED:** No subagent fanout. Sequential bounded audit only.

### Difficult diagnosis

- **PROPOSED:** Initial runner: Codex or Claude Code Sonnet with `HIGH` reasoning and a concrete failure artifact.
- **PROPOSED:** Escalation: Claude Code Opus for deep refactor/debug, then GPT-5.6 Pro supervisor if findings conflict.
- **PROPOSED:** Model escalation occurs only after root-cause confidence fails to reach the required threshold, not after environment failure.
- **PROPOSED:** Validation: reproducible failure, root-cause evidence, regression test.

### Architecture

- **PROPOSED:** Primary: GPT-5.6 Pro.
- **PROPOSED:** Reasoning: `MAX` or equivalent.
- **PROPOSED:** Challenger: Gemini CLI for broad-context contradiction search or Claude Code Opus for implementation-depth challenge.
- **PROPOSED:** Output: ADR, contract boundary, alternatives, evidence ledger, open questions.
- **PROPOSED:** No code implementation by the architecture route.

### Security and authority

- **PROPOSED:** Primary: GPT-5.6 Pro or an independently certified high-assurance model route.
- **PROPOSED:** Reasoning: `HIGH` or `MAX`.
- **PROPOSED:** Network: restricted and explicitly approved.
- **PROPOSED:** Containment: OS/wrapper enforcement required; prompt-only controls are ineligible.
- **PROPOSED:** Audit: independent and mandatory.
- **PROPOSED:** Unknown actual identity blocks identity-dependent certification and release-sensitive conclusions.

### Release judgment

- **PROPOSED:** Route selection cannot itself approve release.
- **PROPOSED:** Recommendation: GPT-5.6 Pro supervisor review only when PR Steward is blocked, unknown, conflicting, stale, security-sensitive, or authority-boundary touching.
- **PROPOSED:** Otherwise PR Steward `READY` plus current proof/checks can avoid a second supervisor prompt under the project operating model.
- **PROPOSED:** Human approval remains external where required.

### Desktop advisory operation

- **PROPOSED:** Desktop apps are operator consoles only.
- **PROPOSED:** Their output can be imported as advisory evidence with transcript/hash/redaction refs.
- **PROPOSED:** No desktop output becomes an execution request, provider attestation, policy promotion, audit pass, or release approval by itself.
- **PROPOSED:** Model picker/entitlement facts are fast-decaying and snapshot-scoped.

### API automation

- **PROPOSED:** API route requires explicit API/provider path, cost ceiling, network posture, credential presence without value capture, identity/usage adapter, and local schema validation where structured output matters.
- **PROPOSED:** Consumer-plan availability is not treated as general API entitlement.
- **PROPOSED:** Freeflow remains admission and cap authority for routes it owns.

## Exceptional conditions

### Runner unavailability

- **PROPOSED:** Choose a certified same-tier alternative with equal or stronger containment and validation posture.
- **PROPOSED:** If none exists, return `BLOCKED` or `ESCALATED`.
- **PROPOSED:** Do not jump to a premium route merely because a runner is unavailable.

### Unknown cost

- **PROPOSED:** Unknown cost is not zero.
- **PROPOSED:** Low-risk advisory recommendation may proceed with operator confirmation if no hard ceiling exists.
- **PROPOSED:** Cost-capped automation, paid fallback, security, and release-sensitive routes block until cost posture is known or explicitly approved.

### Unknown credits

- **PROPOSED:** Unknown plan credits are not inferred from tokens.
- **PROPOSED:** Plan-sensitive routes require operator confirmation or a direct observation.
- **PROPOSED:** The router may prefer an API route only when doing so does not violate cost or policy constraints. It must not assume API is cheaper.

### Unknown model identity

- **PROPOSED:** Ordinary low-risk advisory work may proceed if model identity is not a declared control and the uncertainty is visible.
- **PROPOSED:** Pinned-model certification, benchmark certification, independent-audit identity claims, security/release-sensitive routes, and policy-required exact-model routes block.

### Stale snapshots

- **PROPOSED:** Read/draft recommendations may be emitted with low confidence and refresh required.
- **PROPOSED:** Write, audit, benchmark, security, authority, and release-sensitive routes block on required stale evidence.

### Provider drift

- **PROPOSED:** If provider/model differs from the configured or certified route, identity becomes `CONFLICTING`.
- **PROPOSED:** Low-risk advisory use may continue only without certification claims.
- **PROPOSED:** Protected routes block or escalate.

### Environment failure

- **PROPOSED:** Classify filesystem, sandbox, proxy-local, DNS, authentication, and host-network failures separately from model quality.
- **PROPOSED:** Retry the same route at most once when idempotent and transient.
- **PROPOSED:** Consider a same-tier alternative only if the environment path differs and all controls remain satisfied.
- **PROPOSED:** Never automatically promote to a more expensive model.

## Escalation ladder

```text
quality or capability failure only:
  LOW -> MEDIUM -> HIGH/MAX reasoning
  then one stronger model tier or runner
  then NEEDS_SUPERVISOR

environment/auth/network failure:
  same-route retry once
  same-tier alternate path if certified
  repair recommendation or BLOCKED
  no premium escalation
```

## Demotion and continuous optimization

- **PROPOSED:** Shadow evaluation may demote expensive routes when a cheaper certified route matches quality and safety thresholds.
- **PROPOSED:** Demotion is policy-versioned, benchmark-backed, and reviewed.
- **PROPOSED:** No route is demoted solely because the provider reports fewer reasoning tokens or because a small sample appears cheaper.
- **PROPOSED:** Operator overrides and severe failures feed the evaluation corpus but do not automatically rewrite policy.
