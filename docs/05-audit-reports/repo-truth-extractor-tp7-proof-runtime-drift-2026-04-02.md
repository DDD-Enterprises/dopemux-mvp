---
id: repo-truth-extractor-tp7-proof-runtime-drift-2026-04-02
title: TP7 Proof To Runtime Drift Inspection
type: reference
owner: '@codex'
author: '@codex'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-06-30'
prelude: Inspection report for TP7 proof-to-runtime drift before TP8C reconciliation.
---
# TP7 Proof To Runtime Drift Inspection

## Claimed by TP7 proof

- `extraction_hygiene.py` supports `--scan-mode actionable|full`
- resume-state buckets are `stale_resume_state`, `orphaned_resume_state`, and `blocked_promptset`
- default scan groups warnings into summary buckets and reduces warning noise
- runbooks exist at:
  - `docs/92-runbooks/repo-truth-extractor-v5-hygiene-cleanup.md`
  - `docs/92-runbooks/repo-truth-extractor-v5-offline-envelope.md`

## Observed on current main-based checkout before reconciliation

- `extraction_hygiene.py` had no `--scan-mode`
- resume-state buckets were `stale_failed`, `orphan_failed`, and `blocked_promptset`
- scan appended per-path warnings directly
- `docs/92-runbooks/` did not exist on this branch
- TP7 proof bundle was present in `proof/`, but the corresponding runtime/docs commits were not on `main`

## Root cause classification

`Partial commit isolation failure`

Reachable history contains the missing runtime/tests/docs commits:

- `2c38e8a8c` `fix(rte-v5): finalize batch diagnostics, route readiness reconciliation, and hygiene scan signal improvements (TP3-TP7)`
- `250c039ce` `test(rte-v5): add coverage for prelive hardening, hygiene scan modes, and batch failure classification (TP3-TP7)`
- `b5c4afcc0` `docs(rte-v5): add offline envelope, hygiene cleanup runbook, and packet lineage reconciliation (TP2, TP6, TP7, TP8)`

Current `main` contained the TP7 proof bundle without those commits.
