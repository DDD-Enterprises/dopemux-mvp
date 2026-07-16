# API Fallback and OpenRouter Policy

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `14_API_FALLBACK_AND_OPENROUTER_POLICY.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Decision

`PROPOSED` Use API routes only as explicit, governed fallback after plan/local routes are unavailable or unsuitable and after privacy, identity, cost, and certification gates pass.

`PROPOSED` Prefer a direct approved provider API for private or governed work. Restrict OpenRouter to public, low-risk work by default. Any private OpenRouter use requires a formal endpoint-specific exception.

## Fallback eligibility

All gates must pass:

1. Mechanical validation cannot answer the semantic question.
2. Fallback reason is explicit and approved.
3. Data classification permits the route.
4. Exact model, provider, endpoint, and required parameters are pinned.
5. Route has a current evaluation certificate.
6. Retention and feature policy are approved.
7. Worst-case cost reservation fits request, daily, and monthly caps.
8. Credential is isolated to the route environment.
9. Returned provider/model/request metadata can be validated.
10. Human approval exists where required.

## Allowed fallback reasons

- `PLAN_THROTTLED`
- `PLAN_UNAVAILABLE`
- `STRUCTURED_OUTPUT_REQUIRED`
- `PROVENANCE_REQUIRED`
- `OPERATOR_APPROVED_EXCEPTION`

`REJECTED` Environment failure alone does not justify a stronger or more expensive model. A fallback is a new policy decision, not a retry costume.

## OpenRouter route profiles

| Profile | Required controls | Data class | Status |
|---|---|---|---|
| `OR-PUBLIC-CHEAP-CHALLENGER` | Model allowlist, provider allowlist, parameter enforcement, token caps, unit-price cap, metadata enabled | Public low-risk | `BLOCKED_UNTIL_CERTIFIED` |
| `OR-PUBLIC-STRICT-REVIEW` | Exact model and provider endpoint, fallback disabled, parameters required, data-deny, ZDR tag, price cap, metadata | Public reproducibility-sensitive | `BLOCKED_UNTIL_CERTIFIED` |
| `OR-PRIVATE-EXCEPTION` | Strict profile plus legal/security approval of router and upstream endpoint, redaction, per-run human approval | Private without suspected secrets | `DEFAULT_DENY` |
| `OR-SENSITIVE-DENY` | No route | Secrets, client data, security-sensitive or release-authority content | `DENIED` |

OpenRouter policy tags are filtering inputs, not definitive third-party contract evidence.

## Direct API profiles

| Profile | Use | Status |
|---|---|---|
| `DIRECT-PRIVATE-STRUCTURED` | Approved private semantic review with strict output and trace IDs | `DESIGNABLE_DISABLED` |
| `DIRECT-SECURITY-EXCEPTION` | Security-sensitive review after redaction and explicit security approval | `DEFAULT_DENY_WITH_EXCEPTION` |
| `DIRECT-PUBLIC-CHALLENGER` | Public evaluation and shadow testing | `BLOCKED_UNTIL_CERTIFIED` |

## OpenRouter request constraints

`PROPOSED`

- Pin exact model slug.
- Pin exact provider endpoint where supported.
- Disable fallback when provenance matters.
- Require parameters so the endpoint cannot silently ignore structured-output controls.
- Apply data collection and ZDR filters as router controls, then independently approve the upstream provider contract.
- Set unit-price limits.
- Enable and capture routing metadata.
- Bound input, output, reasoning, tools, searches, retries, and total time.
- Reject missing or mismatched returned provider/model metadata.

## Cost admission

`PROPOSED` Reserve worst-case cost atomically before dispatch:

```text
estimated_run_max =
    input_tokens_max * input_unit_price
  + output_tokens_max * output_unit_price
  + cache_components_max
  + tool_and_search_max
  + route_or_region_uplift_max
  + retry_budget_max
```

Reject when the estimate exceeds per-request, daily, or monthly remaining budget. Provider alerts and router `max_price` do not replace caller-side reservation.

## Postflight reconciliation

Record:

- requested and returned provider/model/endpoint;
- provider and upstream request IDs;
- token categories and tool/search usage;
- provider-reported cost and independently recomputed cost;
- price catalog version and timestamp;
- retry and failure cost;
- variance and mismatch disposition.

A material mismatch invalidates governed proof.

## Subscription accounting rule

`UNKNOWN` No stable cross-vendor per-request plan-credit debit is established.

`PROPOSED` Store plan-credit debit as `null` with status `UNKNOWN`. Never convert tokens into plan credits. Record subscription invoice, observed plan state, reset time, throttling, and API spend separately.

## Privacy rules

| Data class | Subscription tool | Direct API | OpenRouter |
|---|---|---|---|
| Public low-risk | Operator-triggered if terms permit | Approved route | Approved public profile only |
| Private, no secrets | Operator-triggered commercial/workspace route | Preferred after approval | Default deny |
| Possible secrets | No egress until triage | Approved direct route after redaction/approval | Deny |
| Client data | Consumer plan deny | Contract-approved commercial route only | Deny by default |
| Security-sensitive | No unattended authority | Direct approved route plus human/security review | Deny by default |
| Release authority | Evidence only | Evidence only | Not permitted |

## ZDR posture

`CLAIMED` Accepted research documents route- and feature-specific retention exceptions across providers.

`PROPOSED` A route proof must enumerate every enabled feature and its retention status. Unknown retention blocks sensitive egress. ZDR never means zero transient processing, universal tool coverage, or router-enforced upstream compliance.
