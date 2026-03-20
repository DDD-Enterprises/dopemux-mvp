---
id: STRATEGY_SELECTION_RULES
title: Strategy Selection Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Strategy Selection Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Strategy Selection Rules

## Purpose
Heuristics for choosing the optimal merge strategy based on case context and role feedback.

## Selection Heuristics

### Prefer OURS_THEN_PORT_SELECTIVE when:
- 'Ours' has a cleaner structural base (e.g. following a large refactor).
- 'Theirs' contains targeted fixes or bounded behavior additions.
- Challenger objects to full synthesis due to structural noise.

### Prefer THEIRS_THEN_REAPPLY_LOCAL_BEHAVIOR when:
- 'Theirs' represents the authoritative structural future (e.g. upstream migration).
- 'Ours' contains local-only behavior or environment-specific logic.

### Prefer STAGED_SEQUENCE_MERGE when:
- Conflict spans multiple layers (infra + code).
- Verification can be meaningfully staged (e.g. build -> config -> logic).

### Prefer MIGRATION_FIRST_THEN_FEATURE_REPLAY when:
- Migration/schema/config is the critical safety surface.
- Behavioral logic can be safely replayed on top of the new schema.

### Prefer INTERFACE_FIRST_RECONCILIATION when:
- Shared contract or type drift is the primary blocker.
- Both branches are currently 'broken' relative to the shared boundary.

### Prefer PATCH_ISOLATION_PLAN when:
- A small, high-risk conflict nucleus is hidden within a large, noisy diff.
- Isolating the change set reduces total integration uncertainty.
