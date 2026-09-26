# Supervisor MacroPacket Contract v1

Schema: `control_tower.supervisor_macro_packet.v1`.

A MacroPacket is a multi-workstream delegation envelope, never a pooled authority
token. The supervisor issues it; the team lead coordinates it. Canonical child
Task Packets remain repository-owned immutable artifacts, not a new nested kit
packet schema.

## Required envelope

The installed schema requires identity/objective/repository/base policy, global
constraints, a coordinator ExecutionBinding reference, child workstreams, DAG
dependencies/joins, parallel limits, evidence budget and aggregate-return rules.
Each child retains its objective, preferred/fallback route tuples, delivery risk,
DCP status/class, workflow reference, allowed/forbidden actions, write surfaces,
canonical writers, semantic scope, rollback boundary and audit/return requirements.

Child packet and coordinator references use `{path, sha256}`: relative regular
package members, no symlink traversal, exact digest match. Coordinator binding
must validate and bind this macro_id. Child formats remain opaque to the kit;
repository adapters own parsing/authentication of canonical child authority.
Digest equality establishes byte integrity, not authorship or execution authority.

The JSON template contains placeholder paths/digests. It is a structural example;
it cannot pass package admission until replaced with actual immutable references.

## Read-only validation and previews

`ct validate-macro --file SUPERVISOR_MACRO_PACKET.json` checks schema, reference
integrity, coordinator binding, child/edge identities, acyclicity, joins and every
parallel pair. Success is STATIC_VALID with authority NONE, never authorization.

Write overlap accepts literal relative paths and terminal directory prefixes
(`path/` or `path/**`). Other glob syntax fails closed. Path comparisons
conservatively fold case. Shared semantic scope or canonical writer blocks
parallel mutation; a transitive DAG dependency explicitly serializes the pair.
Read-only companions may coexist subject to external custody/workflow checks.

`preview_macro(macro, snapshots)` is a pure, advisory projection for tests and
future project adapters. It never invokes a runner, queries a service, writes
workflow state, advances a transition or accepts a result. It does not authenticate
snapshot producers or implement a DCP/Task Orchestrator integration.

A project adapter must first validate immutable package references and authenticate
current upstream snapshots. It supplies one child-specific snapshot, bound by
task_packet_sha256, containing:

- canonical_authority: allowed/forbidden actions, exact delivery lane, semantic
  scope/canonical writers, write allowlist, rollback, mutating flag, audit
  obligation and exact preferred/fallback route set;
- verified_upstream plus physical write/custody verification from actual sources;
- applicable operator/repository action ceilings, denials and source references;
- legal workflow status, blockers, actions and source reference;
- policy applicability, status, action bounds, denials and audit requirements;
- actual child status, operator gate verification, route failure/fallback choice;
- verified completion and its source reference when satisfying a dependency.

These flags are an internal adapter contract, not self-attestable model fields.
Passing a model-authored dictionary cannot create execution authority. Unverified,
unknown, blocked or mismatched inputs hold the affected child. Generic projects
without DCP explicitly supply required=false and NOT_APPLICABLE, retaining
dcp_status=NOT_RUN; applicable DCP UNKNOWN/BLOCKED never becomes a candidate.

Candidate batches are inert proposals. A current canonical workflow gate must
still authorize scheduling and execution outside this kit. Claimed PASS requires
verified, subject-bound completion evidence before satisfying a dependency.
Independent failures hold dependents, not unrelated legal siblings. An observed
global stop propagates to every child; listing stop conditions does not trigger them.

The derived dcp_summary has authority NONE, keeps child DCP statuses separate and
computes maximum delivery lane without mapping the risk taxonomies.

## Delegation and audit invariants

A child cannot take another child's actions or write allowlist, omit known
canonical writers/semantic scope, change its risk/rollback, remove denials, waive
audit or use a non-authorized fallback. Effective obligations include repository,
operator, workflow and applicable policy requirements. L3 holds at its operator
gate while legal L0/L1 siblings may continue.

The coordinator cannot create canonical packets across authority/risk/writer/
rollback/audit/security/activation boundaries, change operator-only gates,
grant merge/activation, or independently audit its own supervised implementation.
An actual collision, unknown canonical truth, authority conflict, required audit
failure or route ceiling failure triggers the applicable supervisor return.

## Aggregate returns

`macro_return(macro, child_returns)` preserves child reports and validates child/
receipt subject binding. It emits RETURNED_FOR_SUPERVISOR or BLOCKED, authority
NONE. It never emits a global PASS/READY/DONE verdict. Proof/audit receipts bind
both task_packet_sha256 and execution_subject; mismatches block the return.
Operator gates and supervisor decisions are surfaced, not inferred away.

Returns retain macro subject and coordinator binding, each child packet/status/
subject/route/files/validation/proof/audit/blockers/next legal action, joins,
unknowns/conflicts and required decisions. Actual audit/proof acceptance remains
with canonical external authorities. No finality can be minted by aggregation.

Manual supervisor-issued multi-workstream coordination is supported. Autonomous
creation/promotion/next-action dispatch remains deferred to separately authorized
governed-delivery work.
