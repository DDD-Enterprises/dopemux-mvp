---
id: g0-lite-implementation-authority
title: G0 Lite Implementation Authority
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-26'
last_review: '2026-08-26'
next_review: '2026-11-24'
prelude: G0 Lite Implementation Authority (reference) for dopemux documentation and developer workflows.
---
# G0-Lite Implementation Authority

```text
AUTHORITY_RECORD_ID=DMX-GOV-G0-LITE-IMPLEMENTATION-AUTHORITY-001
AUTHORITY_CLASS=SUPERVISOR_IMPLEMENTATION_AUTHORITY
REPOSITORY=DDD-Enterprises/dopemux-mvp

PACKET_ID=TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-G0-LITE-001
PACKET_SHA256=5d636307ad1ba7b6ec1498cac4fd79afcf9f480c9b96dad208f3f03e3f807cc9
PACKET_BLOB=cfbd08daad4e2b3c9550fc36fc287829eaffb01f

IMPLEMENTATION_BASE=c7bc2fb479d7386825df73e028acdce723ee3388
SOURCE_CUSTODY_PR=1268
SOURCE_CUSTODY_SHA=caa4ec2913d0463c7e38835029f3f7adeb915ac6
SOURCE_MERGE_BASE=d40e43dd70307d2c000a4efd581be7c11248728c
SOURCE_OVERLAP=COMPATIBLE
SOURCE_SHARED_PATHS=0

AUTHORITY_RECORD_AUTHORING=YES
AUTHORITY_RECORD_PUSH=YES
AUTHORITY_RECORD_PR_CREATION=YES
AUTHORITY_RECORD_IMPLEMENTATION_EFFECTIVE_BEFORE_MERGE=NO

IMPLEMENTATION_AUTHORIZED=YES_WHEN_EFFECTIVE_CONDITIONS_PASS
RUNNER=DIRECT_CODEX
AGENT_CEILING=ONE_DELEGATED_CODEX_PRIMARY_NO_NESTED_SUBAGENTS
DOPETASK_EXECUTION_ROUTE=FORBIDDEN_NOT_IMPLEMENTED

FINAL_AUDITOR=DIRECT_CLAUDE_CODE
FINAL_AUDIT_COUNT=ONE
FINAL_AUDITOR_SUBAGENTS=0
FINAL_AUDITOR_INDEPENDENCE=DIFFERENT_MODEL_FAMILY_FROM_IMPLEMENTER_REQUIRED

TASK_ORCHESTRATOR_MUTATION=FORBIDDEN
GITHUB_MUTATION_BY_G0_LITE_RUNTIME=FORBIDDEN
AUTOMATIC_DISPATCH=FORBIDDEN
MERGE_AUTHORITY_FROM_THIS_RECORD=NONE
ACTIVATION_AUTHORITY_FROM_THIS_RECORD=NONE
PR_1268_MUTATION=FORBIDDEN
```

## 1. Decision

The supervisor authorizes one bounded G0-Lite implementation run under
`TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-G0-LITE-001`, but this authority becomes
effective only after this exact authority record is independently validated,
merged to `main`, and reharvested from current `main`.

Before those effective conditions pass:

```text
IMPLEMENTATION_AUTHORIZED=NO
```

After those effective conditions pass:

```text
IMPLEMENTATION_AUTHORIZED=YES
```

only for the exact scope, base, runner ceiling, and stop conditions below.

This record does not authorize merge of the implementation PR, activation,
automatic dispatch, Task Orchestrator mutation, or any mutation of PR #1268.

## 2. Authority basis

This record binds the exact merged G0-Lite Task Packet:

```text
PACKET_ID=TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-G0-LITE-001
PACKET_SHA256=5d636307ad1ba7b6ec1498cac4fd79afcf9f480c9b96dad208f3f03e3f807cc9
PACKET_BLOB=cfbd08daad4e2b3c9550fc36fc287829eaffb01f
```

and the exact implementation base:

```text
IMPLEMENTATION_BASE=c7bc2fb479d7386825df73e028acdce723ee3388
```

The implementation base is provenance-bearing for this authority grant.

If the authority-record publication itself moves `main`, the implementation worktree
must start from the authority-record merge commit on current `main`, while proving that
the original bound base `c7bc2fb479d7386825df73e028acdce723ee3388` is its ancestor and that intervening
changes are authority-record-only or otherwise non-overlapping with the substantive
G0-Lite payload.

A generic requirement that execution HEAD equal `c7bc2fb4...` after this authority
record merges is forbidden because the act of publishing this record necessarily
advances `main`.

## 3. Source custody

PR #1268 is an evidence donor only.

