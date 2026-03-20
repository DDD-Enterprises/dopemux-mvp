---
id: TRIGGER_CRITERIA
title: Trigger Criteria
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Trigger Criteria (explanation) for dopemux documentation and developer workflows.
---
# High-Risk Arbitration Trigger Criteria

## Overview
Arbitration is reserved for complex integration cases where automated `rerere` paths are insufficient. This document defines the explicit triggers for activating the evidence-packaging lane.

## Primary Triggers
Arbitration MUST be triggered if any of the following are true:

1. **High-Risk Conflict Class**: `conflict_class` is explicitly identified as `HIGH_RISK` by the `ConflictAnalyzer`.
2. **Semantic Overlap**:
    - Same file, overlapping line ranges changed on both sides.
    - Same symbol (function, class, method) modified on both sides.
3. **Critical Boundary Touch**:
    - Migration files (`migrations/`, `alembic/`) changed on both sides.
    - Public API surfaces or core contracts modified.
    - Config/Auth boundaries touched.
4. **Governance Blockers**:
    - Unresolved `HUMAN_DECISION_REQUIRED` feedback items related to integration.
    - Conflicting reviewer intent on integration logic.
5. **Queue Failure**:
    - The PR was ejected from the Merge Queue due to a failure attributable to the merge state.

## Non-Triggers (Mechanical)
Arbitration MUST NOT be triggered for:
- Routine version bumps or lockfile updates.
- Changes to non-overlapping documentation files.
- Mechanical conflicts easily resolvable by existing `rerere` logic.
- Low-risk formatting or whitespace-only changes.
