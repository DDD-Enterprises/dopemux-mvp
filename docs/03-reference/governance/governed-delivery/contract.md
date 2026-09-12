---
id: governed-delivery-contract
title: Governed Delivery Contract
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-24'
last_review: '2026-08-24'
next_review: '2026-11-24'
prelude: Governed Delivery Contract (reference) for dopemux documentation and developer workflows.
---

# Governed Delivery Contract

G0 of `DMX-GOV-WORKFLOW-OPT-001`. Defines seven versioned contracts and a
deterministic read-only library that answer six delivery questions from
referenced evidence, without mutating workflow state or becoming an authority
source.

**Repair cycle 2.** G0 disables proof-only audit reuse. Equivalence remains a
diagnostic, but every result has `authority_effect=NONE` and
`audit_reuse_authorized=false`; diagnostic `PASS` never preserves audit or bears
readiness. Gate and identity profiles are fixed, audit acceptance is bound to an
exact subject, all Git object identifiers are complete 40- or 64-hex values, and
runtime parsers fail closed against the seven schemas.

## Authority position

The governed-delivery package is **derived, read-only and non-authoritative**.
It references evidence; it does not replace evidence.

| Owner | Remains authoritative for |
|---|---|
| Task Packet | bounded authority envelope |
| DCP | classification, risk, privacy, authority obligations |
| Task Orchestrator | workflow legality, dependency, coarse state |
| Audit | independent judgment |
| Proof | evidence binding |
| GitHub | canonical GitHub state |
| PR Steward | exact-head readiness classification |
| Operator | architecture, red-lane, merge, activation |

Nothing in this package is a canonical writer for any of the above.

## The six questions

`snapshot.build_snapshot` answers exactly these, from supplied evidence:

```text
WHERE_IS_THIS_WORK        -> phase
WHAT_GATES_ARE_SATISFIED  -> gate ledger
WHAT_BLOCKS_IT            -> blockers, preserved individually
WHAT_EVIDENCE_IS_CURRENT  -> per-reference freshness
WHO_ACTS_NEXT             -> next_legal_action.actor_class
WHAT_ACTION_IS_LEGAL      -> next_legal_action (never dispatchable in G0)
```

## Contracts

All seven schemas live in `schemas/governed_delivery/`. Each pins its
`schema_version` with a JSON Schema `const`, so an unknown major version is
denied rather than coerced.

### EvidenceReference v1

Identifies evidence without copying its authoritative body. `authority_effect`
records the referent's effect **in its owning system**; a reference can never
raise it. Digests and identities come from deterministic tooling — a
model-generated value may never satisfy a trust boundary.

Twenty canonical `evidence_class` values are enumerated from architecture
section 05.

### GovernedDeliveryEnvelope v1

One transport wrapper, five payload kinds: `FACT`, `REQUEST`, `FINDING`,
`DECISION`, `RECEIPT`. The census found 39 semantic message classes sharing
producer, consumer, binding, idempotency and retention mechanics, so they are
carried by five kinds rather than 39 standalone schemas.

`event_type` carries semantic identity; `kind` carries transport identity. The
checked-in `MESSAGE_CLASS_CENSUS` table maps all 39, and a mismatch between an
event type and its declared kind is denied.

Transport never adds authority: `authority_effect` defaults to `NONE` and
`mutation_authorized` is structurally `false`.

Duplicate `idempotency_key` with an identical payload is an accepted duplicate;
with a different payload it is denied. G0 keeps no cache, so the caller-supplied
batch is the entire universe considered.

### GateLedger v1

Eight states: `NOT_APPLICABLE`, `PENDING`, `SATISFIED`, `UNSATISFIED`, `STALE`,
`BLOCKED`, `UNKNOWN`, `CONFLICTING`.

`SATISFIED` is not permission. It never implies execution, merge or activation
authority. `UNKNOWN` and `CONFLICTING` **fail closed** for consequential next
actions, alongside the overt blocking states. Every entry carries a `reason`
even when satisfied, so the ledger is never a bare boolean.

