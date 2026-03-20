---
id: BASE_BRANCH_DETECTION_RULES
title: Base Branch Detection Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Base Branch Detection Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Base Branch Detection Rules

## Purpose
Determining the correct target base branch is critical for calculating accurate diffs and identifying obligations.

## Sources (in priority order)

### 1. Explicit Configuration
User-provided overrides (e.g., via CLI flag `--base-branch`) or repository-specific config files.

### 2. Upstream Tracking
The branch's configured tracking remote branch (e.g., `origin/main`).
- **Command**: `git rev-parse --abbrev-ref --symbolic-full-name @{u}`

### 3. Repository Default Branch
The primary default branch of the repository.
- **Source**: `git symbolic-ref refs/remotes/origin/HEAD` or fallback to `main`/`master`.

### 4. Heuristic Search
If no upstream is tracked, search for common base branches:
- `main`
- `master`
- `develop`
- `release/*`

Evaluate candidates based on:
- **Proximity**: Closest common ancestor with minimal divergence.
- **Naming**: Patterns like `feat/*` or `fix/*` often target `develop` or `main`.

## Confidence Model

| Confidence | Description |
|---|---|
| **HIGH** | Explicitly configured OR upstream tracked and consistent with default. |
| **MEDIUM** | Closest heuristic candidate with a plausible merge base. |
| **LOW** | Multiple ambiguous candidates OR significant divergence from all candidates. |
| **UNKNOWN** | Unable to find any common base branches. |

## Posture Impact
- **LOW** confidence triggers `CAUTION` posture.
- **UNKNOWN** confidence triggers `BLOCK_UNTIL_CLEAN`.
