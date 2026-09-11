---
id: governed-execution-contract-v2
title: Governed Execution Contract v2
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-09-11'
last_review: '2026-09-11'
next_review: '2026-12-10'
prelude: Terminology, authority ceilings, schema table and freeze lifecycle for the Governed Execution Contract v2 schema set under schemas/governed_execution/.
---
# Governed Execution Contract v2

## Purpose and scope

This reference freezes the terminology, authority ceilings, schema catalogue and
compatibility/deprecation rules for Governed Execution Contract v2 (W01 of
MACRO-DMX-GOVERNED-EXECUTION-CONTRACT-V2-001). It is scope, not authority: every
schema in `schemas/governed_execution/` describes a shape a document may take,
never a grant that a document is legal, admitted, merge-ready or activatable.
Schema-valid does not imply authority-valid.

This packet published schemas, fixtures, tests and this document only. It
performed no runtime implementation, no dispatch, no merge, no activation and no
credential change.

## Terminology

- **MacroPacket** - the Control Tower supervisor's single issuance describing a
  bounded set of child workstreams. `macro_packet.v2.schema.json` is the
  additive successor of the kit's `control_tower.supervisor_macro_packet.v1`.
- **ExecutionBinding** - the runtime runner/model/effort decision recorded for a
  packet or macro. `execution_binding.v2.schema.json` is the additive successor
  of the kit's `control_tower.execution_binding.v1`.
- **TaskPacket** - the scoped, repo-bound unit of execution law a single
  mutating implementer follows. `task_packet.v2.schema.json` is a superset of
  the pre-existing `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`.
- **AdmissionReceipt** - records whether a TaskPacket is admitted for execution,
  with schema/authority/classification/audit/execution validity tracked as
  separate fields (see Invariant I17 below); `admission_status` is a derived,
  fail-closed aggregate, never an independently asserted grant.
- **WriterCustodyReceipt** - records the identity, lease, allowlist digest and
  filesystem scope of the single mutating implementer holding custody of a
  packet's write surface.
- **FreezeReceipt** - records a content freeze of a packet's substantive paths.
  No audit receipt may predate the freeze it evaluates
  (`no_audit_before_freeze` is always `true`).
- **FinalityReceipt** - records the terminal state of an independently audited
  packet. It never carries merge or activation authority
  (`merge_authorized` and `activation_authorized` are always `false`).
  `steward_readiness` *records* the PR Steward's own, separately produced
  upstream verdict (`schemas/pr_steward/merge_readiness.schema.json`'s
  `readiness` field, copied in) - it is not a readiness predicate minted by
  this receipt, and recording it is distinct from the "no readiness,
  dispatch-eligible, merge-ready or approval predicate" invariant below,
  which bars a schema in this set from *originating* such a verdict.
- **AggregateReturnEnvelope** - the team lead's single aggregate return for a
  MacroPacket: referential only (refs and digests, never a copy of evidence);
  `is_canonical_truth` is always `false`, so aggregation cannot mint PASS,
  READY or DONE.
- **Enums** - every shared enum and reusable pattern (`git_oid`, `sha256`,
  `rfc3339_utc`) lives once in `enums.v1.schema.json` and is consumed by
  `$ref` everywhere else in this schema set; no schema here declares an
  inline duplicate enum literal list.

## Section 2 invariants as they bind these schemas

- **I17 (validity is not one field)**: `admission_receipt.v1.schema.json`
  carries `schema_validity`, `authority_validity`, `classification_validity`,
  `audit_validity` and `execution_validity` as five separate `status_class`
  fields; `admission_status` is derived from them and fails closed.
- **UNKNOWN is legal, never coerced**: every `status_class`-shaped field
  accepts `UNKNOWN` as a first-class value; missing required fields fail
  schema validation rather than being defaulted to any status.
