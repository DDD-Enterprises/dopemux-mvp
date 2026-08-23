# Fresh publication-integrity audit — TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PUBLICATION-001 (S8)

You are an independent read-only auditor. You are NOT re-electing any ADR
disposition and you are NOT authorizing implementation. This is a publication
integrity audit only.

## Frozen head under audit

```
C_PUB = 9e819f38c5f8c9da44cd396abe740d378f035d1a
```

You are running inside a git worktree already checked out at `C_PUB`. Do not
switch branches, do not commit, do not modify any file. Use `git show`, `git
diff`, `git log` and plain file reads only.

## Background (trust nothing below without checking it yourself against the repo)

- The human operator dispositioned all ten Second Brain ADRs `ADR-SB-001`
  through `ADR-SB-010` as `ACCEPT` on 2026-08-14.
- That acceptance was persisted on local branch `tp/DMX-SB-ADR-ACCEPTANCE-002`
  at content head `d38ec2f8715c6f4e594145e4d271b40e2d86bb69`, and independently
  audited PASS 0 blockers / 0 must-fix at audited head
  `0defe1cab46a9e6d02e88d3aa94a9edf195b4b84`
  (see `proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001/AUDITOR_REPAIR_REPORT.md`,
  verdict `PASS_ADR_ACCEPTANCE_PERSISTENCE_FAITHFUL_AND_ADDITIVE`).
- This publication packet (`TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PUBLICATION-001`)
  merged current `origin/main` (`57b239e76b8fbb0016ba497bc4a34ec0abee51bb`) into
  that branch with `git merge --no-ff`, after a drift guard found
  `NO_NEW_MATERIAL_DRIFT` and zero same-path overlap between the acceptance
  branch's own changes and main's delta. See
  `proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PUBLICATION-001/PUBLICATION_DRIFT_RECHECK.md`
  and `.../POST_MAIN_SYNC_ACCEPTANCE_INTEGRITY.json` for the claimed evidence.
- Nothing in this packet is authorized to implement Second Brain, touch
  runtime/production, or change any ADR's substance.

## Audit question

Does the local acceptance-persistence branch, at `C_PUB`, still truthfully and
completely encode the operator's 10x ACCEPT dispositions, preserve the accepted
architecture and prior audit lineage, incorporate current main without material
Second Brain drift, and grant no implementation/runtime authority?

## Required verifications (perform each yourself; do not take the proof records' word for it)

1. **10 accepted ADRs exactly.** Read
   `docs/03-reference/architecture/second-brain/adr-candidates/ADR_ACCEPTANCE_HEAD.json`.
   Confirm `accepted_adr_count == 10`, all ten `operator_disposition == "ACCEPT"`,
   no eleventh Second Brain ADR record exists under `docs/90-adr/` (list the
   directory yourself and grep for `adr-sb-`).
2. **No disposition drift.** Compare this file's content at `C_PUB` against its
   content at `d38ec2f8715c6f4e594145e4d271b40e2d86bb69` (`git diff
   d38ec2f871 C_PUB -- <path>`). Must be byte-identical.
3. **Accepted records correspond to the operator decision.** Spot-check at
   least 3 of the ten `docs/90-adr/adr-sb-*.md` records against
   `ADR_ACCEPTANCE_HEAD.json`'s per-ADR `path`/`sha256` fields; recompute
   sha256 yourself and compare.
4. **Historical audit head remains an ancestor.** Run
   `git merge-base --is-ancestor 0defe1cab46a9e6d02e88d3aa94a9edf195b4b84 C_PUB`
   yourself and confirm it succeeds.
5. **Post-audit deltas explained.** Run
   `git log --oneline 0defe1cab4..C_PUB` and classify every commit as
   AUDITED_SUBSTANCE / PROOF_ONLY / RECEIPT_ONLY /
   OPERATOR_DISPOSITION_PERSISTENCE / OTHER. Flag anything you cannot cleanly
   classify, or that touches `docs/90-adr/**`,
   `docs/03-reference/architecture/second-brain/adr-candidates/ADR_ACCEPTANCE_HEAD.json`,
   or `schemas/second_brain/**` outside of what the persistence packet's own
   proof already accounts for.
6. **Fresh publication drift guard is valid.** Independently re-derive: what
   changed between `75b4cfc581786a53445e412bfc8e25a6e0fdb978` (the prior
   audited MA-08 main SHA) and `57b239e76b8fbb0016ba497bc4a34ec0abee51bb`
   (current main, merged in)? Confirm the file list matches what
   `PUBLICATION_DRIFT_RECHECK.md` claims (6 files, all under
   `proof/TP-DMX-CI-TRUST-MERGE-GATE-INCIDENT-001-REVERT-1235/**` and
   `proof/pr_merge/embedded-audit/pr-1235/**`), and confirm none of those paths
   are Second Brain / ADR / authority / governance-index / privacy-boundary
   related.
7. **Current-main merge contains no hidden authority change.** Confirm the
   merge commit (find it: it is the merge of `origin/main` into this branch,
   after `d38ec2f871`) is a clean two-parent merge with no manual conflict
   resolution touching any accepted-authority path. Confirm zero overlap
   between the acceptance branch's own changed-file set (relative to
   `75b4cfc581`) and main's changed-file set (relative to the same base).
8. **Reasoning correction is append-only and accurate.** Read
   `proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/R2_AUDITOR_IDENTITY_REASONING_CORRECTION.json`
   and confirm: `record_modified_by_this_correction: false`; the corrected
   record `R2_AUDITOR_IDENTITY_RECONCILIATION.json` is unchanged from its
   state on `main` at `75b4cfc581` (`git show 75b4cfc581:<path>` vs the
   worktree copy, byte-for-byte); `identity_conclusion_changed: false`;
   `primaryModelId_independent_corroboration: false`; `provider_attestation:
   "UNKNOWN"`.
9. **Implementation remains NOT_AUTHORIZED.** Grep the accepted ADR records
   and `ADR_ACCEPTANCE_HEAD.json` / persistence proof for any authorization
   language and confirm none of it authorizes implementation, runtime, or
   production. Confirm `denial fixtures / runtime conformance / retrieval
   benchmarks / purge completeness / multi-project isolation / split-brain
   proof / encryption implementation` are still recorded as
   NOT_IMPLEMENTED/NOT_RUN/ABSENT somewhere in the accepted-authority record
   set (not silently upgraded).
10. **No Slice 0 content.** Confirm no runtime/service/application code was
    added or modified anywhere in `C_PUB` relative to
    `d38ec2f8715c6f4e594145e4d271b40e2d86bb69` outside of
    `proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PUBLICATION-001/**` and the files
    imported unmodified by the `origin/main` merge.

## Required output

Return, in this order:

```
VERDICT: PASS_ADR_ACCEPTANCE_PUBLICATION_INTEGRITY   (or a FAIL verdict, named)
BLOCKERS: <count>
MUST_FIX: <count>
```

followed by an enumerated list of BLOCKERS (if any), an enumerated list of
MUST_FIX items (if any, with severity reasoning), and a short per-check pass/fail
table for the 10 verifications above. If you cannot complete a verification
(tool/access limitation), say so explicitly — do not assume PASS.

`PASS_ADR_ACCEPTANCE_PUBLICATION_INTEGRITY` requires `BLOCKERS=0` and
`MUST_FIX=0`.
