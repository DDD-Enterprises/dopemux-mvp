---
id: DNH-EXTENSION-MAPPING
title: dNh CRM Extension Mapping (Packet 7)
type: reference
owner: '@hu3mann'
author: claude
date: '2026-06-22'
last_review: '2026-06-22'
next_review: '2026-09-20'
prelude: dNh CRM Extension Mapping (Packet 7) (reference) for dopemux documentation
  and developer workflows.
---
# dNh CRM Extension Mapping

**Status**: PROPOSED — artifact-only, read-only stage (Packet 7).

**Scope**: This document describes how the dNh CRM extension attaches to PCP Core
as a set of READ and PROJECTION adapters. No CRM write, Telegram send, calendar
write, identity import, policy write, event-store write, or runtime-DB write is
authorized. Reconciliation service and Task Orchestrator visibility are later
packets and are out of scope here.

---

## What dNh CRM Is

dNh CRM is PCP Core plus the dNh extension. PCP Core provides the contract schemas
(`extension_manifest.schema.json`, `authority_map.schema.json`) that govern how any
extension may attach. The dNh extension declares itself via two JSON instances that
validate against those contract schemas:

- `schemas/dnh_extension/extension_manifest.dnh.json` — declares the extension
  identity, capabilities, owned schemas, and the five hard invariants.
- `schemas/dnh_extension/authority_map.dnh.json` — maps every dNh domain as a
  READ/PROJECTION/MIRROR/ADAPTER surface with the canonical upstream owner
  (`dnh-crm`).

