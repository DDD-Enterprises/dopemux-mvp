You are performing an INDEPENDENT, READ-ONLY ARCHITECTURE-CONTRACT AUDIT. You did not author this work. Do not modify any file. Derive every conclusion from the committed bytes you read yourself.

You are in a git worktree at frozen content head `8a9b0ee53c72062a0a68738082e5a056fad38f27`, base `main` = `6153bd4fb30ed3d038e51b371ad9ebfb4916bfac`.

## Background

The repository has ten Second Brain ADR candidates (ADR-SB-001..010) in
`docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md`
(sha256 `e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c`). All are
status `PROPOSED`; none is accepted. Each carries acceptance condition #2:

> Machine contracts required by this ADR MUST parse and cover the decision at ADR
> acceptance. Required denial fixtures MUST be implemented, executed, and pass
> before the affected implementation capability is authorized for enablement.

Before this change the repository contained NO machine contract for any Second Brain
type; `schemas/second_brain/` did not exist. This change adds architecture-time
contract evidence ONLY. It must NOT implement runtime behaviour, must NOT accept any
ADR, must NOT claim denial fixtures exist, and must NOT invent architecture semantics
the candidate does not state.

## Provenance you may rely on

`proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/ADR_CLAUSE_INVENTORY.json`
(97 clauses) was committed at `a9397e5630577ac5a2b0c8f89ad7d62d8ff7b296`, a commit
containing no file under `schemas/second_brain/`. The contracts were then GENERATED
FROM that frozen inventory, so inventory-to-contract agreement is true by construction
at authoring time. Verify this with `git show --stat a9397e5630` if you wish.

## Files to read

- `docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md`
- `docs/03-reference/architecture/second-brain/adr-candidates/fo-01-repair-status.json`
- `proof/TP-DMX-SECOND-BRAIN-ADR-TRACEABILITY-REPAIR-001/FO01_RESOLUTION_RECEIPT.json`
- `proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/ADR_CLAUSE_INVENTORY.json`
- everything in `schemas/second_brain/contracts/`
- `scripts/governance/validate_second_brain_adr_contracts.py`
- `tests/governance/test_second_brain_adr_contracts.py`

## The eight questions you must answer independently

1. Does every ADR decision have a sufficient machine-contract representation?
2. **Denominator completeness.** Read all ten ADRs' Context / Proposed decision /
   Consequences sections and name any MATERIAL decision content that has NO
   corresponding clause among the 97. Be concrete and specific.
3. Do the contract rules actually CORRESPOND to the ADR decision, or do they merely
   NAME it? A rule that restates a label with no checkable machine value is
   "merely naming".
4. Was any NEW architecture semantic INVENTED that the candidate does not state?
   Check especially the closed `AUTHORITY_TARGETS` set in the validator, the
   LocalSpoolPort/CustodyPort operation lists, the JSON Schema property sets, and any
   enum or const not traceable to candidate text.
5. Are the typed artifacts for ADR-SB-006 (LocalSpoolPort, CustodyPort), ADR-SB-008
   (OpenLoopCandidate, TaskProposal, TaskPromotionRequest) and ADR-SB-009
   (ProjectIdentityEnvelope, ServiceCapabilityReceipt) sufficient to make those ADR
   decisions machine-expressible?
6. **CAN THE VALIDATOR FALSE-GREEN? Attack this hardest.** Try to construct a concrete
   mutation that changes architecture MEANING while the validator still exits 0.
   Consider specifically:
   - `covered_by` self-pointers: most clauses point at their own node in their own
     file. Is coverage circular?
   - the A09 four-field match (subject/rule_type/operator/machine_value): given
     by-construction agreement, does it test anything real?
   - are the hard-coded invariants in `semantic_invariants()` load-bearing or
     decorative?
   - WHICH ARCHITECTURE DECISIONS HAVE NO GROUP-S GUARD, and could therefore be
     silently weakened by editing inventory and contract consistently? Enumerate them.
   - could coverage be satisfied by clauses individually valid but collectively
     missing a decision?
   You may run the validator and the tests read-only to check your reasoning:
   `python3 scripts/governance/validate_second_brain_adr_contracts.py --json`
7. Is the FO-01 reconciliation evidence-correct: does `fo-01-repair-status.json` only
   MIRROR `FO01_RESOLUTION_RECEIPT.json`, or does it OVERSTATE it anywhere?
8. Did any runtime, implementation, or enablement claim leak in?

## Output format

```
VERDICT: PASS | FAIL
BLOCKERS: <count>
<list — a BLOCKER is something that makes the evidence unsound or false>
MUST_FIX: <count>
<list>
NONBLOCKING OBSERVATIONS:
<list>
```

Then your answers to the eight questions, with file and line references.

Be adversarial and specific. A plausible-looking coverage matrix that cannot actually
fail is the exact failure mode under investigation. If the work is sound, say so
plainly — but only after genuinely trying to break it. Do not soften real findings,
and do not invent findings to appear rigorous.
