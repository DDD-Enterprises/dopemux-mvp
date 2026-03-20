---
id: LAYERED_VALIDATION_MODEL
title: Layered Validation Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Layered Validation Model (explanation) for dopemux documentation and developer
  workflows.
---
# Layered Validation Model

## Overview
Validation in `pr-prep-specialist` is a layered gate process. It ensures a PR is mechanically sound before invoking any expensive consensus or arbitration layers.

## Layer 1: Deterministic Local Gates
- **Pre-commit**: Runs configured pre-commit hooks.
- **Lint/Format**: Static analysis checks.
- **Branch Cleanliness**: Ensures no dirty worktree state remains.
- **Template Sufficiency**: Verifies all required PR body sections are populated.

## Layer 2: Consensus Gate (Conditional)
- Invoked only if deterministic gates pass BUT the branch is flagged as `HIGH_RISK_ESCALATE` or ambiguity is `HIGH`.
- Used to adjudicate whether complex overlaps (e.g., migrations touching uncommitted state) are safe to proceed.

## Final Decision States
- `CLEAN_CREATE_READY`
- `DRAFT_RECOMMENDED`
- `BLOCKED_MISSING_DOCS`
- `BLOCKED_MISSING_CHANGELOG`
- `BLOCKED_VERIFICATION_GAP`
- `BLOCKED_ADJACENT_WORK_AMBIGUITY`
- `HIGH_RISK_HANDOFF_REQUIRED`
