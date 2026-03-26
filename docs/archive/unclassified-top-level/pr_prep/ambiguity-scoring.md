---
id: AMBIGUITY_SCORING
title: Ambiguity Scoring
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Ambiguity Scoring (explanation) for dopemux documentation and developer workflows.
---
# Ambiguity Scoring

## Overview
Ambiguity scoring quantifies the risk that a PR is incomplete based on local git state. The score ranges from 0 to 100.

## Score Components

| Factor | Weight/Formula | Description |
|---|---|---|
| **Branch Overlap** | `max_overlap_ratio * 40` | The highest overlap ratio with any sibling branch. |
| **Stash Overlap** | `max_overlap_ratio * 40` | The highest overlap ratio with any git stash. |
| **Dirty Worktree** | `+20` | Any uncommitted work that overlaps with current branch changes. |
| **High Signal** | `+10` | Any overlap occurring in migrations, config, or documentation. |

## Interpretation

| Score | Level | Decision |
|---|---|---|
| **0–19** | `NONE` | `PROCEED` |
| **20–39** | `LOW` | `PROCEED_WITH_CAUTION` |
| **40–69** | `MEDIUM` | `DRAFT_ONLY` |
| **70–100** | `HIGH` | `BLOCK_PENDING_REVIEW` |

## Hard Blockers
The `BLOCK_PENDING_REVIEW` decision is triggered for any score over 70, indicating high confidence that significant related work is missing from the branch.
