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

`next_legal_action` is a recommendation. `dispatch_eligible` is structurally
`false` throughout G0.

### ContentAuditBinding v1

Binds a supplied auditor judgment to an immutable subject. **No G0 runtime may
invoke an auditor**; this object only represents a result produced elsewhere.

The five auditor identity layers are recorded separately and never collapsed, so
an `UNKNOWN` provider attestation stays visible instead of being silently
upgraded to a proven identity.

### ProofOnlySuccessorEquivalence v1

Closes the blocking acceptance requirement `GOV-AUD-F1`. See below.

### OperatorDecisionRequest v1

Requests authority; creating one grants nothing. Five decision types, each
routing to a human.

## GOV-AUD-F1: semantic proof-only equivalence

The independent architecture audit constructed this attack against a
path-membership predicate:

> The path-membership predicate cannot detect a semantic change *inside* an
> allowed proof-only path: hand-editing the proof bundle's known risks/unknowns
> fields or evidence-ref list passes every equivalence conjunct yet alters
> governance-relevant content the PR Steward and operator merge card consume — a
> laundered semantic change with no re-audit and no supervisor review.

A path allowlist is therefore **necessary but not sufficient**. Two design
choices answer the attack.

**1. Classification is total and fails closed.** Every compared field resolves to
`GOVERNANCE_RELEVANT`, `INERT`, or `UNKNOWN`. The governance net is a broad
substring match applied first; the inert set is a tight exact-name allowlist
applied second; anything left is `UNKNOWN` and is **rejected**. Over-matching
costs a false rejection, under-matching would let a governance change through,
and only the second failure mode is unsafe. A compound name containing a
governance token therefore beats an inert-looking leaf — `audit_result_checksum`
is governance-relevant even though `checksum` alone is inert.

**2. Governance fields are compared as a path-independent aggregate.** Relocating
a proof reference with byte identity leaves the aggregate untouched and passes,
while semantic drift fails regardless of which file carries it.

The aggregate maps each field name to the **sorted multiset of its values**
across all documents. A multiset rather than a single value per name: an earlier
design disambiguated a field repeated across documents by synthesising a
`field#document` key, but that key shared a namespace with real field names and
was therefore forgeable. An edited bundle could drop a risk from one document and
re-encode it as a literal `known_risks#B` key in another, reproducing the
original aggregate exactly and passing equivalence. Counting values removes the
synthesised namespace, so no crafted field name can restore a multiset that a
dropped value has changed. Regression fixtures cover the forgery directly.

**Known boundary.** Because the aggregate is path-independent, content
*exchanged* between two documents that both remain in the bundle preserves it and
passes. This contract asserts that the bundle's set of governance assertions is
unchanged; it deliberately does not bind an assertion to the particular document
carrying it, since that binding is what a byte-identical relocation must be
allowed to break.

### Anti-vacuity

The receipt enumerates every compared field with its classification and outcome,
so a vacuous evaluation is visibly different from a genuine one. The evaluator
rejects:

- an empty compared-field set while proof content exists
- a missing audited or successor bundle
- any unclassifiable field
- any governance-relevant mutation, even inside an allowed path

`raw_diff_digest` is retained on every receipt so a laundered change stays
detectable post hoc, as the audit's finding requires.

### Structural conjuncts

Architecture section 08 states eight conjuncts under
`WHEN_PROOF_ONLY_SUCCESSOR_IS_SUFFICIENT`; all must hold. The evaluator
implements each one:

| Source conjunct | Implementation |
|---|---|
| `current_head_descends_from_or_is_patch_equivalent_to_audited_head` | `ancestry_established` with `ancestry_basis` (`UNKNOWN` fails closed, since the evaluator performs no I/O) |
| `actual_changed_paths_subset_of_allowed_proof_only_paths` | path allowlist check, `non_allowed_diff_count` |
| `raw_diff_contains_no_substantive_source_change` | `raw_diff_contains_no_substantive_source_change` attestation |
| `audited_content_tree_equal_under_exclusion` | `content_tree_equivalent_under_exclusion` |
| `packet_and_policy_digests_unchanged` | `packet_digest_unchanged`, `policy_digest_unchanged` |
| `audit_result_bytes_unchanged` | `audit_result_digest_unchanged` |
| `no_new_finding_or_acceptance_criterion` | semantic aggregate — `blocking_findings` and `acceptance_criteria` are governance-relevant, so any change including an addition is rejected |
| `equivalence_validator_passes` | the evaluator itself, with anti-vacuity |

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

Consequential reductions bind `project_id`, `repository_id`, `workspace_id`,
`worktree_id`, `instance_id` and `packet_id` where applicable. Git subjects
preserve `base_sha`, `head_sha`, `tree_sha` and `content_digest` separately.

Unknown identity fails closed — blank, missing, or the literal `UNKNOWN` is
denied. Cross-project reuse is forbidden. Cross-worktree reuse is forbidden
absent an explicit deterministic equivalence.

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

`snapshot.py` reads local git through a fixed-argv, `shell=False` subprocess
restricted to a four-command read allowlist; anything else raises a containment
denial. The package contacts no network service, invokes no auditor or runner,
and writes no workflow state, proof or cache.

## Inspection CLI

```bash
python -m dopemux.governed_delivery.cli validate-ref <json>
python -m dopemux.governed_delivery.cli validate-envelope <json>
python -m dopemux.governed_delivery.cli equivalence --audited <path> --successor <path>
python -m dopemux.governed_delivery.cli snapshot --packet <path> --as-of <instant>
```

Exit codes: `0` accepted, `1` denied or not equivalent, `2` usage error. No
command mutates external state.

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
