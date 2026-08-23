---
id: DCP-EXTENSION-MAPPING
title: DCP Extension Mapping (Packet 5)
type: reference
owner: '@hu3mann'
author: claude
date: '2026-06-20'
last_review: '2026-06-20'
next_review: '2026-09-18'
prelude: DCP Extension Mapping (Packet 5) (reference) for dopemux documentation and
  developer workflows.
---
# DCP Extension Mapping

**Status**: PROPOSED — read/projection stage only (Packet 5).

**Scope**: This document describes how the Dopemux DCP extension (DCP = PCP Core + the Dopemux
extension) attaches to PCP Core as a set of READ and PROJECTION adapters. No system is promoted to
authority. No live writes are authorized. Routing, OpenClaw, and OpenRouter are out of scope
for this packet (Packet 6).

---

## What DCP Is

DCP is PCP Core plus the Dopemux extension. PCP Core provides the contract schemas
(`extension_manifest.schema.json`, `authority_map.schema.json`) that govern how any extension
may attach. The DCP extension declares itself via two JSON instances that validate against those
contract schemas:

- `schemas/dcp_extension/extension_manifest.dcp.json` — declares the extension identity,
  capabilities, owned schemas, and the five hard invariants.
- `schemas/dcp_extension/authority_map.dcp.json` — maps every Dopemux system as a
  READ/PROJECTION adapter with an explicit canonical owner (the upstream system, not DCP).

DCP never owns or writes any domain. Every entry in the authority map is an adapter, projection,
mirror, or index surface. The canonical authority owner in each entry is the upstream system that
actually holds the data.

---

## Extension Manifest

The manifest (`extension_manifest.dcp.json`) declares:

| Field | Value |
|---|---|
| `extension_id` | `dopemux-dcp` |
| `extension_kind` | `DOPEMUX_DCP` |
| `status` | `PROPOSED` |
| `compatible_pcp_core_versions` | `pcp.authority_map.v0`, `pcp.extension_manifest.v0`, `pcp.project_evidence_export.v0` |

The five hard invariants are all pinned `true` by the schema. A manifest that sets any of them
`false` is invalid by construction.

---

## Authority Map — Mapped Systems

Each entry below represents a Dopemux system exposed as a DCP read/projection adapter. The
`canonical_authority_owner` is the upstream system — the source of truth. DCP is a bridge or
proxy, never the authority.

| Domain | Action | Canonical Owner | Surface Class | DCP Surface |
|---|---|---|---|---|
| `workflow.tasks` | project | task-orchestrator | PROJECTION | dcp task-orchestrator read projection |
| `memory.decisions` | read | conport | ADAPTER | dcp conport read adapter |
| `memory.chronicle` | read | dope-memory | ADAPTER | dcp dope-memory read adapter |
| `retrieval.code_docs` | query | dope-context | INDEX | dcp dope-context retrieval index |
| `transport.events` | read | dopecon-bridge | ADAPTER | dcp dopecon-bridge transport adapter |
| `operator.cognitive_state` | read | adhd-engine | ADAPTER | dcp adhd-engine signal adapter |
| `repo.truth_extraction` | read | repo-truth-extractor | ADAPTER | dcp repo-truth-extractor artifact reader |
| `execution.external_runner` | map | dopetask | ADAPTER | dcp dopetask execution-mapping adapter |
| `operator.control` | project | dopemux-cli | PROJECTION | dcp dopemux operator-control projection |
| `pr.readiness` | read | pr-steward | ADAPTER | dcp pr-steward readiness intake |
| `pm.metadata` | read | leantime | ADAPTER | dcp leantime PM-metadata read adapter |

All entries share these fail-closed properties:

- `live_write_allowed: false`
- `canonical_writer: null`
- `unknown_behavior: BLOCK_OR_ESCALATE`
- `proof_required: true`
- `surface_class` is one of PROJECTION, ADAPTER, or INDEX — never SOURCE

---

## Invariant Enforcement

Enforcement comes from two layers — the PCP Core contract schema, and this packet's test suite.

**What the contract schema enforces (generic PCP Core):**

1. A non-SOURCE (derived) surface must have `canonical_writer: null` and `live_write_allowed: false`.
2. `live_write_allowed: true` is valid only on a `SOURCE` surface with a non-empty `canonical_writer`.
3. A manifest with any of the five invariants set to `false` is invalid.

**What the contract schema does *not* enforce:** the generic schema deliberately permits a `SOURCE`
entry to declare a live write — PCP Core must let a real project's authority map name actual
sources. So the schema alone does not prove that *DCP specifically* owns or writes nothing.

**What guarantees DCP is read-only:** this packet's test suite. `test_surface_class_is_not_source`
asserts no DCP entry is `SOURCE`, and `test_source_write_escalation_caught_by_dcp_guard` confirms
that flipping any DCP entry to `SOURCE` + `live_write_allowed: true` — an edit the generic schema
would *accept* — is caught by the DCP boundary guard. DCP therefore cannot silently acquire write
authority without failing the DCP test gate.

---

## Owned Schemas

The extension owns two DCP-specific schemas (it does not override any PCP Core schema):

- `dcp_extension/dopetask_packet_mapping.schema.json`
- `dcp_extension/orchestrator_item.schema.json`

The following PCP Core schemas are explicitly listed as forbidden overrides:

- `project_evidence_export.schema.json`
- `authority_map.schema.json`
- `extension_manifest.schema.json`

---

## Deferred / Not Mapped in Packet 5

The Packet 5 target maps exactly the ten Dopemux systems in the original table. One additional
system was mapped as a post-P5 loose-end amendment:

- **Leantime** — added as a `pm.metadata` read ADAPTER (closing the AIR §7 gap; `canonical_authority_owner: leantime`, `surface_class: ADAPTER`, `live_write_allowed: false`). The AIR §7 component table now includes a Leantime row. This brings the total mapped systems to **11**.

One system named elsewhere in the architecture is still intentionally **not** mapped here:

- **GitHub / CI readiness** — named in AIR §7 but assigned there to the *PR Steward
  proof-readiness* packet, not this one. It will be added as an additional read/projection
  (`ci.evidence`) entry by that packet.

Adding entries later remains additive — new authority-map entries, no core schema change.

---

## Out of Scope (Packet 6)

Routing, OpenClaw, and OpenRouter authority-map entries are deferred to Packet 6. They will
follow the same additive-only pattern — additional entries in the authority map, no core
schema changes.

---

## Validation

The two JSON instances and their test suite are verified by:

```
python -m pytest -q tests/dcp_extension/
python -m jsonschema -i schemas/dcp_extension/extension_manifest.dcp.json \
    schemas/project_control_plane/extension_manifest.schema.json
python -m jsonschema -i schemas/dcp_extension/authority_map.dcp.json \
    schemas/project_control_plane/authority_map.schema.json
```

All checks must pass before any downstream packet that builds on this mapping.
