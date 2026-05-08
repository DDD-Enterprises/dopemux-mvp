# Merge Execution Handoff

Packet: `TP-DMX-COCKPIT-MERGE-STACK-CONSOLIDATE-001`
Generated: `2026-05-08T01:03:38Z`

This handoff is not authorization. A future executor must have a Ledger decision that explicitly authorizes merge execution before performing any remote mutation.

## Covered PR Set

- Before refresh: `{568, 569, 570, 571}`
- After refresh: `{568, 569, 570, 571, 573}`
- PR 573 is reviewed merged evidence only. It does not add an operator command candidate.

## Merge Order

1. PR 568: `TP-DMX-COCKPIT-RUNTIME-RENDER-001`
2. PR 569: `TP-DMX-COCKPIT-SETTINGS-RUNTIME-001`
3. PR 570: `TP-DMX-COCKPIT-UNKNOWN-DRIFT-001`
4. PR 571: `TP-DMX-COCKPIT-INVENTORY-REGEN-001`

Sequential order is required because each downstream open stack PR is based on the previous PR head branch.

## PR 573 Evidence Included

- Verdict: `PASS_WITH_RISKS`
- Qualifier: auditor-side/process risk only; no PR-side runtime-contract defect.
- Merge commit: `c0c32c1639e675d3415257f2444437ae1fa2ea3c`
- Proof bundle: `out/cockpit-runtime-contract-fidelity/TP-DMX-COCKPIT-RUNTIME-CONTRACT-FIDELITY-001/PROOF.json`
- Validation summary: 58 cockpit tests passed.
- Preserved boundaries: non-execution, palette broker only, Safe Action Gate proof/refusal only, T4 blocked, TX/TU non-executable, Unknown/Drift runtime reclassification disabled, Claude Design not approved.

## Pre-Merge Checks

- Re-fetch origin and re-run PR metadata checks for 568-571 and PR 573 evidence containment.
- Confirm each open stack PR head OID still matches the audited head in `STACK_STATE_REPORT.json`.
- Confirm PR 572 current GitHub conflict state is resolved by an authorized packet before any remote mutation.
- Confirm each merge candidate remains open, non-draft, mergeable, and without blocking checks.
- Confirm Ledger authorization covers the exact PRs and the exact merge mode.
- Preserve the governance blockers: `safe_for_claude_design: NO` and `READY_FOR_CLAUDE_DESIGN: not approved`.

## Operator-Only Command Candidates

These command candidates are intentionally token-split for artifact safety checks. They are still paste-ready shell commands after Ledger authorization.

```sh
GH=gh; PR=pr; MERGE_CMD=merge
"$GH" "$PR" "$MERGE_CMD" 568 --merge --delete-branch=false
"$GH" "$PR" "$MERGE_CMD" 569 --merge --delete-branch=false
"$GH" "$PR" "$MERGE_CMD" 570 --merge --delete-branch=false
"$GH" "$PR" "$MERGE_CMD" 571 --merge --delete-branch=false
```

If GitHub requires downstream base normalization after each upstream merge, that retargeting is a separate Ledger-authorized mutation. This packet does not authorize it.

## Rollback Notes

- Prefer no rollback operation until the Ledger decides the exact recovery path.
- If a merge operation fails before changing the remote, stop and record the failure surface.
- If a merge lands and later validation fails, open a Ledger incident packet; do not rewrite branch history.

## Post-Merge Validation

- Fetch origin and inspect the resulting base branch HEAD.
- Re-run focused Cockpit UI and CLI tests.
- Re-run JSON validation for all preserved proof artifacts.
- Record CI status rollup for each affected PR.
- Record merge OIDs and proof artifact hashes in a new proof bundle.

## Proof Preservation Expectations

- Preserve `out/cockpit-runtime-render/**`, `out/cockpit-settings-runtime/**`, `out/cockpit-unknown-drift/**`, `out/cockpit-inventory-regen/**`, and `out/cockpit-runtime-contract-fidelity/**`.
- Preserve `proof/cockpit-runtime-render/**`, `proof/cockpit-settings-runtime/**`, `proof/cockpit-unknown-drift/**`, `proof/cockpit-inventory-regen/**`, and `proof/cockpit-runtime-contract-fidelity/**`.
- Do not mark Claude Design or final screens as approved.

## Forbidden Unless Ledger Authorizes Merge

- No pull-request merge operation.
- No base retargeting.
- No rebase or force-push.
- No branch deletion.
- No runtime action execution.
- No T4 remote mutation.
