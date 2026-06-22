---
id: to-canon-004-dry-run-20260622
title: To Canon 004 Dry Run 20260622
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-22'
last_review: '2026-06-22'
next_review: '2026-09-20'
prelude: To Canon 004 Dry Run 20260622 (reference) for dopemux documentation and developer
  workflows.
---
# TP-TO-CANON-004 Dry-Run Report

Date: 2026-06-22

## Verdict

OBSERVED: The full safe pack dry-run imported all 26 source databases into `/tmp/to-canonical-full-dryrun.sqlite`.

OBSERVED: Imported counts were 539 work items, 463 dependencies, 633 note indexes, 461 role transitions, and 36 root overviews.

OBSERVED: `--resolve-current` materialized 418 current work items from `dopemux-mvp-2e346e2084bca021`.

OBSERVED: The generated reports are:

- `audit_inputs/task-orchestrator-canon/to-all-dbs-20260622T192814Z/IMPORT_REPORT.json`
- `audit_inputs/task-orchestrator-canon/to-all-dbs-20260622T192814Z/COLDSTART_RECONCILIATION.json`
- `audit_inputs/task-orchestrator-canon/to-all-dbs-20260622T192814Z/CONFLICTS.json`

## Coldstart Summary

- The root remains active/in-progress.
- 100, 101, and 109 are classified as repo/PR/proof observed and should not be re-run.
- 102 remains explicitly blocked.
- Queue-only items remain queue-only; high-risk supervisor items are labelled.

## Runtime Impact

No live Task Orchestrator database was written. The canonical SQLite file was generated under `/tmp` only.
