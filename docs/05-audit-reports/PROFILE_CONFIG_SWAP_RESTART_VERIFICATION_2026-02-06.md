---
id: PROFILE_CONFIG_SWAP_RESTART_VERIFICATION_2026_02_06
title: Profile Config Swap Restart Verification 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: draft
prelude: Verification that profile apply now performs backup-safe Claude config swap before activation and supports optional Claude restart command execution.
---
# Profile Config Swap Restart Verification (2026-02-06)

## Scope

Closure verification for execution-packet backlog item:

`3.2.3: Config swap and restart (backup config, atomic write, start Claude, verify success)`

## Runtime Change

Updated `src/dopemux/profile_commands.py` and `src/dopemux/claude_config.py`:

1. `dopemux profile apply/use <profile>` now applies profile MCP filtering to Claude `settings.json` before switching active marker.
1. Config apply uses backup-aware write path and captures backup path for downstream recovery.
1. Added additive `--restart-claude` option to run `dopemux start --profile <name>` and verify command success.

## Test Coverage

Added in `tests/unit/test_profile_use_command.py`:

1. `test_use_profile_applies_config_and_sets_active`
1. `test_use_profile_no_apply_config_skips_claude_updates`
1. `test_use_profile_restart_flag_runs_dopemux_start`

Added in `tests/test_claude_config.py`:

1. `test_apply_profile_returns_backup_path_when_requested`

## Verification

1. `pytest -q --no-cov tests/unit/test_profile_use_command.py` passed.
1. `pytest -q --no-cov tests/test_claude_config.py` passed.
1. `python -m py_compile src/dopemux/profile_commands.py src/dopemux/claude_config.py` passed.

## Status

`implemented`

## Evidence Artifact

- `reports/strict_closure/profile_config_swap_restart_verification_2026-02-06.json`
