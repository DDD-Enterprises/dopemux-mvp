# 05_ACCEPTANCE_PERSISTENCE_CONSTRAINTS — what the persistence step may and may not touch

```text
STATUS   ANALYSIS ONLY — this document persists nothing
WHY      The operator authorized a narrow acceptance-persistence step. Before writing it,
         the constraints the merged validator imposes were mapped from source, because two
         of the obvious ways to persist acceptance would break the gate that makes the
         acceptance evidence trustworthy in the first place.
```

## The problem in one line

`scripts/governance/validate_second_brain_adr_contracts.py` — merged, audited, currently
94 checks / 0 failed — **hard-enforces "no ADR is accepted" in six places.** Persisting the
operator's ten ACCEPT dispositions naively turns that green gate red.

## The six guards, read from source

| Check | What it asserts | Persistence must therefore |
|---|---|---|
| `A34-contracts-record-proposed` | every contract's `adr_status_at_contract_authoring == "PROPOSED"` | leave the contracts alone — the field is historical (status **at authoring**), and stays true forever |
| `A35-document-status-candidate` | the literal `\nstatus: CANDIDATE\n` appears in the candidate document | **not** flip the candidate to accepted |
| `A36-no-accepted-token` | no `ACCEPTED`-class value token anywhere in the contract artifacts | not write acceptance into `schemas/second_brain/contracts/**` |
| `A37-no-runtime-or-implementation-authority` | no truthy `accepted` / `adr_accepted` / `*_authorized` key in the contract artifacts | same |
| `B05-adr-acceptance-not-authorized` | `status.adr_acceptance_authorized is False` **and** `receipt.adr_acceptance_authorized is False` **and** `receipt.accepts_any_adr is False` | not flip those fields |
| `B06` / `B07` | `status.gates.adr_acceptance == "CLOSED"`, `status.gates.merge == "NOT_AUTHORIZED"` | not flip those either |

Plus `B03-pinned-fields-unchanged`, whose pin table includes literal values:

```text
/adr_statuses/all_remain          "PROPOSED (candidate)"
/adr_statuses/document_status     "CANDIDATE"
/adr_statuses/promoted_to_accepted 0
/gates/adr_acceptance             "CLOSED"
/gates/merge                      "NOT_AUTHORIZED"
```

## What the validator does *not* read

Its complete repo surface, from the source constants:

```text
schemas/second_brain/contracts/**
docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md
docs/03-reference/architecture/second-brain/adr-candidates/fo-01-repair-status.json
docs/03-reference/architecture/second-brain/adr-candidates/traceability-matrix.json
proof/TP-DMX-SECOND-BRAIN-ADR-TRACEABILITY-REPAIR-001/FO01_RESOLUTION_RECEIPT.json
proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/{ADR_CLAUSE_INVENTORY,DENOMINATOR_REFREEZE_RECEIPT}.json
```

`grep -c "90-adr"` against the validator returns **0**. Accepted ADR files under
`docs/90-adr/` are outside its scope entirely.

## Therefore: persistence must be purely additive

Write acceptance as **new** authority records; touch nothing the validator reads.

```text
MAY CREATE
  docs/90-adr/adr-sb-001..010-<slug>.md          ten accepted ADR records
  docs/03-reference/architecture/second-brain/adr-candidates/ADR_ACCEPTANCE_HEAD.json
  proof/<acceptance-persistence packet>/**       ledger, binding, receipt, proof

MAY MODIFY
  docs/90-adr/adr-index.md                       ten new rows

MUST NOT TOUCH
  second-brain-adr-candidates.md                 A35 — and it is frozen authority, pinned
                                                 by sha256 in the validator and in all ten
                                                 contracts
  fo-01-repair-status.json                       B02/B03/B05/B06/B07
  FO01_RESOLUTION_RECEIPT.json                   B05/B07 — and it is another packet's
                                                 historical audit record
  schemas/second_brain/contracts/**              A34/A36/A37
  scripts/governance/validate_second_brain_adr_contracts.py   merged audited evidence;
                                                 changing it needs its own audit
```

This is also what the superseded 2026-08-10 attempt did — `19fa74faa9` added ten ADR files,
one acceptance-head record and a proof bundle, and modified only `adr-index.md`. It touched
neither the candidate, the FO-01 records, nor (as they did not yet exist) the contracts.
The shape was right even though that attempt was superseded on other grounds.

## The residual this creates, stated rather than hidden

Additive persistence leaves `fo-01-repair-status.json` on `main` asserting, after ten ADRs
have been accepted:

```text
adr_acceptance_authorized   false
gates.adr_acceptance        "CLOSED"
adr_statuses.promoted_to_accepted   0
```

Two of those three are defensible on their own terms and one is not:

- **`adr_acceptance_authorized: false`** — the file's own `gate_field_semantics` glosses this
  as *"Only the human operator may authorize ADR acceptance."* The operator now has. The
  field is stale.
- **`gates.adr_acceptance: "CLOSED"`** — glossed as closed *"because the other acceptance
  conditions … are still outstanding."* They are no longer outstanding. Also stale.
- **`adr_statuses.promoted_to_accepted: 0`** — becomes false the moment ten ADR files land.

**This cannot be fixed inside a narrow persistence step, and the reason is structural, not
procedural.** `B02` requires the status file to be an exact whole projection of
`FO01_RESOLUTION_RECEIPT.json`. That receipt belongs to a different packet, is a historical
audit record, and says `accepts_any_adr: false` — permanently true of *that* receipt.
So the status file cannot express post-acceptance state without either falsifying its own
projection or rewriting another packet's audited history. Both are forbidden.

Reconciling it therefore requires changing the validator's invariant from *"no ADR is
accepted"* to *"acceptance matches the operator ledger"* — a change to merged, audited,
contract-sensitive governance tooling. That is a separate packet with its own independent
audit, and it is **not** authorized here.

## Recommendation carried to the operator

```text
DO NOW      additive persistence, exactly as scoped above, validator stays 94/0
DECLARE     the three stale FO-01 fields, by name, in the persistence proof bundle
DO LATER    a scoped follow-up that reconciles the FO-01 gate fields and the validator
            invariant together, with its own independent audit
DO NOT      quietly edit the FO-01 records or the validator to make the contradiction
            disappear — that is the exact stale-record class this whole programme exists
            to prevent, and FO-01 itself was one
```

The contradiction is small, bounded, and knowable. Leaving it undeclared is what would make
it dangerous.
