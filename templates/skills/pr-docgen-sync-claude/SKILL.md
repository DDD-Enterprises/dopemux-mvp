---
name: pr-docgen-sync-claude
description: Claude-optimized wrapper for the core pr-docgen-sync workflow. Use when you want PR documentation synchronization with claude-first routing defaults while preserving the same coverage matrix, index reconciliation, ticket sync, and fail-closed validation gates.
---

# PR Docgen Sync Claude Wrapper

Use this wrapper when you want `$pr-docgen-sync` behavior with claude-first defaults.

## Wrapper Defaults

- `preferred_cli=claude`
- `baseline=main...HEAD`
- `sync_tickets=best-effort`

## Delegation

Delegate all logic to `$pr-docgen-sync` and only override routing defaults.