**A required gate with no entry is missing evidence, not silence.** G0 has one
immutable profile containing all fifteen gate classes. No constructor, JSON
field, or CLI argument can narrow it. Any required class without an entry is materialized as a
synthetic `UNKNOWN` gate — section 05's own definition of that state is "required
evidence is missing" — which becomes a root blocker and prevents `READY` and
phase advancement. A lane that genuinely does not need a gate says so with an
explicit `NOT_APPLICABLE` entry; it may not opt out by omission.

This closes `GOV-AUD-003`, where a ledger holding only `AUDIT` and `VALIDATION`
reached `READY` because the thirteen absent gates contributed nothing either way.

When one gate class carries two entries, the ledger reports the more blocking
state, so a satisfied duplicate cannot mask an unsatisfied one.

### WorkItemProjection v1

Ten coarse phases and five postures, both navigational only. Native subsystem
states are preserved verbatim in `native_state_refs` and are never replaced by
the derived phase or posture.

Root blockers are preserved **individually**; collapsing them into a single
status is forbidden. A stale or unknown consequential source prevents `READY`.

Posture precedence follows architecture section 02:

```text
terminal native state          -> TERMINAL
blocking gate or blocker       -> BLOCKED
human decision required        -> DECISION_REQUIRED
all gates for next action pass -> READY
otherwise                      -> ACTIVE
```