- **Fail-closed identifiers**: git object ids match `^[0-9a-f]{40}$`, digests
  match `^[0-9a-f]{64}$`, and timestamps are RFC 3339 strings with an explicit
  `Z` (UTC) suffix - all three are single definitions in `enums.v1.schema.json`
  (`git_oid`, `sha256`, `rfc3339_utc`).
- **No authority-shaped predicate**: no schema in this set defines a property
  named `merge_ready`, `dispatch_eligible`, `approved` or `ready`
  (enforced by `tests/governance/governed_execution/test_dag_and_authority.py`).
- **Kit schemas are read-only**: `.control-tower/schemas/supervisor_macro_packet.schema.json`
  and `.control-tower/schemas/execution_binding.schema.json` are not modified
  by this packet; their sha256 at base is bound in `manifest.v1.json` with
  status `ADOPTED`.

### Enum value sets: UNKNOWN-legal vs. closed outcome sets

| Enum | Values | UNKNOWN? |
| --- | --- | --- |
| `workstream_status` | `NOT_STARTED`, `IN_PROGRESS`, `PASS`, `BLOCKED`, `NEEDS_SUPERVISOR`, `FAIL`, `SUPERSEDED`, `UNKNOWN` | Yes (W01-R1) |
| `freeze_state` | `FROZEN`, `UNFROZEN`, `SUPERSEDED`, `UNKNOWN` | Yes (W01-R1) |
| `dispatch_qualification` | `DISPATCHABLE`, `BLOCKED`, `NEEDS_SUPERVISOR` | No |
| `macro_status` | `PASS_IMPLEMENTATION_PROGRAM_COMPLETE`, `PARTIAL_BLOCKED`, `BLOCKED`, `BLOCKED_TEAM_LEAD_ROUTE_UNPROVEN`, `NO_LEGAL_EXECUTION_ROUTE`, `GLOBAL_AUTHORITY_CONFLICT`, `ARCHITECTURE_INVARIANT_BROKEN`, `NO_VALID_ROLLBACK_FOR_REQUIRED_MUTATION`, `OPERATOR_GATE_REQUIRED_FOR_ALL_REMAINING_WORK` | No |
| `audit_verdict` | `PASS`, `PASS_WITH_RISKS`, `FAIL`, `NEEDS_SUPERVISOR`, `NOT_RUN` | No |

`workstream_status` and `freeze_state` carry `UNKNOWN` per W01-R1 (team-lead
reconciliation, 2026-09-11): a child workstream whose state cannot currently
be determined must be representable without coercion (I16), and a frozen
subject that moved before classification is neither `FROZEN` nor `UNFROZEN`.
`dispatch_qualification`, `macro_status` and `audit_verdict` are closed
outcome sets fixed by the MacroPacket and deliberately carry no `UNKNOWN`
value: each is only ever assigned once its determining inputs are already
resolved, so there is no state in which one of these three is legitimately
unknowable rather than simply not-yet-assigned.

## Authority ceilings

Every schema in this set that carries a scalar `authority` field sets it to
the constant `NONE`. Concretely: `execution_binding.v2`, `task_packet.v2`,
`admission_receipt.v1`, `writer_custody_receipt.v1`, `freeze_receipt.v1`,
`finality_receipt.v1` and `aggregate_return_envelope.v1` all carry
`"authority": "NONE"` directly. `macro_packet.v2` retains the kit v1
`authority` object (`operator_refs`, `global_allowed_actions`,
`global_forbidden_actions`, `global_stop_conditions`) unchanged and
additive-only, so it does not carry a scalar `authority` field of its own.

`macro_packet.v2.authority` is the Control Tower supervisor's authority
**envelope** for the MacroPacket - the operator references and global
allowed/forbidden-action/stop-condition ceilings the supervisor issued - not
an execution-authority claim: nothing in that object asserts that issuing or
holding the MacroPacket grants the right to execute. To make that explicit
and additive (W01-R1 audit repair, W01-R2), `macro_packet.v2` also carries a
new required top-level `execution_authority` field, const `NONE`, on every
v2 instance: schema-valid a MacroPacket may be, but it never carries
execution authority in its own right, matching every other schema in this
set.

