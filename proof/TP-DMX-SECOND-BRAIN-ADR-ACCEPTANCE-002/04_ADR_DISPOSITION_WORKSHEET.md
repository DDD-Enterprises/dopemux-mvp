# 04_ADR_DISPOSITION_WORKSHEET — fresh ten-ADR redisposition

```text
PROGRAM=SECOND_BRAIN
PHASE=POST_MERGE_ACCEPTANCE_READINESS
MA08_MAIN_SHA=75b4cfc581786a53445e412bfc8e25a6e0fdb978
STATUS=READY_FOR_OPERATOR_ADR_REDISPOSITION
```

## How to read this document

Every ADR below has two separate fields, and they are not the same thing:

```text
FACILITATOR_RECOMMENDATION   what this session concluded from the evidence. Advisory. No authority.
OPERATOR_DISPOSITION         PENDING_OPERATOR on every row. Only you fill these in.
```

That separation is deliberate and is the same shape the prior docket used: a recommendation
stated in the disposition field is a facilitator quietly deciding.

**The current dispositions remain 10× DEFER until you replace them.** Nothing in this
packet changes them. `adr_acceptance_authorized` is `false` at
`MA08_MAIN_SHA` and is unchanged by anything here.

## What changed since the DEFER, and what did not

The DEFER was issued because acceptance condition #2, as then written, required denial
fixtures that do not yet exist. Two things have happened since:

1. **AC#2 was clarified** (#1214, on `main`). The amended text separates the acceptance-time
   requirement from the enablement-time one:

   > Machine contracts required by this ADR MUST parse and cover the decision **at ADR
   > acceptance**. Required denial fixtures MUST be implemented, executed, and pass **before
   > the affected implementation capability is authorized for enablement**. Absence of
   > not-yet-implemented denial fixtures does not constitute implementation evidence and
   > does not permit any runtime, production, or enablement claim.

