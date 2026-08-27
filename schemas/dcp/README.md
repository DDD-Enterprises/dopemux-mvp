---
id: dcp-core-contract-schemas
title: DCP Core Contract Schemas
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-08-27'
last_review: '2026-08-27'
next_review: '2026-11-25'
prelude: Strict design-only DCP core contract schemas and validation boundary.
---

# DCP Core Contract Schemas — `schemas/dcp/`

> Task Packet: `TP-DCP-0001` · Synthesis Authority: `DCP_ARCHITECTURE_SYNTHESIS_GPT55_REV1.md`

---

## Purpose

This directory contains the `.v0` JSON Schema files for the DCP (Data Control Plane) core contract floor.
These schemas implement the provenance/validation meta-contract defined in REV1 §6.0.

**Important:** `.v0` is an *unstable version marker*, not an authority claim. These schemas are contract stubs that establish provenance tagging and structural conventions. They are NOT locked as repo authority.

---

## Provenance and Validation Meta-Contract (REV1 §6.0)

Legacy TP-DCP-0001 schemas and fixture instances carry two mandatory blocks:

```json
"provenance": {
  "tag": "<REPO_VALIDATED|EXTERNAL_PROPOSED|SYNTHESIS_INVENTED>",
  "source_ref": "<citation>"
},
"validation": {
  "state": "<REPO_CROSS_CHECKED|PROVISIONAL_UNVERIFIED_ENFORCEMENT|DEFERRED>",
  "notes": "<explanation>"
}
```

The three P0 full-system boundary schemas listed below use manifest-level
`DESIGN_ONLY` provenance instead. Their payloads remain minimal strict authority
records: source/evidence references live in the contract shape, while promotion
state lives only in `manifest.json`. This exception does not promote `.v0` into
runtime authority.

P0 validation is the conjunction `JSON_SCHEMA + P0_SEMANTIC_VALIDATION`:

- Execute Draft 7 with `jsonschema.FormatChecker`; declared `date-time` formats
  are consequential contract constraints, not annotations.
- Execute `scripts/governance/validate_dcp_p0_contract_semantics.py` for dynamic
  relationships Draft 7 cannot compare: READY mandatory-evidence bindings must
  resolve exactly to mandatory context items with matching references, and all
  five SATISFIED audit identity values must exactly match requested identity.
- Neither validator substitutes for the other. A pass requires both.

### Provenance Tag Meanings

| Tag | Meaning |
|-----|---------|
| `REPO_VALIDATED` | Field list/shape derived from and verified against a repo artifact in `origin/main`. |
| `EXTERNAL_PROPOSED` | Shape seeded by an external research document (e.g., DR-016). Not repo-validated. |
| `SYNTHESIS_INVENTED` | Shape invented during architecture synthesis (GPT-5.5 REV1). Not derived from any repo artifact. |

### Validation State Meanings

| State | Meaning |
|-------|---------|
| `REPO_CROSS_CHECKED` | Contract shape has been verified against a repo artifact. |
| `PROVISIONAL_UNVERIFIED_ENFORCEMENT` | Contract shape is provisional; enforcement not verified against repo. May not exit `.v0` without repo-local reconciliation. |
| `DEFERRED` | Contract shape explicitly deferred from this packet. |

---

## The `.v0 = Unstable, Not Authority` Rule

- Every schema in this directory carries a `schema_version` field with a `const` value ending `.v0`.
- `.v0` signals that the contract is a preliminary stub. Field vocabularies are unstable.
- **DR-016-derived and synthesis-invented field lists are PROVISIONAL_UNVERIFIED_ENFORCEMENT** — they are not locked as repo authority and may not exit `.v0` without repo-local field-vocabulary reconciliation.
- No schema in this directory should be treated as the authoritative source for runtime enforcement until upgraded past `.v0` by a subsequent task packet with direct repo derivation.

---

## Per-Contract Provenance Summary