Issuance stays where the kit places it: `macro_packet.v2.issued_by` is const
`control_tower_supervisor`; only the Control Tower supervisor issues a
MacroPacket. A TaskPacket's `authority` is `NONE`: an implementer executing
against a TaskPacket holds no independent authority beyond what the packet
and its ExecutionBinding record. Receipts (`admission_receipt.v1` through
`aggregate_return_envelope.v1`) are records of what happened, not grants of
what may happen next: `finality_receipt.v1.merge_authorized` and
`.activation_authorized` are both const `false`, and
`aggregate_return_envelope.v1.merge_authorized` /
`.activation_authorized` are likewise both const `false`.

## Schema table

| Schema | `$id` filename | `schema_version` | Status |
| --- | --- | --- | --- |
| Shared enums | `enums.v1.schema.json` | `dopemux.governed_execution.enums.v1` | ACTIVE |
| SupervisorMacroPacket v2 | `macro_packet.v2.schema.json` | `dopemux.governed_execution.macro_packet.v2` | ACTIVE - `authority` is the supervisor's authority envelope object (unchanged v1 shape); `execution_authority` is the new const `NONE` field (W01-R2) |
| ExecutionBinding v2 | `execution_binding.v2.schema.json` | `dopemux.governed_execution.execution_binding.v2` | ACTIVE |
| TaskPacket v2 | `task_packet.v2.schema.json` | `dopemux.governed_execution.task_packet.v2` | ACTIVE |
| AdmissionReceipt v1 | `admission_receipt.v1.schema.json` | `dopemux.governed_execution.admission_receipt.v1` | ACTIVE |
| WriterCustodyReceipt v1 | `writer_custody_receipt.v1.schema.json` | `dopemux.governed_execution.writer_custody_receipt.v1` | ACTIVE |
| FreezeReceipt v1 | `freeze_receipt.v1.schema.json` | `dopemux.governed_execution.freeze_receipt.v1` | ACTIVE |
| FinalityReceipt v1 | `finality_receipt.v1.schema.json` | `dopemux.governed_execution.finality_receipt.v1` | ACTIVE |
| AggregateReturnEnvelope v1 | `aggregate_return_envelope.v1.schema.json` | `dopemux.governed_execution.aggregate_return_envelope.v1` | ACTIVE |
| SupervisorMacroPacket v1 (kit) | `.control-tower/schemas/supervisor_macro_packet.schema.json` | `control_tower.supervisor_macro_packet.v1` | ADOPTED |
| ExecutionBinding v1 (kit) | `.control-tower/schemas/execution_binding.schema.json` | `control_tower.execution_binding.v1` | ADOPTED |

The full, sha256-bound record of this table is `schemas/governed_execution/manifest.v1.json`.

Conditionals in this schema set are expressed as closed `oneOf` branches,
never `if`/`then`/`else`: `additionalProperties:false` inside an `if`
subschema would make the conditional never match (an `if` only ever asserts
a *subset* of properties, so an `if` closed to that subset rejects every
instance that also carries the sibling properties the conditional is meant
to gate). Two conditionals in this set therefore duplicate the full object
shape into two closed branches instead: `macro_packet.v2.properties.joins
.items` (`QUORUM` join types require `quorum`; every other `join_type`
forbids it) and the `task_packet.v2` document root (`execution.agent
"gemini"` requires `pal_chain` with `enabled: true`, preserving the
canonical v1 spec's `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
gemini-implies-pal_chain rule; every other agent leaves `pal_chain`
optional). Each pair of branches is guaranteed identical outside its
documented delta by a dedicated drift-guard test in
`tests/governance/governed_execution/test_manifest_and_compatibility.py`
(`test_task_packet_v2_oneof_branches_differ_only_at_agent_and_pal_chain`,
`test_macro_packet_v2_join_oneof_branches_differ_only_at_join_type_and_quorum`),
so the duplication this pattern requires cannot silently drift apart.

