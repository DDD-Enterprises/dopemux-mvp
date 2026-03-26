---
id: TP-PRMS-P2-19-STRATEGY-IN-CONFLICT-ANALYSIS
title: Tp Prms P2 19 Strategy In Conflict Analysis
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Tp Prms P2 19 Strategy In Conflict Analysis (explanation) for dopemux documentation
  and developer workflows.
---
# TP-PRMS-P2-19-STRATEGY-IN-CONFLICT-ANALYSIS

## Summary
When `build_conflict_analysis()` generates a conflict analysis markdown string, include a recommended strategy from `STRATEGY_LIBRARY` based on conflict characteristics. This provides immediate, actionable guidance for handling merge conflicts.

## Why Now
Conflict analysis currently surfaces the fact that conflicts exist and lists the files, but it does not tell the operator *how* to handle them based on our expanded strategy taxonomy. Adding this logic bridges the gap between mechanical conflict detection and strategic integration planning. This is a small, high-value addition that is safe to perform before the larger engine refactor.

## Goals
- Add a heuristic-based strategy recommendation function for merge conflicts.
- Map specific file patterns and conflict types to the existing strategy library.
- Output the recommendation clearly in the conflict analysis markdown artifact.
- Ensure thorough test coverage for the recommendation heuristics.

## Deliverables
- `src/dopemux_pr_merge_specialist/engine.py` (updated with recommendation logic)
- `tests/pr_merge_specialist/test_strategy_library.py` (updated with new tests)

## Ordered Steps
1. **Add Recommendation Logic**: Add `recommend_conflict_strategy(conflict_file_paths, rebase_error, pr)` to determine the best strategy ID and rationale.
    - Heuristic: migration files -> `MIGRATION_FIRST_THEN_FEATURE_REPLAY`
    - Heuristic: interface/API files -> `INTERFACE_FIRST_RECONCILIATION`
    - Heuristic: high file count (>5) -> `STAGED_SEQUENCE_MERGE`
    - Heuristic: test files only -> `PATCH_ISOLATION_PLAN`
    - Heuristic: complex rebase error -> `REVERT_AND_REINTEGRATE`
    - Default: `OURS_THEN_PORT_SELECTIVE`
2. **Update Markdown Generation**: Modify `build_conflict_analysis()` to call the recommendation function, retrieve the full strategy definition from `STRATEGY_LIBRARY`, and append a "Recommended Strategy" section to the output markdown.
3. **Add Tests**: Create `TestRecommendConflictStrategy` in `test_strategy_library.py` to verify each heuristic branch and the markdown inclusion.

## Implementation Requirements
- Use string matching on file paths and error messages for initial heuristics.
- Degrade gracefully to `OURS_THEN_PORT_SELECTIVE` as the standard default.
- Output must include Strategy Name, ID, Rationale, Risk Profile, Verification Burden, and When to use.

## Acceptance Checks
- `build_conflict_analysis` output includes a "Recommended Strategy" section.
- Tests pass for all defined heuristics.
- Does not break existing conflict resolution flows.

## Exit Criteria
Complete when conflict analysis artifacts reliably suggest a specific, taxonomy-aligned merge strategy with a supporting rationale.
