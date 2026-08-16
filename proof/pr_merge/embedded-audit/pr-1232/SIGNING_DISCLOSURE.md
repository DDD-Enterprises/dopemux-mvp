# Signing Disclosure — PR #1232, v2 (TP-DMX-RTE-V5-P1-FAIL-CLOSED-REPAIR-001)

```text
PRIOR_FROZEN_PR_HEAD          = 492208f4684f1b7660be26deda7c29161ea50070
AUDITED_SUBSTANTIVE_TREE_C1R  = 1c59dafd19817d7af7033245d3e1342927c38af5
AUDITED_SUBSTANTIVE_TREE_C1R2 = 8ce48664707a89f39960a603e658c4cf5a39a30d
AUDIT_EVIDENCE_HEAD           = e0a292c06ec05f538dde019d288fad9243abae15
SIGNED_BRIDGE_HEAD            = <filled in after this commit is created>
```

## Why this supersedes the prior (v1) bridge

The prior signed bridge in this directory (`AUDITED_SUBSTANTIVE_TREE = 67f22b4829`,
`AUDIT_EVIDENCE_HEAD = 7acc062344`) attested a version of the code that predates PR #1232
ever being marked ready for review. After it was signed, PR #1232 *was* marked ready and,
in review, two P1 defects were found on the frozen content head `492208f4684f1b7660be26deda7c29161ea50070`:

- **RTE-W1-010**: the source-identity fail-closed gate (`required_execution_source_identity`)
  was reachable *after* several live/provider dispatch paths instead of before them.
- **RTE-W1-006 (V5 terminal)**: a provider terminal-failure batch could be laundered into
  overall success via a clean webhook integration.

Those defects were repaired in two rounds on top of `492208f4`:

- **C1R** (`1c59dafd19`): closed the reachable-async/finalize/batch-watch/batch-retrieve/
  ordinary-phase dispatch paths for RTE-W1-010, and the terminal-batch-failure accounting
  for RTE-W1-006. Independently audited (Claude Opus, isolated worktree pinned to
  `1c59dafd19`): `PASS_WITH_RISKS`, one accepted-but-flagged residual, F-001-MEDIUM-1 —
  `--phase S_INT` still bypassed the gate.
- **C1R2** (`8ce4866470`): closed F-001 — relocated the S_INT dispatch block to run after
  the identity gate, added a mutation-sensitive regression test, and fixed a pre-existing
  test whose fixture only passed because it exercised the bug being closed. Independently
  re-audited (Claude Opus, fresh isolated worktree pinned to `8ce4866470`): `PASS_WITH_RISKS`,
  0 blocking findings.

The prior v1 bridge's underlying grok-cli/grok-4.5 audit never saw either repair round —
it audited a strictly earlier, now-superseded state. Per the packet's own `PROOF.json`
(`pr.note`): "The prior Grok audit and signed embedded-audit bridge for that head are
STALE_FOR_C1R." This v2 bridge replaces it with the controlling audit for the actual
current code.

## What this is

An **operator attestation** re-publishing, under a cryptographic operator signature, the
verdict already recorded at `proof/TP-DMX-RTE-V5-P1-FAIL-CLOSED-REPAIR-001/PROOF.json`
(`embedded_audit`, the C1R2 round) and
`proof/TP-DMX-RTE-V5-P1-FAIL-CLOSED-REPAIR-001/AUDITOR_REPAIR_REPORT.md`. It does not
perform a new audit and does not re-judge the work.

## Facts

- **The Opus audit was independently executed before this bridge**, against an isolated
  git worktree, detached HEAD, verified pinned to `8ce4866470` as its own first action
  (`C1R2_HEAD_MISMATCH` stop condition, not triggered). Full transcript preserved at
  `proof/TP-DMX-RTE-V5-P1-FAIL-CLOSED-REPAIR-001/review_bundle/AUDITOR_RAW_RESPONSE_C1R2.md`.
- **The audit controls the L2 judgment.** Verdict: `PASS_WITH_RISKS`, 4 findings
  (F-A through F-D), all `ACCEPTED_RISK`, none reopening RTE-W1-001/006/010.
- **`e0a292c06e` is a proof/packet successor of the audited substantive commit `8ce4866470`.**
  `git diff --name-only 8ce4866470..e0a292c06e` touches only
  `proof/TP-DMX-RTE-V5-P1-FAIL-CLOSED-REPAIR-001/**` (the C1R2 audit-proof commit and the
  topology-verification/F-D-disposition/PR-draft-restoration commit) — confirmed at
  publication time.
- **No RTE source or test byte changed after `8ce4866470`.**
  `git diff --name-only 8ce4866470..e0a292c06e -- services/repo-truth-extractor` is empty.
- **This bridge is an operator attestation allowing CI to consume already-existing audit
  evidence**, per `scripts/audit/local_audit_acceptance.py`'s own documented trust model:
  "a valid signature proves that a holder of an allow-listed private key attested this
  exact code was audited. It is an operator attestation, not an independent third-party
  audit."
- **It is NOT a new audit or implementation repair.** No RTE source or test file is touched
  by this commit. No new model invocation was made to produce this bridge's verdict — the
  verdict is copied verbatim from the already-published `embedded_audit` object.
- **`head_sha` in the signed `PROOF.json` is `e0a292c06e` (`AUDIT_EVIDENCE_HEAD`), not
  `8ce4866470` (`AUDITED_SUBSTANTIVE_TREE_C1R2`)**, matching the same pattern the v1 bridge
  used: `local_audit_acceptance.py` requires `git diff head_sha..enforced_PR_head` to touch
  only this proof directory, and two packet-proof-only commits (the C1R2 audit-proof commit,
  the topology/F-D/draft-restoration commit) already sit between the substantive tree and
  this bridge in a *different* proof namespace
  (`proof/TP-DMX-RTE-V5-P1-FAIL-CLOSED-REPAIR-001/**`). Binding `head_sha` to `e0a292c06e`
  keeps the mechanical ancestor-diff check honest (nothing but this bridge follows it) while
  this document records, verifiably, that the actual audited and RTE-source-identical
  substantive commit is the ancestor `8ce4866470`.

## Scope of this bridge

Only these files were created or modified by this operation:

```text
proof/pr_merge/embedded-audit/pr-1232/PROOF.json
proof/pr_merge/embedded-audit/pr-1232/PROOF.json.sig
proof/pr_merge/embedded-audit/pr-1232/SIGNING_DISCLOSURE.md
```

No RTE source or test file, no packet-proof file outside this directory, and no file
belonging to PR #1136 or PR #1183 was touched.
