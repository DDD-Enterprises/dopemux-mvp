# AUDITOR_REPORT — TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001

## Custody header

```text
AUDITED_CONTENT_HEAD   7955ef33d7c0ab29daecbab966bc6a9497dc69ce
BASE_MAIN              6153bd4fb30ed3d038e51b371ad9ebfb4916bfac
CANDIDATE_SHA256       e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c
RUNNER                 grok CLI 1.0.0 (3cd0d0cbcebe) [stable]
SESSION                019ff54e-59b1-7a12-bc2a-1cc88f3e3189
WORKTREE               /private/tmp/sb-audit-c1 (throwaway, detached at the audited head)
INDEPENDENT_OF_PRODUCER    true
PRODUCER_CONVERSATION      not shared
SEPARATE_PROCESS           true
PROVIDER_ATTESTATION       UNKNOWN (no provider-side attestation obtained)
```

The prompt (`AUDIT_PROMPT.md`, tracked) names frozen head `8a9b0ee53c`. The audit
actually ran against `7955ef33d7`, one commit later — the A21 value-grounding fix that
a producer self-probe forced. **The auditor detected this discrepancy itself** and
verified the real head before proceeding. The prompt was deliberately NOT rewritten to
match: it is the artifact that was executed, and editing it to name a head it did not
name would falsify custody. See `AUDIT_PROMPT_CUSTODY.json`.

Three earlier audit routes failed before this one and are recorded in that custody
file (pal/gemini quota exhausted; pal/gpt-5-pro — the pal MCP containers have no bind
mounts so they cannot read host files; opencode headless — auto-rejected its own bash
permission and produced no verdict).

## Producer disposition

The controlling verdict is **FAIL**. The packet requires PASS with `BLOCKERS=0` and
`MUST_FIX=0`, so the terminal state is `BLOCKED_INDEPENDENT_AUDIT`. Publication does
not progress; the PR stays a draft and is not marked ready.

The producer independently re-verified the two structural blockers rather than
accepting them on assertion:

- **B2** — `grep -c dopeTask` against the candidate returns **0**. The token was drawn
  from the task packet's own architecture-boundary list, not from the ratified
  candidate. Invention confirmed.
- **B3** — dropping `PURGE` from the ADR-SB-007 deletion-operation set and `Review`
  from the ADR-SB-010 UX operation set, applied consistently to inventory and
  contract, still exits 0. Confirmed: A21's membership test is one-way.
- **B1** was already demonstrated by the producer before the audit ran (rerouting
  ADR-SB-002-C01 canonical capture from Dope-Memory to ConPort), which is what
  prompted A21. The audit's finding is that A21 narrowed the class without closing
  it — also confirmed by producer probe (inverting ADR-SB-003-C01 recall fusion to
  the explicitly rejected vector-first order, and flipping ADR-SB-002-C05 from
  DEFER/NO-MUTATION to auto-apply, both still exit 0).

No finding is disputed.

---

## Verbatim auditor output