```text
PR=1268
EXPECTED_SOURCE_SHA=caa4ec2913d0463c7e38835029f3f7adeb915ac6
EXPECTED_MERGE_BASE=d40e43dd70307d2c000a4efd581be7c11248728c
OBSERVED_MAIN_PATHS=EMPTY
OBSERVED_SOURCE_PATHS=ALL_17
OBSERVED_SHARED_PATHS=EMPTY
OBSERVED_OVERLAP=COMPATIBLE
```

The implementer must re-prove source custody before reading donor payload.

PR #1268 remains:

```text
MUTATION_AUTHORIZED=NO
MERGE_AUTHORIZED=NO
MARK_READY_AUTHORIZED=NO
CLOSE_AUTHORIZED=NO
REBASE_AUTHORIZED=NO
REWRITE_AUTHORIZED=NO
REPAIR_CYCLE_3_AUTHORIZED=NO
```

No merge, cherry-pick, wholesale branch import, or proof transplant from PR #1268 is authorized.

## 4. Substantive implementation allowlist

The implementation may create or modify only these 17 substantive payload paths:

```text
docs/03-reference/governance/governed-delivery/contract.md

schemas/governed_delivery/evidence-reference.schema.json
schemas/governed_delivery/governed-delivery-envelope.schema.json
schemas/governed_delivery/gate-ledger.schema.json
schemas/governed_delivery/work-item-projection.schema.json
schemas/governed_delivery/content-audit-binding.schema.json

src/dopemux/governed_delivery/__init__.py
src/dopemux/governed_delivery/models.py
src/dopemux/governed_delivery/receipts.py
src/dopemux/governed_delivery/snapshot.py
src/dopemux/governed_delivery/cli.py

tests/unit/governed_delivery/__init__.py
tests/unit/governed_delivery/test_models.py
tests/unit/governed_delivery/test_receipts.py
tests/unit/governed_delivery/test_snapshot.py
tests/unit/governed_delivery/test_cross_project_denial.py
tests/unit/governed_delivery/test_schema_conformance.py
```

Packet proof may be written only under:

```text
proof/TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-G0-LITE-001/**
```

The following path is authority input and is immutable during implementation:

```text
task-packets/TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-G0-LITE-001.json
```

Any packet-byte change invalidates this authority record.

The authority record itself is also immutable during the implementation run:

```text
docs/03-reference/governance/governed-delivery/g0-lite-implementation-authority.md
```

## 5. Scope authorized

The one bounded implementer may implement only the G0-Lite responsibilities defined
by the bound Task Packet:

```text
EvidenceReference representation
GovernedDeliveryEnvelope representation
GateLedger evidence representation
native-state preservation
blocker representation
navigational phase/status projection
deterministic freshness
message normalization
failure normalization
read-only inspection
schema/runtime conformance
```

All outputs remain:

```text
DERIVED
READ_ONLY
NON_AUTHORITATIVE
```

G0-Lite does not own or decide:

```text
READY posture
audit acceptability
auditor independence sufficiency
PASS_WITH_RISKS acceptance
proof-only audit reuse
next-action legality
dispatch eligibility
PR readiness
merge readiness
activation readiness
workflow transitions
```

## 6. Explicit exclusions

Forbidden:

```text
ProofOnlySuccessorEquivalence
proof-only audit reuse
OperatorDecisionRequest
NextLegalAction
dispatch_eligible

Task Orchestrator writes
Task Orchestrator transition changes
Task Orchestrator persistence changes

GitHub command-plane behavior
GitHub mutation from runtime code
review mutation from runtime code
merge or auto-merge behavior

Dopetask runner implementation
Dopetask Codex adapter repair
automatic implementer dispatch
automatic auditor dispatch

DCP runtime changes
Second Brain changes
Knowledge Compiler changes
Materialized Wiki changes
GPT facade changes
Universal Router changes
Audit Broker implementation

new database
new service
new daemon
new MCP server
new persistent cache
new credential store
new listener
new provider/API dependency
```

## 7. Implementer route

Authorized route:

```text
RUNNER=DIRECT_CODEX
AGENT_CEILING=ONE_DELEGATED_CODEX_PRIMARY_NO_NESTED_SUBAGENTS
```

The current `dopetask tp exec --agent codex` route is explicitly not authorized as a
substitute because current evidence reports that route as unimplemented.

Before first payload mutation record:

```text
RUNNER_REQUESTED=DIRECT_CODEX
RUNNER_CONFIGURED=
MODEL_REQUESTED=
MODEL_CONFIGURED=
MODEL_RESPONSE_CLAIMED=
MODEL_PROXY_REPORTED=
MODEL_PROVIDER_ATTESTED=
```

Unknown identity layers remain `UNKNOWN`.

The exact Codex model selector is not fixed by this record because current live evidence
did not prove one. This does not permit model substitution through another runner.
The execution route must remain direct Codex.

