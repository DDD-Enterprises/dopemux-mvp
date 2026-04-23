# Dopemux v1 Proof Baseline

## Baseline Choice
Use the dopetask bundle loader subset as the enforceable v1 proof baseline.

Primary runtime authority:
- `src/dopemux_pr_merge_specialist/dopetask_bundle_loader.py`

Reference example:
- `tests/unit/test_dopetask_series_adapter.py`
- minimal writer behavior in `src/dopemux_pr_merge_specialist/dopetask_packet_launcher.py`

## Enforceable Required Fields
A v1 proof bundle must contain:
- `artifacts`
- one of `tp_id | pr_id`

## Canonical Subset for Validation
A v1 proof validator should treat these as canonical subset fields:
- `status`
- `summary`
- `acceptance_checks`
- `validation`
- `manifest`

## v1 Validation States
Suggested validator outputs:
- `missing`
- `present_unvalidated`
- `validated`
- `failed`
- `degraded`

## Hard Rules
- `PROOF_GENERATED` is not accepted proof
- historical proof files under `proof/` are heterogeneous evidence, not schema authority
- governance docs may be richer, but they are advisory until enforced by runtime code
- `scripts/proof_bundle.sh` is not the v1 JSON proof authority

## v1 Acceptance Rule
A proof may be accepted only if:
- required subset is present
- schema validation passes
- referenced artifacts are present
- supervisor review approves acceptance

## Recommended v1 Proof Adapter Responsibilities
- locate proof bundle
- validate subset fields
- check artifact presence
- report validation state
- return structured review inputs to the review lane

## Out of Scope for v1
- enforcing the full aspirational proof governance schema
- treating heterogeneous proof files as interchangeable
- making proof validation equivalent to review acceptance
