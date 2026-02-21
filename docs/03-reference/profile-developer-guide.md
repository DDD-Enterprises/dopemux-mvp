---
id: PROFILE_DEVELOPER_GUIDE_2026_02_06
title: Profile Developer Guide
type: reference
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: active
prelude: Developer reference for profile architecture, runtime interfaces, analytics signals, and extension points.
---
# Profile Developer Guide

## Architecture Overview

Primary modules:

1. `/Users/hue/code/dopemux-mvp/src/dopemux/profile_models.py`: schema and validation model.
1. `/Users/hue/code/dopemux-mvp/src/dopemux/profile_parser.py`: profile file parsing and validation.
1. `/Users/hue/code/dopemux-mvp/src/dopemux/profile_manager.py`: profile storage, marker resolution, config merge, and Claude-config detection.
1. `/Users/hue/code/dopemux-mvp/src/dopemux/profile_commands.py`: low-level command callbacks (`apply/use/current/create/copy/edit/delete`).
1. `/Users/hue/code/dopemux-mvp/src/dopemux/auto_detection_service.py`: background suggestion policy and debounce/quiet-hour gates.
1. `/Users/hue/code/dopemux-mvp/src/dopemux/profile_analytics.py`: switch telemetry, stats aggregation, optimization suggestion generation, and suggestion archival.
1. `/Users/hue/code/dopemux-mvp/src/dopemux/profile_analyzer.py`: git-history usage pattern analysis.
1. `/Users/hue/code/dopemux-mvp/src/dopemux/profile_wizard.py`: interactive profile generation from usage patterns.

CLI group integration is in `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` under `@profile.command(...)`.

## Runtime Contracts

Core non-breaking profile commands:

1. `dopemux profile apply <name>` and `dopemux profile use <name>`: same callback.
1. `dopemux switch <name>`: top-level alias to profile apply/use flow.
1. `dopemux profile current`: marker or Claude-config-based detection fallback.
1. `dopemux profile stats`: analytics + optimization recommendation output.
1. `dopemux profile analyze-usage`: git-history pattern analysis.

Important apply/switch options:

1. `--apply-config/--no-apply-config`
1. `--restart-claude`
1. `--save-session/--no-save-session`
1. `--restore-context/--no-restore-context`
1. `--target-seconds`

## Analytics Interfaces

ConPort categories:

1. `profile_metrics`: switch telemetry events.
1. `profile_optimization_recommendations`: archived optimization suggestion payloads.

Suggestion generation entrypoint:

1. `generate_optimization_suggestions(stats)` in `/Users/hue/code/dopemux-mvp/src/dopemux/profile_analytics.py`.

Archival entrypoint:

1. `archive_optimization_suggestions_sync(...)` in `/Users/hue/code/dopemux-mvp/src/dopemux/profile_analytics.py`.

## Auto-Detection Extension Points (Signal Collectors)

Current detector stack lives in `/Users/hue/code/dopemux-mvp/src/dopemux/profile_detector.py` and composes context from:

1. Git branch and modified file patterns.
1. Time windows and work-hour behavior.
1. ADHD Engine signal probes.

To add a new signal collector:

1. Add a collection method in `ProfileDetector` returning normalized score and evidence.
1. Add scoring weight and threshold behavior in detector scoring logic.
1. Update tests in `/Users/hue/code/dopemux-mvp/tests/unit/` with confidence-threshold coverage.
1. Extend user-facing explanation output (`format_match_summary`) when signal is surfaced to users.

Design constraints:

1. Keep collectors non-blocking with graceful fallback.
1. Preserve deterministic thresholds for `auto`, `prompt`, and `none`.
1. Maintain backwards-compatible output shapes.

## Test Anchors

Key suites:

1. `/Users/hue/code/dopemux-mvp/tests/unit/test_profile_use_command.py`
1. `/Users/hue/code/dopemux-mvp/tests/unit/test_profile_manager_detection.py`
1. `/Users/hue/code/dopemux-mvp/tests/unit/test_auto_detection_service.py`
1. `/Users/hue/code/dopemux-mvp/tests/unit/test_profile_analytics.py`
1. `/Users/hue/code/dopemux-mvp/tests/unit/test_profile_analyzer.py`
1. `/Users/hue/code/dopemux-mvp/tests/unit/test_profile_wizard.py`
