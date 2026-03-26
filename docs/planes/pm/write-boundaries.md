---
id: pm-plane-write-boundaries
title: PM Plane Write Boundaries
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-26'
last_review: '2026-03-26'
next_review: '2026-06-24'
status: active
prelude: Explicit write classification and Leantime reflection boundary for the normalized PM-plane write surface.
---
# PM Plane Write Boundaries

## Objective

Keep PM metadata writes, workflow-law transitions, and progress logging on distinct authority paths so the PM plane cannot silently invent shadow workflow truth.

## Classification policy

All payloads entering the normalized PM-plane write layer are classified before execution.

### Metadata-only writes

`pm_update_work_item` may carry only PM-record fields such as:

- `title`, `headline`
- `description`, `details`
- `assignee`, `assigned_to`, `owner`
- `labels`, `tags`
- `due_date`, `start_date`, `end_date`
- `priority`, `estimate`, `story_points`
- `notes`, `comments`
- `linked_ids`, `refs`, `meta`
- `reflection_metadata`

### Workflow-significant writes

The generic PM update path must reject any field that could change workflow legality or next-action semantics, including:

- `status`, `state`, `phase`, `stage`
- `transition`
- `blocked`, `blocker`, `blocked_reason`
- `promote`, `demote`, `next_action`
- `dependencies`
- unknown field names that still look state-bearing, such as custom `*_status`, `*_state`, or `*_phase` keys

Mixed payloads fail closed. The PM plane does not silently split metadata and workflow changes into separate backend calls.

## Canonical routing

- `pm_update_work_item`
  - Canonical backend: `Leantime`
  - Allowed only for metadata-only payloads
  - Rejects workflow-significant fields

- `pm_transition_work_item`
  - Canonical backend: `Task Orchestrator`
  - Only sanctioned path for workflow-significant changes
  - `Leantime` mirrors the adjudicated outcome only

- `pm_log_progress`
  - Canonical backend: `ConPort`
  - `dope-memory` receives the chronicle mirror

## Reflection semantics

Normalized PM-plane write receipts expose reflection state explicitly:

- `succeeded`
  - Canonical write succeeded and the configured mirror write also succeeded
- `degraded`
  - Canonical write succeeded, but the mirror write failed or the mirror client was unavailable

Canonical write failure does not return a success receipt. It raises and must be surfaced as a failed operation by the caller.

`reconciliation_state` stays authoritative for downstream handling:

- `SYNCED` means the canonical and mirrored states are aligned
- `PARTIAL` means the canonical write succeeded and reconciliation is still required for a mirror

## Boundary consequences

- Direct workflow-significant Leantime writes are not lawful workflow transitions.
- Bridge and CLI callers must use `pm_transition_work_item` for workflow changes.
- `dopemux.pm.writes` is the canonical PM write surface.
- `dopemux.pm.write` may remain only as temporary compatibility glue while older callers are migrated.
