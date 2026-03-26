---
id: ADJACENT_WORK_DISCOVERY
title: Adjacent Work Discovery
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Adjacent Work Discovery (explanation) for dopemux documentation and developer
  workflows.
---
# Adjacent Work Discovery

## Overview
The `pr-prep-specialist` audits nearby local state to detect likely missing related work. This ensures that a PR is complete and doesn't leave important changes in a stash, sibling branch, or dirty worktree.

## Discovery Layers

### 1. Sibling Branches
The auditor lists all local branches and compares their changed files (relative to the base branch) with the current branch.
- **Signal**: Overlapping file paths, especially in high-signal areas like `migrations/`, `config/`, or `docs/`.
- **Action**: Reports branches with significant overlap as "candidates" for missing work.

### 2. Git Stashes
The auditor inspects the local stash list and retrieves the changed files for each entry.
- **Signal**: Overlapping files or related commit messages in the stash.
- **Action**: Alerts the user if a stash appears to contain PR-relevant edits.

### 3. Uncommitted Changes
The auditor checks staged, unstaged, and untracked files in the current worktree.
- **Signal**: Dirty files that were also modified in the current branch.
- **Action**: Recommends staging or committing these files before finalizing the PR.

## Output
The discovery process results in an `ADJACENT_WORK_REPORT.json` containing all overlaps and a final `ADJACENT_WORK_DECISION.json`.
