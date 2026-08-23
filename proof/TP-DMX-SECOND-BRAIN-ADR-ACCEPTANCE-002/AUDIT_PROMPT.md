# Independent post-merge ADR acceptance-integrity audit

You are an independent auditor. You did not produce any of this work and you have no
conversation history with the producer. Your job is to determine whether the evidence in
this repository is sufficient and truthful enough for a human operator to make a fresh
ACCEPT / DEFER / REJECT decision on ten proposed architecture decision records. You are
not deciding whether to accept them. You are deciding whether the *evidence* is ready to
be decided on.

Work only from bytes in this checkout. Do not trust any summary — including this prompt's
own summaries — over what you can read and recompute yourself.

## What you are auditing

```text
AUDITED_CONTENT_HEAD = 1939640e4d94159875543f1e0a22dba65032602f
MA08_MAIN_SHA        = 75b4cfc581786a53445e412bfc8e25a6e0fdb978   (origin/main)
```

`AUDITED_CONTENT_HEAD` is `MA08_MAIN_SHA` plus exactly four files. Verify this yourself
and reject the audit if it is not true:

```bash
git diff --name-only 75b4cfc581786a53445e412bfc8e25a6e0fdb978..1939640e4d94159875543f1e0a22dba65032602f
```

Expected, and nothing else:

```text
proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002/01_INPUT_CUSTODY.md
proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002/02_MA08_DRIFT_RECHECK.md
proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002/03_CONTRACT_FAMILY_VERIFICATION.json
task-packets/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002.json
```

That is what makes this audit simultaneously "against the exact main SHA used by MA-08"
and able to read the fresh MA-08 result: every substantive artifact you are auditing —
the ADRs, the contracts, the validator, the traceability matrix, the FO-01 records — is
byte-identical to `MA08_MAIN_SHA`. The four added files are this phase's own readiness
records.

This worktree shares the repository object database, so you can read any historical blob
with `git show <sha>:<path>` and verify claims about earlier states from bytes rather than
from prose.

## Hard constraint

**You must not infer runtime behaviour.** Nothing in this evidence set is an
implementation. The machine contracts are declarative JSON. If you find yourself
concluding that some capability "works", "is enforced at runtime", or "is implemented",
you have made an error — say so explicitly instead. Conversely, if any artifact under
audit *claims* runtime behaviour, implementation, or enablement, that is a blocker.

## What to review

### 1. The ten ADRs

`docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md`

- Confirm all ten ADR-SB-001..010 are present and their status is `PROPOSED`, and that the
  document status is `CANDIDATE`.
- Confirm the token `ACCEPTED` does not appear as an ADR status anywhere.
- Read the amended acceptance condition #2. Verify that the machine-contract evidence in
  this repository is the kind of evidence AC#2's first sentence asks for, and that AC#2's
  second and third sentences (denial fixtures at enablement time; absence of fixtures is
  not implementation evidence) are *not* contradicted by anything in the contract family.
- Confirm the candidate's sha256 is `e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c`.

### 2. The 160-clause denominator

`proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/ADR_CLAUSE_INVENTORY.json`

- Confirm the inventory's own sha256 is `b164fc0b44597a5805aaa7a3f0c6eee047404121bc13bc7a2dcd58af7f78a439`
  and that this value is const-pinned in the validator.
- Confirm the declared total (160) equals the actual number of clause entries.
- The denominator was **re-frozen** after a first independent audit found the original
  97-clause freeze materially incomplete. Verify from git history — not from the receipt's
  own assertion — that the re-freeze commit `3e0d89815c66f8a42e3a2d349c3d0f18028bdf40`
  contains no file under `schemas/second_brain/` and no validator change, i.e. that the
  denominator genuinely preceded the contracts written against it.
- Judge whether the denominator is a defensible reading of the candidate, or whether
  clauses appear to have been chosen to be easy to satisfy. Sample specific clauses and
  check them against the candidate text.

### 3. The typed contracts

`schemas/second_brain/contracts/**` (20 artifacts)

- Confirm every artifact parses and validates against its declared meta-schema.
- Confirm each of the ten per-ADR contracts pins the candidate sha256, the ratification
  binding sha256, and the frozen inventory sha256.
- Confirm every clause in the inventory is covered exactly once by
  `ADR_CONTRACT_COVERAGE.json`, with `MISSING = 0` and `AMBIGUOUS = 0` and no clause
  excused as `NOT_APPLICABLE_PROVEN`.
