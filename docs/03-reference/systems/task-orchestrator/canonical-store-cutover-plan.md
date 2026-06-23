---
id: canonical-store-cutover-plan
title: Canonical Store Supervised Cutover Plan
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-22'
last_review: '2026-06-22'
next_review: '2026-09-20'
prelude: Canonical Store Supervised Cutover Plan (reference) for dopemux documentation and developer
  workflows.
---
# Task Orchestrator Canonical Store — Supervised Cutover Plan

> **STATUS: PLAN ONLY — NOT APPROVED FOR EXECUTION.**
> This document describes how the offline canonical reconciliation datastore *could* be promoted
> to a runtime-backed store. It authorizes **no** write cutover and performs **no** live mutation.
> Every step past the approval gate requires explicit operator sign-off and fails closed without it.

## Scope and relationship to the contract

This plan extends [canonical-datastore-contract.md](canonical-datastore-contract.md). Today the canonical
reconciliation datastore is an **offline artifact** — `tools/task_orchestrator_reconcile/import_pack.py`
writes it only to a caller-supplied `--output` SQLite path and never opens a live `current-tasks.db`.

This document plans two *future* phases that are intentionally **not** executed here:

1. A read-only runtime shadow of the offline store (the surface built by `TP-TO-CANON-006`, gated by
   `CANONICAL_STORE_READ_VIEW_ENABLED`, default off).
2. A possible later **write** cutover. This is explicitly **NOT AUTHORIZED** by this plan and would
   require a separate ADR (see "Canonical writer" below).

## Authority boundaries (must be preserved through any cutover)

| System | Authority | Cutover rule |
|--------|-----------|--------------|
| task-orchestrator | workflow views, roles, transition memory only | remains the live workflow writer |
| Leantime | passive PM metadata | unchanged; not a target |
| ConPort | structured decisions / progress / context / custom-data | unchanged; not a target |
| dope-memory | chronicle / evidence receipts | unchanged; not a target |
| dopecon-bridge | adapter / proxy / event transport only | **MUST NOT** be promoted to a data authority |

A cutover **must not** flatten these into a single PM datastore. The canonical reconciliation store is a
**derived, read-only, point-in-time** view — never a replacement for split PM authority.

## Canonical writer

The canonical writer of live workflow transitions remains the **upstream Task Orchestrator MCP service**
(`config/runtime_authority_manifest.json` → `task-orchestrator`, `authority_status: CONFLICTING`). The
canonical reconciliation datastore is **DERIVED** and read-only; it is **not** the canonical writer and is
not registered with a `canonical_*` authority role. Any future write cutover would have to *redefine the
canonical writer* — an architecture-level change that is out of scope for this plan and requires a
dedicated ADR plus operator approval before it may even be designed.

## Preconditions (ALL required before any write cutover is even considered)

1. `TP-TO-CANON-006` read-only view is enabled (`CANONICAL_STORE_READ_VIEW_ENABLED=true`) and validated
   against a freshly regenerated point-in-time snapshot.
2. Explicit operator approval is recorded (see approval gate).
3. A full, verified backup exists of **every** live `current-tasks.db` (see Backup).
4. Replay / idempotency / dedupe behavior is verified against the offline store.
5. A green dry-run of the cutover steps has been produced with no live writes.

If any precondition is unmet, **STOP** — the plan fails closed.

## Phased plan

### Phase 0 — Read-only shadow (covered by TP-TO-CANON-006)
Expose the derived view read-only behind the feature flag. Operators compare the derived view against live
Task Orchestrator state. **No writes.** This is the only phase any current packet builds.

### Phase 1 — Backup (no mutation of source)
Snapshot every live workspace DB to a **uniquely timestamped** archive directory using SQLite's online
backup (WAL/-shm consistent). Archive, never delete.

```bash
# For each workspace's live DB (path derived by the stdio/http wrapper):
#   ~/.local/share/dopemux-mission-control/task-orchestrator/<workspace-id>/current-tasks.db
ARCHIVE="audit_inputs/task-orchestrator-canon/backups/$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short HEAD)"
mkdir -p "$ARCHIVE"
# Use SQLite's online backup, NOT a bare cp: cp of current-tasks.db alone can miss
# the -wal/-shm sidecars and capture a torn snapshot under the WAL-lock contention
# this DB is known for. .backup produces a single consistent file.
sqlite3 "<live current-tasks.db>" ".backup '$ARCHIVE/current-tasks.<workspace-id>.db'"
sqlite3 "$ARCHIVE/current-tasks.<workspace-id>.db" 'PRAGMA integrity_check;'
```

### Phase 2 — Operator-approval gate
No step beyond this point may run without explicit, recorded operator approval. Default = denied.

### Phase 3 — Write cutover (**NOT AUTHORIZED — design only, requires ADR + approval**)
Out of scope for this plan. Documented only so the boundary is explicit: redefining the canonical writer,
migrating live writes, and decommissioning the stdio/http path would each be separate, approval-gated work.

## Rollback (exact)

```bash
# 1. Disable the read view (default is already off):
unset CANONICAL_STORE_READ_VIEW_ENABLED

# 2. Revert any code change introduced by a cutover step:
git revert <cutover-commit-sha>

# 3. Restore a live DB from backup ONLY under explicit operator direction (only if a write occurred):
#    Quiesce writers first (stop task-orchestrator MCP for this workspace).
#    Use SQLite restore — NOT bare cp — to avoid WAL/-shm inconsistency (same invariant as Phase 1).
sqlite3 "<live current-tasks.db path>" ".restore '$ARCHIVE/current-tasks.<workspace-id>.db'"
sqlite3 "<live current-tasks.db path>" 'PRAGMA integrity_check;'
# Remove stale WAL/SHM sidecars from the pre-restore live file if they remain:
rm -f "<live current-tasks.db path>"-wal "<live current-tasks.db path>"-shm
```

## Stale / recovery databases

Stale, legacy, empty-shell, and recovery DBs (per `ADJUDICATION_MANIFEST.json`) are **archived, never
deleted**, and remain provenance-only per the contract. Cutover does not promote them to active state.

## Out of scope

- Any actual write cutover (this is a plan).
- Deletion of any database.
- Promotion of `dopecon-bridge` to a data authority.
- Flattening PM authority into a single store.

## Risk assessment

See the companion red-team risk doc:
[canonical-store-cutover-risk.md](../../../05-audit-reports/task-orchestrator/canonical-store-cutover-risk.md).
