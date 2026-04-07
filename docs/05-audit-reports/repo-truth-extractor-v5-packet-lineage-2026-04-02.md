---
id: AUDIT-RTE-V5-PACKET-LINEAGE-2026-04-02
title: Repo Truth Extractor V5 Packet Lineage Reconciliation
type: reference
owner: '@codex'
author: '@codex'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-07-01'
prelude: Packet-lineage reconciliation for TP1-TP7 state and TP8 branch hygiene normalization
  attempt.
---
# Repo Truth Extractor V5 Packet Lineage Reconciliation

Packet: `TP-CODEX-RTE-V5-BRANCH-HYGIENE-AND-COMMIT-ISOLATION-20260402`

## Branch used

- Inspection started on `codex/rte-v5-hygiene-signal-and-batch-failure-cleanup-20260402`
- TP8 cleanup branch created from the same dirty state:
  - `codex/rte-v5-branch-hygiene-and-commit-isolation-20260402`
- Current `HEAD` at TP8B docs reconciliation:
  - `250c039ce4a4dc8dcacb8df90766111c6ff9d6ff`
- `main` merge-base:
  - `196cd7b0b0c7ad16eec6ddef166ef43b8601ba13`

## Why this branch was kept

Continuing from the TP7 lineage was safer than checking out `main` because the TP6 and TP7 changes existed only as mixed staged, unstaged, and untracked worktree state. Rewinding to `main` first would have required stashing unsplit source, doc, and generated report material before packet boundaries were reconstructed.

## Packet lineage status

### TP1

- Packet: `TP-CODEX-RTE-V5-COLLECT-AND-HARDEN-20260401`
- Proof bundle exists and is clean.
- Proof metadata records implementation commits:
  - `d92bf55ef43a30f06f5347b8e5392bb375dd26f8`
  - `76a7cd8a761d65c0e4a39badbdcfe9a454bd3922`
  - `a952ecb64c778db8e777258ff60b3b9c94d5c51b`

### TP2

- Packet: `TP-CODEX-RTE-V5-OPERATOR-SAFETY-AND-PREFLIGHT-20260401`
- Proof bundle exists and is clean.
- Proof metadata does not record commit ids.
- Later normalized into TP8B docs commit scope:
  - `docs/02-how-to/extraction/repo-truth-extractor-v5-first-live-run.md`
  - `docs/92-runbooks/repo-truth-extractor-v5-billing-verification-drill.md`

### TP3

- Packet: `TP-CODEX-RTE-V5-VALIDATOR-UNBLOCK-AND-LIVE-READINESS-20260402`
- Proof bundle exists and is clean.
- Proof metadata does not record commit ids.
- Current dirty-state overlap attributable to TP3 descendants:
  - `services/repo-truth-extractor/run_extraction_v5.py`
  - `services/repo-truth-extractor/validate_pre_live_gate_v25.py`
  - `services/repo-truth-extractor/tests/test_pre_live_gate_v25.py`
  - `services/repo-truth-extractor/tests/test_run_extraction_v5_operator_safety.py`

### TP4

- Packet: `TP-CODEX-RTE-V5-ONLINE-READINESS-AND-COST-TRUST-20260402`
- Proof bundle exists and is clean.
- Proof metadata does not record commit ids.
- Current dirty-state overlap attributable to TP4 descendants:
  - `services/repo-truth-extractor/run_extraction_v5.py`
  - `services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py`

### TP5

- Packet: `TP-CODEX-RTE-V5-OFFLINE-HARDENING-AND-TRUST-CLEANUP-20260402`
- Proof bundle exists and is clean.
- Proof metadata records implementation commit:
  - `4f56b1e2cd863befbc8a66e129a5bdf5b74f2ede`
- TP5 proof/doc commit present on current branch:
  - `ca67492f9083bdb1eee8475015857338a5b83bc2`

### TP6

- Packet: `TP-CODEX-RTE-V5-ROUTE-READINESS-DRIFT-RECONCILIATION-20260402`
- Proof bundle exists and is clean.
- Proof metadata does not record commit ids.
- Normalized into TP8B source/test/doc commits:
  - `docs/02-how-to/extraction/repo-truth-extractor-v5-first-live-run.md`
  - `services/repo-truth-extractor/run_extraction_v5.py`
  - `services/repo-truth-extractor/tests/test_pre_live_gate_v25.py`
  - `services/repo-truth-extractor/tests/test_run_extraction_v5_operator_safety.py`
  - `services/repo-truth-extractor/validate_pre_live_gate_v25.py`
- TP6 proof references report directories that exist on disk but are untracked:
  - `reports/repo-truth-extractor/pre_live_gate_v25/tp6_default_validator/`
  - `reports/repo-truth-extractor/pre_live_gate_v25/tp6_bounded_offline/`
  - `reports/repo-truth-extractor/pre_live_gate_v25/tp6_bounded_online/`

### TP7

- Packet: `TP-CODEX-RTE-V5-HYGIENE-SIGNAL-AND-BATCH-FAILURE-CLEANUP-20260402`
- Proof bundle exists and is clean.
- Proof metadata records no commits and explicitly states that overlapping worktree changes prevented commit creation.
- Later normalized into TP8B source/test/doc commits:
  - `docs/92-runbooks/repo-truth-extractor-v5-offline-envelope.md`
  - `docs/92-runbooks/repo-truth-extractor-v5-hygiene-cleanup.md`
  - `services/repo-truth-extractor/extraction_hygiene.py`
  - `services/repo-truth-extractor/run_extraction_v5.py`
  - `services/repo-truth-extractor/tests/test_hygiene_noise_detection.py`
  - `services/repo-truth-extractor/tests/test_hygiene_resume_state.py`
  - `services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py`
  - `services/repo-truth-extractor/tests/test_run_extraction_v5_rollup_reports.py`

