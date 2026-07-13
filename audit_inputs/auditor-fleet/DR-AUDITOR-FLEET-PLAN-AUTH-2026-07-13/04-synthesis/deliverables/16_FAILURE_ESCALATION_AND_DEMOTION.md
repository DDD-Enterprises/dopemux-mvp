# Failure, Escalation, and Demotion

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `16_FAILURE_ESCALATION_AND_DEMOTION.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Failure taxonomy

`PROPOSED` Keep execution, output, quality, policy, conflict, and human escalation separate.

| Class | Examples | Automatic route change? |
|---|---|---|
| `EXECUTION_FAILURE` | Worker crash, timeout, network outage, quota, login expiry | No |
| `MODEL_OUTPUT_FAILURE` | Schema invalid, truncated output, missing metadata | No |
| `MODEL_QUALITY_FAILURE` | Missed severe issue, unsupported finding | No, route may later be demoted or revoked |
| `POLICY_BLOCK` | Privacy, cost, auth, containment, certification, stale head | No |
| `AUDITOR_CONFLICT` | Severe disagreement between valid audits | No, requires certified adjudication or human |
| `HUMAN_ESCALATION` | Operator chooses specialist or premium review | Fresh approved request |

## Failure state transitions

```text
DISPATCHED
  -> SUCCESS
  -> EXECUTION_FAILURE
  -> MODEL_OUTPUT_FAILURE
  -> POLICY_BLOCK
  -> CONTAINMENT_VIOLATION
  -> STALE_HEAD

VALID_RESULT
  -> FINDINGS
  -> AUDITOR_CONFLICT
  -> MODEL_QUALITY_FAILURE after adjudication
```

There is no automatic edge from a failure state to a stronger model.

## Retry policy

`PROPOSED`

- Same frozen route only.
- Only for explicitly transient transport or worker startup failures.
- New disposable worker for each retry.
- Bounded retry count and reserved cost.
- No retry on auth, terms, privacy, containment, schema, identity, provider mismatch, stale head, or cost-admission failure.
- Respect provider reset and retry-after evidence.
- No account rotation or credential sharing to evade limits.

## Fallback policy

A fallback requires:

1. a new route eligibility calculation;
2. a pre-certified equivalent or stronger route for the same privacy class;
3. a fresh worst-case cost reservation;
4. explicit human approval;
5. preserved original failure evidence;
6. no weakening of identity, privacy, independence, or proof requirements.

If those conditions are absent, the request remains blocked.

## Escalation triggers

`PROPOSED`

- security-critical or irreversible change;
- cross-boundary ambiguity;
- severe finding with low confidence;
- conflict with deterministic evidence;
- disagreement between certified auditors;
- missing authoritative source needed for adjudication;
- human-requested specialist review.

Plan exhaustion, runner failure, parser error, and latency are not quality escalation triggers.

## Demotion and revocation

| Trigger | Immediate action |
|---|---|
| Tool/version drift | Demote to `CONFORMANCE_PENDING` |
| Credential class or owner change | Disable until auth review |
| Identity metadata missing | Block route proof and independence claim |
| Provider fallback observed | Invalidate result, disable route profile |
| Containment violation | Terminate, quarantine worker/profile, revoke certificate |
| Privacy or terms change | Disable affected data classes |
| Cost variance beyond limit | Suspend route pending catalog and billing review |
| Severe production miss | Revoke certification and require adjudicated incident review |
| Schema-validity degradation | Suspend automatic use |
| Security incident | Disable adapter, revoke credentials, preserve evidence |

## Manual recovery queue

`PROPOSED` Failed or blocked requests enter an operator-visible queue containing:

- request and exact head;
- typed failure;
- route and adapter state;
- retry eligibility;
- privacy and cost state;
- required evidence or approval;
- cleanup status;
- whether the head is still current.

The queue may recommend actions but cannot execute a new route without approval.

## Conflict resolution

`PROPOSED` Do not average conflicting findings into a vague midpoint. Preserve each finding, evidence location, identity, confidence, and route. Resolve severe conflict with either:

- a separately certified independent auditor; or
- a human adjudicator with exact code and proof context.

## Fail-safe terminal states

- `BLOCKED_TOOL_INELIGIBLE`
- `BLOCKED_PRIVACY`
- `BLOCKED_COST`
- `BLOCKED_IDENTITY`
- `BLOCKED_CERTIFICATION`
- `STALE_HEAD`
- `QUARANTINED`
- `PUBLICATION_PENDING`
- `HUMAN_REVIEW_REQUIRED`

A terminal block is an honest result, not a system embarrassment to be routed around.
