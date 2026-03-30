---
id: REPO_TRUTH_EXTRACTOR_RECOVERY_2026-03-26
title: Repo Truth Extractor Recovery Ledger (2026-03-26)
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-03-26'
last_review: '2026-03-26'
next_review: '2026-06-26'
prelude: Recovery ledger for isolating extractor work into a dedicated worktree after an unrelated interrupted rebase changed the primary workspace state.
---
# Repo Truth Extractor Recovery Ledger (2026-03-26)

## Summary

Observed and recovered state:

- A fresh recovery worktree was created at `/Users/hue/.codex/worktrees/extractor-prod/dopemux-mvp`.
- Recovery branch: `codex/v5-extractor-production-recovery`.
- Recovery branch base: `feat/v5-extractor-production` at `2c0998a01ba2a4bb1bdf40aa17552bbf6fb5be97`.
- Verified extractor baseline beyond `main`:
  - `339d447e4edca543b1563f2b2dfa762a64f26b4a` `rescue(extractor): save validation toolchain from PR #301`
  - `2c0998a01ba2a4bb1bdf40aa17552bbf6fb5be97` `merge: refresh main baseline into feat/v5-extractor-production`
- Shared git ref corruption was caused by `.git/refs/.DS_Store`.
- That invalid ref was quarantined to `/Users/hue/.codex/quarantine/dopemux-git-refs/refs.DS_Store.20260326-1409`.
- `git fsck --full --no-reflogs --unreachable --no-progress` now runs without the ref-format failure.

## Interrupted Main Worktree Snapshot

This recovery intentionally does not modify the primary worktree at `/Users/hue/code/dopemux-mvp`.

Latest observed interrupted state:

- detached HEAD: `9a31db5348487a7d458ff297062a392abbf093f6`
- rebase branch: `refs/heads/codex/pm-continue-04-truth-rebaseline`
- rebase onto: `2a933865d5280cd910d16345d38df7ca833cc393`
- stopped on: `6be08a00b25d4a17b56f0aafe5fbe14498b6b2fd`
- step: `2 / 4`
- unresolved files at snapshot time:
  - `services/dopecon-bridge/dopecon_bridge/services/task_integration.py`
  - `services/dopecon-bridge/tests/test_task_integration_unit.py`
  - `services/task-orchestrator/app/api/project_workflow.py`
  - `tests/unit/pm/test_reads.py`
  - `tests/unit/test_task_orchestrator_project_workflow_contract.py`

Note:
- Earlier in-session observations showed a different conflict set and different stopped commit. The main worktree was actively changing while recovery was in progress, so this ledger records the latest directly observed state only.

## Provenance Boundary

Recovered from git history:

- the PR301 validation foundation already committed on `feat/v5-extractor-production`
- the merge of current `main` into that branch
- historical unreachable extractor-related commits that exist in object storage but were not automatically imported into the recovery branch

Not recovered as code evidence in the new branch:

- the later chat-described production-readiness changes such as spend ledger, branded validation UI, batch-policy tests, and model-pricing files
- any uncommitted local edits from the interrupted main worktree

Working rule from this point:

- continuation starts from the PR301 validation baseline on `codex/v5-extractor-production-recovery`
- later chat-described work must be reimplemented or explicitly recovered from dangling objects before it can be claimed as code truth

## Dangling Object Review

Observed:

- `git fsck` reports many unreachable commits/blobs/trees in the shared object store
- some unreachable commit subjects are extractor-related historical work
- no later production-readiness files were proven recovered into the new branch during this recovery step

Conservative conclusion:

- only the committed PR301 baseline plus the branch merge are authoritative recovered extractor code
- dangling extractor history may be mined later if a specific missing change is worth recovering by SHA and diff review

## Subsequent Drift After Snapshot

After the interrupted-state snapshot was recorded, the primary worktree continued changing outside this recovery flow and later returned to a clean branch state:

- branch: `codex/pm-continue-04-truth-rebaseline`
- HEAD: `2c32f1449c6e1ec06ab5ed8ae59325d639e4f15a`
- status: clean at observation time

This confirms the main worktree was being actively mutated by another process during recovery. The isolated extractor worktree remains the only stable continuation surface for extractor work.

## Archived External Extractor Delta

A separate staged extractor patch bundle was observed in the primary worktree after the recovery worktree was created. It was archived read-only under:

- `/Users/hue/.codex/worktrees/extractor-prod/dopemux-mvp/reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/`

Archived artifacts:

- `status.txt`
- `diffstat.txt`
- `name-status.txt`
- `staged.patch`

This patch bundle was not applied to the recovery branch during this step. It remains evidence only until provenance and intent are reviewed.

## Selective Salvage Note

First selective salvage completed from the archived staged patch bundle.

Accepted from the archived patch:

- offline smoke helpers and minimal fixture content
- offline smoke tests for deterministic artifact generation, resume handling, and phase verification
- focused observability and thread-safety tests for shared HTTP session reuse, retry-delay accounting, and repair counters
- minimal `run_extraction_v5.py` support required by those tests only:
  - shared HTTP session helper
  - retry-delay accumulation in failure metadata
  - repair-counter lock and snapshot helper
  - coverage-manifest emission of repair-counter snapshot

Explicitly excluded from salvage:

- `model_map.yaml` rewrite
- `run_extraction_v3.py` changes
- `run_extraction_v5.py` routing/model/audit hunks outside the minimal observability support above
- all tests coupled to unresolved routing/model/pre-live contract changes

Classification authority for the archived patch is recorded in:

- `reports/work-recovery/2026-03-26/salvage-classification.md`
