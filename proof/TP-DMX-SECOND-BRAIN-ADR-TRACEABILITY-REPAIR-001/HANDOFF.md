# HANDOFF — TP-DMX-SECOND-BRAIN-ADR-TRACEABILITY-REPAIR-001

## What this packet did

Resolved FO-01, the ADR-to-decision traceability defect carried forward by the
Second Brain architecture ratification. It repaired **references only**.

```text
FO-01 traceability defect:  REPAIRED_AND_INDEPENDENTLY_REVERIFIED
ADR gate eligibility:       YES
ADR acceptance:             NO
```

## Root cause

The frozen `24_ADR_CANDIDATES.md` reference lists form an exact partition of
`SB-DEC-001..030` — each decision cited exactly once, in contiguous blocks
(ADR-SB-001 got 001-002, ADR-SB-002 got 003-005, ADR-SB-003 got 015-017, and so
on), with SB-DEC-031/032 left over. That is the signature of consecutive
allocation, not semantic mapping. Some blocks landed correctly by coincidence;
most did not. FO-01 named five defective ADRs; the defect class was systemic.

## What changed

```text
ADRs inspected:                      10/10
ADRs correct as written:              2  (ADR-SB-001, ADR-SB-005)
ADRs repaired:                        8
  known FO-01 defective:              5  (ADR-SB-003, -006, -007, -009, -010)
  additional found by full sweep:     3  (ADR-SB-002, -004, -008)
decision-reference line changes:     28
non-reference lines:                332  byte-identical to the frozen source
```

Repaired reference sets:

```text
ADR-SB-001  001, 002, 027                unchanged
ADR-SB-002  003, 004, 005, 006           -029 +006
ADR-SB-003  016, 017                     -015
ADR-SB-004  010, 011, 012                -013 -014 -030 +010
ADR-SB-005  018, 019                     unchanged
ADR-SB-006  014, 015                     -020 -021 -022 +014 +015
ADR-SB-007  019, 029                     -023 +019 +029
ADR-SB-008  006, 007, 008, 030           +008 +030
ADR-SB-009  009, 013, 022, 024           -008 -010 -028 +013 +022 +024
ADR-SB-010  020, 021                     -024 -025 -026 +020 +021
```

`SB-DEC-022` into ADR-SB-009 is the one repair beyond the ratification
finding's expected baseline. It is disclosed rather than folded in silently: the
ADR's own decision text requires "current service capability receipts for
authority operations" and "wrong-project denial", both verbatim in SB-DEC-022,
which the baseline's removals would otherwise have orphaned. The independent
auditor judged it JUSTIFIED.

## Unlinked decisions (deliberate, not coverage failure)

```text
SB-DEC-023  deployment topology constraint
SB-DEC-025  v1 scope control
SB-DEC-026  DCP integration boundary — adjacency to ADR-SB-001 recorded AMBIGUOUS
SB-DEC-028  cross-cutting receipts discipline
SB-DEC-031  cross-cutting claims discipline (NOT_RUN)
SB-DEC-032  historical evidence observation
```

No ADR was created and none was broadened to manufacture coverage. Traceability
quality means every ADR cites the correct decisions, not that every decision has
an ADR.

## Independent verification

```text
runner:        OpenCode CLI 1.18.14
model:         openrouter/moonshotai/kimi-k3, variant max
session:       fresh, separate process, separate clone, no producer history
audited head:  25b50f019765263d1abf21fd5bc3ae9c6e522c7a
verdict:       PASS_FO01_TRACEABILITY_REPAIR_WITH_NONBLOCKING_OBSERVATIONS
blockers:      0
must-fix:      0
observations:  3
```

The auditor derived its own traceability matrix from the register bytes and
matched the producer's 10/10.

## What this packet did NOT do

```text
modify the R2 ZIP:                      NO (94b735c7... unchanged)
modify ratification source records:     NO
change any SB-DEC disposition:          NO (32 ACCEPT / 0 DEFER / 0 REJECT intact)
change ADR substantive text:            NO
accept any ADR:                         NO (all 10 remain PROPOSED)
write into docs/90-adr/:                NO
create implementation code:             NO
mutate runtime, services, DB, creds:    NO
merge:                                  NOT AUTHORIZED
```

## Still unproven

```text
runtime conformance:       NOT_RUN
retrieval benchmarks:      NOT_RUN
purge completeness:        NOT_RUN
multi-project isolation:   NOT_RUN
split-brain proof:         NOT_RUN
encryption implementation: ABSENT
```

This repair proves none of these.

## Next

After operator merge, run `TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001`: fresh
MA-08, bind the repaired candidate head and `FO01_RESOLUTION_RECEIPT.json`,
review each ADR individually with ACCEPT / DEFER / REJECT, and persist only
accepted ADRs into the canonical ADR surface. The acceptance gate should
consciously confirm the SB-DEC-023 and SB-DEC-026 unlinked dispositions rather
than inherit them.

`TP-DMX-SECOND-BRAIN-IMPLEMENTATION-PLANNING-001` may proceed in parallel;
implementation execution remains forbidden until separately authorized.
