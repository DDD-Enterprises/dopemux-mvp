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

## What the operator is being asked for

**Nothing yet beyond a merge decision.** This packet stops at Human Gate A. ADR
dispositions are Phase B and remain operator-only.

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

## Next steps in order

1. **Operator merge decision** on this PR (Human Gate A). Squash or rebase only;
   the repository has `delete_branch_on_merge = true`, so if the branch must
   survive, either flip that setting first or re-push the ref immediately after —
   omitting `--delete-branch` is not sufficient.
2. **Phase B**: re-run the validator from clean `main`; run a fresh full-diff
   MA-08 from discovery base `72af781e42e0702d9047946e0f5a250e7dff0fa5` (the
   candidate's own standing baseline, not the ratification snapshot); produce a
   fresh `DRIFT_RECHECK.md`.
3. **Fresh post-merge acceptance-integrity audit** against the exact post-merge
   `main`. Do not reuse the audit in this bundle — it binds this content head.
4. **Fresh operator worksheet**, then `AWAITING_OPERATOR_ADR_DISPOSITIONS`.

Recommendations in that worksheet are advisory. Prior DEFER dispositions are not
auto-converted; only the operator fills ACCEPT / DEFER / REJECT.