dNh never writes any domain. All ten entries in the authority map are artifact-only
surfaces with `live_write_allowed: false`, `canonical_writer: null`, and
`unknown_behavior: BLOCK_OR_ESCALATE`. See **Invariant Enforcement** below for how this
is guaranteed (the generic schema plus this packet's test gate).

---

## Extension Manifest

The manifest (`extension_manifest.dnh.json`) declares:

| Field | Value |
|---|---|
| `extension_id` | `dnh-crm` |
| `extension_kind` | `DNH_CRM` |
| `status` | `PROPOSED` |
| `compatible_pcp_core_versions` | `pcp.authority_map.v0`, `pcp.extension_manifest.v0`, `pcp.project_evidence_export.v0` |

**Extension identity**: matches project IDs `dnh-crm` and `dnh-crm-fixture`;
discovered via repo marker `.dnhroot`.

**Capabilities** (additive-only):

- `authority_map_contributions`: `schemas/dnh_extension/authority_map.dnh.json`
- `red_lane_contributions`: `reports/project-control-plane/fixtures/dnh_crm_fixture/red_lanes.json`
- `evidence_export_sections`: `dnh_profile`, `dnh_authority_docs`, `dnh_proof_roots`
- `proof_status_mappings`: `[]` (none — artifact-only)
- `runtime_mappings`: `[]` (none — artifact-only)
- `adapter_mappings`: 10 adapters (one per domain; see table below)

**Schemas**:

- `owned_schema_ids`: `[]` — dNh owns no new schema files in this packet.
- `forbidden_core_overrides`: `project_evidence_export.schema.json`,
  `authority_map.schema.json`, `extension_manifest.schema.json`,
  `project_red_lanes.schema.json`, `project_profile.schema.json`.

**Five hard invariants** (all pinned `true` by the schema):

| Invariant | Value |
|---|---|
| `cannot_override_core_fail_closed` | `true` |
| `cannot_weaken_proof_gates` | `true` |
| `cannot_weaken_audit_gates` | `true` |
| `cannot_promote_adapter_to_authority` | `true` |
| `cannot_require_extension_for_baseline_core` | `true` |

---

## Authority Map

The authority map (`authority_map.dnh.json`) contains exactly ten entries.
Every entry is artifact-only: `live_write_allowed: false`, `canonical_writer: null`,
`surface_class` is `PROJECTION`, `ADAPTER`, or `MIRROR` (never `SOURCE`).

| Domain | Action | Surface class | Reader / projection surface | Upstream owner |
|---|---|---|---|---|
| `dnh.project_profile` | `project` | `PROJECTION` | dnh project-profile projection | `dnh-crm` |
| `dnh.authority_docs` | `read` | `ADAPTER` | dnh authority-docs reader | `dnh-crm` |
| `dnh.proof_roots` | `read` | `ADAPTER` | dnh proof-roots pointer mapping | `dnh-crm` |
| `dnh.crm` | `read` | `ADAPTER` | dnh CRM runtime read mapping (artifact-only) | `dnh-crm` |
| `dnh.telegram` | `read` | `ADAPTER` | dnh Telegram adapter (no-send) | `dnh-crm` |
| `dnh.calendar` | `read` | `ADAPTER` | dnh Calendar adapter (no-write) | `dnh-crm` |
| `dnh.identity` | `read` | `ADAPTER` | dnh Identity authority mapping (no-merge) | `dnh-crm` |
| `dnh.policy` | `read` | `ADAPTER` | dnh Policy mapping (no-write) | `dnh-crm` |
| `dnh.event_store` | `read` | `MIRROR` | dnh event-store read-only evidence map | `dnh-crm` |
| `dnh.runtime_db` | `read` | `ADAPTER` | dnh runtime-DB FORBIDDEN/red-lane (read-only) | `dnh-crm` |

All entries require `proof_required: true` and fail-closed on unknown ownership
(`unknown_behavior: BLOCK_OR_ESCALATE`).

---

## Invariant Enforcement

Enforcement comes from two layers — the PCP Core contract schema, and this packet's test suite.

**What the contract schema enforces (generic PCP Core):**

1. A non-SOURCE (derived) surface must have `canonical_writer: null` and `live_write_allowed: false`.
2. `live_write_allowed: true` is valid only on a `SOURCE` surface with a non-empty `canonical_writer`.
3. The five manifest invariants are pinned `const: true`; a manifest setting any to `false` is invalid.

**What the contract schema does *not* enforce:** the generic schema deliberately permits a `SOURCE`
entry to declare a live write — PCP Core must let a real project's authority map name actual sources.
So the schema alone does not prove that *dNh specifically* owns or writes nothing.

**What guarantees dNh is artifact-only:** this packet's test suite. The per-entry checks assert no dNh
entry is `SOURCE` (all are `PROJECTION`/`ADAPTER`/`MIRROR`), and `test_source_write_escalation_caught_by_dnh_guard`
confirms that flipping any dNh entry to `SOURCE` + `live_write_allowed: true` — an edit the generic schema
would *accept* — is caught by the dNh boundary guard. dNh therefore cannot silently acquire write authority
without failing the dNh test gate.

---

## Red-Lane Fixture

`reports/project-control-plane/fixtures/dnh_crm_fixture/red_lanes.json` covers the
five primary mutation red lanes for the dNh CRM project:

| Lane ID | Result |
|---|---|
| `crm-write` | `PASS` (no fixture path triggered) |
| `telegram-send` | `PASS` (no fixture path triggered) |
| `calendar-write` | `PASS` (no fixture path triggered) |
| `runtime-db` | `PASS` (no fixture path triggered) |
| `identity-merge` | `PASS` (no fixture path triggered) |

`default_on_unknown: BLOCK` — any unclassified action blocks by default.

The fixture validates against `schemas/project_control_plane/project_red_lanes.schema.json`.

AIR §9 lists identity among the red-lane domains and requires an *authority map + secret policy* proof
for identity. The `identity-merge` red lane plus the read-only `dnh.identity` authority-map entry cover
the authority-map half and the no-merge stop condition. The **secret-policy** proof is recorded here as a
**forward requirement**: enforcing dNh identity secret handling belongs to a later runtime/live-write
packet, not this artifact-only mapping.

---

## dNh Must Never Be Required by PCP Core

The invariant `cannot_require_extension_for_baseline_core: true` is the contractual
guarantee that dNh CRM is a **project extension**, not a PCP Core template or dependency.
PCP Core operates fully without any dNh artifacts. The extension attaches additively and
may be removed without breaking PCP Core behavior.

This invariant is pinned `const: true` in `extension_manifest.schema.json`, so any
manifest that declares it `false` is **invalid by construction**.

---

## Out of Scope (Later Packets)

- Reconciliation service between dNh CRM and PCP Core task state.
- Task Orchestrator visibility / queue projection for dNh tasks.
- Live-write authorization for any dNh domain.
- Identity secret-policy enforcement (AIR §9 identity proof) — recorded as a forward requirement here; runtime enforcement is a later packet.
- Runtime execution mapping (`runtime_mappings` remains `[]`).
