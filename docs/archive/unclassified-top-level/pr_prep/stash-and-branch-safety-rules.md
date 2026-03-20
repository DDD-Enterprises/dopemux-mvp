---
id: STASH_AND_BRANCH_SAFETY_RULES
title: Stash And Branch Safety Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Stash And Branch Safety Rules (explanation) for dopemux documentation and
  developer workflows.
---
# Stash and Branch Safety Rules

## Core Mandates

### 1. Read-Only Operations
The `pr-prep-specialist` is strictly read-only during the discovery phase. It never performs any of the following:
- `git stash apply`
- `git stash pop`
- `git checkout` (except for temporary worktree operations)
- `git merge`
- `git cherry-pick`

### 2. No Worktree Mutation
The current branch and uncommitted worktree must not be modified by discovery. If worktree inspection is required, the specialist should use the current state without altering it.

### 3. Transparent Recommendations
Instead of performing actions, the specialist provides clear recommendations to the user:
- "Please check `stash@{0}` for missing changes."
- "Review sibling branch `feat/related-work` for overlapping commits."
- "Stage or commit uncommitted changes before finalizing the PR."

## Decision Constraints

- **High-Risk Overlap**: If overlap occurs in `migrations/` or `config/`, the decision must default to `DRAFT_ONLY` or `BLOCK_PENDING_REVIEW` to prevent breaking changes from being split across PRs.
- **Ambiguity**: If evidence is split across multiple sources (e.g., both a stash and a sibling branch), the ambiguity score must reflect the cumulative risk.
- **User Confirmation**: Any inclusion of adjacent work MUST be performed manually by the user or through an explicit implementation directive.
