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

## Round 2 — what the operator authorized and what was done

Round 1 ended at `BLOCKED_INDEPENDENT_AUDIT`: the independent audit of frozen head
`7955ef33d7` returned **FAIL, 3 blockers, 5 must-fix**. The producer re-verified
all three blockers from repository bytes and disputed none.

On 2026-08-12 the operator authorized a **denominator re-freeze and a
class-level repair of the whole finding set in one wave**, and required a fresh
independent audit returning PASS with zero blockers and zero must-fix before this
can reach a merge decision. That ruling is reproduced verbatim inside
`DENOMINATOR_REFREEZE_RECEIPT.json`, because the validator now pins the frozen
denominator's hash and that pin claims an authorization an auditor must be able
to read from the repository.

### The re-freeze

The superseded denominator declared its authority to be
`TASK_PACKET_SECTION_5_MANDATORY_COVERAGE`. That is the root cause of two
findings at once: §5 calls itself a *minimum*, so the denominator was incomplete
(MUST_FIX 1); and because the packet's own boundary list was being read as
architecture, `dopeTask` — a string that appears **nowhere** in the candidate —
became a canonical authority value (BLOCKER 2).

The replacement denominator comes from a fresh sentence-by-sentence census of the
candidate under the operator's INCLUDE / DO-NOT-INCLUDE rule. **160 clauses: 63
added, 86 modified, 11 unchanged, 0 removed.** Every normative unit of the
document is disposed of in `DENOMINATOR_CENSUS_WORKSHEET.json` — mapped to clause
IDs, or excluded with the operator's own reason quoted. Judgment calls are
recorded there by name so the auditor can attack them directly instead of
reconstructing them.

`removed_clause_ids` is empty because every superseded requirement still has a
home. The invented content was removed at *value* level and each such change is
recorded with its prior and current value in `modified_clauses` — the four-way
recall ordering, the `dopeTask` member, `CURRENT_DIRECTORY` (grounded only in a
rejected alternative), and `classification` where the candidate says `class`.

The re-freeze is its own commit containing no contract file and no validator
change, so git history proves the denominator preceded the contracts written
against it. The old freeze at `a9397e5630` stays in history and is **not**
described as valid in hindsight.

### The repairs

| Finding | Class-level repair |
|---|---|
| **B1** bilateral-edit false-green | The frozen inventory sha256 is const-pinned in the validator (A09). Any post-freeze clause edit fails, and since every contract rule must equal its inventory clause (A22), editing both sides consistently fails too — including for booleans, which have no text to check. |
| **B2** invented `dopeTask` authority | Removed. Authority values must appear verbatim in the cited candidate text (A26); a named regression guard (A27) restates it across the clause set and every contract file. |
| **B3** one-way set grounding | Closed sets are compared against the deterministic tokenization of a verbatim `source_enumeration` (A26). Shrinking now fails exactly as widening does. |
| **MF1** denominator gaps | Re-frozen under operator authorization. All six omissions the auditor named by hand are present and are checked **by name** at generation time. |
| **MF2** invented typed surface | Port operation catalogues deleted; invented properties, enums and lifecycle states deleted. Every remaining property name, enum member and const string is bound in `x-grounding` to a clause and a verbatim candidate phrase, recomputed by A31/A32. |
| **MF3** invented recall ordering | The four-way ranking is gone. `authority_first` is a boolean; the four recall source classes are a closed set; no relative order is asserted among chronology, source-native state and advisory retrieval. |
| **MF4** label-only pseudo-contracts | The taxonomy no longer has a shape that can carry an opaque label. `REQUIRE/MUST_EXIST` token rules became boolean predicates on precise subjects, and A25 rejects any other shape. |
| **MF5** FO-01 partial receipt lock | Group B computes the full expected projection from the receipt and compares all 39 mapped fields, pins the 37 that are not receipt-derived, requires the traceability matrix rather than skipping when absent, and fails on any status leaf that is not classified. |

Two repairs were not on the auditor's list and came out of the census:

- **Fragment provenance (A23).** "Vector-first answer generation" is verbatim
  candidate text, so before this a clause could have cited a *rejected* design as
  its own grounding. Every fragment must now fall inside its own ADR's Context /
  Proposed decision / Consequences span.