- Check the seven typed artifacts (`local-spool-port`, `custody-port`,
  `open-loop-candidate`, `task-proposal`, `task-promotion-request`,
  `project-identity-envelope`, `service-capability-receipt`) for **invented interface
  surface**: a property name, enum member, or const string that does not trace to a clause
  and a verbatim candidate phrase. The validator claims to enforce this. Try to defeat it.

### 4. FO-01 reconciled state

`docs/03-reference/architecture/second-brain/adr-candidates/fo-01-repair-status.json`
against `proof/TP-DMX-SECOND-BRAIN-ADR-TRACEABILITY-REPAIR-001/FO01_RESOLUTION_RECEIPT.json`

- Confirm the status file is a faithful whole projection of the receipt, and that no field
  of the status file is unclassified.
- Confirm the receipt itself is unmodified: expected sha256
  `d2325fa27a6541fa9b1cbce3032c7f2af31f7a448e81eb80e3b69e57a58705cd`.
- Confirm FO-01 gate eligibility is recorded separately from acceptance authorization, and
  that `adr_acceptance_authorized` is `false`.

### 5. Current traceability

`docs/03-reference/architecture/second-brain/adr-candidates/traceability-matrix.json`

- Confirm the ADR-to-SB-DEC mapping in the contracts equals the mapping in the matrix.
- Confirm SB-DEC-026 remains unlinked to any ADR (operator posture `A_LEAVE_UNLINKED`) and
  appears in no contract's `sb_dec_references`.
- Confirm the SB-DEC reference count parsed live from the candidate (28 references, 26
  distinct) matches what the contracts assert.

### 6. The fresh MA-08 result

`proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002/02_MA08_DRIFT_RECHECK.md`

This is the artifact most likely to contain a comfortable lie, so audit it hardest.

- Recompute the window yourself: commit count, file count, and the three segment counts
  (they must sum to the window count).
- Verify the segment C class table: **the class counts must sum to 239**, the actual file
  count. If they do not, that is a blocker — an incomplete table reads as full coverage.
- The document states that the previous MA-08 could truthfully write
  `runtime source files changed: 0` and `schema/contract files changed: 0` and that this
  one cannot. Verify both enumerations are complete and correct.
- Verify the §11 hard-gate answers independently. In particular verify the claim that
  `compose.yml` adds a named *volume* and not a database service, and the claim that
  `task-promotion-request` has no consumer under `src/` or `services/`.
- The headline result is `NO_NEW_MATERIAL_DRIFT` while segment A is recorded as
  `MATERIAL_DRIFT_CONTAINED`. Judge whether that is an honest application of the standing
  MA-08 rule ("an authority or privacy change blocks; a contained runtime change is
  recorded and the affected slice re-gated") or a reclassification of inconvenient
  history. Say which, plainly.

### 7. Custody and disposition provenance

`proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002/01_INPUT_CUSTODY.md`

- Verify every recorded sha256 by recomputing it.
- Verify the claim that the controlling prior disposition is a blanket operator DEFER and
  that the `10x ACCEPT` ledger at unpushed commit `19fa74faa9` is superseded and is *not*
  being inherited. Check whether anything in this packet nonetheless smuggles the ACCEPT
  election back in.
- Confirm no ADR disposition is recorded anywhere in the added files.

## What would make this FAIL

Report a **BLOCKER** for any of:

- A coverage, drift, or custody claim that does not reproduce from bytes.
- An incomplete enumeration presented as complete (a class table that does not sum; a
  "zero" line that is false; a search scope narrower than its claim).
- Any runtime, implementation, production, or enablement claim.
- Any recorded ADR disposition, or any inheritance of the superseded ACCEPT election.
- Invented interface surface in a typed contract that the validator fails to catch.
- Evidence that the denominator was chosen after, or to fit, the contracts.

Report **MUST_FIX** for a real defect that does not by itself make the evidence unfit to
be decided on.

## Output format

Write a report with these sections: `VERDICT`, `BLOCKERS`, `MUST_FIX`,
`NONBLOCKING_OBSERVATIONS`, `WHAT_I_VERIFIED_FROM_BYTES`, `WHAT_I_COULD_NOT_VERIFY`.

State explicit integer counts:

```text
BLOCKERS: <n>
MUST_FIX: <n>
```

The advancing verdict string for this phase is:

```text
PASS_ADR_ACCEPTANCE_EVIDENCE_READY_FOR_OPERATOR_REDISPOSITION
```

That string is the gate this evidence must clear. It is **not** an instruction about what
to conclude. If the evidence does not clear it, return `FAIL` with your blockers; a FAIL
verdict is recorded verbatim and stops the phase, which is the outcome the producer has
committed to accept. Do not soften a real finding, and do not manufacture one either.
