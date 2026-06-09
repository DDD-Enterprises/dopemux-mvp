---
id: project-workstream-registry
title: Project Workstream Registry
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
last_review: '2026-06-06'
next_review: '2026-09-04'
prelude: Project Workstream Registry (reference) for dopemux documentation and developer
  workflows.
---
# Project & Workstream Registry

> **Note:** Registry JSON schemas are deferred to `TP-DMX-DEVELOPMENT-FACTORY-CONTROLLER-DESIGN-001`.
> This document defines the design, field contracts, and concurrency policy.

---

## Project Registry

One entry per active initiative. Projects are the top-level organizational unit of the factory.

| Field | Description |
|---|---|
| `project_id` | Stable slug (e.g., `DDF`, `RTE`, `COCKPIT`, `ADHD-REMEDIATION`) |
| `display_name` | Human-readable name |
| `status` | `ACTIVE` / `PAUSED` / `ARCHIVED` |
| `lead_packet_series` | Root task packet series for this project (e.g., `TP-DMX-DDF-*`) |
| `authority_scope` | List of systems / directories this project is authorized to modify |
| `open_obligations` | Count of unresolved obligations in the ledger for this project |

Projects with `status: ARCHIVED` may not receive new capsules. All obligations for archived projects
must be in `VERIFIED_CLOSED` or formally `DEFERRED` to a named successor project before archival.

---

## Workstream Registry

A workstream is a sub-scope within a project. It maps to a single line of parallel work — typically
one active branch and one active PR at a time.

| Field | Description |
|---|---|
| `workstream_id` | Stable slug within the project (e.g., `DDF-MODEL-ROUTING`, `RTE-PLAN-B`) |
| `project_id` | Parent project |
| `scope_description` | Plain-language description of what this workstream covers |
| `active_capsule` | Capsule ID currently executing in this workstream (null if idle) |
| `blocked_by` | Capsule ID or obligation ID blocking this workstream (null if unblocked) |

A workstream is `idle` when `active_capsule` is null and `blocked_by` is null. Only idle
workstreams may accept a new capsule assignment.

---

## Branch / Worktree Lease

- One worktree per active execution — capsules do not share worktrees.
- Lease is granted by the Factory Controller at capsule start.
- Lease expires if no commit is recorded within N hours (configurable per project, default 4 hours).
- On lease expiry, the Factory Controller:
  1. Logs an `ORPHAN` obligation if no proof bundle was filed.
  2. Reclaims the worktree (`git worktree remove --force`).
  3. Sets the workstream's `active_capsule` to null.
- On capsule completion (proof bundle filed and accepted), the Factory Controller releases the lease
  and cleans up the worktree as part of the capsule finalization step.

---

## PR Lease

Only one PR per workstream may be open at a time unless explicitly overridden by the supervisor.

If a PR is open for a workstream and a new capsule attempts to open a second PR, the Factory
Controller blocks the attempt and logs a `BLOCKER` obligation. The existing PR must be merged,
closed, or the override explicitly granted before a new PR can be created.

---

## Concurrency Policy

| Factory Level | Capsule Concurrency |
|---|---|
| L2 | Single capsule at a time across all workstreams |
| L3 | Parallel capsules allowed across different workstreams, after L3 is unblocked |
| L4+ | Per-workstream parallel capsules; cross-workstream concurrency requires supervisor approval |

At L2, the Factory Controller serializes all capsule execution. A capsule attempting to start while
another is active is queued, not rejected, unless the two capsules have overlapping `allowed_files`
(in which case the second is blocked until the first completes and files its proof bundle).

---

## Cross-Project Isolation

Capsules from different projects are strictly isolated:

- No shared worktrees.
- No shared branches.
- No obligation ledger writes to another project's obligations without supervisor authorization.
- `authority_constraints.forbidden_authority` for any capsule implicitly includes all systems owned
  exclusively by other projects.

Cross-project reads are permitted (e.g., reading a shared schema for reference), but cross-project
writes require an explicit `AUTHORITY_CONFLICT` review and supervisor sign-off recorded in the
obligation ledger before any edit is made.

---

## Evidence Retrieval Rules

A capsule may read evidence from the following sources:

1. **Live filesystem at capsule start** — files present in the worktree at the moment execution
   begins. Stale evidence from a prior session is not live evidence.
2. **Proof bundles from prior packets** — `PROOF.json` files under `proof/TP-DMX-*/` are
   authoritative records of prior verified work.
3. **ConPort knowledge graph queries** — decisions, patterns, progress entries, and linked items
   retrieved via `mcp__conport__*` tools at query time.

A capsule MUST NOT treat `claudedocs/` as primary evidence. Content in `claudedocs/` is advisory
only — it may have been generated by a prior agent run, may be stale, and has no proof bundle.
If a capsule relies on a `claudedocs/` finding for an authority decision, it must independently
verify the claim against a live source (code, schema, or ConPort) and record that verification in
its proof bundle.