Independent read-only audit. Reading committed evidence and contracts, then attacking validator false-green paths.HEAD is `7955ef33`, not stated freeze `8a9b0ee`. Checking that, then reading ADR candidates, inventory, and contracts.HEAD is one commit past stated freeze (`A21` grounding fix). Reading remaining ADRs, inventory, and key contracts.Digging into typed artifacts, invented values, FO-01 overstatement, and false-green attack surfaces.Confirming bilateral edits that also update port invariants, and A21 enum-shrink hole.Checking one more detail: inventory freeze vs contract generation and whether `covered_by` is ever validated as non-self.```
VERDICT: FAIL
BLOCKERS: 3
1. Validator can false-green on material architecture-meaning mutations: inventory+contract (and mirrored invariants) edited consistently still exit 0 for many load-bearing decisions. A09 is largely circular self-agreement; Group S + A21 pin only a minority of the 97 clauses.
2. Invented canonical authority token `dopeTask` — not present in candidate text — appears in AUTHORITY_TARGETS, authority_targets_permitted, and AUTHORITY_TARGET/IN machine_values (ADR-SB-001-C03, ADR-SB-002-C06).
3. A21 ENUM/SET_EQUALS is one-way (members ⊆ cited text): closed decision sets can be silently shrunk (drop PURGE; drop UX Review) while still PASS.

MUST_FIX: 5
1. Material decision content missing from the 97-clause denominator (see Q2): policy evaluation dimensions; purge completion receipt; ConPort-never-owns-task-state / Dope-Memory-no-PM; historical-vs-current recall distinction.
2. LocalSpoolPort/CustodyPort `operations` lists and several typed-artifact property/enum sets invent API/schema surface the candidate never states (admit/append/flush/…; proposal_state; freshness_state CURRENT/STALE; etc.). Validator does not constrain them — e.g. inventing `cloud_offload` still exits 0.
3. ADR-SB-003-C01 full 4-way fusion ranking invents relative order beyond candidate “authority-first” + context span; bilateral reorder false-greens.
4. Many rules are token-labels (REQUIRE/MUST_EXIST `PURGE_DEPENDENCY_GRAPH`, `FRESHNESS_METADATA`, …) with no checkable structure — “cover” is naming, not machine expression.
5. FO-01 status is not fully receipt-locked: Group B ignores several status fields (`independent_verification.nonblocking_observations`, `authority.architecture_accepted_as_law`, expanded coverage metrics); those can diverge while Group B still PASS.

NONBLOCKING OBSERVATIONS:
- Pristine tree: validator exit 0 (114 checks); pytest 52/52 pass.
- Inventory freeze provenance holds: `a9397e5630` has ADR_CLAUSE_INVENTORY.json and zero `schemas/second_brain/`; live inventory sha256 `f073ca2880…` matches freeze.
- Candidate sha256 `e4b2894615…` matches stated; all 10 ADRs remain PROPOSED; denial fixtures correctly `NOT_IMPLEMENTED_IMPLEMENTATION_TIME_GATE`; no enablement/runtime-authorized truthy claims in contracts.
- Group S pins are load-bearing for their surfaces (restricted spool matrix, promotion `enabled:const false`, wrong-project DENY, queue max 7, residual 0, PM property denylist on OpenLoopCandidate).
- A21 (HEAD `7955ef33d7`, past stated freeze `8a9b0ee53c`) does catch some bilateral authority EQUALS reroutes and enum *widening*; residual false-green surface remains large.
- FO-01 verification core fields that Group B checks do mirror the receipt; no overstated audit PASS/blockers.
- Audited tree is HEAD `7955ef33d7`, not freeze `8a9b0ee53c` (A21 fix on top).
```

---

### Scope / bytes read

| Item | Value |
|------|--------|
| HEAD audited | `7955ef33d7` (A21 fix) |
| Stated freeze | `8a9b0ee53c` (ancestor; no A21) |
| Base main | `6153bd4fb3` |
| Candidate sha256 | `e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c` |
| Inventory sha256 | `f073ca28802e6b140dd5789d5fad5839962635f7b287cac589ec704efc663288` |
| Validator | exit 0, 114 checks, 0 failures |
| Tests | 52 passed |

---

## Q1 — Sufficient machine-contract representation?

**Partial structural yes; semantic lock no.**

Present and parseable:
- 10 ADR contracts under `schemas/second_brain/contracts/`
- Typed artifacts for 006/008/009
- 97 coverage entries, all `COVERED`
- Frozen inventory + candidate hash binding

Not sufficient as evidence that decisions are *held*:
- Coverage is inventory ↔ structured rule self-agreement (A09), not independent semantic lock to candidate law.
- Large false-green surface (Q6) means `PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE` does not prove decision fidelity.
- ADRs 001–005, 007, 010 lack required typed artifacts beyond clause token lists — many decisions only “exist” as labeled `machine_value` strings.

---

## Q2 — Denominator completeness (material content with no clause)

Read all ten Context / Proposed decision / Consequences. **Material gaps (no matching clause among 97):**

| ADR | Missing material content | Candidate locus |
|-----|--------------------------|-----------------|
| **ADR-SB-004** | Required policy evaluation dimensions: identity, grants, provider, embedding, custody, backup, operation | Proposed decision L140 — only stage ordering ADR-SB-004-C03 exists, not dimension set |
| **ADR-SB-007** | **Completion receipt** in purge chain | Proposed decision L243: “residual scan, and completion receipt” — C02–C06 cover graph/preview/approval/per-surface/residual; no completion-receipt clause |
| **ADR-SB-008** | **ConPort never owns task state**; **Dope-Memory not granted PM authority** (only Second Brain PM forbid in boilerplate) | Consequences L285; MA-06 L279 |
| **ADR-SB-003** | **Historical and current states remain distinct** | Consequences L111 |
| **ADR-SB-008** | Confirmed events are **open/close/cancel** kinds (as decision content) | Proposed decision L277 — only append-target C04; no event-kind enum (OpenLoopCandidate has `loop_state` open/closed/cancelled as schema invention, not inventory clause) |