`BLOCKED` deliberately outranks `DECISION_REQUIRED`: an item that is both
blocked and awaiting a decision is reported as blocked. Phase follows the same
section's precedence, `TERMINAL > ACTIVATE > POST_MERGE > MERGE > REVIEW >
VERIFY > IMPLEMENT > AUTHORITY > DESIGN > REQUEST`, choosing one display
location without hiding concurrent native states.

Phase advances through the **longest satisfied prefix** of the gate sequence, not
to the highest phase any single satisfied gate represents. Advancement stops at
the first gate that is not satisfied, so a reported phase implies every phase
before it. Without this, a lone satisfied `AUDIT` gate reported `REVIEW` while
identity, scope and validation were entirely unevidenced (`GOV-AUD-003`).

Only a gate explicitly marked `NOT_APPLICABLE` may be stepped over. It is not a
barrier and is not evidence of arrival, so it is skipped without advancing. A
missing gate or a gate present in a non-satisfied state — `UNSATISFIED`,
`BLOCKED`, `STALE`, `UNKNOWN`, `CONFLICTING` or `PENDING` — halts advancement
at that point. `required_gate_classes` always emits the fixed profile;
`missing_required_gate_classes` exposes every absent class.

`READY` additionally requires an acceptable exact-subject `ContentAuditBinding`.
Caller-owned booleans such as `audit_acceptable` are not contract inputs.

`next_legal_action` is a recommendation. `dispatch_eligible` is structurally
`false` throughout G0.

### ContentAuditBinding v1

Binds a supplied auditor judgment to an immutable subject. **No G0 runtime may
invoke an auditor**; this object only represents a result produced elsewhere.

The five auditor identity layers are recorded separately and never collapsed, so
an `UNKNOWN` provider attestation stays visible instead of being silently
upgraded to a proven identity.

Acceptance is contextual, never `verdict == PASS`. Binding must match exact full
`audited_head`, `audited_tree`, content digest, packet digest, policy digest and
audit-result digest. Verdict must be `PASS` or `PASS_WITH_RISKS`; independence
must be `PROVEN` or `LIMITED`; configured and response-claimed identities must be
explicit. Missing binding makes `AUDIT` unknown and blocks `READY`.

### ProofOnlySuccessorEquivalence v1

Diagnostic only. It cannot preserve audit or authorize readiness. See below.

### OperatorDecisionRequest v1

Requests authority; creating one grants nothing. Five decision types, each
routing to a human.

## Diagnostic proof-only equivalence

The independent architecture audit constructed this attack against a
path-membership predicate:

> The path-membership predicate cannot detect a semantic change *inside* an
> allowed proof-only path: hand-editing the proof bundle's known risks/unknowns
> fields or evidence-ref list passes every equivalence conjunct yet alters
> governance-relevant content the PR Steward and operator merge card consume — a
> laundered semantic change with no re-audit and no supervisor review.

A path allowlist is therefore **necessary but not sufficient**. R2 removes this
evaluator from G0 trust boundaries: even a diagnostic `PASS` has no governance
effect. Remaining comparison logic fails closed and supports investigation only.

**1. Classification is total and fails closed.** Every compared field resolves to
`GOVERNANCE_RELEVANT`, `INERT`, or `UNKNOWN`. The governance net is a broad
substring match applied first; the inert set is a tight exact-name allowlist
applied second; anything left is `UNKNOWN` and is **rejected**. Over-matching
costs a false rejection, under-matching would let a governance change through,
and only the second failure mode is unsafe. A compound name containing a
governance token therefore beats an inert-looking leaf — `audit_result_checksum`
is governance-relevant even though `checksum` alone is inert.

**2. Governance fields are compared per exact path and document role.** A
document's **role** is its authority class, and the
role is **derived from the path's basename** through a closed table. A basename
the table does not list resolves to `UNKNOWN` and is **rejected**; a
caller-declared role that contradicts the derivation is rejected too. Derivation
rather than declaration is the point: a role a caller could simply assert would
be a relabelling channel.

The table is **injective** — one role per distinct document kind, 23 of them. An
earlier draft grouped `AUDITOR_REPORT.md`, `AUDIT.md`, `AGY_AUDIT.md` and
`AUDITOR_REPAIR_REPORT.md` under a single `AUDIT_RESULT` role, on the theory that
same-role documents are interchangeable carriers of one authority. They are not
reliably interchangeable: a consumer reading only `AUDITOR_REPORT.md` would not
see an assertion moved into `AUDIT.md`, which is `GOV-AUD-001`'s own shape at
finer grain. Architecture section 08 rules that genuinely ambiguous semantic
status is classified as substantive, so grouping is refused. Splitting can only
ever reject more; it cannot admit a change grouping would have caught.

Exact path is also part of comparison identity. Relocation fails closed, and two
same-basename documents in different directories never share an aggregate.
Cross-directory risk and blocker swaps are therefore visible.

This closes `GOV-AUD-001`. The previous design compared a bundle-wide aggregate
and documented as a known boundary that content *exchanged* between two documents
would pass. That boundary was not safe: downstream consumers read these documents
differently, so a risk could be removed from the `AUDIT_RESULT` the PR Steward and
operator merge card actually consume and re-encoded in a `SUMMARY` with no
authority, leaving the bundle-wide totals identical. That is `GOV-AUD-F1` one
level up. The blessed positive fixture that required such a swap to pass is now a
negative fixture.

**3. Values are compared as a sorted multiset under a tuple key.**
The aggregate maps `(path, role, field_name)` to the sorted multiset of that
field's values. A multiset rather than a single value
per name, and a **tuple** rather than a concatenated string: an earlier design
disambiguated a repeated field by synthesising a `field#document` key, but that
key shared a namespace with real field names and was therefore forgeable. An
edited bundle could drop a risk from one document and re-encode it as a literal
`known_risks#B` key in another, reproducing the original aggregate exactly and
passing. A tuple key has no textual namespace for a crafted field name to collide
with. Regression fixtures cover the forgery directly.

**4. Structural conjuncts must be observed, not asserted.** See below.

### Anti-vacuity

The receipt enumerates every compared field with its classification and outcome,
so a vacuous evaluation is visibly different from a genuine one. The evaluator
rejects:

- an empty compared-field set while proof content exists
- a missing audited or successor bundle
- any unclassifiable field
- any governance-relevant mutation, even inside an allowed path
- any document whose role the path-derived table cannot place
- any declared role contradicting the derived one
- any structural conjunct that holds only on a claimed or unknown basis
- a frozen digest absent on both sides, which is an unmade comparison rather
  than an unchanged one
- a named digest path missing at either head
- a missing `raw_diff_digest`

`raw_diff_digest` is retained on every receipt so a laundered change stays
detectable post hoc, as the audit's finding requires.

### Structural conjuncts, and why a claim is not one

Architecture section 08 states eight conjuncts under
`WHEN_PROOF_ONLY_SUCCESSOR_IS_SUFFICIENT`; all must hold. Six are structural
facts about git, one is the semantic comparison, and the last is the conjunction
itself:

| Source conjunct | Implementation |
|---|---|
| `current_head_descends_from_or_is_patch_equivalent_to_audited_head` | observed via `git merge-base --is-ancestor`. Only descent is tested; patch-equivalence is permitted by the architecture but is not established here, so a non-descendant fails closed |
| `actual_changed_paths_subset_of_allowed_proof_only_paths` | observed via `git diff --name-only`, then checked against the allowlist; `non_allowed_diff_count` |
| `raw_diff_contains_no_substantive_source_change` | **derived**, never attested: path membership ∧ tree equality under exclusion |
| `audited_content_tree_equal_under_exclusion` | observed via `git ls-tree -r --full-tree` at both heads, filtered by the allowlist, digesting `mode type oid` per path — not the oid alone, since a permission change (`100644`→`100755`) or a type change (regular file → symlink) preserves the blob oid exactly while altering what the file is |
| `packet_and_policy_digests_unchanged` | observed by hashing the named files' bytes at each head; absent on both sides is an unmade comparison, not an unchanged one |
| `audit_result_bytes_unchanged` | same, for the named audit result |
| `no_new_finding_or_acceptance_criterion` | role-scoped semantic comparison — `blocking_findings` and `acceptance_criteria` are governance-relevant, so any change including an addition is rejected |
| `equivalence_validator_passes` | the evaluator itself, with anti-vacuity |

Each of the six structural conjuncts carries the **basis** on which it was
established: `OBSERVED_GIT`, `CLAIMED_INPUT`, or `UNKNOWN`. **Only `OBSERVED_GIT`
supports a `PASS`.** A conjunct that holds on a `CLAIMED_INPUT` basis produces a
`conjunct_not_observed:<name>` failure — the assertion may well be true, but
nothing here established it.

This closes `GOV-AUD-002`. Previously the evaluator accepted caller booleans for
ancestry, tree equivalence, raw-diff safety and every frozen digest, and the CLI
fed them straight from input JSON, so a caller could manufacture a `PASS` the
evaluator never established. The attestation for
`raw_diff_contains_no_substantive_source_change` has been removed outright rather
than re-based: it is now derived from two observed facts.

**Observation boundary.** Public observed evaluation takes `repo_root`, exact
heads and paths, then calls `snapshot.observe_proof_only_facts`, which reads Git
through a shape-validated read-only allowlist. Caller-constructed
`StructuralFacts` are labelled `CLAIMED_INPUT` and cannot produce diagnostic
`PASS`; public construction cannot label them `OBSERVED_GIT`. Receipt records
`observer_version` and an `observation_digest` over the observer's inputs and
outputs, so a later auditor **re-runs the observer and compares** rather than
taking receipt's word. None of this authorizes audit reuse.

## Failure normalization

The census's 44 failure branches map to eleven normalized classes, recorded in
`FAILURE_BRANCH_CENSUS`. This is deterministic checked-in data, not 44 new
workflow states.

```text
CONTROL_EVENT_NOT_FAILURE        INVALID_INPUT_OR_ARTIFACT
STALE_OR_MISMATCHED_EVIDENCE     VALIDATION_FAILURE
BLOCKING_FINDING                 AUTHORITY_OR_JUDGMENT_REQUIRED
CAPABILITY_UNAVAILABLE           EXTERNAL_SYSTEM_UNAVAILABLE
SCOPE_OR_CONTAINMENT_VIOLATION   SECURITY_OR_TRUST_INCIDENT
TERMINAL_REJECTION_OR_ROLLBACK
```

Several branches are control events rather than defects — main movement,
pre-commit mutation, `PASS_WITH_RISKS`, CI pending, review comment, deferred
review, PR Steward `NOT_READY`/`BLOCKED`, and rollback. They are routed, not
treated as failures.

**Carried caveat (audit note GOV-AUD-N3).** `F-32` (review thread) maps to
`BLOCKING_FINDING`, but architecture section 09 rules that an unresolved thread
is not automatically blocking absent policy or an authorized disposition. The
mapping is transcribed as the census states it; a consumer must condition it on
an authoritative blocking classification rather than inferring blocking status.

## Identity and isolation

