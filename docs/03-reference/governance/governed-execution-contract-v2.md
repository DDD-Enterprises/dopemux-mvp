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

## Authority ceilings

Every schema in this set that carries an `authority` field sets it to the
constant `NONE`. Concretely: `execution_binding.v2`, `task_packet.v2`,
`admission_receipt.v1`, `writer_custody_receipt.v1`, `freeze_receipt.v1`,
`finality_receipt.v1` and `aggregate_return_envelope.v1` all carry
`"authority": "NONE"`. `macro_packet.v2` retains the kit v1 `authority` object
(`operator_refs`, `global_allowed_actions`, `global_forbidden_actions`,
`global_stop_conditions`) unchanged and additive-only; it does not carry a
scalar `authority` field, so the `NONE` const does not apply to it.

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
| SupervisorMacroPacket v2 | `macro_packet.v2.schema.json` | `dopemux.governed_execution.macro_packet.v2` | ACTIVE |
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
  `macro_packet.v2` (`team_lead.binding_policy`, each workstream's
  `audit_group` and `return_contract`, and each join's `join_type` with a
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
