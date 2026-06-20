---
id: PCP-DEDOPEMUX-BOUNDARY
title: De-Dopemux Boundary Repair for PCP Core
type: explanation
owner: '@hu3mann'
author: claude
date: '2026-06-19'
last_review: '2026-06-19'
next_review: '2026-09-17'
prelude: De-Dopemux Boundary Repair for PCP Core (explanation) for dopemux documentation
  and developer workflows.
---
# De-Dopemux Boundary Repair for PCP Core

## Context

PCP Core is the reusable, project-agnostic parent substrate that any Git repository can
adopt. DCP (Dopemux Control Plane) is PCP Core plus the Dopemux extension. The previous
iteration of `project_evidence_export.schema.json` contained three boundary violations
that embedded Dopemux-specific concepts directly into the core schema. This document
records the four repairs applied to correct that.

## Changes Applied

### 1. `generated_from_fixture` Relaxed

**Before:** `"const": true` — hard-coded the exporter to always claim it ran from a
fixture. This trapped every export in fixture mode and made the field useless for
distinguishing real runtime exports from fixture-shaped ones.

**After:** `"type": "boolean", "default": false` — the field is now an honest boolean.
Fixture runs set it to `true`; real runtime exports leave it `false` (the default). The
schema no longer mandates a particular value.

### 2. Dopemux Extension Schemas Moved to `schemas/dcp_extension/`

Two schemas that model Dopemux-specific concepts were living inside the PCP Core schema
directory and therefore implied they were part of PCP Core:

- `schemas/project_control_plane/dopetask_packet_mapping.schema.json`
- `schemas/project_control_plane/orchestrator_item.schema.json`

Both have been moved to `schemas/dcp_extension/`. Their `$id` URIs reflect the new
location (`https://dopemux.dev/schemas/dcp_extension/…`). The PCP Core schema directory
no longer contains Dopemux concepts.

### 3. `forbidden_action_confirmation` Keys Generalized

**Before:**

| Old key | Meaning |
| --- | --- |
| `dopetask_executed` | Dopetask (Dopemux task runner) executed |
| `live_task_orchestrator_written` | Task Orchestrator (Dopemux MCP) written |

These names embedded the Dopemux system labels into the core schema's confirmation
block, making the block meaningless for any non-Dopemux project.

**After:**

| New key | Meaning |
| --- | --- |
| `external_runner_executed` | Any external task runner executed (e.g. Dopetask in the DCP extension) |
| `external_workflow_written` | Any external workflow system written (e.g. Task Orchestrator in the DCP extension) |

The DCP extension layer maps `external_runner` → Dopetask and `external_workflow` →
Task Orchestrator. This mapping will be formalized in Packet 5 (extension contract).
The values remain `const: false` — these are still fail-closed attestations that no
live writes occurred.

All four instance files (`dnh_crm_fixture`, `dopemux_fixture`, `minimal_fixture`
`evidence_export.json` and `E2E_DRY_RUN_RESULT.json`) have been updated to use the new
key names.

### 4. Runtime `head_sha` Gate Added

A new `allOf` conditional enforces that any real (non-fixture) export must capture a
real commit SHA:

- When `generated_from_fixture` is `false`, `repo_state.head_sha` must be a non-null
  string with `minLength: 1`.
- When `generated_from_fixture` is `true` (fixture mode), `head_sha` may be any
  string or `null` (e.g. the placeholder `"sha256:PLACEHOLDER-illustrative-not-computed"`
  used in fixture files remains valid).

This gate prevents a real exporter from accidentally emitting `null` for the SHA and
having the export accepted as trustworthy evidence.

---

## Scope

These are **contracts only** — schema definitions and instance files. No runtime
exporter has been implemented. A real generic exporter that reads a live repository
and emits a valid `project_evidence_export.v0` instance is the subject of Packet 4.

Until Packet 4 ships, every real-runtime usage of this schema requires a hand-authored
or tool-assisted instance. The fixture files in
`reports/project-control-plane/fixtures/` serve as reference shapes.

## Test Coverage

`tests/project_control_plane/test_core_boundary.py` covers:

- Schema meta-validates (Draft 2020-12).
- `dopetask_packet_mapping` and `orchestrator_item` schemas exist in `schemas/dcp_extension/`
  and meta-validate, and are absent from `schemas/project_control_plane/`.
- A minimal real-runtime instance (generated_from_fixture=False, head_sha non-null)
  validates with zero errors.
- The same instance with head_sha=None is rejected by the runtime gate.
- An instance using the old key names (`dopetask_executed`,
  `live_task_orchestrator_written`) is rejected by `additionalProperties: false`.
- Each of the three fixture `evidence_export.json` files validates against the schema.
