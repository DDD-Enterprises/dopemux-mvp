# Auditor Report — TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001 (controlling: R2)

**Audited commit**: `cdc83dda65cf6cf0337f5c4a88b76d048e2854f1`
**Auditor**: `agy` / `gemini-3.1-pro-high`, `--mode plan`, read-only git worktree audit

This is the CONTROLLING report. It supersedes the R1 audits (against
`ab57983171` and its narrow follow-up `05c41b3e6b`) preserved in
`review_bundle/` as non-controlling historical evidence — those audits
examined an earlier state of this branch before real PR review (7 findings
on live PR #1236) required a second repair round.

## Verdict: PASS

Independent verification of the R2 commit `cdc83dda65` on
`feat/local-audit-proof-binding-001`, addressing all 7 findings from live
review on PR #1236.

### Itemized findings disposition

1. **P1 (proof-only rewrites redefining audited head)**: **RESOLVED**. The
   script's "LIMITATION" docstring accurately documents `ATTESTED_AUDITED_SHA`
   as an operator attestation, not independently-verified cryptographic
   proof. The structural guarantee remains intact: the diff between the
   attested commit and the PR head is still restricted to the two allowed
   proof trees only. Right disposition — document the trust-model boundary,
   don't oversell it, keep the enforceable guarantee.
2. **P2 (report_path resolving to a directory)**: **RESOLVED**. Exact
   `_tree_type(...) == "blob"` check closes the `git ls-tree` string-prefix
   gap. `test_report_path_resolving_to_directory_is_rejected` exercises it.
3. **Copilot (packet_id identity)**: **RESOLVED**. Packet `PROOF.json`'s own
   `packet_id` must now string-match the PACKET_ID derived from the signed
   `report_path`. `test_packet_proof_packet_id_mismatch_is_rejected` covers
   it.
4. **P1 (task packet schema)**: **RESOLVED**. Independent validation of
   `TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001.json` against
   `dopetask-canonical-spec.json` via `jsonschema` executed with zero errors.
5. **P2 (review_bundle as a file)**: **RESOLVED**. `_tree_has_entries` now
   asserts `_tree_type(...) == "tree"` before enumerating contents.
   `test_review_bundle_as_a_file_is_rejected` covers it.
6. **P2 (signer preflight parity)**: **RESOLVED**.
   `scripts/audit/sign_local_audit_proof.sh` mirrors the backend's
   PACKET_ID derivation, object-type checks, and identity comparisons
   before signing. `bash -n` confirms valid syntax.
7. **P1 (ancestor check)**: **RESOLVED / not applicable**.
   `git merge-base --is-ancestor 05c41b3e6bebaa6b8854af5da0dbad9207ac5227 HEAD`
   returns ANCESTOR against the real branch. The original finding was
   anchored to a GitHub squash-merge preview artifact, not this branch's
   true history.

### Pytest counts (real execution, not summarized)
- `tests/audit`: **396 passed, 1 skipped**
- `tests/audit/test_local_audit_acceptance.py`: **64 passed**

### Newly-introduced risks
None identified. The repair replaces string-prefix inference with precise
git object-type binding (`blob` / `tree`), closing the false-positive edge
cases without opening new smuggling vectors or brittle regex.

### Bottom line
Commit `cdc83dda65` is structurally sound, test-covered, and ready to be
treated as the controlling audited head for this canonical proof bundle.

---

Full raw transcript and prompt: `review_bundle/AGY_AUDIT_R2_RAW.json`,
`review_bundle/AGY_AUDIT_R2_PROMPT.md`. Two prior AGY invocation attempts for
this same R2 round failed at the transport layer (empty response,
`"timeout waiting for response"` after 67s and 157s respectively, with only
1 turn each) — preserved as
`review_bundle/AGY_AUDIT_R2_ATTEMPT{1,2}_TRANSPORT_ERROR_NONCONTROLLING.json`
and explicitly NOT promoted to any verdict; the third attempt (`AGY_AUDIT_R2_RAW.json`)
is the one and only controlling run for R2.
