---
id: ADHD_ENGINE_PROFILE_DETECTOR_VERIFICATION_2026_02_06
title: Adhd Engine Profile Detector Verification 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: draft
prelude: Verification that profile detection now queries ADHD Engine runtime endpoints for energy and attention signals with graceful fallback behavior.
---
# ADHD Engine Profile Detector Verification (2026-02-06)

## Scope

Closure verification for execution-packet backlog item:

`2.1.3: ADHD Engine client signal (query runtime endpoint, extract energy/attention, graceful fallback)`

## Implementation

1. Updated `src/dopemux/profile_detector.py`:
   - removed direct imports of ADHD service internals
   - added HTTP probing for:
     - `/api/v1/energy-level/{user_id}`
     - `/api/v1/attention-state/{user_id}`
   - base URL priority includes `http://localhost:5448` first with fallback support
   - returns `(None, None)` when service is unavailable or invalid
2. Stability fix:
   - added `get_profiles_directory` helper in `src/dopemux/profile_commands.py`
   - switched detector profile-dir default to `ProfileManager().profiles_dir`

## Verification

1. `pytest -q --no-cov tests/unit/test_profile_detector_adhd_client.py` passed.
2. `pytest -q --no-cov tests/unit/test_profile_cli_registration.py` passed.
3. `python -m py_compile src/dopemux/profile_detector.py src/dopemux/profile_commands.py` passed.

## Status

`implemented`

## Evidence Artifact

- `reports/strict_closure/adhd_engine_profile_detector_verification_2026-02-06.json`
