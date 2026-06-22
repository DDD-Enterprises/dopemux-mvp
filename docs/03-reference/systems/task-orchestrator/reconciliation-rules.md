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