## v1 -> v2 compatibility and deprecation rule

v1 records remain accepted; v2 is preferred for new records; a v2 successor
adds fields only and never removes or retypes a v1 field. Concretely:

- Every property `macro_packet.v2` and `execution_binding.v2` inherit from
  their kit v1 predecessor keeps the same JSON type (or the same enum value
  set, when the v1 inline enum was replaced by a `$ref` into `enums.v1`).
  `execution_binding.v2` additionally promotes `macro_id` from
  conditionally-required (v1's `oneOf(packet_id, macro_id)`) to
  unconditionally required; `packet_id` remains an ordinary optional string.
- New fields on `execution_binding.v2` (`runner_version`, `effort_requested`,
  `effort_observed`, `auth_profile_ref`, `network_posture`,
  `containment_posture`, `fallback_outcome`, `response_claimed_model`,
  `provider_attested_model`, `independence_class`,
  `qualification_receipt_ref`, and now-required `macro_id`), and on
  `macro_packet.v2` (top-level `execution_authority` const `NONE`,
  `team_lead.binding_policy`, each workstream's `audit_group` and
  `return_contract`, and each join's `join_type` with a
  conditionally-required `quorum` when `join_type` is `QUORUM`) are all
  required and additive.
  `schema_version`'s *value* intentionally differs between v1 and v2 (that is
  what a version bump means); its *type* - a string const - is unchanged.
  `tests/governance/governed_execution/test_manifest_and_compatibility.py`
  proves both directions: the kit's own `EXECUTION_BINDING.template.json` and
  `SUPERVISOR_MACRO_PACKET.template.json` validate cleanly against kit v1, and
  fail v2 only on the new required fields (plus the expected `schema_version`
  const difference) - never on a type change to a retained property.
- `execution_binding.v2.compatibility.legacy_record` narrows the kit's
  untyped `{"type": "object"}` to `{"type": "object", "additionalProperties":
  false}` to satisfy this contract's blanket
  additionalProperties-false-at-every-object-level rule. This is the one
  place a v1 record can fail v2 for a reason other than a missing new
  required field: a v1 `ExecutionBinding` whose `compatibility.legacy_record`
  carries properties would need those properties re-declared (or the field
  omitted) to validate against v2. See Residual Risks in the W01 return.
- Deprecation of any schema in this set requires a MacroPacket-authorized
  successor; no schema is deprecated by this packet. The full rule is
  recorded machine-readably in `manifest.v1.json.compatibility`.

## Freeze lifecycle

`freeze_receipt.v1.freeze_state` (`$ref` to `enums.v1#/definitions/freeze_state`)
takes the values `FROZEN`, `UNFROZEN` and `SUPERSEDED`. The lifecycle a packet
moves through is:

```text
FROZEN -> UNFREEZE -> REPAIR -> REVALIDATE -> REVIEW_SETTLE -> NEW_FREEZE
```

A `FreezeReceipt` records the `FROZEN` state at a given `head_sha`/`tree_sha`
over a declared set of `substantive_paths`, each covered by a
`substantive_path_digest`. `no_audit_before_freeze` is const `true`: no audit
receipt may predate the freeze it evaluates. If a defect is found, the packet
is UNFROZEN, REPAIRed, REVALIDATEd deterministically, has its review threads
settled (REVIEW_SETTLE), and receives a NEW_FREEZE - a new `FreezeReceipt`
whose `supersedes_freeze_ref` points at the one it replaces, with
`freeze_state` `SUPERSEDED` recorded on the prior receipt's referencing
context. This packet does not implement lifecycle transition automation; it
freezes the receipt shape the lifecycle is recorded against.

## Exact-head rule

