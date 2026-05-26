---
id: runbook-daily-ops
title: DevOps AutoPR Daily Ops Runbook
type: how-to
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Daily operating checks for optimized Dopemux development workflow packets.
---
# DevOps AutoPR Daily Ops Runbook

## Daily Checks

1. Refresh local repo state safely: inspect `git status --short --branch` before any fetch, pull, rebase, or branch switch.
2. Confirm the active task packet and allowlist before editing.
3. Confirm local tool help for any auditor or PR Steward invocation before use.
4. Confirm GitHub authentication before expecting PR Steward to harvest live PR state.
5. Keep proof current after each validation slice.
6. Preserve `UNKNOWN`, `CONFLICTING`, and `NOT_RUN` states in proof and summaries.

## Routine Outputs

- current branch and head SHA
- changed files
- validation table with exit codes
- embedded audit status
- PR Steward readiness when a PR exists
- blockers and escalation needs
