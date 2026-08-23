# Independent audit — ADR acceptance persistence

You are an independent auditor with no producer conversation history. A human operator
accepted ten architecture decision records, and this change persists that acceptance into
repository authority. Your job is to determine whether the persistence is **faithful,
additive, and non-inflationary**: does it record exactly what the operator decided, does it
avoid touching anything it must not, and does it avoid claiming any authority the operator
did not grant?

Work only from bytes in this checkout. Do not trust this prompt's summaries over what you
can recompute.

```text
AUDITED_CONTENT_HEAD = 5f9f38acd465ea9a30df0a6251b6e4960704f5cc
MA08_MAIN_SHA        = 75b4cfc581786a53445e412bfc8e25a6e0fdb978   (origin/main)
```

## Why this audit exists

`proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/SUPERSESSION_LINEAGE.md`, which
is merged operator instruction, specifies a replacement acceptance chain and says at step 6
that **only the audited rebuilt chain may become authoritative**. This is that audit. A PASS
does not accept anything further; it establishes that the persistence may stand.

## The one thing that must not have happened

An earlier acceptance attempt, commit `19fa74faa9`, was **superseded** because its ADR files
carried the *pre-amendment* acceptance condition #2:

```text
* Machine contracts and denial fixtures parse and cover the decision.
```

The operator ruled that wording ambiguous and replaced it. The lineage forbids inheriting
anything from that attempt.

**Verify from bytes that the pre-amendment string appears in none of the ten new ADR files**,
and that each carries the amended AC#2 instead. If any accepted record carries the old
wording, that is a blocker and the persistence is invalid.

## What to verify

### 1. Scope — additive, and nothing else

```bash
git diff --name-only 75b4cfc581786a53445e412bfc8e25a6e0fdb978..5f9f38acd465ea9a30df0a6251b6e4960704f5cc
```

Every path must fall inside the allowlist in
`task-packets/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001.json` or its predecessor
packet's. Confirm **zero** uncovered paths yourself.

`AUDIT_PROMPT.md` and `C1_CONTENT_HEAD.txt` are **not** committed at `AUDITED_CONTENT_HEAD`
— they are authored after the freeze so the prompt can name the head it audits, and they are
recorded in the next proof-only commit together with your report. Their absence, or a
`C1_CONTENT_HEAD.txt` naming an earlier head, is expected and is not a finding.

These surfaces are declared read-only. **Any diff touching one is a blocker:**

```text
docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md
docs/03-reference/architecture/second-brain/adr-candidates/fo-01-repair-status.json
docs/03-reference/architecture/second-brain/adr-candidates/traceability-matrix.json
docs/03-reference/architecture/second-brain/authority/**
proof/TP-DMX-SECOND-BRAIN-ADR-TRACEABILITY-REPAIR-001/FO01_RESOLUTION_RECEIPT.json
proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/R2_AUDITOR_IDENTITY_RECONCILIATION.json
schemas/second_brain/contracts/**
scripts/governance/validate_second_brain_adr_contracts.py
```

### 2. The validator still passes, and passes honestly

```bash
python3 scripts/governance/validate_second_brain_adr_contracts.py --json
python3 -m pytest -q tests/governance/test_second_brain_adr_contracts.py
```

Expect `PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE`, 94 checks, 0 failed, and 63/63.

Then satisfy yourself that it passes because the persistence was genuinely additive and
**not because a guard was weakened**. Diff the validator against `MA08_MAIN_SHA` — it must
be byte-identical. Confirm checks `A34`, `A35`, `A36`, `A37`, `B05`, `B06`, `B07` are all
still present and still asserting what they assert.

### 3. The accepted records derive from the candidate

The generator is committed at
`proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001/generators/gen_accepted_adrs.py`.

- Re-run it and confirm the ten files are reproduced byte-identically.
- Independently confirm each record's decision body is a **substring of the candidate** at
  `e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c`. Do not take the
  generator's own post-write check as proof; recompute.
- Confirm the ten `## ADR-SB-NNN` titles and the ten contract paths match.
- Check the slug rule is applied uniformly. The superseded attempt hand-shortened one slug;
  if any of the ten deviates from the stated rule, say so.

### 4. No authority inflation

This is the heart of the audit. Acceptance is architecture law and nothing more.

