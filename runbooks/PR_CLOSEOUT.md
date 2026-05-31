---
id: runbook-pr-closeout
title: DevOps AutoPR PR Closeout Runbook
type: how-to
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Check-only PR closeout runbook for embedded audit and PR Steward gates.
---
# DevOps AutoPR PR Closeout Runbook

## Closeout Sequence

1. Confirm `git status --short` and `git diff --stat`.
2. Run packet validation commands and record exit codes.
3. Run `git diff --check`.
4. Run embedded audit if required and record auditor output.
5. If a PR is opened, run PR Steward check-only intake.
6. Verify proof freshness against branch head SHA.
7. Skip second GPT-5.5 Pro review only if embedded audit and PR Steward are READY.
8. Escalate otherwise.

## Explicit Non-Actions

This runbook does not authorize auto-fix, review-thread resolution, merge queue mutation, PR approval, or auto-merge.
