---
name: testgen-copilot
description: Copilot-oriented wrapper for the core testgen workflow. Use when you want testgen defaults aligned to copilot routing while preserving deterministic traceability, layer policy, and fail-closed coverage gates.
---

# Testgen Copilot Wrapper

Use this wrapper when you want `$testgen` behavior with copilot-oriented defaults.

## Wrapper Defaults

- `preferred_cli=copilot`
- `use_pal_testgen=auto`
- keep `coverage_target=90` unless caller overrides
- when equivalent subagent routing is unavailable, fall back to built-in test specialist

## Delegation

Delegate all logic to `$testgen` and only override routing defaults.
