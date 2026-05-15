# RTE-PKT-09 Authorization Model

This model defines authorization for a future live validation run. It is not authorization to run one now.

## Required Explicit Approval

A future live validation packet must require operator language equivalent to:

`I authorize bounded live provider validation for RTE under the accepted RTE-PKT-09 plan.`

The future approval must also name:
- providers and lanes
- models or route patterns
- spend cap
- timeout cap
- batch request cap
- artifact root
- whether cancellation is authorized
- whether remote file deletion/cleanup is authorized

## Non-Approval Examples

These are not sufficient:
- `continue`
- `run the packet`
- `review the source`
- `generate proof`
- credentials exist in environment
- `DPMX_LIVE_OK` is set
- dry-run commands
- draft PR approval
- acceptance of this planning packet alone

## Relationship To DPMX_LIVE_OK

`DPMX_LIVE_OK` is a runtime guard, not governance approval.

Future live execution must require both:
- explicit operator authorization in the conversation or future packet
- runtime live guard satisfaction where the runtime requires it

If either is absent, the future run must stop closed.

## Credential Handling

Allowed:
- Boolean presence checks, if explicitly needed.
- Environment variable names.
- Redacted provider account status.
- Redacted request IDs.

Forbidden:
- printing credential values
- storing authorization headers
- storing raw request payloads containing secrets
- copying credentials into proof artifacts
- treating credential presence as approval
- writing unredacted downloaded provider files into permanent proof

## Future Cap Requirements

Spend:
- Must be explicit before any provider contact.
- Recommended first cap is USD 5.00 or lower.
- Spend estimate is not billing truth.
- Provider billing truth requires separately authorized provider-side evidence.

Timeout:
- Provider preflight: 60 seconds per lane.
- Minimal sync response probe: 180 seconds per request.
- Batch pilot: 30 minutes wall-clock maximum for first run.

Batch:
- 1 to 3 requests total for first pilot.
- Synthetic non-sensitive content only.
- No production repo payloads.
- Polling cadence no faster than every 30 seconds unless future packet justifies otherwise.

Cleanup:
- Cancel only validation-created jobs.
- Delete only validation-created files.
- Remote deletion requires separate explicit authorization.

## Operator Responsibilities For Future Live Run

The operator must provide:
- approval language
- provider set
- cap values
- confirmation that credentials are intentionally available
- cleanup/deletion decision
- acceptance that live results may still be provider/account/region/model-version specific

## Agent Responsibilities For Future Live Run

The implementing agent must:
- re-run static readiness checks first
- avoid printing secrets
- stop on any redaction hit
- preserve raw failures in redacted form
- avoid retries beyond the approved cap
- mark every untested lane `NOT_TESTED`
- mark every failed lane `LIVE_FAILED` or `LIVE_BLOCKED`
- avoid upgrading provider billing, retention, or ZDR claims without direct evidence
