---
id: MERGE_STRATEGY_TAXONOMY
title: Merge Strategy Taxonomy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Merge Strategy Taxonomy (explanation) for dopemux documentation and developer
  workflows.
---
# Merge Strategy Taxonomy

## Overview
This document defines the canonical library of merge strategies used by the high-risk arbitration lane.

## 1. Structural Strategies
Focus on branch-level precedence and structural integrity.
- **OURS_ONLY**: Discard all incoming changes; maintain current branch state.
- **THEIRS_ONLY**: Discard all local changes; adopt incoming branch state.
- **OURS_THEN_PORT_SELECTIVE**: Use 'ours' as the base, then port specific hunks from 'theirs'.
- **THEIRS_THEN_REAPPLY_LOCAL_BEHAVIOR**: Use 'theirs' as the base, then reapply Preserved local logic.

## 2. Sequential Strategies
Focus on ordered integration stages to manage multi-layer risk.
- **STAGED_MERGE_THEN_PATCH**: Perform git merge, then apply automated fix-ups.
- **STAGED_SEQUENCE_MERGE**: Merge structural -> apply config -> reapply behavior.
- **MIGRATION_FIRST_THEN_FEATURE_REPLAY**: Validate schema/data first, then replay logic.

## 3. Contract-driven Strategies
Focus on shared boundaries and agreed interfaces.
- **SYNTHESIZE_BOTH**: Re-implement overlapping logic to satisfy both intents.
- **INTERFACE_FIRST_RECONCILIATION**: Stabilize the contract first, then implement sides.

## 4. Risk-reduction Strategies
Focus on safety and uncertainty management.
- **PATCH_ISOLATION_PLAN**: Isolate the high-risk core into a standalone patch first.
- **REVERT_AND_REINTEGRATE**: Revert risky side, merge safe core, reintroduce later.
- **SPLIT_DECISION_REQUIRED**: Decouple the integration into separate operations/PRs.
- **HUMAN_DEFER**: Immediate escalation; automated strategy deemed unsafe.