**Borderline / not scored as blockers** (consequences or packaging, not core decision machinery): “One package plus optional worker” (001 L39), “Mac mini remains optional” (009 L321), “No dashboard dependency” (010 L357), “Replayable candidate history” (002 L74 — partly implied by Dope-Memory append), “Crash-safe eligible capture” / “Custody product remains replaceable” (006 L213–215).

MA-08 standing drift recheck (L21–23) is pre-acceptance process, not an ADR decision clause — correctly out of the 97.

---

## Q3 — Correspond vs merely name?

**Mixed. Many high-value pins correspond; many others only name.**

**Real correspondence (checkable values):**
- Domain/classification enums (004-C01/C02)
- Unknown denies / residual 0 / queue ≤7 / promotion `enabled:false`
- Classification matrix strings for spool
- OpenLoop PM denylist + `additionalProperties:false` + `due_at` x-semantics
- Project envelope `wrong_project_write_disposition: DENY`, `maximum:1`, rejected identity sources

**Merely naming (token / label without structure):**
- `REQUIRE`/`MUST_EXIST` → `PURGE_DEPENDENCY_GRAPH`, `PURGE_IMPACT_PREVIEW`, `RESIDUAL_SCAN`, `FRESHNESS_METADATA`, `CONTRADICTION_SET`, `REVIEW_DIGEST_SHA256`, `INTEGRITY_DIGEST`, `WRITER_EPOCH`, `PROJECTION_CONTENT_SHA256` — name an artifact class; no schema of that artifact
- `INTERFACE_REQUIREMENT`/`MUST_EXIST` for types that have no further shape on ADRs without typed files
- `FORBID`/`MUST_NOT_EXIST` `SILENT_WRITE_BACK`, `CROSS_AUTHORITY_ATOMIC_TRANSACTION`, `SECOND_BRAIN_CANONICAL_DATABASE` — string tokens
- ADR-SB-005-C09: `FORBID`/`EQUALS`/`OPTIONAL_OPENER_NEVER_AUTHORITY` — role slogan, not a checkable forbid of authority writes

**Self-pointer naming:** every clause’s primary `covered_by` / coverage pointer is its own `decision_clauses[i]` (or mirrored invariant with same four fields). Validator never reads `covered_by` (`validate_second_brain_adr_contracts.py` has no `covered_by` check). Coverage is “I point at myself and match inventory.”

---

## Q4 — Invented architecture semantics?

**Yes.**

| Invention | Where | Candidate support |
|-----------|--------|-------------------|
| **`dopeTask` as authority** | Validator `AUTHORITY_TARGETS` L71; `adr-machine-contract.schema.json` L100–106; ADR-SB-001-C03 / ADR-SB-002-C06 lists | Candidate never contains `dopeTask`. Names ConPort, Dope-Memory, Leantime, Task Orchestrator, “existing authorities” only |
| **4-tuple fusion order** | ADR-SB-003-C01 `['AUTHORITY','CHRONOLOGY','SOURCE_NATIVE','ADVISORY_RETRIEVAL']` | “authority-first fusion” + context “spans … authority, chronology, source-native … advisory” — not a total order among the non-authority three |
| **LocalSpoolPort ops** | `admit`, `append`, `flush`, `expire`, `participate_in_purge` | Candidate defines port name + properties, not operation inventory |
| **CustodyPort ops** | `put`, `verify_integrity`, `residual_scan`, `backup_eligibility`, `tombstone` | Same |
| **Custody matrix token** | `REMOTE_BACKUP_FORBIDDEN_FOR_SPOOL_DERIVED_CONTENT` | Elaborates “never remote backed up” into a new enum member |
| **OpenLoop / TaskProposal field sets** | `confidence`, `proposal_state` enum `proposed/withdrawn/superseded`, etc. | Not in candidate |
| **ServiceCapabilityReceipt** | `freshness_state` `CURRENT`/`STALE`; `unknown_capability_disposition` | “current service capability receipts” — CURRENT/STALE and unknown-capability DENY are elaboration |
| **Token constants** | `EXTENSION_CONTROL_PLANE`, `SHORT_LIVED_BOUNDED_TTL`, `DEFER_NO_MUTATION`, `SYNTHETIC_ONLY`, … | Codifications of prose; acceptable if locked to text — most are **not** A21-grounded |

Normalization `class`→`classification` is acknowledged in A21 comments and is fine.

---

## Q5 — Typed artifacts for 006 / 008 / 009 sufficient?

**Mostly yes for architecture-time expression of the named decisions; with caveats.**

