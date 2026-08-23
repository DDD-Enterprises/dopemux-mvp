---
id: AMBIGUITY_SCORING
title: Ambiguity Scoring
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Ambiguity Scoring (explanation) for dopemux documentation and developer workflows.
---
# Ambiguity Scoring

## Overview

Ambiguity scoring quantifies, from local git state (sibling-branch overlap,
stash overlap, dirty-worktree overlap, and overlap in high-signal paths
such as migrations/config/docs), the risk that a PR is missing related work.
The score ranges from 0 to 100 and remains a useful evidence/uncertainty
signal that feeds the S1/S2 scope-and-obligations steps of
[`operator-contract.md`](./operator-contract.md) §5.

## Score Components

| Factor | Weight/Formula | Description |
|---|---|---|
| **Branch Overlap** | `max_overlap_ratio * 40` | The highest overlap ratio with any sibling branch. |
| **Stash Overlap** | `max_overlap_ratio * 40` | The highest overlap ratio with any git stash. |
| **Dirty Worktree** | `+20` | Any uncommitted work that overlaps with current branch changes. |
| **High Signal** | `+10` | Any overlap occurring in migrations, config, or documentation. |

## What this score is not

Superseded: this file previously mapped `LOW`/`MEDIUM`/`HIGH` ambiguity
bands directly to `PROCEED`/`PROCEED_WITH_CAUTION`/`DRAFT_ONLY`/
`BLOCK_PENDING_REVIEW` decisions, as a standalone risk-classification table
competing with the PR risk lane. That decision table is retired.

The ambiguity score is evidence recorded during S1/S2 (`operator-contract.md`
§5); it does not itself set `risk_lane`, gate PR creation, or determine
whether independent audit is required. Current PR risk uses the `L0-L3`
risk lanes (§4) exclusively, and current creation posture defaults to
`DRAFT_ONLY` (§S4) regardless of ambiguity score. A high ambiguity score is
reported as an obligation/warning for the operator, not as an autonomous
`BLOCK_PENDING_REVIEW` decision.
