---
id: PROFILE_CURRENT_DETECTION_VERIFICATION_2026_02_06
title: Profile Current Detection Verification 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: draft
prelude: Verification that active profile detection now falls back to Claude config MCP-state matching with workspace marker caching.
---
# Profile Current Detection Verification (2026-02-06)

## Scope

Closure verification for execution-packet backlog item:

`4.1.1: Detect current profile from config (read config, match MCP list, cache result)`

## Runtime Change

Updated `src/dopemux/profile_manager.py`:

1. Added `detect_profile_from_claude_config(...)`:
- reads Claude settings JSON
- checks `_dopemux_active_profile` metadata first
- falls back to MCP-set matching against known profiles
- uses overlap-based fallback match (`>= 0.8`) when exact match is absent
1. Added optional workspace marker cache write for detected profile.

Updated `src/dopemux/profile_commands.py`:

1. `profile current`/`profile show` now attempts detection from Claude config when no active-profile marker exists.
1. Detected result is cached to workspace marker to avoid repeated recomputation.

## Test Coverage

Added in `tests/unit/test_profile_manager_detection.py`:

1. `test_detect_profile_uses_embedded_active_profile_and_caches`
1. `test_detect_profile_matches_exact_mcp_set`
1. `test_detect_profile_uses_overlap_threshold`
1. `test_detect_profile_returns_none_when_match_is_weak`

## Verification

1. `pytest -q --no-cov tests/unit/test_profile_manager_detection.py tests/unit/test_profile_use_command.py tests/unit/test_profile_cli_registration.py` passed.
1. `python -m py_compile src/dopemux/profile_manager.py src/dopemux/profile_commands.py` passed.

## Status

`implemented`

## Evidence Artifact

- `reports/strict_closure/profile_current_detection_verification_2026-02-06.json`