| ADR | Artifacts | Sufficient for? | Gaps |
|-----|-----------|-----------------|------|
| **006** | `local-spool-port.contract.json`, `custody-port.contract.json` | Non-canonical spool; classification gates; integrity/TTL/idempotent flush/purge-aware/no remote backup **as matrix + invariants** | Op lists invent API; no machine encoding of “custody product remains replaceable” |
| **008** | `open-loop-candidate.schema.json`, `task-proposal.schema.json`, `task-promotion-request.schema.json` | MA-06 PM firewall (closed shape + denylist + advisory `due_at`); separate TaskProposal; promotion disabled-by-const + dual proofs + operator approval | TaskProposal almost empty of decision law; open/close/cancel as events not as inventory clauses; ConPort/Dope-Memory PM forbids not in schemas |
| **009** | `project-identity-envelope.schema.json`, `service-capability-receipt.schema.json` | Registry-backed, ≤1 active capture, explicit switch, writer epoch, wrong-project DENY, rejected identity sources, multi-project capture off | Receipt does not machine-require “must accompany every authority operation” beyond type existence; “no host-singleton routing authority” only via rejected `SINGLETON_EVENT_STREAM` |

**Verdict on Q5:** sufficient to *express* the main proposed decisions in machine form; not sufficient alone to *prove* fidelity (depends on validator — which fails Q6).

---

## Q6 — Can the validator false-green? (attacked)

**Yes. Demonstrated on this tree (temp sandboxes only; repo untouched).**

### `covered_by` / A09 circularity

- Primary pointer: own `decision_clauses[N]` for all 97.
- A09 checks: pointer resolves + has `{subject,rule_type,operator,machine_value}` + **equals inventory clause**.
- Inventory and contracts were generated together (“true by construction”). A09 proves **they still match each other**, not that values match candidate law.
- `covered_by` field itself is **never read** by the validator.

### A09 four-field match

Given by-construction generation: **tests serialization consistency**, not independent coverage. Bilateral edit of both sides keeps A09 green while changing architecture meaning.

### Group S — load-bearing where present, thin overall

| Pin | Catches |
|-----|---------|
| S01 classification_matrix | restricted/confidential encryption gate; unknown DENY; internal OS-protected |
| S02 OpenLoop/TaskProposal | PM property names; `additionalProperties:false`; due_at advisory markers |
| S03 TaskPromotionRequest | `enabled.const false`; required proofs; target authorities |
| S04 inventory pins | 004-C04 DENY; 004-C07 indexing classes |
| S05 envelope/receipt | wrong-project DENY; max 1; multi-project false; rejected sources |
| S06–S08 | queue 7; DEFER/CANCEL; no surprise writes / productivity scoring; residual 0 |

**Full consistent mutation still caught:** restricted→ALLOWED (S01); promotion enabled (S03); multi-project true on schema (S05).

**Clause-only lies that still PASS:** e.g. 006-C14 `machine_value=ALLOW` while matrix stays `DENY` — inventory claims one architecture, matrix another, exit 0.

### Concrete false-greens (exit 0 after bilateral consistent edit)

| Mutation | Architecture meaning change |
|----------|----------------------------|
| ADR-SB-002-C05 → `ALLOW_MUTATION` | Review default no longer DEFER/NO MUTATION |
| ADR-SB-003-C01 reorder → advisory first | Authority-first fusion inverted |
| ADR-SB-004-C03 reorder → model before policy | Pre-disclosure policy evaluation broken |
| ADR-SB-007-C04 → `IMPLICIT_APPROVAL` | Explicit purge approval removed |
| ADR-SB-002-C04 → `NONE` | Digest-bound review removed |
| ADR-SB-001-C01 → `CANONICAL_MEMORY_PLANE` | Extension non-authority role inverted |
| ADR-SB-003-C08 → `true` | Search rank becomes authority |
| ADR-SB-005-C07 flipped to require silent write-back | Projection write-back forbid inverted |
| ADR-SB-006-C07 → `UNBOUNDED_RETENTION` | Short-lived spool removed |
| ADR-SB-006-C10 → `true` | Remote backup forbid inverted |
| ADR-SB-008-C06 → only `LEANTIME_PROOF` | Dual-proof + approval preconditions gutted |
| ADR-SB-010-C06 → `ALWAYS_ON` | Session-end batching removed |
| ADR-SB-007-C01 drop `PURGE` | Closed deletion ops shrunk (**A21 miss**) |
| ADR-SB-010-C01 drop `Review` | UX ops shrunk (**A21 miss**) |
| ADR-SB-001-C03 drop `dopeTask` from IN | Authority set edited without A21 (IN not EQUALS) |
| Add `cloud_offload` to LocalSpoolPort ops | New architecture surface unconstrained |
| TaskProposal `proposal_state` += `promoted_to_task` | Schema admits promotion-shaped state |

