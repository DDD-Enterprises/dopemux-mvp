# TP007 Artifact Truth Audit

## Scope

No TP007 live run artifacts exist because no live run was attempted.

## Raw Truth Inputs Used

- validator scope:
  - `reports/repo-truth-extractor/pre_live_gate_v25/pre_live_gate_v25_20260405T191013Z/VALIDATION_SCOPE.json`
- validator preflight results:
  - `reports/repo-truth-extractor/pre_live_gate_v25/pre_live_gate_v25_20260405T191013Z/ONLINE_PREFLIGHT_RESULTS.json`
- validator verdict:
  - `reports/repo-truth-extractor/pre_live_gate_v25/pre_live_gate_v25_20260405T191013Z/VALIDATION_VERDICT.json`

## Observed Truth

- Current validator authority is phase-wide for `A`, not step-scoped for `A2`
- Active required routes now include both:
  - OpenRouter routes for `A0/A1/A11/A12/A13/A99`
  - xAI routes for `A2/A3/A4/A5/A6/A7/A8/A9/A10`
- The validator therefore no longer answers the same bounded question that TP006 used

## Contradictions / Drift

1. Packet-declared canonical validator command includes `--step A2`, but current validator CLI rejects `--step`
2. Packet-declared bounded target is `A2`, but current validator scope for `--target-phases A` includes multiple non-`A2` steps
3. OpenRouter routes now block the gate even though TP006 bounded truth depended only on xAI routes

## Artifact Truth Result

- `all_consistent: false`
- contradiction class:
  - bounded-validator contract drift
- because no live run occurred, there is no raw-vs-aggregate run artifact comparison to perform for TP007 itself
