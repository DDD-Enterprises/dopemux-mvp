## Objective

Investigate stale-branch clobbers and propose merge-integrity architecture for exact-candidate admission.

## Scope

Docs and proof only. No implementation code, GitHub settings, existing PRs, labels, comments, reviews, or branch protection were mutated.

## Incidents Investigated

- PR #720 / #734: current evidence is CONFLICTING for reported clobber causality.
- PR #932 / #936: ConPort migration/proof deletion and restoration observed.
- PR #1025 / #1037: MCP runtime stack deletion and restoration observed.

## Actual Execution Base

`b176747b339685e781de04268c46b7ae123abfbf`

## ADR Status

`PROPOSED`

## Decision Summary

Agent-produced branches are untrusted patch sources. Authorized changes must be transplanted onto current `main`, validated against explicit intent and protected surfaces, audited against the exact candidate tree, and merged only through final expected-head readiness.

## Important Unknowns And Conflicts

- PR #720 causality remains CONFLICTING.
- GitHub merge queue behavior is UNKNOWN for exact tree-SHA binding.
- Reserved-singleton port allocator regression remains open and out of scope.
- Trusted-runner isolation and mass-deletion gate detail are implementation obligations.

## Validation Results

- JSON and document contract checks passed before audit.
- Independent AGY/Sonnet audit returned `PASS_WITH_RISKS`.
- Final validation details are in `proof/TP-DMX-MERGE-INTEGRITY-0001/PROOF.json`.

## Embedded Audit

- auditor_tool: `agy`
- auditor_model: `sonnet`
- audited_content_sha: `b71e13a9b8691217dc6b35d148ccc122bc7d0f06`
- verdict: `PASS_WITH_RISKS`

## Proof Bundle

`proof/TP-DMX-MERGE-INTEGRITY-0001/`

## Merge Warning

Do not merge until supervisor review accepts the proposed ADR, architecture, and proof bundle.

## Rollback

Before merge: close this draft PR and delete the branch only with operator authorization. After accidental merge: do not reset `main`; create a focused revert PR for the documentation/proof commits after supervisor review.
