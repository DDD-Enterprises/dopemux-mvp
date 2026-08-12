# HANDOFF — TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001

## What this packet did

Amended acceptance condition #2 requires that "machine contracts required by this
ADR MUST parse and cover the decision at ADR acceptance." Nothing in the
repository could satisfy that. Every type the ADRs name by hand — `LocalSpoolPort`,
`CustodyPort`, `OpenLoopCandidate`, `TaskProposal`, `TaskPromotionRequest`, the
project identity envelope, the service capability receipt — existed only as prose.
`schemas/second_brain/` did not exist at all. That is why the operator's standing
disposition was 10× DEFER.

This packet builds the missing evidence and nothing else. It accepts no ADR.

## Status: BLOCKED_INDEPENDENT_AUDIT — do not merge

The independent audit of frozen head `7955ef33d7` returned **FAIL, 3 blockers,
5 must-fix**. Packet §19 requires PASS with zero of each, so publication does not
progress. PR #1227 stays a **draft** and is not marked ready.

**The operator is not being asked for a merge decision.** They are being asked to
direct remediation. The artifacts below are real and the mechanical gates are green,
but the audit found the evidence is not yet sufficient to carry ADR acceptance.

The producer independently re-verified all three blockers from repository bytes and
**disputes none of them**.

## Structure of the evidence

Two layers under `schemas/second_brain/contracts/`:

- **Layer A** — `ADR-SB-001..010.contract.json`, each validated by
  `adr-machine-contract.schema.json`. 97 decision clauses total, each one a
  structured machine rule: `subject`, `rule_type`, `operator`, `machine_value`,
  plus the verbatim candidate fragments it derives from and their hash.
- **Layer B** — typed artifacts for the seven types the ADRs name directly. Ports
  use `interface-contract.schema.json`; data contracts are JSON Schema draft-07.

`ADR_CONTRACT_COVERAGE.json` maps all 97 clauses to the rules expressing them:
**97/97 COVERED, MISSING=0, AMBIGUOUS=0**, and `NOT_APPLICABLE_PROVEN` used zero
times — no clause was excused.

## Why the coverage number is trustworthy

A coverage matrix that scores itself is worthless. Three things make this one hard
to fake:

1. **The denominator is frozen in an earlier commit.** `ADR_CLAUSE_INVENTORY.json`
   (97 clauses, sha256 `f073ca28…`) was committed at `a9397e5630` — a commit that
   contains no file under `schemas/second_brain/`. Git history proves the freeze
   preceded authoring; a hash recorded alongside the contracts would prove nothing.
2. **The denominator is anchored to text nobody here wrote.** Every clause cites
   exact substrings of the ratified candidate `e4b28946…`, and the validator
   re-checks that each fragment is genuinely a substring and that its hash
   recomputes. A clause cannot cite decision text the architecture does not contain.
3. **The validator is proven to reject, not just to accept.** 46 tests execute the
   real validator against mutated repository copies. Each asserts the specific
   guard responsible fires — not merely that something failed, which would let an
   unrelated check take the credit while the intended guard sits dead.

## The part worth reviewing most carefully

Structural validation alone green-lights a contract with the right shape and the
wrong content. So the validator hard-pins the values that carry the architecture
decision: restricted spooling stays disabled until verified encryption,
`OpenLoopCandidate` is `additionalProperties: false` with no PM-semantic property,
`TaskPromotionRequest.enabled` is `const: false`, unknown policy eligibility
denies, wrong-project writes deny, the visible queue maximum is exactly 7.

The adversarial tests for these apply the mutation **consistently across the
inventory and the contract**, so cross-file agreement still holds and only the
semantic invariant can catch it. That is the real false-green attempt, and it is
what those hard-coded invariants exist for.

## FO-01

Two records on `main` disagreed about whether FO-01 still blocked ADR acceptance.
`fo-01-repair-status.json` said repair complete *pending* independent
verification, with `performed: false`. `FO01_RESOLUTION_RECEIPT.json` — written
later, after the audit — said repaired *and independently re-verified*, gate
eligible. The stale copy lives in the authority tree, so it surfaces first and
reads as "never verified". **The finding is the disagreement, not an absence of
verification.** The receipt is later and supersedes; the status record now mirrors
it, using only receipt-derived values.

One trap handled explicitly: `gates.adr_acceptance: "CLOSED"` means the acceptance
gate is *shut*, while "FO-01 gate condition = CLOSED" means the *blocker* is
closed — opposite senses of one word. Neither field was overloaded. Eligibility
went into separately named keys and the distinction is recorded in
`gate_field_semantics` inside the file. `adr_acceptance_authorized` remains
`false`.

