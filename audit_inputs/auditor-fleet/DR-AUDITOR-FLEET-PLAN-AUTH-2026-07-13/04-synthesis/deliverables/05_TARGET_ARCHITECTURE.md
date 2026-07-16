# Target Architecture

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `05_TARGET_ARCHITECTURE.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Architecture principle

`PROPOSED` Split the system by authority and blast radius, not by product branding.

## First-release architecture

```text
Human operator
  |
  | approve repo, PR, exact head, privacy class, route
  v
Dopemux operator control and classifier
  |
  | canonical local request
  v
Audit Broker user
  |  verify repo/PR/base/head/digests/freshness
  |  acquire durable one-job lease
  |  never execute candidate code
  |
  +--> Mechanical route
  |      disposable credential-free worker
  |      network NONE, read-only allowlist
  |      sealed mechanical result
  |
  +--> Manual receipt intake
         human-operated tool or app
         receipt labeled manual and evidence-limited

Audit Broker sealed result spool
  |
  v
Human operator
  |
  +--> embedded-audit proof path
  +--> PR Steward intake
  +--> manual GitHub publication where appropriate
```

### First-release component status

| Component | Disposition | Notes |
|---|---|---|
| Dopemux classification and recommendation contract | `DESIGNABLE_BUT_DISABLED` | Policy can be specified now; automatic selection waits for certification. |
| Local Audit Broker | `DESIGNABLE_BUT_NOT_IMPLEMENTED` | No provider credential and no GitHub write credential. |
| Mechanical worker | `CURRENTLY_IMPLEMENTABLE` | Only accepted executable lane. |
| Manual receipt normalizer | `CURRENTLY_DESIGNABLE` | Required for AGY, Grok, and any blocked interactive tool. |
| Local model adapters | `BLOCKED_PENDING_EVIDENCE` | Registered disabled. |
| API fallback | `BLOCKED_PENDING_EVIDENCE` | No route is approved or certified. |
| GitHub publisher | `DEFERRED` | Human publication first. |

## Later automation architecture

```text
Untrusted PR data
  |
  v
GitHub-hosted trusted-main request workflow
  |  no PR-head checkout
  |  fetch PR diff/metadata as data through API
  |  emit canonical request artifact and digest
  v
GitHub artifact store
  |
  | local pull using read-only verifier credential
  v
Audit Broker
  |  verify workflow/run/repo/PR/base/head/freshness/digests
  |  reject replay or stale head
  |  apply certified route eligibility
  |
  +--> Disposable credential-free VM
  |      mechanical or authorized candidate execution
  |
  +--> Per-tool isolated model worker
  |      data-only input, provider credential only for that tool
  |      no GitHub write, no candidate execution
  |
  +--> API fallback worker
         exact provider/model/profile, budget reservation

Sealed result spool
  |
  v
Separate publisher GitHub App
  |  verify broker seal and current head
  v
Exact-head GitHub check or status
  |
  v
PR Steward and human approval
```

## Component boundaries

| Component | Owns | Must not own |
|---|---|---|
| Dopemux | Operator control, classification, route recommendation | Provider credentials, merge approval, audit-proof canonical semantics |
| Audit Broker | Verification, leasing, dispatch, normalization, sealing | Candidate execution, broad provider secrets, GitHub write, merge readiness |
| Worker | One bounded request | Route policy, publication, durable authority |
| Tool adapter | One tool's invocation and receipt normalization | Upstream terms authority, route certification, fallback selection |
| Embedded audit | Governed audit-proof semantics | Execution transport |
| PR Steward | PR review intake and merge-readiness evaluation | Provider execution details beyond evidence |
| Publisher | Exact-head GitHub write | Model execution, route selection, provider credentials |
| Human | Approval, exceptions, final authority | None delegated automatically |

## Data movement rules

`PROPOSED`

- The broker receives immutable request data and digests, not a writable repository checkout.
- Candidate code executes only in a credential-free disposable worker.
- A model adapter receives a normalized data package, not a live repo with hooks, instructions, or tools.
- Provider credentials never cross tool boundaries.
- Results travel through a sealed local spool with content hashes.
- Publication occurs only after a current-head recheck.

## State model

```text
RECEIVED
  -> VERIFIED
  -> CLASSIFIED
  -> AWAITING_HUMAN_APPROVAL
  -> LEASED
  -> DISPATCHED
  -> RESULT_RECEIVED
  -> RESULT_VALIDATED
  -> SEALED
  -> AWAITING_PUBLICATION
  -> PUBLISHED | STALE_HEAD | BLOCKED | FAILED
```

No state transition from `FAILED` to a different route is automatic.

## Deployment topology

| Zone | Preferred deployment | Credential posture | Network posture |
|---|---|---|---|
| Broker | Dedicated non-admin local OS user | Read-only verifier at most | GitHub verification only when needed |
| Mechanical worker | Disposable VM, container accepted for lower-risk profile | None | None by default |
| Plan-auth model adapter | Dedicated non-admin user or isolated VM | One provider/tool only | Provider-only after allowlist proof |
| Direct API worker | Separate service account or secret boundary | One project/key only | Exact provider endpoint |
| Publisher | Separate service or GitHub App process | GitHub write only | GitHub API only |

## Architectural simplifications deliberately retained

`PROPOSED`

- One audit at a time in the first release.
- Human route approval.
- Human publication.
- No automatic policy promotion.
- No model adapter execution until certified.
- No shared runner pool.
- No bridge bus or agent orchestration framework in the critical path.

The result is less glamorous and much harder to rob. That trade is correct.
