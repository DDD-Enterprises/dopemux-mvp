---
title: "Memory and State"
plane: "pm"
component: "dopemux"
status: "skeleton"
---

# Memory and State

## Purpose

What state exists, where it lives, and how it is written/read without cross-worktree contamination.

## Scope

TODO: Define the scope of memory and state management in Dopemux.

## Non-negotiable invariants

TODO: List the memory-related invariants that must never be violated.

## FACT ANCHORS (Repo-derived)

TODO: Link to actual state store implementations and schemas.

## Open questions

TODO: List memory/state unknowns and how to resolve them.

## State taxonomy

### Ephemeral
- session state
- focus window state
- transient caches

### Workspace (per-worktree)
- workspace_id
- local state store
- per-worktree memory views

### Project (per repo)
- canonical repo-level stores
- shared but controlled read paths

### Global (rollups)
- cross-repo summaries
- only if explicitly enabled

TODO: List the actual stores and their file paths once verified.

## ConPort as memory authority
- decisions
- progress
- links
- provenance

TODO: Define the minimum required ConPort records for a run.

## Session Context SQLite usage

TODO: Document the schema and the read/write lifecycle.

## Rollup index contract
- what is promoted
- what is never promoted
- when promotion happens
- how promotion is attributed (interpretation vs facts)

TODO: Define promotion gates.

## Redaction and safety boundaries
- what never persists
- how sensitive fields are handled
- operator controls

TODO: Insert the redaction rules and do-not-store list.

## Hard invariants
- No cross-worktree reads unless explicitly requested.
- Promotion is interpretation, not elevation of fact.
- Immutable ledger semantics for events.

TODO: Expand each into enforceable tests or checks.

## Failure modes

TODO: List memory corruption, contamination, stale reads, and how to detect.

## Acceptance criteria

TODO: Define how we prove these invariants in tests or audits.