| Schema File | Provenance Tag | Validation State | Notes |
|-------------|---------------|-----------------|-------|
| `dcp_red_lane_taxonomy.schema.json` | `REPO_VALIDATED` | `REPO_CROSS_CHECKED` | Core lane taxonomy verified against origin/main. Each lane carries its own `provenance_tag` (may include `REPO_VALIDATED_BY_AUDIT`). |
| `dcp_control_snapshot.schema.json` | `SYNTHESIS_INVENTED` | `PROVISIONAL_UNVERIFIED_ENFORCEMENT` | Envelope + authority-metadata plus TP-DCP-0004 local derived snapshot fields. Per-surface fields remain non-authoritative. |
| `dcp_proof_pointer.schema.json` | `SYNTHESIS_INVENTED` | `PROVISIONAL_UNVERIFIED_ENFORCEMENT` | Pointer shell only; no live SHA/hash. `auditor_verdict` and `validation_state` are DISTINCT fields — see invariant below. |
| `dcp_evidence_hit.schema.json` | `EXTERNAL_PROPOSED` | `PROVISIONAL_UNVERIFIED_ENFORCEMENT` | 17-field DR-016 shape. 13 repo-only UNKNOWNs pending before exit from `.v0`. |
| `dcp_chronicle_receipt.schema.json` | `EXTERNAL_PROPOSED` | `PROVISIONAL_UNVERIFIED_ENFORCEMENT` | DR-016 envelope only. 22 candidate fields not locked. |
| `dcp_helper_receipt.schema.json` | `EXTERNAL_PROPOSED` | `PROVISIONAL_UNVERIFIED_ENFORCEMENT` | DR-016 envelope only. No repo-runtime helper-receipt analog exists. Advisory; cannot certify readiness. |
| `dcp_mutation_class.schema.json` | `REPO_VALIDATED` | `REPO_CROSS_CHECKED` | TP-DCP-0002. Tier vocabulary (T0-T6, TX, TU) verified against `approval_policy.yaml` + `policy.py`. PROVISIONAL classes per-entry where noted. Hard-block class `MC-MERGE-SEAM-FORBIDDEN`. |
| `dcp_approval_artifact.schema.json` | `SYNTHESIS_INVENTED` | `PROVISIONAL_UNVERIFIED_ENFORCEMENT` | TP-DCP-0002. Envelope SYNTHESIS_INVENTED; tier/decision vocab REPO_VALIDATED. Approval record only — not a write executor. |
| `dcp_project_resource_map.schema.json` | `REPO_VALIDATED` | `PROVISIONAL_UNVERIFIED_ENFORCEMENT` | TP-DCP-0002. Path roots REPO_VALIDATED from ARCHITECTURE.md + filesystem. Endpoint bindings PROVISIONAL or UNKNOWN only. |
| `capability_requirement_ref.schema.json` | `SYNTHESIS_INVENTED` | `DESIGN_ONLY` | P0 capability requirement and exact-identity evidence policy only; grants no execution authority. |
| `context_plan.schema.json` | `SYNTHESIS_INVENTED` | `DESIGN_ONLY` | P0 requirements and policy plan only; contains no fulfilled-evidence claim or mutation authority. |
| `run_context_packet.schema.json` | `SYNTHESIS_INVENTED` | `DESIGN_ONLY` | P0 derived runtime-context envelope; READY rejects stale, UNKNOWN, conflicting, undereferenced, or truncated context. |

### TP-DCP-0002 Contracts (present as of branch `dcp/contract-derivation-tp-0002`)

The following contracts were deferred from TP-DCP-0001 and delivered by TP-DCP-0002 with direct repo derivation:

- `DCP_MUTATION_CLASS` — DELIVERED by TP-DCP-0002 (tier vocab from `approval_policy.yaml` + `policy.py`)
- `DCP_APPROVAL_ARTIFACT` — DELIVERED by TP-DCP-0002 (SYNTHESIS_INVENTED envelope; REPO_VALIDATED vocab)
- `DCP_PROJECT_RESOURCE_MAP` — DELIVERED by TP-DCP-0002 (path roots from ARCHITECTURE.md + filesystem)

### TP-DCP-0004 Control Snapshot Generator

TP-DCP-0004 extends the existing repo-local schema file
`schemas/dcp/dcp_control_snapshot.schema.json`. It does not introduce
`schemas/dcp/dcp_control_snapshot.v0.schema.json`.

The generated `DCP_CONTROL_SNAPSHOT` object is a local, derived,
non-authoritative inspection view. Source task packets, proof artifacts,
schemas, and tests remain more authoritative than generated snapshots.

---

## Critical Invariant: `auditor_verdict` vs `validation_state`

In `dcp_proof_pointer.schema.json` and its fixtures, these are **distinct sibling fields**:

- `auditor_verdict` — the auditor's assessment of the pointed-at artifact (e.g., `GO`, `GO_WITH_FIXES`, `NO_GO`, `PENDING`). Requires `auditor != implementer`.
- `validation_state` — the contract enforcement status of the artifact (from the §6.0 enum).

These fields must never be merged, proxied, or treated as aliases. Mirrors, caches, indexes, and cache-freshness checks are never authority.

---

## DCP-RED-MERGE-SEAM-0001

The red-lane taxonomy encodes a named absolute red line:

**`DCP-RED-MERGE-SEAM-0001`** — DCP must NEVER import, call, wrap, or wire:
- `src/dopemux_pr_merge_specialist/queue_drain.py` (the `execute=True` seam)
- `scripts/batch_resolve_and_merge.py`

Both paths are present in `origin/main`. Note: `steward_gate.py` was absent at TP-DCP-0001 audit time but is now present in main (added by ADHD cognitive-remediation stack #798). The hard block remains active — steward_gate.py does not remove it. Gate: `hard_block`. Provenance: `REPO_VALIDATED_BY_AUDIT`.

---

## Source of Truth for Field Lists

- **This packet (TP-DCP-0001):** REV1 §4 (contract registry), §5 (red-lane taxonomy), §6 (envelope field-lists + §6.0 meta-contract).
- **Fixture data:** Populated ONLY from pasted evidence text. No filesystem traversal of the target repo. All SHA/hash/digest values are illustrative placeholders (`sha256:PLACEHOLDER-illustrative-not-computed`).

---

## Contract Promotion Ladder (L0–L3) — added by DMX-DCP-TOOLING-101

Each schema in this directory has a **level** that tracks its promotion from draft to locked contract. Levels are recorded in `manifest.json` (see below).

| Level | Name | Key Exit Criteria |
|-------|------|-------------------|
| **L0** | DRAFT | Schema file present; structural tests pass; `schema_version` ends `.v0`; `validation_state` = `PROVISIONAL_UNVERIFIED_ENFORCEMENT` or `DESIGN_ONLY` |
| **L1** | RECONCILED | L0 PLUS shape verified against a repo artifact on `origin/main`; `validation_state` = `REPO_CROSS_CHECKED` |
| **L2** | WIRED | L1 PLUS at least one `runtime_producer` AND one `runtime_consumer` in `manifest.json`; CI gate exercises the coupling |
| **L3** | LOCKED | L2 PLUS CI gate enforces on merge path; `schema_version` bumped `.v0`→`.v1`; change-control lane active |

### Version-Precedence Rule

Two version fields govern each contract:

- **`schema_version`** (inside the `.schema.json` file, as a `const`) is the **stability marker**. `.v0` = unstable/DRAFT; `.v1` = locked. This field is the authority: a contract at `.v0` is UNSTABLE regardless of `contract_version`.
- **`contract_version`** (in `manifest.json`, semver string) is the **operational version** of the manifest entry. It tracks metadata changes independently of the schema file.

Both fields bump together at L2→L3: `schema_version` moves from `.v0` to `.v1`, `contract_version` moves from `0.x.y` to `1.0.0`.

---

## Contracts Manifest — `manifest.json`

`schemas/dcp/manifest.json` is the machine-readable registry of all 22 contracts in this directory. It:

- Lists one entry per `.schema.json` file (excluding `dcp_contracts_manifest.schema.json` itself).
- Records `level`, `validation_state`, `enforcement_side`, `ci_gates`, `instance_files`, `runtime_producers`, and `runtime_consumers` for each contract.
- Validates against `schemas/dcp/dcp_contracts_manifest.schema.json` (JSON Schema draft-07).
- Is enforced by `tests/dcp/test_contracts_consistency.py` on every CI run.

**Do not edit `manifest.json` without updating the corresponding promotion-ladder entry.** Promote a contract's `level` only when all exit criteria for the target level are met (see table above).

DMX-DCP-TOOLING-102 promotes the red-lane taxonomy seed from the aggregate test fixture into the standalone instance file `schemas/dcp/dcp_red_lane_taxonomy.instance.json`. The local scanner reads that instance for report metadata only; it does not gain live-write, external API, or PR mutation authority.

### Deterministic vs LLM Enforcement Boundary

Enforcement surfaces are classified in [ADR-222](../../docs/90-adr/adr-222-deterministic-vs-llm-boundary.md). The short rule:

> "A probabilistic guard is a vibe plane, not a red-lane gate."
> "No deny may exist only in an LLM surface."

- `enforcement_side: deterministic` — the contract is or will be enforced by a hard-blocking deterministic surface (CI gate, CLI non-zero exit, PreToolUse hook).
- `enforcement_side: llm_advisory` — the contract is only checked by LLM reasoning surfaces (skills, personas); advisory output only, never a hard block.
- `enforcement_side: human` — enforcement requires human approval (e.g. CODEOWNERS, approval artifact).

See [ADR-222](../../docs/90-adr/adr-222-deterministic-vs-llm-boundary.md) for the full 7-row surface table and L0–L3 promotion criteria.