## Dirty-state inventory at TP8 inspection

### TP-related source

- `services/repo-truth-extractor/extraction_hygiene.py`
- `services/repo-truth-extractor/run_extraction_v5.py`
- `services/repo-truth-extractor/tests/test_hygiene_noise_detection.py`
- `services/repo-truth-extractor/tests/test_hygiene_resume_state.py`
- `services/repo-truth-extractor/tests/test_pre_live_gate_v25.py`
- `services/repo-truth-extractor/tests/test_run_extraction_v5_operator_safety.py`
- `services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py`
- `services/repo-truth-extractor/tests/test_run_extraction_v5_rollup_reports.py`
- `services/repo-truth-extractor/validate_pre_live_gate_v25.py`

### TP-related docs

- `docs/02-how-to/extraction/repo-truth-extractor-v5-first-live-run.md`
- `docs/92-runbooks/repo-truth-extractor-v5-billing-verification-drill.md`
- `docs/92-runbooks/repo-truth-extractor-v5-offline-envelope.md`
- `docs/92-runbooks/repo-truth-extractor-v5-hygiene-cleanup.md`

### Generated validator / proof-adjacent artifacts

- Staged timestamped validator directories:
  - `pre_live_gate_v25_20260402T000219Z`
  - `pre_live_gate_v25_20260402T004046Z`
  - `pre_live_gate_v25_20260402T010329Z`
  - `pre_live_gate_v25_20260402T011103Z`
  - `pre_live_gate_v25_20260402T011128Z`
  - `pre_live_gate_v25_20260402T012434Z`
  - `pre_live_gate_v25_20260402T015439Z`
  - `pre_live_gate_v25_20260402T022443Z`
  - `pre_live_gate_v25_20260402T022444Z`
  - `pre_live_gate_v25_20260402T023618Z`
- Untracked timestamped validator directories:
  - `pre_live_gate_v25_20260402T030239Z`
  - `pre_live_gate_v25_20260402T030758Z`
  - `pre_live_gate_v25_20260402T030853Z`
  - `pre_live_gate_v25_20260402T032850Z`
- Untracked named validator directories:
  - `tp6_default_validator`
  - `tp6_bounded_offline`
  - `tp6_bounded_online`

### Unrelated non-packet dirt

- `MEMORY_AUTHORITY_RESOLUTION_OPTIONS.md`
- `SYSTEM_Dopemux.md`
- `SYSTEM_Dopetask.md`

## Intended isolation decisions

### Keep in TP8 packet scope

- all TP2, TP6, and TP7 repo-truth-extractor source/doc files listed above
- TP8 lineage documentation and TP8 proof bundle

### Exclude from source commits

- all `reports/repo-truth-extractor/pre_live_gate_v25/...` runtime report directories
- unrelated non-RTE docs listed above

### Reconciliation policy for proof artifacts

- Existing TP1-TP7 proof bundles under `proof/TP-CODEX-RTE-V5-*` should remain committed as lineage evidence.
- Runtime validator report directories under `reports/repo-truth-extractor/pre_live_gate_v25/` should be referenced by path in lineage/proof notes, not mixed into source commits.
- TP6 and TP7 proof-to-code traceability therefore depends on:
  - the clean proof bundles already under `proof/`
  - the report directories remaining available on disk
  - a future Git-normalization pass that can create commits once `.git` writes are permitted

## Git mutation blocker observed in TP8

TP8 could inspect Git state and create a new branch, but normal index/object writes from the shell were blocked in this environment.

Observed failures:

- `git restore --staged -- MEMORY_AUTHORITY_RESOLUTION_OPTIONS.md`
  - failed with `fatal: Unable to create '/Users/hue/code/dopemux-mvp/.git/index.lock': Operation not permitted`
- `git reset HEAD -- docs/92-runbooks/repo-truth-extractor-v5-billing-verification-drill.md`
  - failed with `fatal: Unable to create '/Users/hue/code/dopemux-mvp/.git/index.lock': Operation not permitted`
- `printf 'tp8-probe\n' | git hash-object -w --stdin`
  - failed with `error: unable to create temporary file: Operation not permitted`
  - then `fatal: Unable to add (null) to database`

This prevented:

- unstaging existing staged paths
- staging modified tracked files
- writing new Git objects for new files
- creating the reviewable commits requested by TP8

## Commit ids created in TP8B so far

- `2c38e8a8c`
  - `fix(rte-v5): finalize batch diagnostics, route readiness reconciliation, and hygiene scan signal improvements (TP3-TP7)`
- `250c039ce`
  - `test(rte-v5): add coverage for prelive hardening, hygiene scan modes, and batch failure classification (TP3-TP7)`

## Remaining dirty state after runtime/test commit normalization

At this point TP3-TP7 source and tests have been normalized into commits. Remaining work is limited to:

- TP2, TP6, and TP7 docs still unstaged before the docs commit
- TP8 proof-bundle updates still unstaged before the proof commit
- unrelated non-packet files and generated report directories that remain intentionally outside these commits
