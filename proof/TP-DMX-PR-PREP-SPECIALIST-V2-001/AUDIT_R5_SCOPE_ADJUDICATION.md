# R5 audit scope adjudication — TP-DMX-PR-PREP-SPECIALIST-V2-001 / PR #1224

## Record of the initial R5 audit and its disposition

```text
AUDIT_R5_INITIAL_VERDICT=FAIL
AUDIT_R5_INITIAL_DISPOSITION=SUPERSEDED_AS_CONTROLLING_AUDIT_DUE_TO_SCOPE_MISMATCH
FINDING_VALIDITY=REAL_PREEXISTING_REPO_DEBT
PACKET_BLOCKING_EFFECT=NONE_AFTER_SUPERVISOR_SCOPE_ADJUDICATION
```

The initial R5 audit (prompt: `S4_AUDIT_PROMPT_R5_INITIAL.md`, raw transcript:
`AGY_AUDIT_RAW_R5_INITIAL.txt`) is **not deleted, overwritten, or relabeled**.
Its actual verdict was, and remains on record as, **FAIL**. This file
documents why that FAIL does not control this packet's readiness, without
disturbing the FAIL itself.

## What the initial audit found (verified independently, not taken on faith)

Scope item 2 of the initial R5 prompt required a whole-repository-tree scan
for unresolved git conflict markers (`<<<<<<<`/`=======`/`>>>>>>>`). The
auditor found real, literal, unresolved markers in (at least)
`docs/pr_merge/usage-patterns.md`, `docs/planes/pm/write-boundaries.md`,
and `docs/planes/pm/pm-implementation-ledger.md`, plus additional hits
reported under `docs/archive/` and `proof/`. These are genuine leftover
conflict-resolution fragments, not false-positive prose — confirmed by
direct read of the flagged line ranges, not by trusting the auditor's
summary alone.

## Why this does not block TP-DMX-PR-PREP-SPECIALIST-V2-001 / PR #1224

Deterministically proven, independently of the auditor, before this
adjudication:

```bash
git show 6626aa9a58:docs/pr_merge/usage-patterns.md | grep -n '^<<<<<<<\|^=======$\|^>>>>>>>'
git show 88c3cc73cd:docs/pr_merge/usage-patterns.md | grep -n '^<<<<<<<\|^=======$\|^>>>>>>>'
# identical byte-for-byte on both C1-R5 merge parents
```

- The markers are byte-identical on **both** parents of the R5 merge commit
  (`a89c11dbfd9d132797575118f3f7b8c4f819a2ab`): the pre-merge branch head
  `88c3cc73cdcd7c5373beae41a17c5c8a1c76f56c` and `main` at merge time
  `6626aa9a58dd82e62226cfca63498cc3f711bb75`. The R5 merge neither
  introduced nor altered them.
- `git log --oneline -- docs/pr_merge/usage-patterns.md` traces the markers
  to commit `09b648f176` ("feat: consolidate and reconcile all active
  work", 2026-03-30, #361) — a commit with no relationship to this packet.
- None of the affected paths (`docs/pr_merge/**`, `docs/planes/pm/**`,
  `docs/archive/**`, unrelated `proof/**` entries) are inside this packet's
  owned surfaces: `docs/03-reference/pr-pipeline/prep/**`,
  `docs/pr_prep/**`, `tests/governance/test_pr_prep_contract_v2.py`,
  `task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001.*`,
  `proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/**`,
  `proof/pr_merge/embedded-audit/pr-1224/**`.
- Task Packets control scope; validation here is changed-path/allowlist
  based. Treating unrelated, pre-existing, whole-tree hygiene debt as a
  blocker for this packet would expand it into unbounded repository
  cleanup, contrary to its bounded-change discipline.

## Governing ruling

Per operator decision (`## Decision` — "Choose (a)"), the whole-tree
conflict-marker finding is ruled **out of scope** for
TP-DMX-PR-PREP-SPECIALIST-V2-001. It is **not** waived as a real defect —
it is real, pre-existing repository debt and is tracked as such — but it
does not control this packet's readiness gate. A scoped re-audit is
authorized against the **unchanged** C1-R5 (`a89c11dbfd9d132797575118f3f7b8c4f819a2ab`),
restricting the conflict-marker scan to this packet's own audit universe
(the #1224 delta vs. main, files touched by the R5 merge resolution if
any, and packet-owned canonical/compat/governance surfaces) rather than
the whole tree.

## Separate tracked debt

The genuine, pre-existing conflict markers require their own bounded
repository-hygiene packet. Not created or scheduled by this adjudication;
noted here so it is not lost. Affected files identified so far (non-
exhaustive, from the initial R5 audit): `docs/pr_merge/usage-patterns.md`,
`docs/planes/pm/write-boundaries.md`, `docs/planes/pm/pm-implementation-ledger.md`,
plus further hits under `docs/archive/` and `proof/` not yet enumerated.
