# R2 Implementation Notes

Packet: `TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-001`
Repair: `TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-001-R2`
Superseded failed head: `bc8c68dc1338e77994b55d63ed56ba35cbb84055`

## Observed authority

- Supervisor authorized one final bounded substantive repair cycle, OpenAI-family implementer, L2.
- Proof-only audit reuse is disabled in G0.
- Existing GitHub embedded-audit artifact and PR Steward workflow provide external exact-head audit closure; tracked post-audit edits to `PROOF.json` and `SUMMARY.md` are unnecessary and forbidden for R2.
- `origin/main` and PR base were `d40e43dd70307d2c000a4efd581be7c11248728c` at R2 preflight. No governed-delivery overlap observed after failed head.

## Implementation decisions

- Retain equivalence evaluator only as diagnostic. Serialized results always carry `authority_effect=NONE` and `audit_reuse_authorized=false`.
- Bind diagnostic semantic comparison to exact path, document role, and field. Relocation and same-basename carrier swaps fail closed.
- Expose public observed evaluation through local read-only Git observation. Caller-created structural facts remain `CLAIMED_INPUT` and cannot produce diagnostic PASS.
- Remove caller-owned G0 gate profiles, raw `audit_acceptable`, and identity-dimension weakening inputs.
- Require complete fixed gate set plus contextual exact-subject `ContentAuditBinding` for derived READY.
- Require full 40- or 64-hex Git object IDs wherever Git identity is claimed.
- Parse all seven contract documents with strict keys and security-relevant runtime checks; pair runtime parsers with JSON Schema conformance fixtures.

## Preserved repairs

- REPAIR-P1: any present non-satisfied gate halts contiguous phase walk; only `NOT_APPLICABLE` may be skipped.
- REPAIR-P2: tree equivalence digest retains path, mode, type, and object ID.

## Validation at note creation

- Focused governed-delivery tests: PASS, `317 passed`.
- Seven-contract conformance corpus: PASS, `7 passed` including five core-identity schema/runtime denial cases.
- Ruff over implementation and focused tests: PASS.
- Broader tests, change-contract validation, pre-commit, secret scan, and final Git freeze: NOT_RUN at note creation.
- Final independent L2 audit: NOT_RUN; must use different family after exact PR-head freeze.

## Residual boundary

- Diagnostic equivalence may emit `PASS`, but G0 assigns it no governance effect. Audit reuse remains disabled regardless of diagnostic result.
- Merge, mark-ready, activation, and repair cycle 3 remain unauthorized.
