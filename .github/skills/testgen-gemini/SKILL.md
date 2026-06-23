---
name: testgen-gemini
description: Gemini-optimized wrapper for the core testgen workflow. Use when you want the testgen skill defaults to route specialist test generation through Gemini-first subagent strategy while preserving the same contracts and fail-closed coverage behavior.
---

# Testgen Gemini Wrapper

Use this wrapper when you want `$testgen` behavior with Gemini-first specialization defaults.

## Wrapper Defaults

- `preferred_cli=gemini`
- `use_pal_testgen=auto`
- keep `coverage_target=90` unless caller overrides

## Delegation

Delegate all logic to `$testgen` and only override routing defaults.
