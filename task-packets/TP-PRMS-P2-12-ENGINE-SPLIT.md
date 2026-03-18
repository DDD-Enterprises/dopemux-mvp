---
id: TP-PRMS-P2-12-ENGINE-SPLIT
title: Tp Prms P2 12 Engine Split
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Tp Prms P2 12 Engine Split (explanation) for dopemux documentation and developer
  workflows.
---
# TP-PRMS-P2-12-ENGINE-SPLIT

## Summary
Split `src/dopemux_pr_merge_specialist/engine.py` (which has grown to ~1900 lines and 70+ functions) into 9 focused, maintainable modules while preserving all existing imports and test compatibility via a backward-compatible re-export facade.

## Why Now
`engine.py` has become a "god module," making it difficult to navigate, test, and safely extend. Splitting it now, while the test suite is green and comprehensive (120+ tests), is the safest and most critical structural improvement needed to support future expansion of the PR Merge Specialist. It must happen before writing new, complex integration tests.

## Goals
- Decompose `engine.py` into semantically grouped modules (e.g., classification, queue, thread_resolution).
- Maintain 100% backward compatibility for existing callers (CLI and tests) via a facade.
- Eliminate circular dependencies.
- Ensure all 120+ existing tests continue to pass without modification.

## Deliverables
- `src/dopemux_pr_merge_specialist/classification.py`
- `src/dopemux_pr_merge_specialist/queue.py`
- `src/dopemux_pr_merge_specialist/thread_resolution.py`
- `src/dopemux_pr_merge_specialist/conflict.py`
- `src/dopemux_pr_merge_specialist/merge.py`
- `src/dopemux_pr_merge_specialist/worktree.py`
- `src/dopemux_pr_merge_specialist/preflight.py`
- `src/dopemux_pr_merge_specialist/plan_builder.py`
- `src/dopemux_pr_merge_specialist/queue_drain.py`
- `src/dopemux_pr_merge_specialist/engine.py` (rewritten as facade)
- Updates to `cli.py` to import from new modules.

## Ordered Steps
1. **Create New Modules**: Create the 9 new `.py` files with `from **future** import annotations`.
2. **Migrate Leaf Modules**: Move functions and constants for `classification.py`, `worktree.py`, and `conflict.py`. Update their internal imports.
3. **Migrate Intermediate Modules**: Move functions for `preflight.py`, `queue.py`, `merge.py`, and `thread_resolution.py`. Update cross-module imports.
4. **Migrate Root Modules**: Move functions for `plan_builder.py` and `queue_drain.py`.
5. **Establish **all****: Define `**all**` in every new module to tightly control exports.
6. **Implement Facade**: Rewrite `engine.py` to simply re-export everything from the new modules (`from .classification import *`, etc.), plus `CommandResult` from `runtime` and `summarize_checks` from `github_api`.
7. **Update CLI**: Update `cli.py` to import functions from their new specific modules, while retaining its own compatibility exports (`_classify_pr = engine.classify_pr`).
8. **Verify Suite**: Run `pytest tests/pr_merge_specialist/` to ensure the facade perfectly preserves the API contract.

## Implementation Requirements
- Do not rewrite logic during the split; only move code and update imports.
- `queue_drain.py` is the orchestrator and depends on others; do not allow circular imports flowing back to it.
- Constants like `CLASS_PRIORITY` and `VALID_TRANSITIONS` must move to `classification.py`.

## Acceptance Checks
- `engine.py` is < 50 lines.
- All 120+ tests pass without modification.
- `dopemux pr-merge self-check` functions perfectly.
- No circular import errors on module load.

## Exit Criteria
Complete when `engine.py` is fully decomposed into 9 modules, the facade is active, and the test suite is fully green.
