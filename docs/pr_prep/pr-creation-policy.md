---
id: PR_CREATION_POLICY
title: PR Creation Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: PR Creation Policy for pr-prep-specialist.
---
# PR Creation Policy

## Final PR Creation Allowed Only When:
- Final prep decision is `CREATE_READY`.
- Deterministic blockers are absent.
- Docs/changelog obligations are satisfied (or policy explicitly waives them).
- No high-risk pre-creation block remains.
- Local creation policy (`allow_live_creation`) allows final PRs.

## Draft PR Creation Allowed When:
- Final prep decision is `DRAFT_RECOMMENDED`.
- High-risk review needs a visible draft artifact.
- Adjacent-work ambiguity is medium but non-blocking by policy.

## No Creation Allowed When (Fallback to PACKAGE_ONLY or BLOCKED):
- Prep decision is any `BLOCKED_*` state.
- Branch truth is insufficient (e.g., detached HEAD).
- Adjacent-work ambiguity is too high.
- Required obligations are `REQUIRED_MISSING`.
- Creation transport (e.g., `gh cli`) is unavailable (fallback to `PACKAGE_ONLY`).