### A21 limits (even on HEAD)

Only grounds:
- `AUTHORITY_TARGET` + `EQUALS` + string
- `ENUM` + `SET_EQUALS` members present in text (**not** “all text members present”)
- integer numeric bounds

Does **not** ground: `AUTHORITY_TARGET`/`IN`, `ORDERING`/`PRECEDES`, most `REQUIRE`/`FORBID`/`CONSTANT`/`LIFECYCLE`/`CAPABILITY_GATE` string tokens, boolean flips except where Group S also pins.

### Clauses with **no Group-S guard** (can be bilaterally weakened unless A21 happens to apply)

**~88/97 lack Group S.** A21 covers only ~15 clause IDs (mostly EQUALS authorities, a few enums, a few ints).

**Neither Group S nor A21 (~75 clauses)** — includes essentially all of 001, most of 002–003, 005, 006 (clause side), 007 (except residual 0), most of 008 field forbids (schema side partially helps), parts of 009/010.

**High-risk no-S examples:** 002-C05 default disposition; 003-C01 fusion order; 004-C03/C05/C06; 005-C07 silent write-back; 006 retention/remote backup (clause+invariant without matrix pin); 007-C04 approval; 008-C06 preconditions; 010-C06 batching.

### Collective missing decisions

A08 freezes **inventory total = 97** and 1:1 coverage of *that* inventory. It does **not** re-derive the denominator from candidate text. Omitting a decision at inventory authoring time is permanent; you cannot drop below 97 later without fail, but you also cannot detect “never inventoried.” Combined with Q2 gaps: **coverage of an incomplete denominator can still green.**

---

## Q7 — FO-01 reconciliation: mirror or overstate?

**Core verification: mirror. Not overstated on audit PASS.**

Group B requires (and live files satisfy):
- `fo01_status` == receipt `status` == `TRACEABILITY_REPAIRED_AND_INDEPENDENTLY_REVERIFIED`
- `independent_verification.verdict` == receipt `audit_verdict`
- heads, auditor_report_sha256, blockers=0, must_fix=0
- `adr_acceptance_authorized: false`, `implementation_execution: NOT_AUTHORIZED`, merge not authorized
- `preserved_not_run` exact equality
- source/candidate/ratification hashes match receipt

**Not pure mirror (status-only / interpretive; not audit overclaim):**
- `fo01_gate_condition: CLOSED` — interpretive of receipt `closes_fo01_required_repair_condition` + eligibility
- `gates.adr_acceptance: CLOSED` — conservative, not on receipt
- `authority.architecture_accepted_as_law: true` — not on receipt; Group B does not check it (flip still PASS)
- `independent_verification.nonblocking_observations: 3` matches receipt `audit_nonblocking_observations` numerically but **validator does not enforce** (inflate to 99 still PASS)
- Expanded `coverage` block (adrs_changed, ambiguous_mappings, …) beyond receipt fields
- Stale `required_resolution: REPAIR_AND_REVERIFY…` while status is already REPAIRED — inconsistent wording, **under**-clears rather than overclaims success

**B08 oddity:** checks `status.coverage.decisions_linked == 26` **and** `receipt.decision_reference_changes == 28` as separate constants — not that status only copies receipt. Different metrics; both pass.

---

## Q8 — Runtime / implementation / enablement leak?

**No material leak in contracts.**

Observed:
- All ADR contracts: `runtime_claims_permitted: false`, `adr_status_at_contract_authoring: PROPOSED`
- `denial_fixtures: NOT_IMPLEMENTED_IMPLEMENTATION_TIME_GATE`
- Ports: `implementation_status: NOT_IMPLEMENTED`
- `implementation_deferred` includes `DENIAL_FIXTURES` + NOT_RUN surfaces
- Meta-schema const-pins runtime false and denial-fixture token
- A14/A15/A16/A18 enforce this on validation

FO-01: `implementation_planning: AUTHORIZED` appears on **both** status and receipt — planning authorization from prior FO-01 work, not this contract packet inventing execution. Execution/merge remain NOT_AUTHORIZED.

No contract claims ADRs accepted, fixtures implemented, or enablement authorized.

---

### Bottom line

Work delivers real architecture-time artifacts, freeze provenance, honest non-implementation labeling, and a validator that **does** catch many structural and some high-risk semantic edits. It does **not** deliver a non-circular, fail-closed proof that machine contracts cover ADR decisions: **the coverage PASS can survive silent architecture rewrites** on most clauses, **`dopeTask` is invented**, and **A21 enum shrink is a hole**. That is the investigated failure mode — FAIL.
