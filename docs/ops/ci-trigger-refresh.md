---
id: ci-trigger-refresh
title: CI Trigger Refresh Runbook
type: how-to
owner: '@hu3mann'
date: '2026-05-26'
---

# CI Trigger Refresh Runbook

## What Changed (TP-DMX-CI-TRIGGERS-008)

Three workflows were updated to fire on `ready_for_review` PR events and support manual `workflow_dispatch`:

| Workflow | Before | After |
|---|---|---|
| `ci-complete.yml` | `[opened, synchronize, reopened]` | `[opened, synchronize, reopened, ready_for_review]` + `workflow_dispatch` |
| `pr-steward.yml` | bare `pull_request:` | `[opened, synchronize, reopened, ready_for_review]` |
| `preflight.yml` | bare `pull_request:` | `[opened, synchronize, reopened, ready_for_review]` |

## Why

A bare `pull_request:` trigger fires on `opened`, `synchronize`, `reopened` but NOT on `ready_for_review`. Draft PRs converted to ready did not trigger CI, causing false confidence from stale results. `ci-complete.yml` also lacked `workflow_dispatch`, preventing manual reruns without a push or dummy commit.

## Invariants Preserved

- `merge_group: types: [checks_requested]` in `ci-complete.yml` is unchanged.
- PR Steward `workflow_dispatch.inputs` block (pr_number) is unchanged.
- PR Steward `permissions: read` block is unchanged — still check-only.
- All job names are unchanged — required check configuration is unaffected.
- `if: github.event_name != 'pull_request'` guards on advisory lanes (installer-smoke, scoped-coverage, integration) remain correct: `ready_for_review` is still a `pull_request` event type, so these lanes continue to be skipped on PR events.
- No `pull_request_target` introduced.

## Manual Rerun (ci-complete.yml)

```bash
gh workflow run "🚀 Complete CI Pipeline (ADHD-Optimized)" \
  -R DDD-Enterprises/dopemux-mvp \
  --ref <branch>
```

## Admin Follow-Up (Supervisor Required)

Branch protection required-check names reference the stable job names (`ci-summary`, `preflight`, etc.). No branch protection changes are needed for this trigger repair — the check names are unchanged. If required checks need reconfiguration, that is a separate admin action outside this packet.
