---
id: GO_NO_GO_CRITERIA
title: Go No Go Criteria
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Go No Go Criteria (explanation) for dopemux documentation and developer workflows.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Flight deck reference

## Flight Deck Go/No-Go Criteria

## Decision Framework
The governance decision for the flight deck is based on safety, utility, and stability metrics.

## Posture Criteria

### 1. GO_SUPERVISED_ONLY
- **Utility**: > 75% of synthesized patches accepted or auto-applied safely.
- **Safety**: 0 destructive overwrites during Auto-Apply.
- **Stability**: Gating refresh successfully clears resolved blockers in > 95% of cases.

### 2. EXPAND_CAUTIOUSLY
- **Utility**: > 90% acceptance of live synthesis.
- **Safety**: 0 overrides required for auto-applied low-risk patches.
- **Prerequisite**: Meets all `GO_SUPERVISED_ONLY` criteria across 20+ runs.

### 3. RESTRICT_AND_HARDEN
- **Utility**: < 60% acceptance of synthesized patches (too much noise/hallucination).
- **Safety**: 1 or more instances where a HIGH risk patch was mistakenly auto-applied.
- **Action**: Disable auto-apply; return all synthesis to mandatory manual review.

### 4. ROLLBACK_SELECTED_SURFACES
- **Stability**: Continuous gating frequently fails or misreports status.
- **Action**: Disable auto-refresh; require manual CLI restarts.

### 5. NO_GO_REMAIN_SUPERVISED_MINIMAL
- **Utility**: Operators find the Spaceage UX too noisy or visually overwhelming compared to raw JSON.
- **Action**: Provide a `--plain` flag default; deprecate rich rendering.