## What is still NOT true after this merges

Contract coverage is architecture-time evidence. It licenses nothing downstream:

```text
denial fixtures            NOT_IMPLEMENTED   (implementation-time gate)
runtime conformance        NOT_RUN
retrieval benchmarks       NOT_RUN
purge completeness         NOT_RUN
multi-project isolation    NOT_RUN
split-brain proof          NOT_RUN
encryption implementation  ABSENT
```

Therefore still unauthorized: runtime or production enablement, Slice 0
implementation, automatic capture, task promotion, real Dom data, multi-project
background capture, and confidential/restricted spooling.

## The audit findings, and what each actually requires

**BLOCKER 1 — the coverage PASS can survive silent architecture rewrites.**
Editing the inventory *and* the contract consistently changes an ADR decision while
the validator still exits 0. Confirmed on ~75 of 97 clauses. Demonstrated: recall
fusion inverted to the explicitly rejected vector-first order; the review default
flipped from DEFER/NO-MUTATION to auto-apply.

*Class-level remedy* (one change, not per-finding): **const-pin the frozen inventory
sha256 `f073ca28…` inside the validator.** Any post-freeze inventory edit then fails
regardless of coverage-matrix agreement, and because A09 already requires
contract ≡ inventory, editing the contract alone fails too. That closes the whole
bilateral class rather than narrowing it, and puts the freeze on the same trust
boundary as the validator itself. A21 becomes defence in depth.

**BLOCKER 2 — `dopeTask` is an invented canonical authority.** `grep -c dopeTask`
against the candidate returns **0**. It came from this task packet's own
architecture-boundary list, not from the ratified candidate. Remedy: remove it from
`AUTHORITY_TARGETS`, `authority_targets_permitted`, and the two `AUTHORITY_TARGET/IN`
clause values, then regenerate.

**BLOCKER 3 — A21's enum grounding is one-way.** It rejects *widening* (a new member
is absent from the cited text) but accepts *shrinking*: dropping `PURGE` from the
deletion-operation set and `Review` from the UX operation set both still pass.
Remedy: make the membership test bidirectional against the enumerated terms in the
cited fragment.

**MUST_FIX 1 — denominator gaps.** The 97 clauses were derived from the packet's §5
list, which §5 itself calls a *minimum*. The auditor names material decision content
with no clause: the ADR-SB-004 policy-evaluation *dimensions* (identity, grants,
provider, embedding, custody, backup, operation — only the stage ordering was
captured); the ADR-SB-007 purge *completion receipt*; "ConPort never owns task state"
and the Dope-Memory PM-authority forbid (ADR-SB-008); "historical and current states
remain distinct" (ADR-SB-003); open/close/cancel event kinds (ADR-SB-008). This
requires expanding and **re-freezing** the denominator — a governance act, not a
patch, and the reason this cannot be quietly fixed in place.

**MUST_FIX 2–4 — invented surface and token-label rules.** The port `operations`
lists, several schema property/enum sets, and the four-way fusion ranking assert
structure the candidate never states; and many `REQUIRE/MUST_EXIST` rules name an
artifact class without giving it a shape. Remedy: either delete the invention or
justify each against an exact clause, and give the named artifacts real structure.

**MUST_FIX 5 — FO-01 Group B is partial.** Several status fields
(`nonblocking_observations`, `authority.architecture_accepted_as_law`, the expanded
coverage metrics) can diverge from the receipt while Group B still passes.

## Recommended sequence

1. **Operator directs remediation scope.** In particular: whether the denominator is
   re-frozen to include the MUST_FIX 1 content, since that supersedes the freeze
   recorded at `a9397e5630` and is the one decision the producer should not take
   alone.
2. Apply the **class-level** fixes in one pass — inventory const-pin, `dopeTask`
   removal, bidirectional enum grounding, denominator expansion, invented-surface
   removal, Group B field locking. Per-finding patching is what has historically kept
   these review carousels turning; the A21 experience in this very packet shows a
   narrowed class comes back.
3. Re-freeze a new content head and run **one** fresh independent audit.
4. Only then Human Gate A.

Phase B (post-merge MA-08, fresh acceptance-integrity audit, operator worksheet) is
unreachable from here and is not started. Opening a PR does not begin it.

Prior DEFER dispositions stand. Only the operator fills ACCEPT / DEFER / REJECT.
