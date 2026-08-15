# HANDOFF — TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001

```text
HUMAN_GATE               = PASSED
ADR-SB-001..010          = ACCEPTED_BY_OPERATOR, 2026-08-14
ARCHITECTURE_ACCEPTANCE  = PERSISTED
INDEPENDENT_AUDIT        = PASS, BLOCKERS 0, MUST_FIX 0
IMPLEMENTATION           = NOT_AUTHORIZED
```

## What landed

Ten accepted architecture decision records under `docs/90-adr/adr-sb-001..010-*.md`, ten
index rows, an acceptance head, an operator decision ledger, an acceptance binding, an
acceptance receipt, and a derived staleness declaration.

The persistence is **additive**. The merged validator hard-enforces "no ADR is accepted" in
six places, so nothing it reads was touched: the candidate document is byte-identical and
still `CANDIDATE`, and the FO-01 records, the machine contracts and the validator itself are
untouched. It reports 94 checks / 0 failed before and after.

The ten records are **generated** from the amended candidate bytes by a committed
fail-closed generator. Nothing is salvaged from the superseded attempt at `19fa74faa9`,
whose files carry the pre-amendment AC#2 — the substantive ground on which the operator
superseded them. Every decision section is a verified byte-slice of the candidate.

## The finding worth reading

Audit round 1 returned `MUST_FIX 1`: the staleness declaration named three stale FO-01
fields and presented that list as complete. It was not. That is the defect class this
programme exists to prevent, and it was mine.

The repair was structural rather than "add the two the auditor named":

- A first attempt enumerated the validator's `PINNED` table instead of hand-listing — and
  still missed `still_forbidden`, which lives in `NARRATIVE_PREFIXES`. Enumerating one
  collection inside the validator is not the same as enumerating the universe.
- The declaration is now derived over **all 103 leaves of the status record**, with two
  fail-closed rules: every leaf must be classified, and a leaf whose path or value mentions
  acceptance may not be covered by a category default.

That second rule found **two more stale fields the auditor also missed** — the
`gate_field_semantics` glosses for `gates.adr_acceptance` and `adr_acceptance_authorized`.
They carry no machine-checkable assertion, so nothing flagged them, but in words they assert
the gate is shut and authorization is still false.

Final count: **seven**, not three. Round 2 re-derived the set independently, matched seven,
and found no eighth.

## What is now stale, and deliberately left so

Seven fields in `fo-01-repair-status.json` describe a world that has changed. They are
enumerated with individual reasons in `FO01_STALENESS_DECLARATION.json`.

They are not fixed here because they structurally cannot be: the status file must remain an
exact whole projection of a historical receipt belonging to another packet, and every stale
field is validator-pinned or B-group-asserted. Reconciling them means changing the validator
invariant from "no ADR is accepted" to "acceptance matches the operator ledger" — a separate
packet with its own independent audit. **Not authorized.**

## State

```text
branch   tp/DMX-SB-ADR-ACCEPTANCE-002   (LOCAL ONLY)
tip      see git log; audited content head 0defe1cab46a9e6d02e88d3aa94a9edf195b4b84
pushed   NO      PR   NONE      merged   NO
```

## Still closed

```text
IMPLEMENTATION_EXECUTION   NOT_AUTHORIZED
SLICE_0                    NOT_AUTHORIZED
RUNTIME_ENABLEMENT         NOT_AUTHORIZED
RUNTIME_MUTATION           FORBIDDEN
DENIAL_FIXTURES            NOT_IMPLEMENTED
PUSH / PR / MERGE          NOT_AUTHORIZED

runtime conformance / retrieval benchmarks / purge completeness /
multi-project isolation / split-brain proof            ALL NOT_RUN
encryption implementation                              ABSENT
```

The 32 ratified SB-DEC decisions are untouched (32 ACCEPT / 0 DEFER / 0 REJECT) and
SB-DEC-026 remains `A_LEAVE_UNLINKED`.

## Carried forward

```text
ADR-SB-009 re-gate     the ConPort project wall is directionally aligned but establishes
                       no registry-backed identity; any slice must re-gate against what it
                       actually guarantees
typed artifacts        acceptance-time evidence that the named types exist and are grounded;
                       NOT implementation-ready interfaces
denial-fixture scope   not enumerated per ADR; cheaper to pin before implementation
fo-01 reconciliation   seven stale fields; needs a validator change and its own audit
```