2. **The machine contracts now exist and verify** (#1227, on `main`). That is the evidence
   the first sentence asks for, and it did not exist when the DEFER was issued.

What did **not** change: no runtime, no implementation, no denial fixtures, no enablement.
Accepting an ADR here makes it architecture law. It authorizes nothing to be built.

## Evidence common to all ten

| Acceptance condition | Status at `MA08_MAIN_SHA` | Source |
|---|---|---|
| #1 Independent reviewer confirms alignment with accepted repository authority | **MET** | FO-01 traceability audit; AC#2 amendment audit (grok-4.5, PASS); contract-evidence R2 audit (grok-4.5, PASS 0/0); this phase's audit (grok-4.5, PASS 0/0 at round 2) |
| #2 Machine contracts parse and cover the decision at acceptance | **MET** | validator PASS, 94 checks / 0 failed; 10/10 ADRs; 160/160 clauses; MISSING 0; AMBIGUOUS 0; recomputed independently of the producer's coverage receipt |
| #3 No runtime, implementation, or production claim inferred | **MET** | all ten contracts carry `runtime_claims_permitted: false` and `denial_fixtures: NOT_IMPLEMENTED_IMPLEMENTATION_TIME_GATE`; validator rejects a truthy `accepted` / `implemented` / `*_authorized` key as a class |
| #4 Authority-corpus drift re-adjudicated | **MET** | fresh MA-08 this run: `NO_NEW_MATERIAL_DRIFT` over `72af781e42..75b4cfc581` |

Supporting: adversarial suite 63/63 with every negative test asserting the specific guard
fires; false-green matrix 10/10 `FAILED_AS_INTENDED`; the coverage denominator const-pinned
at `b164fc0b…` and frozen in a commit that touches no contract and no validator.

### One check worth stating, because it is where a producer could have made the bar easy

Seven of the ten ADRs declare `required_artifacts: []`. That is not a convenience: those
seven name no type in their decision text. The three that do name types are exactly the
three carrying required artifacts — ADR-SB-006 (`LocalSpoolPort`, `CustodyPort`),
ADR-SB-008 (`OpenLoopCandidate`, `TaskProposal`, `TaskPromotionRequest`), ADR-SB-009
(identity envelope, service capability receipt). The mapping is 2 / 3 / 2 and it matches
the prose exactly.

---

## ADR-SB-001 — Extension Boundary and Non-Authority

```text
MACHINE CONTRACT   schemas/second_brain/contracts/ADR-SB-001.contract.json
CLAUSES            11 (8 BOOLEAN, 1 ENUM, 1 CONSTANT, 1 NUMERIC)  — 11/11 COVERED
TYPED ARTIFACTS    none required (the decision names no type)
SB-DEC             SB-DEC-001, SB-DEC-002, SB-DEC-027
PARSE / COVERAGE   PASS · MISSING 0 · AMBIGUOUS 0
MA-08              NO_NEW_MATERIAL_DRIFT
AUDIT              PASS · BLOCKERS 0 · MUST_FIX 0
```

Remaining implementation-time requirements: `DENIAL_FIXTURES`, `RUNTIME_CONFORMANCE`,
`RETRIEVAL_BENCHMARKS`, `PURGE_COMPLETENESS`, `MULTI_PROJECT_ISOLATION`,
`SPLIT_BRAIN_PROOF`, `ENCRYPTION_IMPLEMENTATION` — the standard seven carried by every ADR.

ADR-specific note: SB-DEC-026 ("DCP integration is read-first") was adjudicated by you as
`A_LEAVE_UNLINKED`, and that posture is preserved — it is linked to no ADR and appears in
no contract. That ruling explicitly recorded ADR-SB-001 as eligible for adjudication with
no further traceability amendment required.

```text
FACILITATOR_RECOMMENDATION: RECOMMEND_ACCEPT
OPERATOR_DISPOSITION:       PENDING_OPERATOR
OPERATOR_NOTE:
```

## ADR-SB-002 — Capture, Candidate, Review, and Promotion

```text
MACHINE CONTRACT   ADR-SB-002.contract.json
CLAUSES            14 (10 BOOLEAN, 3 AUTHORITY_TARGET, 1 CONSTANT) — 14/14 COVERED
TYPED ARTIFACTS    none required
SB-DEC             SB-DEC-003, SB-DEC-004, SB-DEC-005, SB-DEC-006
PARSE / COVERAGE   PASS · MISSING 0 · AMBIGUOUS 0
MA-08              NO_NEW_MATERIAL_DRIFT
AUDIT              PASS · BLOCKERS 0 · MUST_FIX 0
```

Remaining implementation-time requirements: the standard seven.

ADR-specific note: three clauses are `AUTHORITY_TARGET` — the shapes that say *where* a
canonical write goes. The validator's `NEVER_AUTHORITY` guard makes it unexpressible for
`second_brain` or `dope-context` to appear as an authority target, so the non-authority
posture is enforced structurally rather than by review.

```text
FACILITATOR_RECOMMENDATION: RECOMMEND_ACCEPT
OPERATOR_DISPOSITION:       PENDING_OPERATOR
OPERATOR_NOTE:
```

## ADR-SB-003 — Recall Fusion and Provenance

```text
MACHINE CONTRACT   ADR-SB-003.contract.json
CLAUSES            13 (11 BOOLEAN, 2 ENUM) — 13/13 COVERED
TYPED ARTIFACTS    none required
SB-DEC             SB-DEC-016, SB-DEC-017
PARSE / COVERAGE   PASS · MISSING 0 · AMBIGUOUS 0
MA-08              NO_NEW_MATERIAL_DRIFT
AUDIT              PASS · BLOCKERS 0 · MUST_FIX 0
```

Remaining implementation-time requirements: the standard seven.

ADR-specific note: this is the ADR whose rejected alternative ("Vector-first answer
generation") is verbatim candidate text, and an earlier contract round did ground a clause
in it. The validator now forbids grounding a clause in a `Rejected alternatives`,
`Evidence and traceability`, or `Acceptance conditions` subsection, and check A23 passes.
The specific way this ADR could have been misrepresented is now closed by a guard, not by
someone remembering.

```text
FACILITATOR_RECOMMENDATION: RECOMMEND_ACCEPT
OPERATOR_DISPOSITION:       PENDING_OPERATOR
OPERATOR_NOTE:
```

## ADR-SB-004 — Domain, Classification, and Provider Policy

```text
MACHINE CONTRACT   ADR-SB-004.contract.json
CLAUSES            11 (7 BOOLEAN, 3 ENUM, 1 CONSTANT) — 11/11 COVERED
TYPED ARTIFACTS    none required
SB-DEC             SB-DEC-010, SB-DEC-011, SB-DEC-012
PARSE / COVERAGE   PASS · MISSING 0 · AMBIGUOUS 0
MA-08              NO_NEW_MATERIAL_DRIFT
AUDIT              PASS · BLOCKERS 0 · MUST_FIX 0
```

Remaining implementation-time requirements: the standard seven, with
`ENCRYPTION_IMPLEMENTATION` load-bearing here.

ADR-specific note: the three closed sets (domains, classifications, policy evaluation
inputs) are checked **bidirectionally** against a verbatim source enumeration, so dropping
a member fails exactly like adding one. This is the ADR where a quiet set-shrink would have
been a privacy change, and it is the guard that a previous round did not have. The ADR's own
consequence "No confidential/restricted semantic indexing in v1" is encoded, not assumed.

```text
FACILITATOR_RECOMMENDATION: RECOMMEND_ACCEPT
OPERATOR_DISPOSITION:       PENDING_OPERATOR
OPERATOR_NOTE:
```

## ADR-SB-005 — Markdown Projection Contract

```text
MACHINE CONTRACT   ADR-SB-005.contract.json
CLAUSES            14 (10 BOOLEAN, 3 CONSTANT, 1 ENUM) — 14/14 COVERED
TYPED ARTIFACTS    none required
SB-DEC             SB-DEC-018, SB-DEC-019
PARSE / COVERAGE   PASS · MISSING 0 · AMBIGUOUS 0
MA-08              NO_NEW_MATERIAL_DRIFT
AUDIT              PASS · BLOCKERS 0 · MUST_FIX 0
```

Remaining implementation-time requirements: the standard seven.

```text
FACILITATOR_RECOMMENDATION: RECOMMEND_ACCEPT
OPERATOR_DISPOSITION:       PENDING_OPERATOR
OPERATOR_NOTE:
```

## ADR-SB-006 — Local Spool and Custody Interface

```text
MACHINE CONTRACT   ADR-SB-006.contract.json
CLAUSES            17 (9 BOOLEAN, 4 CONSTANT, 2 ENUM, 2 INTERFACE_REQUIREMENT) — 17/17 COVERED
TYPED ARTIFACTS    local-spool-port.contract.json, custody-port.contract.json
SB-DEC             SB-DEC-014, SB-DEC-015
PARSE / COVERAGE   PASS · MISSING 0 · AMBIGUOUS 0
MA-08              NO_NEW_MATERIAL_DRIFT
AUDIT              PASS · BLOCKERS 0 · MUST_FIX 0
```

Remaining implementation-time requirements: the standard seven, with
`ENCRYPTION_IMPLEMENTATION` decisive — the ADR itself holds confidential/restricted spooling
disabled until verified encryption and key ownership exist. Accepting the ADR accepts that
disablement; it does not relax it.

ADR-specific note: both port contracts carry `implementation_status: NOT_IMPLEMENTED`. They
are acceptance-time evidence that the named types exist and are grounded in the decision
text — not implementation-ready interface definitions. The independent auditor separately
observed that the surface-grounding rule is substring-based and theoretically defeatable by
a future invented property, while finding no such property in the present artifacts. Treat
these ports as sufficient for acceptance and as requiring interface review before any
implementation slice.

```text
FACILITATOR_RECOMMENDATION: RECOMMEND_ACCEPT
OPERATOR_DISPOSITION:       PENDING_OPERATOR
OPERATOR_NOTE:
```

## ADR-SB-007 — Forget, Purge, and Residual Verification

```text
MACHINE CONTRACT   ADR-SB-007.contract.json
CLAUSES            17 (11 BOOLEAN, 3 CONSTANT, 2 ENUM, 1 NUMERIC) — 17/17 COVERED
TYPED ARTIFACTS    none required
SB-DEC             SB-DEC-019, SB-DEC-029
PARSE / COVERAGE   PASS · MISSING 0 · AMBIGUOUS 0
MA-08              NO_NEW_MATERIAL_DRIFT
AUDIT              PASS · BLOCKERS 0 · MUST_FIX 0
```

Remaining implementation-time requirements: the standard seven, with `PURGE_COMPLETENESS`
decisive. The NUMERIC clause encodes "searchable residual count must be zero"; proving it
holds at runtime is exactly the `PURGE_COMPLETENESS` gate, which is `NOT_RUN`.

ADR-specific note: this ADR is the reason label-only rule shapes were banned. A rule of the
form `MUST_EXIST → "PURGE_DEPENDENCY_GRAPH"` asserts that something is *named*, not that
anything must be *true*, and the deletion-operation set was the case where dropping `PURGE`
once passed validation. Both holes are closed — the shape taxonomy no longer admits opaque
labels, and closed sets are checked bidirectionally.

```text
FACILITATOR_RECOMMENDATION: RECOMMEND_ACCEPT
OPERATOR_DISPOSITION:       PENDING_OPERATOR
OPERATOR_NOTE:
```

## ADR-SB-008 — Open Loop and Task Proposal Boundary

```text
MACHINE CONTRACT   ADR-SB-008.contract.json
CLAUSES            36 (25 BOOLEAN, 3 AUTHORITY_TARGET, 3 ENUM, 3 INTERFACE_REQUIREMENT, 1 CONSTANT, 1 NUMERIC) — 36/36 COVERED
TYPED ARTIFACTS    open-loop-candidate.schema.json, task-proposal.schema.json, task-promotion-request.schema.json
SB-DEC             SB-DEC-006, SB-DEC-007, SB-DEC-008, SB-DEC-030
PARSE / COVERAGE   PASS · MISSING 0 · AMBIGUOUS 0
MA-08              NO_NEW_MATERIAL_DRIFT
AUDIT              PASS · BLOCKERS 0 · MUST_FIX 0
```

Remaining implementation-time requirements: the standard seven. The task-promotion path is
disabled by the decision itself (Slice 6) and has **zero consumers** in `src/` or
`services/` — verified this run, not assumed.

ADR-specific note, and it is the one the candidate document singles out: the standing MA-08
text says *"ADR-SB-008 in particular is not accepted merely because MA-06 was applied to it
here."* This is the largest contract in the family precisely because the MA-06 PM-semantics
firewall is encoded clause by clause — the closed set of forbidden PM fields (assignee, PM
priority, workflow status, sprint state, ownership, due-driven escalation, automatic
scheduling, task completion state) is bidirectionally grounded, so removing one member fails
validation. `due_at` is pinned as advisory display metadata. This ADR now has the strongest
evidence in the set, and it needs the strongest, because it is the one that touches PM
authority.

```text
FACILITATOR_RECOMMENDATION: RECOMMEND_ACCEPT
OPERATOR_DISPOSITION:       PENDING_OPERATOR
OPERATOR_NOTE:
```

## ADR-SB-009 — Single-Project Safety and Identity Dependencies

```text
MACHINE CONTRACT   ADR-SB-009.contract.json
CLAUSES            12 (9 BOOLEAN, 1 ENUM, 1 CONSTANT, 1 NUMERIC) — 12/12 COVERED
TYPED ARTIFACTS    project-identity-envelope.schema.json, service-capability-receipt.schema.json
SB-DEC             SB-DEC-009, SB-DEC-013, SB-DEC-022, SB-DEC-024
PARSE / COVERAGE   PASS · MISSING 0 · AMBIGUOUS 0
MA-08              NO_NEW_MATERIAL_DRIFT — with a carried re-gate obligation, below
AUDIT              PASS · BLOCKERS 0 · MUST_FIX 0
```

Remaining implementation-time requirements: the standard seven, with
`MULTI_PROJECT_ISOLATION` and `SPLIT_BRAIN_PROOF` decisive — both `NOT_RUN`, and the ADR
itself keeps multi-project background capture disabled until isolation proof exists.

**Carried re-gate obligation.** This is the only ADR in the set that the drift recheck
touches substantively. The ConPort "project wall" (#1188, in segment A of the MA-08 window)
moved credentials from a bare `workspace_id` string to a per-project database and LOGIN
role. That is directionally aligned with this ADR — fail-closed identity, wrong-project
denial — but it establishes **no registry** and grants no authority, so it neither satisfies
nor contradicts the ADR's registry-backed-identity requirement. Under the standing MA-08
rule this is a contained runtime change: it is recorded and it re-gates the affected slice;
it does not block acceptance. Any ADR-SB-009 implementation slice must re-gate against what
the project wall actually guarantees rather than assume it discharges the requirement.

The auditor also noted `service-capability-receipt.schema.json` carries a thin `current`
property — traceable to "current service capability receipts" in the decision text, so not
invented, but sparse as an interface. Same disposition as ADR-SB-006's ports: sufficient as
acceptance-time evidence, requiring interface review before implementation.

```text
FACILITATOR_RECOMMENDATION: RECOMMEND_ACCEPT
OPERATOR_DISPOSITION:       PENDING_OPERATOR
OPERATOR_NOTE:
```

## ADR-SB-010 — UX Contract

```text
MACHINE CONTRACT   ADR-SB-010.contract.json
CLAUSES            15 (8 BOOLEAN, 3 ENUM, 3 NUMERIC, 1 CONSTANT) — 15/15 COVERED
TYPED ARTIFACTS    none required
SB-DEC             SB-DEC-020, SB-DEC-021
PARSE / COVERAGE   PASS · MISSING 0 · AMBIGUOUS 0
MA-08              NO_NEW_MATERIAL_DRIFT
AUDIT              PASS · BLOCKERS 0 · MUST_FIX 0
```

Remaining implementation-time requirements: the standard seven.

ADR-specific note: three NUMERIC clauses make this the most directly testable ADR in the
set — at most seven visible queue items, one dominant next action, zero productivity
scoring. The validator's S-group checks these as semantic invariants independently of the
inventory, so they hold even if the denominator pin were edited.

```text
FACILITATOR_RECOMMENDATION: RECOMMEND_ACCEPT
OPERATOR_DISPOSITION:       PENDING_OPERATOR
OPERATOR_NOTE:
```

---

## Summary sheet

| ADR | Clauses | Typed artifacts | Coverage | MA-08 | Audit | Recommendation | Your disposition |
|---|---:|---:|---|---|---|---|---|
| ADR-SB-001 Extension Boundary and Non-Authority | 11 | 0 | 11/11 | NO_NEW_MATERIAL_DRIFT | PASS 0/0 | RECOMMEND_ACCEPT | `PENDING_OPERATOR` |
| ADR-SB-002 Capture, Candidate, Review, Promotion | 14 | 0 | 14/14 | NO_NEW_MATERIAL_DRIFT | PASS 0/0 | RECOMMEND_ACCEPT | `PENDING_OPERATOR` |
| ADR-SB-003 Recall Fusion and Provenance | 13 | 0 | 13/13 | NO_NEW_MATERIAL_DRIFT | PASS 0/0 | RECOMMEND_ACCEPT | `PENDING_OPERATOR` |
| ADR-SB-004 Domain, Classification, Provider Policy | 11 | 0 | 11/11 | NO_NEW_MATERIAL_DRIFT | PASS 0/0 | RECOMMEND_ACCEPT | `PENDING_OPERATOR` |
| ADR-SB-005 Markdown Projection Contract | 14 | 0 | 14/14 | NO_NEW_MATERIAL_DRIFT | PASS 0/0 | RECOMMEND_ACCEPT | `PENDING_OPERATOR` |
| ADR-SB-006 Local Spool and Custody Interface | 17 | 2 | 17/17 | NO_NEW_MATERIAL_DRIFT | PASS 0/0 | RECOMMEND_ACCEPT | `PENDING_OPERATOR` |
| ADR-SB-007 Forget, Purge, Residual Verification | 17 | 0 | 17/17 | NO_NEW_MATERIAL_DRIFT | PASS 0/0 | RECOMMEND_ACCEPT | `PENDING_OPERATOR` |
| ADR-SB-008 Open Loop and Task Proposal Boundary | 36 | 3 | 36/36 | NO_NEW_MATERIAL_DRIFT | PASS 0/0 | RECOMMEND_ACCEPT | `PENDING_OPERATOR` |
| ADR-SB-009 Single-Project Safety and Identity | 12 | 2 | 12/12 | NO_NEW_MATERIAL_DRIFT + re-gate | PASS 0/0 | RECOMMEND_ACCEPT | `PENDING_OPERATOR` |
| ADR-SB-010 UX Contract | 15 | 0 | 15/15 | NO_NEW_MATERIAL_DRIFT | PASS 0/0 | RECOMMEND_ACCEPT | `PENDING_OPERATOR` |
| **Total** | **160** | **7** | **160/160** | | | | |

## The uncomfortable thing about this recommendation, said plainly

Ten `RECOMMEND_ACCEPT` is the same shape as the superseded election of 2026-08-10. That
resemblance deserves suspicion, so here is exactly how this one was reached and what would
have changed it.

It was not inherited. The superseded ledger at `19fa74faa9` was read once, read-only, and
only to establish that it is *not* the controlling prior disposition. Its recommendations
were not consulted when forming these. Each ADR above was assessed against the four
acceptance conditions using evidence that did not exist when that election was made — the
amended AC#2, the contract family, the fresh MA-08, and two independent audit rounds.

The reason the answers converge is structural, not sloppy: the four acceptance conditions
are largely document-level, and the one that was genuinely unmet for all ten — AC#2's
first sentence — has now been met for all ten by a single body of work. An ADR-by-ADR
split would require an ADR whose contracts fail to parse or cover, or whose clauses are not
grounded in its own decision text. There is no such ADR: `MISSING` and `AMBIGUOUS` are zero
per ADR, not just in aggregate.

What would have produced a different recommendation, and was checked for:

- **Any ADR with `MISSING > 0` or `AMBIGUOUS > 0`** → `RECOMMEND_DEFER` for that ADR. None.
- **An ADR whose `required_artifacts` was empty because the bar was set low** rather than
  because it names no type → checked; the 2/3/2 mapping matches the prose exactly.
- **A clause grounded in a rejected alternative** → the exact defect that once affected
  ADR-SB-003; now blocked by check A23, which passes.
- **New material authority or privacy drift in the window** → would have stopped the phase
  at `BLOCKED_NEW_MATERIAL_DRIFT` before this worksheet existed. There is none.
- **An audit blocker** → round 1 returned one must-fix, which was repaired and re-audited
  to 0/0 rather than argued down.

The honest summary is that these recommendations rest on evidence that is *complete for
what acceptance requires* and *silent about everything else*. Nothing here says the Second
Brain works, is safe to run, or should be built. It says the ten decisions are described
precisely enough, and traced faithfully enough, to be ruled on.

## What accepting does and does not do

```text
DOES      make the ten ADRs accepted architecture records
DOES      make their clauses the reference a future implementation is measured against
DOES      make ADR-SB-009's re-gate obligation explicit rather than latent

DOES NOT  authorize implementation, a slice, a task packet, or any runtime change
DOES NOT  imply denial fixtures exist  (they do not; enablement-time gate)
DOES NOT  imply runtime conformance, retrieval benchmarks, purge completeness,
          multi-project isolation, or split-brain proof  (all NOT_RUN)
DOES NOT  imply encryption exists  (ABSENT)
DOES NOT  reopen or alter the 32 ratified SB-DEC decisions (32 ACCEPT / 0 DEFER / 0 REJECT)
DOES NOT  change SB-DEC-026's A_LEAVE_UNLINKED posture
```

## If you DEFER again

A DEFER is a fully coherent outcome and needs no justification, but it is worth knowing
what it would now be waiting on. AC#2's first sentence is met; the second sentence
(denial fixtures) is an **enablement-time** gate by your own authorized wording, so it
cannot be discharged before implementation without contradicting the amendment. A DEFER at
this point therefore defers on judgment about the decisions themselves, not on missing
acceptance evidence — and it is worth saying which, so a future run does not go looking for
evidence that was never the blocker.

One live residual from the AC#2 amendment audit is relevant here: the scope of "required
denial fixtures" is **not enumerated per ADR**. That is your own authorized wording, and
sentence three plus AC#3 stop it becoming an enablement loophole, but if you want that
scope pinned per ADR, doing it before acceptance is cheaper than after.

## Terminal state

```text
READY_FOR_OPERATOR_ADR_REDISPOSITION
AWAITING_OPERATOR_ADR_DISPOSITIONS

ADR_ACCEPTANCE_AUTHORIZED = false
ADR_DISPOSITIONS          = 10x DEFER  (unchanged; current until you replace them)
IMPLEMENTATION_EXECUTION  = NOT_AUTHORIZED
RUNTIME_MUTATION          = FORBIDDEN
DENIAL_FIXTURES           = NOT_IMPLEMENTED
```

No further work proceeds without your dispositions.
