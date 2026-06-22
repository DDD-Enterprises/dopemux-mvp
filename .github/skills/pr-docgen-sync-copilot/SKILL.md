---
name: pr-docgen-sync-copilot
description: Copilot-oriented wrapper for the core pr-docgen-sync workflow. Use when you want PR documentation synchronization with copilot-oriented routing defaults while preserving the same coverage matrix, index reconciliation, ticket sync, and fail-closed validation gates.
---

# PR Docgen Sync Copilot Wrapper

Use this wrapper when you want `$pr-docgen-sync` behavior with copilot-oriented defaults.

## Wrapper Defaults

- `preferred_cli=copilot`
- `baseline=main...HEAD`
- `sync_tickets=best-effort`

## Delegation

Delegate all logic to `$pr-docgen-sync` and only override routing defaults.
