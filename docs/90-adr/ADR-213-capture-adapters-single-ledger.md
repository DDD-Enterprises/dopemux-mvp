---
id: ADR-213-capture-adapters-single-ledger
title: Adr 213 Capture Adapters Single Ledger
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-21'
last_review: '2026-02-21'
next_review: '2026-05-22'
prelude: Adr 213 Capture Adapters Single Ledger (adr) for dopemux documentation and
  developer workflows.
status: proposed
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# Context

Dopemux needs reliable capture across Claude Code hook/plugin mode and
CLI/MCP-driven execution mode. Capture must remain deterministic and auditable
under degraded conditions, including MCP unavailability or tool drift.

Project memory authority is currently a per-project chronicle ledger. That
boundary must stay strict while enabling cross-project lookup through a global
rollup index.

# Decision

1. Dopemux adopts dual capture adapters with a shared capture client.
1. Both adapters write to one canonical per-project ledger path:
   `repo_root/.dopemux/chronicle.sqlite`.
1. MCP is not a capture authority. MCP remains a capability surface for explicit
   retrieval and downstream processing.
1. Capture uses deterministic idempotency (`event_id`) plus uniqueness-backed
   dedupe semantics.
1. Redaction occurs before persistence and fails closed on redaction dependency
   errors.
1. Injection remains explicit and opt-in only. No implicit prompt injection is
   permitted in capture paths.

# Architecture

Capture adapters:

1. Claude adapter: hook/plugin events route through `dopemux capture emit`.
1. CLI/MCP adapter: trigger/tool events route through the same capture client.

Shared capture guarantees:

1. Deterministic repo-root resolution using `.git` or `.dopemux` markers.
1. Fail-closed behavior outside a repository context.
1. Append-only raw event writes into `raw_activity_events`.
1. Duplicate-safe retries via `INSERT OR IGNORE` keyed by unique `event_id`.

# Consequences

Positive:

1. Capture remains available even when MCP services are disabled.
1. Deterministic event semantics stay consistent across adapters.
1. Memory quality improves by enforcing one canonical project ledger.

Tradeoffs:

1. Hook reliability depends on Claude runtime surfaces.
1. Deterministic `event_id` design must avoid coarse collisions.
1. Global rollup must stay read-only to avoid split-brain memory ownership.

# Non-goals

1. Making global rollup a write authority for project ledgers.
1. Introducing implicit prompt injection or hidden recap insertion.
1. Rewriting WMA promotion logic in this ADR scope.

# Acceptance Criteria

1. Both adapters write the same schema into `repo_root/.dopemux/chronicle.sqlite`.
1. Dedupe is enforced by schema uniqueness and deterministic `event_id`.
1. Redaction is applied before write and fails closed on dependency failures.
1. Disabling MCP does not stop baseline capture.
1. No implicit injection defaults are introduced.