No subagents, research forks, delegated coding agents, background implementers, or
parallel mutation agents are authorized.

Read-only deterministic helper commands are allowed.

## 8. Worktree and base requirements

Implementation must occur in a fresh dedicated worktree.

The dirty primary checkout is forbidden for payload implementation.

Before mutation:

```text
1. Fetch current origin/main.
2. Verify the authority record exists on current main.
3. Verify this authority record's bytes/digest against the independently validated
   authority subject.
4. Verify the Task Packet SHA-256 is exactly
   5d636307ad1ba7b6ec1498cac4fd79afcf9f480c9b96dad208f3f03e3f807cc9.
5. Verify `c7bc2fb479d7386825df73e028acdce723ee3388` is an ancestor of execution main.
6. Compute all changes from `c7bc2fb4...` to execution main.
7. Require those intervening changes to be authority-publication-only or otherwise
   non-overlapping/compatible with all 17 substantive payload paths.
8. Create a fresh worktree from the reharvested current main.
9. Verify clean status before first payload edit.
```

If publication introduces substantive overlap:

```text
STOP_RELEVANT_MAIN_DRIFT
```

## 9. Source-custody gate

Before reading donor payload:

```text
1. Bounded-fetch refs/pull/1268/head into a SHA-qualified local custody ref.
2. Require that ref^{commit} to equal
   caa4ec2913d0463c7e38835029f3f7adeb915ac6.
3. Require exactly one merge base.
4. Compute MAIN_PATHS and SOURCE_PATHS across the exact 17-path payload.
5. Compute SHARED_PATHS as the exact intersection.
6. Compare final path state for every shared path.
7. Classify overlap using the packet's six-class vocabulary.
```

Only:

```text
COMPATIBLE
IDENTICAL
SUBSET
```

may proceed automatically.

`SUPERSET` requires supervisor adjudication.

`CONFLICTING` or `UNKNOWN` stops.

The existing harvest:

```text
MAIN_PATHS=EMPTY
SOURCE_PATHS=ALL_17
SHARED_PATHS=EMPTY
OVERLAP=COMPATIBLE
```

is authoring evidence and must be revalidated, not blindly inherited.

## 10. Validation requirements

At minimum run the bound packet's current deterministic gates:

```text
Task Packet schema validation
all governed-delivery JSON Schema validation
runtime/schema conformance
ruff
focused governed-delivery tests
complete affected tests required by imports/ownership
validate_audit_proof.py
validate_change_contract.py
pre-commit for changed range
git diff --check
canonical secret/sensitive-data scan
no-network/no-external-mutation containment tests
```

A test failure, schema mismatch, hidden mutation path, or path outside the authority
allowlist is a hard stop until repaired within scope or escalated.

No model audit is run on intermediate commits.

## 11. Content freeze

After implementation and deterministic validation:

```text
CONTENT_HEAD=
CONTENT_TREE=
CONTENT_DIGEST=
CHANGED_PATHS=
PACKET_SHA256=5d636307ad1ba7b6ec1498cac4fd79afcf9f480c9b96dad208f3f03e3f807cc9
AUTHORITY_RECORD_REF=
```

Freeze the substantive subject.

Any substantive repair after freeze creates a new subject.

## 12. Final independent audit

Exactly one final independent audit is authorized after content freeze.

```text
AUDITOR_ROUTE=DIRECT_CLAUDE_CODE
AUDITOR_COUNT=ONE_FINAL_ONLY
AUDITOR_SUBAGENTS=0
IMPLEMENTER_INDEPENDENCE=REQUIRED
DIFFERENT_MODEL_FAMILY=REQUIRED
```

Record separately:

```text
AUDITOR_REQUESTED_IDENTITY=
AUDITOR_CONFIGURED_IDENTITY=
AUDITOR_RESPONSE_CLAIMED_IDENTITY=
AUDITOR_PROXY_REPORTED_IDENTITY=
AUDITOR_PROVIDER_ATTESTED_IDENTITY=
INDEPENDENCE=
```

Accepted substantive verdicts:

```text
PASS
PASS_WITH_RISKS
```

`PASS_WITH_RISKS` may proceed only if every risk is explicitly nonblocking under
existing governance.

Hard stop:

```text
FAIL
NEEDS_SUPERVISOR
SKIPPED
MALFORMED
HEAD_MISMATCH
SUBJECT_MISMATCH
UNKNOWN_REQUIRED_AUDITOR_IDENTITY
```

No auditor shopping after a substantive verdict.

## 13. Proof and PR finality

After acceptable final audit:

```text
1. Produce/update canonical packet proof.
2. Validate proof mechanically.
3. Push only after all required pre-push gates pass.
4. Create/update the implementation PR.
5. Resolve review findings only within active scope.
6. Run current exact-head PR Steward.
7. Stop for operator merge decision.
```

