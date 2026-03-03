# Dopemux Coverage Policy

## Overview

To maintain high code quality without being blocked by historical baseline coverage, Dopemux enforces a **Scoped Coverage Policy**.

Instead of a repo-wide 80% coverage gate (which is currently unachievable), we require >= 80% coverage only on **newly developed or actively touched modules**.

## Policy Rules

1.  **Repo-wide tests must pass**: All unit tests in `tests/` must pass. There is no global coverage threshold for the entire repository.
2.  **Scoped thresholds**: Specific modules listed in the coverage manifest must maintain >= 80% coverage.
3.  **Local and CI parity**: Developers should use the same scripts used in CI to verify coverage before merging.

## Scoped Modules

Currently enforced modules:
- `dopemux.mcp.provision`
- `dopemux.mcp.instance_overlay`

## Canonical Commands

### Run all tests (no coverage gate)
```bash
pytest
```

### Run scoped coverage check
```bash
./scripts/check_coverage.sh
```

## Adding New Modules to Scope

When adding a new feature or refactoring a module, add its package path to `scripts/check_coverage.sh` in the `MODULES` variable to ensure it stays covered.