- **Naming honesty.** `ProjectIdentityEnvelope` and `ServiceCapabilityReceipt` are
  this repository's names for things the candidate describes but never names, so
  they are no longer stated as named-type requirements. The two schema files say
  so in the file.

## Structure of the evidence

Two layers under `schemas/second_brain/contracts/`:

- **Layer A** — `ADR-SB-001..010.contract.json`, each validated by
  `adr-machine-contract.schema.json`. 160 decision clauses, each a structured
  machine rule: `subject`, `rule_type`, `operator`, `machine_value`, the section
  it comes from, the verbatim candidate fragments it derives from, and their hash.
- **Layer B** — typed artifacts for the seven types the ADRs name directly. Ports
  use `interface-contract.schema.json`; data contracts are JSON Schema draft-07.

`ADR_CONTRACT_COVERAGE.json` maps all 160 clauses to the rules expressing them:
**160/160 COVERED, MISSING=0, AMBIGUOUS=0**, with `NOT_APPLICABLE_PROVEN` used
zero times — no clause was excused.

## Why the coverage number is trustworthy

A coverage matrix that scores itself is worthless. Four things make this one hard
to fake:

1. **The denominator is frozen in an earlier commit and pinned in the validator.**
   Git history proves the ordering; the pin makes a later edit fail.
2. **The denominator is anchored to text nobody here wrote.** Every clause cites
   exact substrings of the ratified candidate, inside its own ADR's normative
   sections, and the validator re-checks both the substring and the hash.
3. **Every non-boolean value must appear in the text it cites**, and closed sets
   must equal their source enumeration exactly in both directions.
4. **The validator is proven to reject.** 63 tests execute the real validator
   against mutated repository copies, each asserting the specific guard responsible
   fires. Roughly half of them additionally re-pin the validator and the
   supersession receipt to the mutated state, so the freeze hash cannot take credit
   for a semantic guard's work.

## The false-green matrix

`FALSE_GREEN_MATRIX.json` records the ten mutations the operator required to be
proven to fail, each with the guard its test requires to fire. **All ten failed as
intended.** Two rows are loops rather than samples: row 9 removes *each* of the 63
clauses the re-freeze added, one at a time; row 10 drifts *each* of the 39
receipt-derived FO-01 fields. Neither is truncated.

The row worth reading is the one that is honest about a limit: with the pin also
rewritten, removing a denominator clause is caught by the coverage matrix and by a
semantic pin if one covers that clause — but denominator *completeness* is held by
the freeze and by independent audit, not by a checker. No amount of validation
proves a decision the census never wrote down.

## FO-01

Two records on `main` disagreed about whether FO-01 still blocked ADR acceptance.
`fo-01-repair-status.json` said repair complete *pending* independent
verification, with `performed: false`. `FO01_RESOLUTION_RECEIPT.json` — written
later, after the audit — said repaired *and independently re-verified*, gate
eligible. The stale copy lives in the authority tree, so it surfaces first and
reads as "never verified". **The finding is the disagreement, not an absence of
verification.** The receipt is later and supersedes; the status record mirrors it,
using only receipt-derived values.

One trap handled explicitly: `gates.adr_acceptance: "CLOSED"` means the acceptance
gate is *shut*, while "FO-01 gate condition = CLOSED" means the *blocker* is
closed — opposite senses of one word. Neither field was overloaded. Eligibility
went into separately named keys and the distinction is recorded in
`gate_field_semantics` inside the file. `adr_acceptance_authorized` remains
`false`.

The status file itself is **unchanged in round 2**. MUST_FIX 5 was about the
strength of the check, not the content of the record.

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

## The embedded-audit gate — was red for representation, now resolved

For rounds 1 and 2 the embedded-audit gate failed for one cause, and not an
evidentiary one: `schemas/proof/embedded_audit.schema.json` was strictly binary —
`SKIPPED` forces `auditor_tool: "none"` / `auditor_model: "unknown"`, and any other
status forbids both — and its enums could not name the auditor that actually ran.
Claiming `SKIPPED` would have hidden a real audit; picking an enum tool would have
fabricated an auditor identity. Packet §19 forbids the second and §1 put
embedded-audit platform repair out of lane, so the gate was left failing and the
representation gap recorded in the open. A PASS from the independent audit did not
turn it green, because it never failed for want of evidence.

