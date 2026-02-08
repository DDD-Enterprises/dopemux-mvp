---
id: PROFILE_SWITCH_COMMAND_VERIFICATION_2026_02_06
title: Profile Switch Command Verification 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: draft
prelude: Verification that dopemux profile switching now provides orchestrated save, swap, optional restart, optional restore, and step-level timing output.
---
# Profile Switch Command Verification (2026-02-06)

## Scope

Closure verification for execution-packet backlog item:

`3.3.1: dopemux switch <profile> command (validate, save session, swap config, restart, restore, report time)`

## Runtime Change

Updated `src/dopemux/profile_commands.py` for `use/apply` and top-level `switch` alias behavior:

1. Added switch orchestration options:
   - `--save-session/--no-save-session`
   - `--restore-context/--no-restore-context`
   - `--target-seconds`
2. Added parallel execution for context save + config apply when both enabled.
3. Added step timing summary output and threshold warning signal.
4. Preserved existing compatibility:
   - `dopemux profile use <profile>`
   - `dopemux profile apply <profile>`
   - `dopemux switch <profile>` (existing alias contract)

## Test Coverage

Added in `tests/unit/test_profile_use_command.py`:

1. `test_use_profile_restart_flag_runs_dopemux_start`
2. `test_switch_full_to_developer_to_full_flow_with_context`
3. `test_use_profile_warns_when_switch_exceeds_target`

## Verification

1. `pytest -q --no-cov tests/unit/test_profile_use_command.py` passed.
2. `pytest -q --no-cov tests/unit/test_profile_cli_registration.py` passed.
3. `python -m py_compile src/dopemux/profile_commands.py` passed.

## Status

`implemented`

## Evidence Artifact

- `reports/strict_closure/profile_switch_command_verification_2026-02-06.json`
