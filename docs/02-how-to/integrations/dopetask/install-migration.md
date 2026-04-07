---
id: dopetask-install-migration
title: dopeTask Installer and Wrapper Migration
type: how-to
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-26'
last_review: '2026-03-26'
next_review: '2026-06-26'
status: active
prelude: Migration guide for upgrading dopeTask to 0.5.1 with hardened wrapper and drift detection.
---
# dopeTask Installer and Wrapper Migration (TP-DSER-002)

## Status
- **Target Version**: 0.5.1
- **Install Method**: `pip` (with `uv` fallback support)
- **Date**: 2026-03-26

## Rationale
TP-DSER-001 proved that `dopetask==0.5.1` is stable and introduces the `series` command group (`exec`, `status`, `finalize`) required for upcoming multi-step task orchestration. Version 0.2.0 was identified as legacy and lacked these capabilities.

## Changes

### 1. Version Pinning
Updated `.dopetask-pin` and `pyproject.toml` to lock `dopetask` at `0.5.1`. This ensures consistency across local environments and CI.

### 2. Wrapper Hardening (`scripts/dopetask`)
The wrapper was rewritten to:
- **Validate Pins**: Strictly read `.dopetask-pin` for the target version and method.
- **Fail Closed**: Exit with an error if `.dopetaskroot` or `.dopetask-pin` are missing.
- **Optimized Install**: Support `install=uv` in the pin for faster execution, with a seamless fallback to `pip` if `uv` is unavailable.
- **Drift Detection**: Automatically trigger a re-install if the local venv version marker does not match the pin.
- **Doctor Awareness**: Added hints for `dopetask doctor` failures on non-main branches, a behavior confirmed in 0.5.x.

### 3. Submodule Decoupling
Removed legacy checks for `.repo_id` and `.dopetask/project.json` within the wrapper to avoid coupling with vendor/submodule logic, focusing purely on the installation contract.

## Verification
- Verified `scripts/dopetask --version` returns `0.5.1`.
- Unit tests in `tests/unit/test_dopetask_wrapper_submodule.py` cover pin parsing, failure modes, and installation triggers.
- Architecture tests in `tests/arch/test_dopetask_submodule_contract.py` confirm no submodule leakage.
