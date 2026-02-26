---
id: MIGRATION_TASKX_TO_DOPETASK
title: Migration Taskx To Dopetask
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-25'
last_review: '2026-02-25'
next_review: '2026-05-26'
prelude: Migration Taskx To Dopetask (explanation) for dopemux documentation and developer
  workflows.
---
# TaskX to dopeTask Migration Guide

## Summary

✅ **MIGRATION COMPLETE** - This document outlines the completed migration from taskX to dopeTask in the dopemux-mvp codebase.

**Action**: Migrated to dopeTask 0.1.4 via pip installation
**Status**: Fully migrated to dopeTask 0.1.4 via pip installation
**Date**: 2024
**Approach**: Comprehensive cleanup with documentation updates

## Changes Made

### 1. Package Migration
- **Before**: taskX 0.1.0 (git submodule)
- **After**: dopetask 0.1.4 (pip package)
- **Action**: Uninstalled taskX, using dopetask pip package

### 2. Configuration Files Updated

#### `.taskx-pin` → `.dopetask-pin`
```diff
- install=git
- repo=https://github.com/hu3mann/taskX.git
- ref=v0.1.2
- commit=f5bd9e390cd485a0cd4db93f8dc5def59ef12a15
+ install=pip
+ dep=dopetask
+ version=0.1.4
```

#### `.gitmodules`
```diff
- [submodule "vendor/taskx"]
-   path = vendor/taskx
-   url = https://github.com/hu3mann/taskX.git
+ [submodule "vendor/dopetask"]
+   path = vendor/dopetask
+   url = https://github.com/hu3mann/dopetask.git
```

### 3. Script Updates

#### `scripts/taskx` → `scripts/dopetask`
- Updated references from `taskX` to `dopeTask`
- Changed environment variable names (`TASKX_*` → `DOPETASK_*`)
- Updated the executable name from `taskx` to `dopetask`

### 4. Directory Structure Changes

```diff
- .taskxroot
- .taskx/
- .taskx_venv/
- vendor/taskx/
+ .dopetaskroot
+ .dopetask/
+ .dopetask_venv/
+ vendor/dopetask/
```

### 5. Documentation Updates

#### `docs/planes/pm/dopemux/07_TASKX_INTEGRATION.md` → `docs/planes/pm/dopemux/07_DOPETASK_INTEGRATION.md`
- Updated all references from TaskX to dopeTask
- Updated invariant IDs (INV-TX-001 → INV-DT-001)
- Updated code examples and file paths

### 6. Test Updates

#### `tests/arch/test_taskx_submodule_contract.py` → `tests/arch/test_dopetask_submodule_contract.py`
- Updated test names and assertions
- Changed file paths from taskx to dopetask

#### `tests/unit/test_taskx_wrapper_submodule.py` → `tests/unit/test_dopetask_wrapper_submodule.py`
- Updated test functions and assertions
- Changed all taskx references to dopetask

## Migration Steps for Supervisors

### 1. Update Environment
```bash
# Remove old taskX
pip uninstall taskx -y

# Ensure dopetask is installed
pip install dopetask==0.1.4
```

### 2. Update File References
- Replace all `taskx` command calls with `dopetask`
- Update any scripts that reference `.taskx_venv` to use `.dopetask_venv`
- Update configuration files to reference `vendor/dopetask` instead of `vendor/taskx`

### 3. Verify Installation
```bash
# Check dopetask is available
dopetask --version

# Should output: 0.1.4
```

## Backward Compatibility

The migration maintains the same core functionality:
- Deterministic task execution kernel
- One-way call direction (Supervisor → dopeTask)
- File artifact communication
- Same CLI interface and arguments

## LLM Integration Updates

For LLM configurations and prompts:

1. **Update command references**:
   ```diff
   - "Run: taskx execute --plan=..."
   + "Run: dopetask execute --plan=..."
   ```

2. **Update tool descriptions**:
   ```diff
   - "taskX: deterministic task execution engine"
   + "dopetask: deterministic task execution engine"
   ```

3. **Update file path references**:
   ```diff
   - ".taskx_venv/bin/taskx"
   + ".dopetask_venv/bin/dopetask"
   ```

## Supervisor Instructions Update

### Updated Workflow
1. **Task Execution**: Use `dopetask execute` instead of `taskx execute`
2. **Plan Validation**: Use `dopetask validate` instead of `taskx validate`
3. **Environment Setup**: Ensure `.dopetaskroot` exists instead of `.taskxroot`

### Command Reference

| Old Command                       | New Command                          |
| --------------------------------- | ------------------------------------ |
| `taskx --version`                 | `dopetask --version`                 |
| `taskx execute --plan=plan.yaml`  | `dopetask execute --plan=plan.yaml`  |
| `taskx validate --plan=plan.yaml` | `dopetask validate --plan=plan.yaml` |

## Verification Checklist

- [x] dopetask package installed (0.1.4)
- [x] taskX package uninstalled
- [x] Configuration files updated
- [x] Scripts updated
- [x] Documentation updated
- [x] Tests updated
- [ ] CI/CD pipeline updated (if applicable)
- [ ] Supervisor configurations updated
- [ ] LLM prompt templates updated

## Rollback Procedure

If issues arise, rollback using:
```bash
# Reinstall taskX
pip install taskx==0.1.0

# Revert configuration files from git
git checkout .taskx-pin .gitmodules

# Restore original scripts
git checkout scripts/taskx
```

## Support

For migration issues, refer to:
- dopeTask documentation: https://github.com/hu3mann/dopetask
- dopemux-mvp integration docs: `docs/planes/pm/dopemux/07_DOPETASK_INTEGRATION.md`
- Test suites: `tests/arch/test_dopetask_submodule_contract.py`
