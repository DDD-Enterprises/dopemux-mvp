---
id: UPSTREAM_CONTRACT_SUMMARY
title: Upstream Contract Summary
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-26'
last_review: '2026-03-26'
next_review: '2026-06-24'
prelude: Upstream Contract Summary (explanation) for dopemux documentation and developer
  workflows.
---
# Upstream Contract Summary - dopetask Migration

## 1. Current Repo Truth
- **Pinned Version**: 0.2.0 (in `.dopetask-pin` and `pyproject.toml`)
- **Integration**: Single-packet via `DopetaskAdapter` and `scripts/dopetask`.
- **Status**: No series or DAG support exists in the current 0.2.0 pin.

## 2. Candidate Versions Probed
- **0.5.1**: Success (Confirmed `tp series` support).
- **0.5.0**: Success (Confirmed `tp series` support).
- **0.2.0**: Baseline (No series support).

## 3. Confirmed Upstream CLI Surface
- `dopetask tp series [exec|status|finalize]` is authoritative in 0.5.x.
- Supports `--agent` (gemini, codex, vibe).
- Supports `--repo` path targeting.

## 4. Confirmed Artifact Surface
- Root marker: `.dopetaskroot`.
- Configuration: `.dopetask/project.json`.
- Task state: Managed via the `status` command (emits JSON/state).

## 5. Unsupported Assumptions in Prior Plan
- **Assumption**: `uv` migration required.
  - **Correction**: `pip` installs of 0.5.x work cleanly in standard venvs; `uv` is optional/separate from the contract.
- **Assumption**: `doctor` is purely optional.
  - **Correction**: `doctor` in 0.5.x enforces branch name checks (`main`).

## 6. Recommended Migration Target
- **Target**: `0.5.1`.
- **Rationale**: Direct path to DAG-aware sequential execution and shared context. Skips early 0.5.0 bugs.

## 7. Risks and Unknowns
- **Branch Enforcement**: Transitioning from `main` to feature branches might trigger `doctor` failures in some commands unless `--force` or specific flags are used.
- **Adapter Refactor**: Current `DopetaskAdapter` must be rewritten to handle the new multi-step state model.

## 8. Go / No-Go Recommendation
- **Go**: Proceed with migration to 0.5.1. The upstream contract is confirmed and aligns with the 2026 roadmap.