- Every accepted record must state that acceptance confers no implementation, runtime,
  production, or enablement authority.
- `ADR_ACCEPTANCE_RECEIPT.json` must not claim implementation, runtime enablement, Slice 0,
  denial fixtures, or merge authority.
- Search the added files for any claim that denial fixtures exist, that conformance or
  benchmarks or purge completeness or isolation or split-brain proof were run, or that
  encryption exists. All are `NOT_RUN`, `NOT_IMPLEMENTED`, or `ABSENT`.
- The candidate document must still read `status: CANDIDATE`. Acceptance was persisted as
  new records, not by promoting the candidate. Confirm it.

### 5. Disposition provenance is the operator's, not the producer's

Read `ADR_OPERATOR_DECISION_LEDGER.yaml` against
`proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002/04_ADR_DISPOSITION_WORKSHEET.md`.

- Ten ACCEPT rows, `facilitator_authored_dispositions: false`,
  `inherited_from_superseded_attempt: false`.
- The worksheet's facilitator recommendations must sit in a field **separate** from the
  disposition field. A recommendation written into a disposition field is a producer
  deciding, and is a blocker.
- The worksheet's evidence and recommendations must be unchanged from the version first
  committed at `fa48fcd201058599fb69ef86a4e3397e21b739a7`, apart from the ten disposition
  fields, the summary-table cells, the header block, and the terminal-state block.
  **Verify with a diff**, not by trust.

  State the custody position honestly, because it bounds how much weight this audit carries:
  **the worksheet was produced after the Phase B acceptance-readiness audit and was never
  covered by it.** That audit bound content head `f7326b18397a4381df88ec4dc933eeb3f0011288`,
  and the worksheet did not exist there — it was written at `fa48fcd201`. The ordering was
  the operator's own sequence (audit the evidence, then produce the worksheet), not an
  omission. This is therefore the **first** independent look at the worksheet itself. Treat
  its evidence table, its per-ADR reasoning, and its recommendations as unaudited claims to
  check, not as previously blessed material. In particular, spot-check its per-ADR clause
  counts, typed-artifact counts, and the "2 / 3 / 2 required_artifacts" claim against the
  contracts.

### 6. The declared staleness is honest and complete

`ADR_ACCEPTANCE_BINDING.json` declares that this persistence makes three fields in
`fo-01-repair-status.json` stale, and asserts two other fields are *not* stale.

- Verify each of the five claims against the file and against the validator's own
  `gate_field_semantics` glosses.
- Then look for a **fourth** stale field the declaration missed. An incomplete declaration
  presented as complete is the defect class this programme cares most about; if you find one,
  that is at least a must-fix.

### 7. The correction record

`proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/R2_AUDITOR_IDENTITY_REASONING_CORRECTION.json`
is an operator-authorized append. Confirm it is a **new file**, that
`R2_AUDITOR_IDENTITY_RECONCILIATION.json` is unmodified against `MA08_MAIN_SHA`, and that the
correction changes no identity conclusion.

## What would make this FAIL

Report a **BLOCKER** for: the pre-amendment AC#2 in any accepted record; any write to a
declared read-only surface; a weakened or removed validator guard; any implementation,
runtime, or enablement claim; a disposition not traceable to the operator; an accepted record
whose decision text is not a candidate byte-slice; or an uncovered changed path.

Report **MUST_FIX** for a real defect that does not by itself invalidate the persistence —
including an incomplete staleness declaration, an inconsistent slug, or a false supporting
number.

## Output format

Sections: `VERDICT`, `BLOCKERS`, `MUST_FIX`, `NONBLOCKING_OBSERVATIONS`,
`WHAT_I_VERIFIED_FROM_BYTES`, `WHAT_I_COULD_NOT_VERIFY`. State explicit integers:

```text
BLOCKERS: <n>
MUST_FIX: <n>
```

The advancing verdict string is:

```text
PASS_ADR_ACCEPTANCE_PERSISTENCE_FAITHFUL_AND_ADDITIVE
```

That string is the gate this change must clear, **not** an instruction about what to
conclude. If it does not clear it, return `FAIL` with your blockers. A FAIL is recorded
verbatim and stops the packet, which is the outcome the producer has committed to accept.
Do not soften a real finding, and do not manufacture one.

Do not write to any file in this checkout; return your report as your final message.