**Resolved 2026-08-12 by `f0a0e839b4` (PR #1228,
`TP-DMX-EMBEDDED-AUDIT-GROK-ROUTE-001`)**, a separate packet on trusted `main` under
operator ruling `TAKE_OPTION_B`. It admits `grok-cli` / `grok-4.5`, bound fail-closed
in both directions. The trusted schema is read from the trusted ref, never from a PR
branch, which is why this could not have been fixed here.

Two things did **not** happen as a result. No audit was re-run, and no verdict
changed — only the vocabulary available to describe the auditor changed. And the
audited contract corpus did not move: of the exact 36 paths in C1 commit
`6e1b4472ba`, the **31-file contract corpus** is byte-identical to that head, verified by
per-file blob hash against `6e1b4472ba` (not by reading a branch diff — a same-path change
arriving from `main` would not appear in a branch diff at all). The other 5 are post-C1
attestation paths under this proof directory, already allowed to evolve by the post-C1
mutation boundary. See `R2_AUDITED_BYTES_HASH_RECHECK.json`.

The round-2 auditor model, honestly recorded at the time as `UNKNOWN_TO_PRODUCER`,
was recovered from the runner's own per-session metadata as **`grok-4.5`** — the
completed run and its killed precursor agree, and the timestamps corroborate the
custody record's account of a killed first attempt. That is
`RUNNER_SESSION_METADATA_VERIFIED`, not provider attestation, and it is written down
that way. See `R2_AUDITOR_IDENTITY_RECONCILIATION.json`.

The historical invocation is preserved exactly and was **not** rewritten to add
`-m grok-4.5`. It never contained a model flag. The invocation records what was
executed; the session metadata records what served it. Merging the two would turn a
true identity repair into fabricated execution history. (Future Grok audits must pin
`-m grok-4.5`, because the runner default has since moved to `grok-4.6`.)

`AUDIT_PROMPT_CUSTODY_R2.json` and `AUDITOR_REPAIR_2_REPORT.md` are untouched.
Reconciliation adds a record; it does not revise one.

## Status: READY_FOR_OPERATOR_CONTRACT_EVIDENCE_MERGE_DECISION

The round-2 independent audit of frozen head `6e1b4472ba` returned **PASS, 0
blockers, 0 must-fix**, which is the bar the operator set. It ran in a fresh
read-only session in a throwaway detached worktree, with no producer
conversation history, and it verified the freeze chain, the census, the closed
sets, the Layer B grounding and the FO-01 lock from bytes and commands rather
than from this document.

Two residual observations were raised, neither a must-fix, both confirmed by the
producer and recorded in `AUDIT_R2_RESIDUALS.json`:

- The census worksheet labels 25 clauses `UNCHANGED` that the computed
  supersession record lists as modified. All 25 are rule-type renames under the
  new taxonomy with byte-identical machine values; the receipt is authoritative.
  Not corrected in place, because editing audited content after the audit is the
  recursion the post-C1 boundary exists to prevent.
- With the validator's own pin and the supersession receipt both rewritten,
  clause booleans that no Group S pin covers can be flipped while the validator
  exits 0. This is the limit written into the validator header before the audit
  ran. A consistent bilateral edit with the pin left alone still fails — that is
  the false-green round 1 found, and it is closed.

**This is not a merge.** It is the point at which the operator has a merge
decision to make. Merge remains OPERATOR_ONLY, the PR stays a draft, and no ADR
disposition changes.

The embedded-audit representation gap that kept two gates red through rounds 1 and 2
is resolved on trusted `main`; see the section above. The audited bytes are unchanged.

## What the operator is being asked for

A merge decision on the contract evidence, and nothing else. Merging this does
not accept an ADR, does not authorize implementation, and does not open the
acceptance gate — the other acceptance conditions are still outstanding and
`adr_acceptance_authorized` remains `false`.

Phase B (post-merge MA-08, fresh acceptance-integrity audit, operator worksheet) is
not started and does not begin by merging.

Prior DEFER dispositions stand. Only the operator fills ACCEPT / DEFER / REJECT.
