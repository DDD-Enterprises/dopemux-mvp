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

The `ci-remediation-specialist` is a constrained agentic skill designed to diagnose and resolve CI/CD failures autonomously. It is integrated into `dopemux-pr-merge` as the canonical remediation worker for repeated validation failures and can also be invoked manually.

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

In the **Flight Deck**, when a PR shows a failed validation path, triggering **[P] Patch** or **[V] Verify** may engage this specialist. It operates in a dedicated worktree so the main workspace stays isolated from speculative fixes.

### Global Fixes
If the orchestrator detects the same failure fingerprint across multiple PRs, it treats that as a global blocker:

- the fingerprint is computed from the failing validation step name plus a bounded slice of error output
- open fix PRs are discovered by the `global-ci-fix` label plus the bot fingerprint marker in the PR body
- if a matching fix PR already exists, blocked PRs record that dependency instead of spawning duplicate fixes
- if no matching fix PR exists, the specialist targets `main` and opens one shared remediation PR

## Invocation Contract

The specialist is currently invoked through Gemini CLI with:

```bash
gemini -p "<prompt>" --skill ci-remediation-specialist --yolo
```

The prompt is expected to include:

- the exact failing command
- bounded error output
- an instruction to follow the reproduce -> auto-fix -> diagnose -> verify runbook

## Writer and Reader Boundaries

- Canonical writer of the skill instructions: `templates/skills/ci-remediation-specialist/SKILL.md`
- Canonical reader in orchestration: `src/dopemux_pr_merge_specialist/queue_drain.py`