This record does not authorize implementation PR merge.

```text
IMPLEMENTATION_PR_MERGE_AUTHORIZED=NO
```

## 14. Hard stop conditions

Stop before further mutation if any of the following occurs:

```text
authority record missing from current main
authority record bytes differ from validated subject
packet SHA-256 differs
packet bytes change
bound base is not ancestor of current main
relevant main drift is CONFLICTING or UNKNOWN
source custody SHA mismatch
PR #1268 changes unexpectedly
source overlap is CONFLICTING or UNKNOWN
worktree is dirty before first payload edit
path outside allowlist is required
scope needs expansion
subagent/delegated implementer would be required
Task Orchestrator mutation would be required
GitHub mutation would be introduced in runtime
new service/database/cache/listener/dependency would be required
provider/network behavior would be introduced
identity/project/worktree/packet binding cannot be proven
validation fails and cannot be repaired within scope
secret scan cannot be run
final auditor identity/independence is insufficient
final audit is nonpassing
PR head moves after finality evidence
PR Steward is not READY
```

## 15. Rollback

G0-Lite is new read-only derived functionality.

Rollback is:

```text
revert/remove G0-Lite source, schemas, tests, and contract
preserve packet/audit/proof history
do not mutate canonical workflow/project state
```

There is no database migration, Task Orchestrator state migration, credential migration,
or production-data rollback authorized by this record.

## 16. Effective conditions

This authority becomes effective only if all are true:

```text
E1=this exact record is independently validated as matching the supervisor-issued text
E2=the validation binds the record digest and the packet digest
E3=the authority-record PR passes required repository checks
E4=the authority-record PR is merged to main under separate operator merge authority
E5=current main is reharvested after merge
E6=current main contains this authority record at the required path
E7=current main contains the exact bound Task Packet bytes
E8=c7bc2fb479d7386825df73e028acdce723ee3388 is an ancestor of current main
E9=intervening main movement is non-overlapping/compatible with the 17 payload paths
E10=direct Codex remains available
```

If any effective condition fails:

```text
IMPLEMENTATION_AUTHORIZED=NO
STOP_IMPLEMENTATION_AUTHORITY_NOT_EFFECTIVE
```

## 17. Publication authority

The operator/supervisor authorizes materializing this exact authority record through a
bounded documentation-only publication flow.

Authorized before implementation:

```text
CREATE_EXACT_AUTHORITY_RECORD=YES
COMMIT_EXACT_AUTHORITY_RECORD=YES
PUSH_AUTHORITY_RECORD_BRANCH=YES
CREATE_AUTHORITY_RECORD_PR=YES
UPDATE_AUTHORITY_RECORD_PR_WITH_NONSEMANTIC_PROOF_ONLY_EVIDENCE=YES
RUN_REQUIRED_CI=YES
RUN_ONE_INDEPENDENT_AUTHORITY_BINDING_VALIDATION=YES
RUN_PR_STEWARD=YES
```

Not granted by this record:

```text
AUTHORITY_RECORD_PR_MERGE=NO
G0_LITE_IMPLEMENTATION_BEFORE_AUTHORITY_RECORD_MERGE=NO
IMPLEMENTATION_PR_MERGE=NO
ACTIVATION=NO
```

Any semantic change to this authority record requires fresh supervisor approval.

## 18. Final supervisor binding

```text
DECISION=AUTHORIZE_G0_LITE_IMPLEMENTATION_CONDITIONALLY

PACKET_ID=TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-G0-LITE-001
PACKET_SHA256=5d636307ad1ba7b6ec1498cac4fd79afcf9f480c9b96dad208f3f03e3f807cc9
PACKET_BLOB=cfbd08daad4e2b3c9550fc36fc287829eaffb01f

BOUND_BASE=c7bc2fb479d7386825df73e028acdce723ee3388

RUNNER=DIRECT_CODEX
AGENT_CEILING=ONE_DELEGATED_CODEX_PRIMARY_NO_NESTED_SUBAGENTS

FINAL_AUDITOR=DIRECT_CLAUDE_CODE
FINAL_AUDIT_COUNT=ONE

AUTHORITY_RECORD_AUTHORING=AUTHORIZED
AUTHORITY_RECORD_MERGE=REQUIRES_SEPARATE_OPERATOR_DECISION

IMPLEMENTATION_AUTHORITY_EFFECTIVE=
ONLY_AFTER_EXACT_RECORD_IS_VALIDATED_MERGED_AND_REHARVESTED_FROM_MAIN

IMPLEMENTATION_PR_MERGE_AUTHORITY=NONE
ACTIVATION_AUTHORITY=NONE
```