`finality_receipt.v1.exact_head_equality` is const `true`, documented as
requiring `audited_head` to equal `finality_head`. A JSON Schema cannot
compare two sibling string fields for equality, so this rule is enforced by
the test suite, not by the schema:
`tests/governance/governed_execution/conftest.py::semantic_violations` flags
any `FinalityReceipt` fixture whose `audited_head` and `finality_head` differ,
and `test_schema_fixtures.py` treats that as an intentionally invalid fixture
even though it is schema-valid. Any later semantic change to a subject
invalidates a prior audit bound to a different `audited_head`; a
`FinalityReceipt` is only legal when the head that was audited is the exact
head being finalized.

## Non-colliding relationships

- **`schemas/dcp/governed_execution_receipt.schema.json`** (const
  `dopemux-governed-execution-receipt.v1`) is a pre-existing, untouched
  predecessor scoped to dopetask's own runner/model identity-stage receipt
  (`runner_identity_stages`, `model_identity_stages`,
  `self_certification` all `NOT_CERTIFIED_BY_THIS_RECEIPT`). It shares this
  contract's fail-closed posture but is a different `$id`, a different
  `schema_version` const, and a different receipt shape; nothing in
  `schemas/governed_execution/` extends, references or supersedes it.
- **`.control-tower/schemas/supervisor_macro_packet.schema.json`** and
  **`.control-tower/schemas/execution_binding.schema.json`** (kit v1,
  `control_tower.*` const namespace) remain byte-identical, sha256-bound in
  `manifest.v1.json` as `ADOPTED`, and are extended - never edited - by
  `macro_packet.v2.schema.json` and `execution_binding.v2.schema.json` under
  the `dopemux.governed_execution.*` const namespace.

## Audit identity and PR Steward boundary (W07)

W07 (L3, operator gate `GATE-W07-L3-001`) adds
`src/dopemux/governed_execution/audit_identity/` - new code only, under
`schemas/audit_broker/` and `schemas/proof/embedded_audit.schema.json`,
neither of which this packet touches. It decouples four concerns that were
previously conflated: audit identity, evidence location, exact-head binding
and the PR Steward's action boundary.

### Identity layers and the no-reconciliation rule

`AuditIdentity` is a frozen dataclass carrying `runner`, `runner_version`,
four model-identity layers (`requested_model`, `configured_model`,
`response_claimed_model`, `provider_attested_model`), `provider`,
`effort_requested`, `effort_observed`, `auth_profile_ref`, `containment`,
`network_posture`, `independence_class` and `qualification_receipt`. The
literals `UNKNOWN` and `NOT_EXPOSED` are legal, uncoerced values on any
string field (I16): no function in the package fills one layer from
another, and a unit test grep-scans the package to guard against that
mistake being reintroduced.

`IdentityLayer` mirrors `enums.v1.schema.json#/definitions/identity_layer`
exactly, including its fifth member, `PROXY_REPORTED`. `AuditIdentity` has
no field for that layer - it follows the same four-layer shape already
used by `execution_binding.v2.schema.json` (`response_claimed_model`,
`provider_attested_model`, plus `selection.configured_identity`), which
has no `proxy_reported` layer either. `PROXY_REPORTED` is a real layer,
owned by the out-of-scope `schemas/audit_broker/` and `schemas/dcp/`
families for LLM-routing-proxy identity; `layers()` therefore returns the
four layers this packet's `AuditIdentity` actually carries, not five.

### Independence classes

`independence(implementer, auditor) -> IndependenceAssessment` is pure and
fail-closed. It never approves anything - it returns an assessment, and
every output carries `authority = "NONE"`. Any `UNKNOWN` or `NOT_EXPOSED`
on a field a determination depends on yields class `UNKNOWN` rather than a
guess. When `runner` and `provider` are both known and differ, the class is
`DIFFERENT_FAMILY_AND_RUNTIME`; provider-only differs is `DIFFERENT_FAMILY`;
runner-only differs is `DIFFERENT_RUNTIME`. When runner and provider are
both the same, a same `auth_profile_ref` is `SELF_CERTIFICATION_RISK`
(class `UNKNOWN`) regardless of `runner_version` - the self-certification
clause is unconditional - and a differing `auth_profile_ref` or
`runner_version` is `SAME_FAMILY_DIFFERENT_SESSION`.

