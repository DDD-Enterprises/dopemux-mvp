---
id: ci-remediation-specialist
title: CI Remediation Specialist Skill
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-20'
last_review: '2026-03-20'
next_review: '2026-06-20'
prelude: Documentation for the CI Remediation Specialist skill used by Dopemux.
---
# CI Remediation Specialist Skill

The `ci-remediation-specialist` is a highly disciplined agentic skill designed to diagnose and resolve CI/CD failures autonomously. It is integrated into the `dopemux-pr-merge` engine but can also be invoked manually.

## Core Mandates

1.  **Reproduce First**: Never attempt a fix without reproducing the failure locally.
2.  **Surgical Precision**: Only modify files directly related to the failing command.
3.  **Automated Tooling**: Prioritize ecosystem auto-fixers (`ruff --fix`, `eslint --fix`) over manual edits.

## The Remediation Runbook

When the specialist is engaged, it follows a strict 4-step sequence:

### 1. Reproduce
The agent executes the exact command reported as failing (e.g., `pytest`, `npm test`) in the local worktree to confirm the error state.

### 2. Auto-Fix
If the error relates to formatting, linting, or basic type issues, the agent attempts to use built-in fixers. If the fixer succeeds, it jumps straight to verification.

### 3. Diagnose & Edit
For test failures or complex logic errors:
- Analyzes the stack trace to find the root cause.
- Reads relevant source code and tests.
- Applies a minimal `replace` or patch to resolve the issue.

### 4. Verify
Re-runs the failing command. If it passes, the mission is complete. If it fails with a *new* error, the cycle repeats.

## Integration with PR Merge

In the **Flight Deck**, when a PR shows a `❌ CI Checks Failed` status, triggering **[P] Patch** or **[V] Verify** may engage this specialist. It operates in a dedicated worktree to ensure your main workspace remains clean.

### Global Fixes
If the specialist identifies a "Global CI Blocker" (the same failure across multiple PRs), it will automatically target the `main` branch to fix the issue at the source, opening a `global-ci-fix` PR.
