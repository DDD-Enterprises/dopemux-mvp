---
id: PCP-EXTENSION-CONTRACT-AND-AUTHORITY-MAP
title: PCP Extension Contract and Authority Map
type: reference
owner: '@hu3mann'
author: claude
date: '2026-06-19'
last_review: '2026-06-19'
next_review: '2026-09-17'
prelude: PCP Extension Contract and Authority Map (reference) for dopemux documentation
  and developer workflows.
---
# PCP Extension Contract and Authority Map

## 1. Background

Two JSON schemas are the keystones of the Project Control Plane (PCP) Core, as defined in `AIR-DMX-PCP-DCP-ROUTING-ARCHITECTURE-0001` §6:

- `schemas/project_control_plane/authority_map.schema.json`
- `schemas/project_control_plane/extension_manifest.schema.json`

Both validate against JSON Schema Draft 2020-12. Neither schema may be modified by extension authors; extensions attach to PCP Core through the extension manifest's additive contribution mechanism only.

## 2. Authority Map Schema

The authority map (`pcp.authority_map.v0`) is a machine-checkable ownership table. For every `(domain, action)` pair it records:

- **`canonical_authority_owner`** — the upstream system that owns the domain. An extension or adapter is a mapper, never the owner.
- **`canonical_writer`** — the only surface permitted to mutate the domain after all gates have been satisfied. `null` when no writer is authorized at this stage.
- **`surface_class`** — one of `SOURCE`, `PROJECTION`, `MIRROR`, `CACHE`, `INDEX`, `ADAPTER`, or `UNKNOWN`. Derived surfaces (`PROJECTION`, `MIRROR`, `CACHE`, `INDEX`, `ADAPTER`) are never authoritative; they read from or reflect a `SOURCE`.
- **`reader_or_projection_surface`** — the surface that exposes the domain without owning it (`null` when none).
- **`source_truth_refs`** — references to the authoritative source artifacts (paths, schema IDs, proof families).
- **`proof_required`**, **`live_write_allowed`**, **`approval_required`**, **`rollback_required`** — boolean gates. `live_write_allowed` defaults `false` (fail-closed); it may only be set `true` after the live-write gate contract for that domain is separately satisfied.
- **`unknown_behavior`** — pinned `const: "BLOCK_OR_ESCALATE"`. This field cannot hold any other value. Unknown ownership must block or escalate; it must never silently proceed.

### Valid authority map example

```json
{
  "schema_version": "pcp.authority_map.v0",
  "project_id": "dopemux-mvp",
  "entries": [
    {
      "domain": "pm.tasks",
      "action": "write",
      "canonical_authority_owner": "conport",
      "canonical_writer": "conport-api",
      "surface_class": "SOURCE",
      "reader_or_projection_surface": null,
      "source_truth_refs": [
        "schemas/project_control_plane/authority_map.schema.json"
      ],
      "proof_required": true,
      "live_write_allowed": false,
      "approval_required": true,
      "rollback_required": true,
      "unknown_behavior": "BLOCK_OR_ESCALATE"
    }
  ]
}
```

## 3. Extension Manifest Schema

The extension manifest (`pcp.extension_manifest.v0`) declares how a named extension attaches to PCP Core. Four `extension_kind` values are recognized: `DOPEMUX_DCP`, `DNH_CRM`, `PROJECT`, and `UNKNOWN`.

Extensions are **additive only**. The manifest does not replace or override core behavior; it names what the extension contributes alongside it:

- **`capabilities`** — six arrays (`authority_map_contributions`, `red_lane_contributions`, `evidence_export_sections`, `proof_status_mappings`, `runtime_mappings`, `adapter_mappings`) listing additive contributions.
- **`schemas`** — three arrays: `owned_schema_ids` (schemas namespaced under and owned by this extension), `core_schema_extensions` (additive sections attached to core schemas), and `forbidden_core_overrides` (core schema IDs this extension must never override).
- **`extension_identity`** — `project_id_patterns`, `repo_markers`, and `discovery_hints` used to identify applicable projects.

### Five hard invariants (all pinned `const: true`)

Every valid manifest must affirm all five invariants. The schema pins each to `const: true`, so declaring any of them `false` makes the manifest invalid by construction:

| Invariant | Meaning |
|-----------|---------|
| `cannot_override_core_fail_closed` | Extension cannot weaken the core fail-closed default. |
| `cannot_weaken_proof_gates` | Extension cannot lower or remove proof requirements. |
| `cannot_weaken_audit_gates` | Extension cannot lower or remove audit trail requirements. |
| `cannot_promote_adapter_to_authority` | An adapter surface declared by the extension cannot be elevated to a canonical authority owner. |
| `cannot_require_extension_for_baseline_core` | Baseline PCP Core must function without this extension present. |

These are not policy; they are structural constraints enforced by the schema validator.

### Valid extension manifest examples

**DOPEMUX_DCP:**

```json
{
  "schema_version": "pcp.extension_manifest.v0",
  "extension_id": "dopemux-dcp-v0",
  "extension_kind": "DOPEMUX_DCP",
  "extension_identity": {
    "project_id_patterns": ["dopemux-*"],
    "repo_markers": [".dopemux"],
    "discovery_hints": ["look for pyproject.toml with [tool.dopemux]"]
  },
  "capabilities": {
    "authority_map_contributions": [],
    "red_lane_contributions": [],
    "evidence_export_sections": [],
    "proof_status_mappings": [],
    "runtime_mappings": [],
    "adapter_mappings": []
  },
  "schemas": {
    "owned_schema_ids": [],
    "core_schema_extensions": [],
    "forbidden_core_overrides": []
  },
  "invariants": {
    "cannot_override_core_fail_closed": true,
    "cannot_weaken_proof_gates": true,
    "cannot_weaken_audit_gates": true,
    "cannot_promote_adapter_to_authority": true,
    "cannot_require_extension_for_baseline_core": true
  }
}
```

**DNH_CRM (with contributions):**

```json
{
  "schema_version": "pcp.extension_manifest.v0",
  "extension_id": "dnh-crm-v0",
  "extension_kind": "DNH_CRM",
  "extension_identity": {
    "project_id_patterns": ["dnh-*"],
    "repo_markers": [".dnh"],
    "discovery_hints": []
  },
  "capabilities": {
    "authority_map_contributions": ["crm.contacts.write"],
    "red_lane_contributions": [],
    "evidence_export_sections": [],
    "proof_status_mappings": [],
    "runtime_mappings": [],
    "adapter_mappings": ["crm-adapter"]
  },
  "schemas": {
    "owned_schema_ids": ["https://dnh.dev/schemas/crm/contact.schema.json"],
    "core_schema_extensions": [],
    "forbidden_core_overrides": [
      "https://dopemux.dev/schemas/project_control_plane/authority_map.schema.json"
    ]
  },
  "invariants": {
    "cannot_override_core_fail_closed": true,
    "cannot_weaken_proof_gates": true,
    "cannot_weaken_audit_gates": true,
    "cannot_promote_adapter_to_authority": true,
    "cannot_require_extension_for_baseline_core": true
  }
}
```

## 4. Scope of These Schemas

These schemas are **contracts only**. They define what a valid authority map document and a valid extension manifest document look like. They do not:

- Export evidence or produce proof artifacts (a later packet).
- Perform live writes to any store.
- Move schema files between locations.
- Enforce any runtime behavior on their own.

Runtime enforcement, exporters, and live-write gate satisfication are addressed in subsequent PCP packets. The schemas here establish the machine-checkable foundation that all later packets build on.
