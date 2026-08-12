# Supersession Lineage — pre-amendment ADR acceptance attempt

```text
classification: SUPERSEDED_PRE_AMENDMENT_ACCEPTANCE_ATTEMPT
authority:      HUMAN_OPERATOR_EXPLICIT
resolution:     CONFLICT RESOLUTION — OPTION 1, HONOUR THE LATER DEFER
```

## The superseded artifact

```text
commit:    19fa74faa9  "docs(second-brain): accept adjudicated ADR set"
branch:    tp/DMX-SB-ADR-ACCEPTANCE-001
worktree:  /Users/hue/code/.worktrees/DMX-SB-ADR-ACCEPTANCE-001
committed: 2026-08-10T01:07:06Z
scope:     20 files, +2112 lines — ten ADRs at docs/90-adr/adr-sb-001..010-*.md
           carrying **Status:** `ACCEPTED`, plus an acceptance ledger, binding, and receipt
state:     UNPUSHED · NO PR · NOT ON MAIN
```

## Why it is superseded — and what is *not* being alleged

Its operator provenance is recorded as **`UNKNOWN`** — downgraded from `GENUINE` on operator
direction after PR #1214 review.

```text
operator_provenance: UNKNOWN
```

The reason is evidentiary reach, not suspicion. Everything below was read from the producer's
local worktree, and commit `19fa74faa9` is unpushed — so `git cat-file -t 19fa74faa9…` fails in
any other checkout, and no consumer of this repository can inspect the ledger or verify these
observations independently. They are therefore recorded as **producer-machine observations,
off-machine-unverifiable**, not as established fact:

```text
06_ADR_OPERATOR_DECISION_LEDGER.yaml   (observed locally; not externally verifiable)
  authority:                            HUMAN_OPERATOR
  facilitator_authored_dispositions:    false
  silence_treated_as_accept:            false
  operator election:                    "ACCEPT all ten" for ADR-SB-001..010
  sb_dec_026_adjudication.operator_choice: A_LEAVE_UNLINKED
committed: 2026-08-10T01:07:06Z         (observed locally; not externally verifiable)
```

The claim was downgraded rather than substantiated because the operator directed that the
superseded commit not be pushed or otherwise promoted; publishing durable archival evidence was
the only alternative remedy and it is foreclosed by that directive.

**No fabrication is alleged, and none was found.** `UNKNOWN` marks the limit of externally
verifiable evidence — it is not an accusation, and it does not downgrade the *classification*
below, which is unaffected.

It is superseded on a **substantive** ground, not a procedural one: those ten dispositions were
made against the **pre-amendment AC#2** —

```text
* Machine contracts and denial fixtures parse and cover the decision.
```

— which the operator subsequently ruled ambiguous as written, on the basis that it requires
denial fixtures that do not yet exist (R2 ships none; they are Slice 0 / `S0-C` output). The
operator then directed, later in time, that ADR dispositions be deferred until AC#2 was
clarified and independently reverified.

```text
2026-08-10T01:07:06Z   pre-amendment acceptance committed (operator elected ACCEPT all ten)
2026-08-10T01:10Z-ish  operator directs: DEFER ADR DISPOSITIONS PENDING AC#2 CLARIFICATION
2026-08-10T01:15:44Z   AC#2 amendment independently verified (Grok 4.5, PASS)
```

The later directive controls.

## Operator disposition of the superseded artifact

```text
do not push it
do not merge it
do not rebase it
do not otherwise promote it
do not delete it until the replacement acceptance chain is sealed and its lineage records
    why the earlier attempt was superseded  (this document is that record)
preserve commit and worktree as historical evidence
```

Nothing in this change touches `tp/DMX-SB-ADR-ACCEPTANCE-001` or its worktree. They remain
exactly as found.

## What this change does instead

It persists **only** the AC#2 acceptance-condition amendment, as its own narrow authority
change. It accepts no ADR.

```text
all ten ADRs:      remain PROPOSED
document status:   remains CANDIDATE
token ACCEPTED:    absent from the amended candidate
dispositions:      NONE recorded
```

## The replacement chain that must follow

Per operator instruction, the post-amendment acceptance chain is rebuilt from scratch and may
not inherit anything from the superseded attempt:

1. this AC#2 amendment merges to `main`;
2. fresh MA-08 drift check against the resulting merged-main SHA;
3. operator supplies **fresh** explicit ADR-SB-001..010 dispositions against the *amended*
   candidate bytes — the earlier ACCEPT dispositions are **not** inherited, copied, or inferred;
4. acceptance ledger, binding, accepted ADR files, and proof are rebuilt from the amended
   candidate;
5. a fresh independent Grok 4.5 acceptance-integrity audit runs against the exact new
   acceptance content head;
6. only that rebuilt post-amendment chain may become authoritative.

## Preserved dispositions carried forward unchanged

```text
SB-DEC-026:  A_LEAVE_UNLINKED   (operator; unchanged unless the operator explicitly changes it)
R-DELTA-06:  RESOLVED_NONBLOCKING_ROUTE_LABEL_VARIANCE
             scope: TP-DMX-SECOND-BRAIN-IMPLEMENTATION-PLANNING-001 only
```

## Standing gates at the time of this change

```text
implementation planning:              COMPLETE
implementation packet authorization:  NOT YET
implementation execution:             NOT_AUTHORIZED
runtime mutation:                     NONE
runtime conformance:                  NOT_RUN
retrieval benchmarks:                 NOT_RUN
purge completeness:                   NOT_RUN
multi-project isolation:              NOT_RUN
split-brain proof:                    NOT_RUN
encryption implementation:            ABSENT
```