### Evidence-location model

`EvidenceLocation(kind, ref)` classifies a repo-relative path as
`CANDIDATE_BRANCH` or `EVIDENCE_STORE`. Paths under `proof/`, `proofs/`,
`out/` or `reports/`, and paths ending in `.proof.json`, `PROOF.json` or
`AUDITOR_REPORT.md`, are `EVIDENCE_STORE`; everything else is
`CANDIDATE_BRANCH`. `split(changed_paths)` partitions a path list into
`(candidate_paths, evidence_paths)`. Target architecture: the candidate
branch carries only substantive candidate content, and the evidence store
carries validation, audit and finality evidence - this packet documents
and enforces the classification, not a migration of existing paths.

### Exact-head binding

`exact_head_binding(audited_head, finality_head, freeze_head)` extends the
[Exact-head rule](#exact-head-rule) above - previously a pairwise
`audited_head == finality_head` check enforced by the test suite - to a
pure, three-way check: `bound` is `True` only when all three inputs are
equal, well-formed 40-hex git oids (lowercase, per
`enums.v1.schema.json#/definitions/git_oid`). Any inequality or malformed
oid yields `bound = False` with the mismatching pair(s) named; no other
code path in the module can produce `bound = True`.

### PR Steward boundary

`classify_steward_action(action) -> "ALLOWED" | "FORBIDDEN"` is fail-closed
over a closed vocabulary: `READ_PR`, `READ_CHECKS`, `READ_REVIEWS`,
`COMPUTE_READINESS` and `EMIT_READINESS_CLASSIFICATION` are `ALLOWED`;
`PUSH_FIX`, `COMMIT`, `APPROVE_REVIEW`, `REQUEST_CHANGES`, `MERGE`,
`MARK_READY`, `AUTHOR_AUDIT`, `WRITE_PROOF` and
`MODIFY_BRANCH_PROTECTION` are `FORBIDDEN`; an action outside both sets is
`FORBIDDEN`. The constants `CHECK_ONLY`, `NO_FIX`, `NO_APPROVAL`,
`NO_MERGE` and `NO_AUDIT_AUTHORING` name the boundary; `READY` exists only
as a classification string, never as anything the module can grant - the
module exposes no `merge`, `approve`, `push` or `write` function. This
boundary governs the live PR Steward's *legal action vocabulary*; the live
PR Steward implementation under `tools/pr_steward/` is out of scope for
this packet.

### Legacy projection and proof self-reference compatibility

`project_legacy_embedded_audit(record)` projects one
`schemas/proof/embedded_audit.schema.json` record into an `AuditIdentity`
without modifying the source record: `auditor_tool` becomes `runner`;
`auditor_model` becomes both `requested_model` and `configured_model`,
since the legacy schema has a single model field; `provider` comes only
from a closed table keyed by `auditor_tool` (`agy`/`antigravity`/
`gemini-cli` -> `google`, `claude-code-cli` -> `anthropic`,
`copilot-cli` -> `github`, `grok-cli` -> `xai`, `opencode-cli` and
`pal-mcp-clink` -> `UNKNOWN`, `none` -> `NONE`), never from model-name
branding; and every field the legacy record has no equivalent for becomes
`UNKNOWN`. The verbatim `invocation` string is preserved as
`legacy_invocation` on the projection wrapper, not placed on
`AuditIdentity` itself.

Proof self-reference behaviour is unchanged by this packet: nothing under
`schemas/proof/` is modified, no existing `embedded_audit` record is
rewritten, and `scripts/audit/run_embedded_audit.py` and
`scripts/audit/local_audit_acceptance.py` continue to read and validate
those records exactly as before. `project_legacy_embedded_audit` is a new,
additive, read-only view for callers that want an `AuditIdentity`-shaped
projection; removing or superseding the legacy record shape is explicitly
deferred to a separately authorized packet.
