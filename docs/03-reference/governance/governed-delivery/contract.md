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

**Repair cycle 1.** The schemas remain at `v1` — nothing has merged and there are
no consumers — but the equivalence evaluator's semantics changed, so
`validator_version` is now `governed-delivery.equivalence.2`. Four blocking
findings from the independent L2 audit of content head `8c309d76` are closed
here: `GOV-AUD-001` (cross-role governance laundering), `GOV-AUD-002` (caller
attestations satisfying PASS-bearing conjuncts), `GOV-AUD-003` (READY and phase
advancement from an incomplete gate ledger), and `GOV-AUD-004` (absent identity
dimensions treated as wildcards). Each is described in place below.

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

**A required gate with no entry is missing evidence, not silence.** The ledger
carries architecture section 05's `policy.required_gate_set`, defaulting to
**every** gate class. Any required class without an entry is materialized as a
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

Exactly two things may be stepped over: a gate explicitly marked
`NOT_APPLICABLE`, and a class that is **both absent and not required**. Neither
is a barrier, and neither is evidence of arrival, so both are skipped without
advancing. A gate that is *present* in a non-satisfied state — `UNSATISFIED`,
`BLOCKED`, `STALE`, `UNKNOWN`, `CONFLICTING` or `PENDING` — halts advancement
**even when the policy does not require it**: "not required" excuses an absence,
never a visible failure. Adversarial probing during repair cycle 1 found that
stepping over a present-but-failed unrequired gate reintroduced `GOV-AUD-003`'s
defect class one level down; a parametrized regression covers all six states.

Because the profile is policy data, a deliberately narrow `required_gate_set`
does let a lane report a late phase from few gates. That is a governance-owned
declaration, not an inference: the default is all fifteen classes, and the
effective profile is emitted as `required_gate_classes` alongside
`missing_required_gate_classes` so a reader can see what was and was not demanded.

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

A path allowlist is therefore **necessary but not sufficient**. Four design
choices answer the attack and the follow-up audit's findings.

**1. Classification is total and fails closed.** Every compared field resolves to
`GOVERNANCE_RELEVANT`, `INERT`, or `UNKNOWN`. The governance net is a broad
substring match applied first; the inert set is a tight exact-name allowlist
applied second; anything left is `UNKNOWN` and is **rejected**. Over-matching
costs a false rejection, under-matching would let a governance change through,
and only the second failure mode is unsafe. A compound name containing a
governance token therefore beats an inert-looking leaf — `audit_result_checksum`
is governance-relevant even though `checksum` alone is inert.

**2. Governance fields are compared per document role, not per path and not
across the whole bundle.** A document's **role** is its authority class, and the
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

Relocating a document keeps its role, because relocation preserves the basename:
`proof/A/PROOF.json` to `proof/B/PROOF.json` stays `PROOF_BUNDLE`. Moving an
assertion to a document of a *different* role does not, and neither does renaming
the document that carries a verdict.

The one residual same-role case is two files with the **same basename** in
different directories; their multisets merge, so a swap between them is
invisible while a drop is not. That is the exact behaviour relocation requires.

This closes `GOV-AUD-001`. The previous design compared a bundle-wide aggregate
and documented as a known boundary that content *exchanged* between two documents
would pass. That boundary was not safe: downstream consumers read these documents
differently, so a risk could be removed from the `AUDIT_RESULT` the PR Steward and
operator merge card actually consume and re-encoded in a `SUMMARY` with no
authority, leaving the bundle-wide totals identical. That is `GOV-AUD-F1` one
level up. The blessed positive fixture that required such a swap to pass is now a
negative fixture.

**3. Within a role, values are compared as a sorted multiset under a tuple key.**
The aggregate maps `(role, field_name)` to the sorted multiset of that field's
values across the documents of that role. A multiset rather than a single value
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

**Trust boundary, stated plainly.** Facts are produced by
`snapshot.observe_proof_only_facts`, which reads git through a shape-validated
read-only allowlist. The evaluator itself still performs no I/O; observation and
judgement are separate so each is testable. The receipt records
`observer_version` and an `observation_digest` over the observer's inputs and
outputs, so a later auditor **re-runs the observer and compares** rather than
taking the receipt's word. An in-process caller can of course construct facts
labelled `OBSERVED_GIT` directly; what the design guarantees is that the
operator-facing CLI cannot, and that a receipt's claim to have observed is
independently reproducible.

Without `--repo-root` the CLI has nothing to observe from, so it records the
input document's values as `CLAIMED_INPUT` and the evaluation cannot pass.

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

**"Where applicable" is mechanical, and absence is not compatibility.** A
dimension present on both sides must match exactly; a *required* dimension absent
on either side is denied. The applicable set is every dimension the expected
identity actually binds, plus `packet_id` for any packet-scoped reduction. So an
expectation bound to `worktree_id=wt-1` refuses evidence that declines to say
which worktree it came from, rather than treating the silence as a match.

This closes `GOV-AUD-004`, where absence was explicitly compatible and a fully
bound identity therefore accepted a project-and-repo-only one as equivalent —
leaving no mechanical way to enforce the packet's own isolation rule. The profile
applies to envelope evidence, receipt reuse, and snapshot evidence.

Precedence for the profile, strongest first: operator `--require-identity-dimension`
flags, then the packet's declared `repo_binding.required_identity_dimensions`,
then inference from what the expected identity binds. Declaration outranks
inference deliberately — inference is weak precisely when it matters, since a
caller who constructs a sparse expected identity would otherwise face a sparse
profile. The packet is the authority on which dimensions apply to its own work.

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
positions are `<sha>` and `<blobspec>`. A `<sha>` must match `[0-9a-f]{7,64}`; a
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
python -m dopemux.governed_delivery.cli snapshot --packet <path> --as-of <instant> \
    [--require-identity-dimension <name> ...]
```

`equivalence` without `--repo-root` records the supplied structural values as
`CLAIMED_INPUT` and therefore cannot return `PASS`.

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
