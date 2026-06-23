---
id: reconciliation-rules
title: Reconciliation Rules
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-22'
last_review: '2026-06-22'
next_review: '2026-09-20'
prelude: Reconciliation Rules (reference) for dopemux documentation and developer
  workflows.
---
# Task Orchestrator Reconciliation Rules

## Active Source

For the 2026-06-22 pack, `dopemux-mvp-2e346e2084bca021` is the active dopemux source because the pack and live wrapper resolution agree.

## Database Classes

- `active_current_dopemux`: promote to current materialized rows.
- `modern_project_with_content`: keep under project-specific provenance.
- `modern_empty_shell`: register as source DB only.
- `legacy_recovery_non_empty`: historical recovery source only; stage and dedupe before any current-state use.
- `legacy_empty_shell`: stale or empty provenance only.

## Dedupe

Title matches across databases are conflicts, not identity. Canonical identity is the active source DB slug plus source row ID unless a later supervised decision creates an alias.

## Coldstart

- 100, 101, and 109 are evidence-observed through local proof paths and PR references from the pack adjudication.
- 102 remains blocked until concrete repo packet authority and allowlist exist.
- Queue-only packets remain queue-only. TO role alone does not imply implementation readiness.
- 107, 108, 113, and 118 remain supervisor/high-risk queue items.

## Coldstart Decision Contract

The coldstart artifact (`COLDSTART_RECONCILIATION.json`, emitted by `--emit-coldstart`) is validated against `schemas/task-orchestrator/reconciliation-decision.schema.json`. The enums are derived from `tools/task_orchestrator_reconcile/resolve.py::coldstart_report`:

- `decision`: `accepted_do_not_rerun`, `remain_active_in_progress`, `keep_blocked_until_repo_packet_allowlist_exists`, `operator_only_do_not_automate`, `do_not_infer_readiness_from_to_role`.
- `classification`: `repo_pr_proof_observed`, `active_root_in_progress`, `explicit_blocked`, `operator_gate`, `queue_only`, `queue_only_supervisor_required`.

## Point-in-Time Knowledge

The completed-PR map (`#886`/`#887`/`#888`), the high-risk packet set (`107`/`108`/`113`/`118`), and the `model.py` schema-class table-count thresholds (`>=25` modern, `==5` legacy) are **point-in-time facts** as of the June 22 safe pack, surfaced in each artifact's `point_in_time` block (`valid_as_of_utc` / `basis`). They are not durable runtime truth and must be revalidated (or moved to a config artifact) before reuse beyond this dry run.
