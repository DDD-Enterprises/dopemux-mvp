---
name: pr-docgen-sync-gemini
description: Gemini-optimized wrapper for the core pr-docgen-sync workflow. Use when you want PR documentation synchronization with gemini-oriented routing defaults while preserving the same coverage matrix, index reconciliation, ticket sync, and fail-closed validation gates.
---

# PR Docgen Sync Gemini Wrapper

Use this wrapper when you want `$pr-docgen-sync` behavior with gemini-first defaults.

## Wrapper Defaults

- `preferred_cli=gemini`
- `baseline=main...HEAD`
- `sync_tickets=best-effort`

## Delegation

Delegate all logic to `$pr-docgen-sync` and only override routing defaults.
