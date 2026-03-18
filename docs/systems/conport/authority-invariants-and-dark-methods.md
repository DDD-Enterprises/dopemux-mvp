---
id: conport-authority-invariants-and-dark-methods
title: ConPort Authority Invariants And Dark Methods
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-12'
last_review: '2026-03-12'
next_review: '2026-06-10'
prelude: Authority invariants for ConPort plus classification of dark or underdocumented methods exposed on active surfaces.
---
# ConPort Authority Invariants And Dark Methods

## Authority invariants

ConPort is canonical for:

- decisions
- progress
- structured durable project context

The following remain non-canonical unless a separate ADR promotes them:

- mirrors
- caches
- graph projections
- search indexes
- dashboard summaries
- adapter-local reflections

Any mutation of canonical decision/progress/context truth must resolve back to ConPort itself.

## Dark-method decisions

| method family | current exposure | PM-plane status | decision |
|---|---|---|---|
| `fork_instance` | REST, JSON-RPC, FastMCP | not part of sanctioned PM-plane contract | retain as internal/admin-only |
| `promote` | REST, JSON-RPC, FastMCP | not part of sanctioned PM-plane contract | retain as internal/admin-only |
| `promote_all` | REST, JSON-RPC, FastMCP | not part of sanctioned PM-plane contract | retain as internal/admin-only |

## Decision counts

- intentionally exposed to the PM plane: `0`
- deprecated from active runtime: `0`
- retained as internal/admin-only: `3`

## Hardening notes

- The active callable surfaces do not show a repo-evidenced auth gate. Treat this as an operational hardening gap, not permission to bypass PM-plane policy.
- AGE / `ag_catalog` assumptions remain an environment-sensitive dependency and should be treated as a deployment risk until runtime evidence is tighter.
- PM-plane integrations should prefer the REST contract and never treat dark/admin methods as general-purpose workflow or PM write tools.