Consequential G0 reductions always require `project_id`, `repository_id`,
`worktree_id` and `packet_id`. `workspace_id` and `instance_id` are optional,
but must match exactly when both expected and observed values are present. Git subjects
preserve `base_sha`, `head_sha`, `tree_sha` and `content_digest` separately.

Unknown identity fails closed — blank, missing, or the literal `UNKNOWN` is
denied. Cross-project reuse is forbidden. Cross-worktree reuse is forbidden
absent an explicit deterministic equivalence.

Missing, blank or `UNKNOWN` core dimension is denied. No caller argument or JSON
profile can remove a core dimension. Operator options may only add future
strictness; G0 exposes no weakening option.

This closes `GOV-AUD-004`, where absence was explicitly compatible and a fully
bound identity therefore accepted a project-and-repo-only one as equivalent —
leaving no mechanical way to enforce the packet's own isolation rule. The profile
applies to envelope evidence, receipt reuse, and snapshot evidence.

## Receipt reuse

A deterministic receipt may be reused only when all ten conjunctive conditions
hold:

```text
same_subject_digest
same_required_input_digests
same_policy_digest
same_schema_digest
same_tool_or_validator_version
same_environment_scope_when_environment_matters
producer_identity_still_trusted
not_expired_when_freshness_is_semantic
not_superseded_or_tombstoned
consumer_adds_no_distinct_authority_or_live_state_check
```

Otherwise: recompute, or mark stale. A receipt is **never** reused merely because
its path or filename is unchanged. Every decision enumerates all ten outcomes, so
a genuine pass is distinguishable from a vacuous one.

## Determinism

No module reads a clock. Every staleness calculation takes an explicit `as_of`,
so identical inputs always produce identical output. Canonical JSON uses sorted
keys and stable separators; digests are SHA-256 over that encoding.

## Read-only containment

`snapshot.py` reads local git through a `shell=False` subprocess restricted to a
**shape allowlist**: each entry is a fixed argv template whose only parameterised
positions are `<sha>` and `<blobspec>`. A `<sha>` must be exactly 40 or 64
lowercase hexadecimal characters; a
`<blobspec>` is `<sha>:<path>` with no absolute path, no NUL and no `..` segment.
Anything else — a write verb, an option-shaped argument, a traversal — raises a
containment denial before reaching the process. The package contacts no network
service, invokes no auditor or runner, and writes no workflow state, proof or
cache.

## Inspection CLI

```bash
python -m dopemux.governed_delivery.cli validate-ref <json>
python -m dopemux.governed_delivery.cli validate-envelope <json>
python -m dopemux.governed_delivery.cli equivalence --audited <path> --successor <path> \
    --repo-root <path> [--packet-path <p>] [--policy-path <p>] [--audit-result-path <p>]
python -m dopemux.governed_delivery.cli snapshot --repo-root <path> \
    --packet <path> --as-of <instant>
```

`equivalence` requires `--repo-root`; no caller-facts input exists. Its exit-zero
diagnostic result still has `authority_effect=NONE` and cannot preserve audit.

Exit codes: `0` accepted, `1` denied or not equivalent, `2` usage error. No
command mutates external state.

## Post-audit closure

Final independent audit is external exact-head evidence. G0 does not edit tracked
`PROOF.json` or `SUMMARY.md` after audit to mirror verdict, identity or findings.
Existing GitHub audit artifacts and PR Steward exact-head consumption carry that
closure. If repository policy later requires a tracked post-audit artifact,
implementation stops for a new closure contract; no proof-only exception is
invented here.

## Out of scope for G0

Task Orchestrator writes or transitions; GitHub webhooks, status writes, review
mutation, merge or mark-ready; audit broker dispatch; implementer or repair
dispatch; DCP, Second Brain or GPT-facade changes; ConPort, Leantime,
dope-memory or dope-context writes; any persistent database, service, daemon,
MCP server, cache, credential store or network listener.

Five contracts named by architecture section 15 are deliberately deferred:
`ContentFreezeReceipt`, `LiveFinalitySnapshot`, `WorkflowTransitionReceipt v2`,
`DispatchToken` and `BenchmarkRecord`.

## Related

- [Proof Contract](../proof-contract.md)
- [Evidence Economy](../evidence-economy.md)
- [Governance Model](../governance-model.md)
