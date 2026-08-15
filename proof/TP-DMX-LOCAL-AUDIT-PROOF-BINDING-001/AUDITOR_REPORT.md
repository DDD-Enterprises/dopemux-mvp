# Auditor Report — TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001 (controlling: R3)

**Audited commit**: `a26474698c09dd0cfdfde737135dbaa821aba234`
**Auditor**: `agy` / `gemini-3.1-pro-high`, `--mode plan`, read-only git worktree audit

This is the CONTROLLING report. It supersedes the R1 (`ab57983171` /
`05c41b3e6b`) and R2 (`cdc83dda65`) audits preserved in `review_bundle/` as
non-controlling historical evidence — each examined an earlier state of
this branch before further rounds of live PR review surfaced more findings.

## Verdict: PASS

Independent verification of the R3 commit `a26474698c` on
`feat/local-audit-proof-binding-001`, addressing 4 fresh findings from live
review on PR #1236 (a 5th, a re-flagged ancestry finding, was independently
confirmed not applicable to real branch history).

### Itemized findings disposition

1. **P1 (ancestry re-flagged against a squash-merge preview)**:
   **RESOLVED / not applicable**. `git merge-base --is-ancestor
   cdc83dda65cf6cf0337f5c4a88b76d048e2854f1 HEAD` returns ANCESTOR against
   the real branch, with exactly the two expected proof-only successor
   commits between them. The finding was anchored to a synthetic
   squash-merge-preview SHA that never exists as a real commit in this
   repository's history.
2. **P1 (task-packet allowlist omission)**: **RESOLVED**. The packet's
   `commit.allowlist` now includes `proof/pr_merge/embedded-audit/pr-1236/**`
   alongside the canonical packet-bundle path, matching what step S04
   actually commits.
3. **P2 (signer preflight schema/policy parity)**: **RESOLVED**.
   `scripts/audit/sign_local_audit_proof.sh` now imports and runs
   `schema_validation_errors`/`policy_errors` from
   `scripts.audit.local_audit_acceptance` against both the PR proof's own
   `embedded_audit` object and the packet proof's, closing the
   local-success/CI-failure gap. Confirmed by running
   `test_signer_preflight_rejects_packet_object_failing_policy_despite_matching_identity`
   directly (1 passed).
4. **P2 (gitlink smuggling in review_bundle)**: **RESOLVED**.
   `_tree_has_entries` now inspects each recursive `git ls-tree -r` entry's
   own object type and requires at least one real `blob` — a
   gitlink/submodule entry (object type `commit`) no longer satisfies the
   check. Confirmed by running `test_review_bundle_gitlink_only_is_rejected`
   directly (1 passed), which constructs a real gitlink via
   `git update-index --add --cacheinfo 160000,...`.

### Pytest counts (real execution, not summarized)
- `tests/audit`: **399 passed, 1 skipped**

### Newly-introduced risks / regressions vs R1/R2
None identified. `git diff cdc83dda65..a26474698c` confirmed no unrequested
logic changes or weakened conditionals.

### Bottom line
Commit `a26474698c` fully remediates all legitimate R3 reviewer findings
without regressions or newly introduced bypasses, and is ready to be
treated as the controlling audited head for this canonical proof bundle.

---

Full raw transcript and prompt: `review_bundle/AGY_AUDIT_R3_RAW.json`,
`review_bundle/AGY_AUDIT_R3_PROMPT.md`. R1 and R2 audits remain in
`review_bundle/` as superseded historical evidence, not controlling.
