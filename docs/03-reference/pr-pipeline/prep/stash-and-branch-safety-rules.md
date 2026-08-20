---
id: STASH_AND_BRANCH_SAFETY_RULES
title: Stash And Branch Safety Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Stash And Branch Safety Rules (explanation) for dopemux documentation and
  developer workflows.
---
# Stash and Branch Safety Rules

The read-only discovery constraints below remain in force. Risk and
posture decisions are governed by [`operator-contract.md`](./operator-contract.md)
§4 (Risk lanes) and §5 (S4 - Draft or verify PR metadata), not by the
retired vocabulary this file previously used; see the note at the end of
this file.

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

- **High-Risk Overlap**: If overlap occurs in `migrations/` or `config/`, treat the change as at least `L2_MATERIAL` (or `L3_RED` if it also touches security, auth, credentials, permissions, or production) per §4, and keep the default `DRAFT_ONLY` posture from §5 S4 rather than proceeding to any non-draft creation.
- **Ambiguity**: If evidence is split across multiple sources (e.g., both a stash and a sibling branch), record the overlap classification (`IDENTICAL`, `SUBSET`, `SUPERSET`, `COMPATIBLE`, `CONFLICTING`, or `UNKNOWN`, per §5 S1) and let that classification — not a standalone ambiguity score — drive whether the branch is ready to proceed.
- **User Confirmation**: Any inclusion of adjacent work MUST be performed manually by the user or through an explicit implementation directive.

This file previously used a `DRAFT_ONLY` / `BLOCK_PENDING_REVIEW` decision
pair driven by a standalone ambiguity score. That pair is folded into the
canonical risk lanes and pre-push gate above; there is no independent
posture vocabulary here anymore.
