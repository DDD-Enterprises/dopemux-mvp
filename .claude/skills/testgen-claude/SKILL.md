---
name: testgen-claude
description: Claude-optimized wrapper for the core testgen workflow. Use when you want the testgen skill defaults to route specialist test generation through Claude-first subagent strategy while preserving the same contracts and fail-closed coverage behavior.
---

# Testgen Claude Wrapper

Use this wrapper when you want `$testgen` behavior with Claude-first specialization defaults.

## Wrapper Defaults

- `preferred_cli=claude`
- `use_pal_testgen=auto`
- keep `coverage_target=90` unless caller overrides

## Delegation

Delegate all logic to `$testgen` and only override routing defaults.
