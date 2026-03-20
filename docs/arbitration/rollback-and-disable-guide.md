---
id: ROLLBACK_AND_DISABLE_GUIDE
title: Rollback And Disable Guide
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Rollback And Disable Guide (explanation) for dopemux documentation and developer
  workflows.
---
# Rollback and Disable Guide

## Overview
Procedures for emergency disablement or reversal of High-Risk Arbitration actions.

## 1. Immediate Disablement
To stop all arbitration activity:
- **CLI**: Set the environment variable `DOPEMUX_ARBITRATION_DISABLED=true`.
- **Policy**: Edit `policy.yaml` and set `mode: advisory`.
- **Agent Profile**: Remove or rename the `.github/agents/pr-merge-specialist.agent.md` file.

## 2. Reverting Supervised Actions
- **Patches**: Use `git revert` or `git checkout` to undo manually applied synthesized patches.
- **Queue**: Use `gh pr merge --dequeue <PR_ID>` to remove a PR from the merge queue.
- **Resolutions**: Manually re-open any incorrectly resolved review threads via the GitHub UI.

## 3. Post-Rollback Audit
After a rollback event:
1. Inspect `proof/pr_merge/arbitration/ops/ONGOING_INCIDENT_REPORT.json` for triggers.
2. Review the `RUNTIME_TRACE.json` for the failing run.
3. Document the root cause and required fixes before re-enabling.
