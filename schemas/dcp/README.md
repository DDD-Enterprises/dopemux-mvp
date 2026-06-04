# DCP Core Contract Schemas — `schemas/dcp/`

> Task Packet: `TP-DCP-0001` · Synthesis Authority: `DCP_ARCHITECTURE_SYNTHESIS_GPT55_REV1.md`

---

## Purpose

This directory contains the `.v0` JSON Schema files for the DCP (Data Control Plane) core contract floor.
These schemas implement the provenance/validation meta-contract defined in REV1 §6.0.

**Important:** `.v0` is an *unstable version marker*, not an authority claim. These schemas are contract stubs that establish provenance tagging and structural conventions. They are NOT locked as repo authority.

---

## Provenance and Validation Meta-Contract (REV1 §6.0)

Every schema and every fixture instance carries two mandatory blocks:

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
| `dcp_control_snapshot.schema.json` | `SYNTHESIS_INVENTED` | `PROVISIONAL_UNVERIFIED_ENFORCEMENT` | Envelope + authority-metadata only. Per-surface fields DEFERRED pending `DCP_PROJECT_RESOURCE_MAP` + canonical-root. |
| `dcp_proof_pointer.schema.json` | `SYNTHESIS_INVENTED` | `PROVISIONAL_UNVERIFIED_ENFORCEMENT` | Pointer shell only; no live SHA/hash. `auditor_verdict` and `validation_state` are DISTINCT fields — see invariant below. |
| `dcp_evidence_hit.schema.json` | `EXTERNAL_PROPOSED` | `PROVISIONAL_UNVERIFIED_ENFORCEMENT` | 17-field DR-016 shape. 13 repo-only UNKNOWNs pending before exit from `.v0`. |
| `dcp_chronicle_receipt.schema.json` | `EXTERNAL_PROPOSED` | `PROVISIONAL_UNVERIFIED_ENFORCEMENT` | DR-016 envelope only. 22 candidate fields not locked. |
| `dcp_helper_receipt.schema.json` | `EXTERNAL_PROPOSED` | `PROVISIONAL_UNVERIFIED_ENFORCEMENT` | DR-016 envelope only. No repo-runtime helper-receipt analog exists. Advisory; cannot certify readiness. |

### Deferred Contracts (NOT present in this directory)

The following contracts are architecture-required but deferred from `TP-DCP-0001`. They must NOT appear in `schemas/dcp/` until a subsequent packet with direct repo derivation locks their shape:

- `DCP_MUTATION_CLASS` — DEFERRED_FROM_TP-DCP-0001
- `DCP_APPROVAL_ARTIFACT` — DEFERRED_FROM_TP-DCP-0001
- `DCP_PROJECT_RESOURCE_MAP` — DEFERRED_FROM_TP-DCP-0001

Locking any of these without direct repo derivation stops the packet.

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

Both paths are present in `origin/main` with the guard (`steward_gate.py`) absent. This is a universal hard block for `TP-DCP-0001` and every subsequent packet. Gate: `hard_block`. Provenance: `REPO_VALIDATED_BY_AUDIT`.

---

## Source of Truth for Field Lists

- **This packet (TP-DCP-0001):** REV1 §4 (contract registry), §5 (red-lane taxonomy), §6 (envelope field-lists + §6.0 meta-contract).
- **Fixture data:** Populated ONLY from pasted evidence text. No filesystem traversal of the target repo. All SHA/hash/digest values are illustrative placeholders (`sha256:PLACEHOLDER-illustrative-not-computed`).
