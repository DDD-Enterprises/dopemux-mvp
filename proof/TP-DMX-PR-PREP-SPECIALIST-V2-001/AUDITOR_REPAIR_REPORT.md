# S4 Independent Audit — TP-DMX-PR-PREP-SPECIALIST-V2-001-R5

## Audit target

`C1-R5 = a89c11dbfd9d132797575118f3f7b8c4f819a2ab` (merge commit, parents
`88c3cc73cdcd7c5373beae41a17c5c8a1c76f56c` [prior branch head, = C1-R4's
already-signed proof head] and `6626aa9a58dd82e62226cfca63498cc3f711bb75`
[`main` at merge time]).

## Why R5 exists

The branch was 19 commits behind `origin/main`; GitHub branch protection
requires the PR head to be up to date with `main` before merge. The
operator authorized a normal merge of `origin/main` into the branch (not
rebase, not squash, no force-push), conditioned on pre-merge drift
classification. Drift classified `COMPATIBLE`: zero file-path overlap
between the 81 files this branch has changed since merge-base `3e8fcc1c70`
and the 104 files `main` changed over the same range (verified via
`comm -12` before merging). `C1-R5` is the resulting two-parent merge
commit.

## Two audit rounds — both preserved

### Round 1 (initial, whole-tree scope) — **FAIL**

Raw transcript: `AGY_AUDIT_RAW_R5_INITIAL.txt`. Prompt:
`S4_AUDIT_PROMPT_R5_INITIAL.md`. The initial audit's scope item 2 required
a whole-repository conflict-marker scan and found real, pre-existing,
unresolved git conflict markers in files with **zero relationship** to
this packet (`docs/pr_merge/usage-patterns.md`,
`docs/planes/pm/write-boundaries.md`,
`docs/planes/pm/pm-implementation-ledger.md`, plus more under
`docs/archive/` and `proof/`). Every other scope item in that round passed
(real merge commit, zero diff on packet-owned files vs. R4, main-drift
disjoint from packet paths, 92/92 governance tests, schema PASS,
docs-prohibited-patterns false positive resolved, 0 commits behind main).

**This FAIL is preserved as historical evidence, unaltered.** It is not
deleted, overwritten, or relabeled. See disposition below.

### Scope adjudication

Full reasoning and deterministic evidence:
`AUDIT_R5_SCOPE_ADJUDICATION.md`. Summary: the flagged conflict markers
were proven byte-identical on **both** parents of the R5 merge commit
before the merge (i.e. present in `main` and in the pre-merge branch head
alike), trace to an unrelated commit from 2026-03-30 (`09b648f176`, #361),
and sit entirely outside this packet's owned paths
(`docs/03-reference/pr-pipeline/prep/**`, `docs/pr_prep/**`,
`tests/governance/test_pr_prep_contract_v2.py`,
`task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001.*`,
`proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/**`,
`proof/pr_merge/embedded-audit/pr-1224/**`). Operator ruling: out of scope
for this packet, tracked separately, not waived as a real defect.

```text
AUDIT_R5_INITIAL_VERDICT=FAIL
AUDIT_R5_INITIAL_DISPOSITION=SUPERSEDED_AS_CONTROLLING_AUDIT_DUE_TO_SCOPE_MISMATCH
FINDING_VALIDITY=REAL_PREEXISTING_REPO_DEBT
PACKET_BLOCKING_EFFECT=NONE_AFTER_SUPERVISOR_SCOPE_ADJUDICATION
```

### Round 2 (scoped, controlling) — **PASS**

Raw transcript: `AGY_AUDIT_RAW_R5_SCOPED.txt`. Prompt:
`S4_AUDIT_PROMPT_R5_SCOPED.md`. Re-verified the exact same, unchanged
`C1-R5` commit, with the conflict-marker scan restricted to this packet's
own audit universe (the #1224 delta vs. main, files touched by the R5
merge resolution, packet-owned canonical/compat/governance surfaces).
Explicit findings:

1. Real two-parent merge commit, not rebase/squash — confirmed.
2. #1224 delta vs. current main maps exactly to this packet's owned
   content universe.
3. No manual conflict-resolution edits — standard merge, clean
   auto-combination of both trees.
4. Packet-owned surfaces byte-identical to the already-audited R4 state
   (`6f32ac97dfd64f4386182fdd24380b2817551303`) — empty diff.
5. Zero conflict-marker hits within the restricted audit universe. The
   whole-tree markers are explicitly acknowledged and labeled
   `PREEXISTING_REPO_DEBT` / non-blocking, per the scope adjudication.
6. `ACTIVE_CONTRADICTION_COUNT` remains 0 (unaffected by the merge).
7. 92/92 governance tests pass.
8. Task packet schema-valid, 0 errors.
9. `docs-prohibited-patterns` false positive confirmed resolved.
10. 0 commits behind `main`.
11. Overall coherence: **PASS** — "R5, within this packet's owned audit
    universe, represents the unmodified, already-audited R4 state cleanly
    merged with current main. The packet introduces zero semantic change,
    zero new test failures, and zero scoped conflict markers."

## Governing verdict for this packet

**PASS** (via the round-2 scoped audit, which controls this packet's
readiness gate per operator scope adjudication). The round-1 FAIL remains
on record as real, valid evidence of separate, tracked, non-blocking
repository debt.

## Scope note

This audit covers `TP-DMX-PR-PREP-SPECIALIST-V2-001` R5 / PR #1224 only.
The pre-existing whole-tree conflict-marker debt requires its own bounded
repository-hygiene packet, tracked separately, not created by this
adjudication.
