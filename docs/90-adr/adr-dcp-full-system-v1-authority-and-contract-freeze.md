---
id: adr-dcp-full-system-v1-authority-and-contract-freeze
title: "ADR: DCP Full-System V1 Authority and Contract Freeze"
type: adr
owner: '@hu3mann'
author: '@codex'
date: '2026-08-27'
last_review: '2026-08-27'
next_review: '2026-09-27'
status: accepted
prelude: Freeze DCP full-system authority boundaries and P0 contracts without granting implementation, merge, or activation authority.
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-dcp-mcp-ro-0009-chatgpt-mcp-exposure-targets-runtime-resolution-ownership-evidence
    - adr-memory-trinity-authority-and-interaction-model
    - adr-sb-001-extension-boundary-and-non-authority
---

# ADR: DCP Full-System V1 Authority and Contract Freeze

## Status and scope

Accepted as a contract freeze for
`TP-DMX-DCP-FULL-SYSTEM-P0-AUTHORITY-CONTRACT-FREEZE-001`. This decision does
not activate runtime wiring, providers, auditors, writes, merges, or follow-on
packets.

## Decision

Adopt the authority topology, context and capability boundaries, exact audit
result classes, six-tool GPT facade, retained GPT-5.5 gate, and separated
activation ladder below as the P0 contract freeze.

## Authority topology

| Slice | Canonical authority | DCP responsibility | Explicit exclusion |
|---|---|---|---|
| Repository/runtime truth | Current code, config, tests, compose wiring, active entrypoints | Read and bind evidence to exact revisions | No source mutation by context or audit contracts |
| PM metadata | Leantime | Carry bounded references | No PM write authority |
| Workflow legality and transitions | Task Orchestrator | Carry state references and blockers | No transition authority |
| Decisions, progress, structured context | ConPort | Retrieve provenance-bound snapshots | No canonical overwrite |
| Chronicle and historical receipts | dope-memory | Retrieve chronicle evidence | No decision, PM, or workflow authority |
| Code/docs retrieval | dope-context | Return retrieval candidates and provenance | Retrieval is not dereference or authority |
| Second Brain | Accepted ADR-SB-001 through ADR-SB-010 | Compile derived claims, Wiki pages, and receipts | No canonical write-back or authority promotion |
| Audit judgment | Independently certified auditor through Audit Broker contracts | Bind capability, identity, subject, execution receipt, and result | No repository or task mutation authority |
| ChatGPT/GPT facade | `dcp-readonly-facade` | Six read-only tools over opaque targets | No mutation, lifecycle, provider, or activation tool |
| Transport | dopecon-bridge and approved adapters | Route/proxy events only | No canonical authority |
| Merge and activation | Human operator through current repository governance | Decide separate gates | Packet, proof, audit, or PASS cannot auto-advance |

Each slice has one authority. Derived projections may cite canonical sources but
cannot replace them.

## Context boundary

`ContextPlan` is requirements and policy only. It cannot claim evidence was
fetched, fresh, complete, or satisfied. `RunContextPacket` is the single P0
runtime context-envelope contract. It is a derived, subject-bound evidence
envelope and grants neither execution nor mutation authority. `READY` requires
all included items to be fresh, dereferenced, and untruncated, with no conflicts.
`UNKNOWN`, `CONFLICTING`, stale, missing, or undereferenced mandatory evidence
fails closed.

## Capability and audit boundary

Capability requirements retain exact requested provider/model identity and
forbid silent substitution. Requested, configured, response-claimed,
proxy-reported, and provider-attested identity layers remain separate; missing
layers are `UNKNOWN`.

Audit result classes remain mechanically distinct:

- substantive judgments: `PASS`, `PASS_WITH_RISKS`, `FAIL`, `NEEDS_SUPERVISOR`;
- terminal intake/binding failures: `MALFORMED`, `HEAD_MISMATCH`,
  `SUBJECT_MISMATCH`, `REQUIRED_IDENTITY_UNKNOWN`;
- pre-judgment execution failures: `TRANSPORT_FAILURE`, `CAPACITY_FAILURE`.

No failure class is converted to PASS or to another model/provider result.

## GPT facade boundary

V1 facade inventory is exactly:

1. `list_targets`
2. `get_target_capabilities`
3. `get_target_repo_state_snapshot`
4. `list_target_proof_bundles`
5. `fetch_target_proof_bundle`
6. `get_target_runtime_receipt`

Adding a seventh tool or treating any tool as a write seam requires a separate
accepted contract change.

## GPT-5.5 named gate

Existing GPT-5.5 named gate remains retained until an exact superseding gate is
accepted. GPT-5.6, including this packet's implementation selector, is not a
substitute and does not satisfy that named gate.

## Second Brain disposition

Accepted ADR-SB decision bodies remain unchanged. Knowledge Compiler outputs,
compiled claims, materialized Wiki pages, and materialization receipts are
derived and non-canonical. Canonical source wins; write-back stays disabled;
purge propagation remains required.

## V1 exclusions

This freeze excludes runtime wiring, provider execution, credential handling,
Task Orchestrator mutation, accepted Second Brain body edits, PR #1138 mutation,
audit execution, readiness, merge, and activation. PR #1138 is stale and
nonauthoritative relative to current main.

## Activation ladder

1. Contract freeze accepted.
2. Separate implementation packet authorized.
3. Deterministic validation passes on exact content.
4. Required independent audit returns a valid exact-subject judgment.
5. Operator separately authorizes merge.
6. Operator separately authorizes runtime enablement.

Every rung is explicit. No rung implies the next.

## Contract set

P0 freezes strict `.v0` shapes for DCP context/capability, Second Brain compiler
materialization, and Audit Broker capability/certification/request/execution/result
records. `.v0` remains design-only and unstable; it is not evidence of runtime
implementation.

## Consequences

Positive and adversarial fixtures can deterministically enforce boundary shape.
Runtime coupling, provider identity attestation, independent audit, merge, and
activation remain `NOT_RUN` until their separate gates execute.
