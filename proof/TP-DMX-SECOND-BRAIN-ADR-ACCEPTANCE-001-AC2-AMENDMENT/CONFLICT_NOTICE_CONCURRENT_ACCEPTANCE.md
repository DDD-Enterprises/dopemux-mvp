# CONFLICT NOTICE — concurrent ADR acceptance discovered

```text
status: RESOLVED — OPTION 1, HONOUR THE LATER DEFER (see SUPERSESSION_LINEAGE.md)
raised by: TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001 (AC#2 amendment track, this session)
discovered: 2026-08-10T01:18Z, during post-amendment mutation verification
action taken: NONE. The conflicting branch and worktree were inspected read-only and not touched.
```

## What exists

A **second, concurrent session** has already performed ADR acceptance and committed it:

```text
branch:    tp/DMX-SB-ADR-ACCEPTANCE-001
worktree:  /Users/hue/code/.worktrees/DMX-SB-ADR-ACCEPTANCE-001
commit:    19fa74faa9  "docs(second-brain): accept adjudicated ADR set"
committed: 2026-08-09T18:07:06-07:00  ==  2026-08-10T01:07:06Z
scope:     20 files, +2112 lines
pushed:    NO
PR:        NONE
on main:   NO
```

It creates ten **accepted** ADRs at `docs/90-adr/adr-sb-001..010-*.md`
(`status: accepted`, `**Status:** \`ACCEPTED\``), updates `docs/90-adr/adr-index.md`, and
ships a full proof bundle including `06_ADR_OPERATOR_DECISION_LEDGER.yaml`,
`07_ADR_ACCEPTANCE_BINDING.json`, and `ADR_ACCEPTANCE_RECEIPT.json`.

## Its provenance is `UNKNOWN` — unverifiable off-machine, not alleged fabricated

**Provenance status: `UNKNOWN`** (downgraded from `GENUINE` on operator direction after PR #1214
review — see `SUPERSESSION_LINEAGE.md`).

The ledger below was read from the producer's local worktree. Commit `19fa74faa9` is unpushed,
so it cannot be resolved in any other checkout and no consumer can verify these values
independently. They are recorded as **producer-machine observations, off-machine-unverifiable**:

```text
06_ADR_OPERATOR_DECISION_LEDGER.yaml   (observed locally; not externally verifiable)
authority: HUMAN_OPERATOR
facilitator_authored_dispositions: false
disposition_confirmed: true
bulk_token_supplied_by_operator: true
  -> operator explicitly elected "ACCEPT all ten" for ADR-SB-001..010
silence_treated_as_accept: false
blank_disposition_treated_as_accept: false
sb_dec_026_adjudication.operator_choice: A_LEAVE_UNLINKED
```

This notice does **not** allege fabrication, and none was found. `UNKNOWN` marks the limit of
externally verifiable evidence. Nothing in this notice depends on the election being verified:
the conflict below is resolved by authority ordering (the later DEFER controls) regardless.

## Why it nevertheless conflicts

Two things are simultaneously true, and they contradict:

| Track | Operator instruction | Result |
|---|---|---|
| Concurrent session (~01:07Z) | "ACCEPT all ten"; SB-DEC-026 `A_LEAVE_UNLINKED` | ten ADRs accepted and committed locally |
| **This session (~01:10Z, later)** | "DEFER ADR DISPOSITIONS PENDING AC#2 CLARIFICATION… Keep all ten ADRs PROPOSED/CANDIDATE… Do not record ACCEPT, DEFER, or REJECT" | dispositions deferred; AC#2 amendment produced and independently verified |

**The substantive problem, independent of ordering:** the accepted ADR set was accepted against
the **old, ambiguous AC#2**. Verified directly — `adr-sb-001-…md` on that branch contains:

```text
* Machine contracts and denial fixtures parse and cover the decision.
```

That is the exact wording the operator subsequently ruled ambiguous and directed be replaced,
on the grounds that it "requires denial fixtures that do not yet exist." The acceptance
therefore rests on an acceptance condition the operator has since ruled unfit as written.

## Current authoritative state is unaffected

```text
origin/main:                    cfa4927a883b469c06f37343c18e6582f23d1443 (unmoved)
ADRs on main:                   all ten PROPOSED, document status CANDIDATE
accepted ADR set on main:       ABSENT
branch pushed:                  NO
PR open:                        NO
```

Nothing has landed. The conflict is entirely recoverable and no authority has actually moved.

## What this session did NOT do

```text
did not modify, delete, rebase, or check out tp/DMX-SB-ADR-ACCEPTANCE-001
did not touch /Users/hue/code/.worktrees/DMX-SB-ADR-ACCEPTANCE-001
did not push anything
did not open, close, or comment on any PR
did not record any ADR disposition
did not land the AC#2 amendment
```

## Operator resolution — OPTION 1 (recorded)

The operator selected **Option 1: honour the later defer**. `19fa74faa9` is classified
`SUPERSEDED_PRE_AMENDMENT_ACCEPTANCE_ATTEMPT`, preserved untouched as historical evidence,
and not pushed, merged, or rebased. The replacement acceptance chain is rebuilt from the
amended candidate with fresh operator dispositions. Full lineage: `SUPERSESSION_LINEAGE.md`.

## Options as originally presented (retained for the record)

1. **Honour the later DEFER (recommended).** Land the AC#2 amendment first, then re-disposition
   the ten ADRs against the amended condition, and rebuild or rebase the accepted set on top.
   The concurrent branch's ADR bodies would need their AC#2 bullet updated to match; everything
   else in it may be salvageable.
2. **Honour the earlier ACCEPT.** Treat the concurrent branch as authoritative, discard the AC#2
   amendment, and accept that the ten ADRs carry an acceptance condition the operator has
   called ambiguous.
3. **Merge the tracks.** Apply the AC#2 amendment to the ten accepted ADR files on the
   concurrent branch, keep the operator's existing "ACCEPT all ten" election, and re-verify the
   combined result independently before landing.

Option 3 preserves both the locally-observed operator election and the amendment, at the cost of
one re-verification pass. Option 1 is cleanest on authority ordering. This facilitator has no
authority to choose between them.

> **Resolved:** the operator selected **Option 1 — honour the later DEFER**. See
> `SUPERSESSION_LINEAGE.md`. Note that Options 2 and 3 would each have required relying on an
> election whose provenance is now recorded as `UNKNOWN` (unverifiable off-machine); Option 1
> does not.
