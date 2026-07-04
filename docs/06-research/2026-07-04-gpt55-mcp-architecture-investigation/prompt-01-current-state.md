---
id: gpt55-mcp-architecture-prompt-01-current-state
title: GPT55 MCP Architecture Prompt 01 Current State
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Phase 1 GPT-5.5 prompt for current-state inventory.
---
# Prompt 01: Current-State Inventory

You are GPT-5.5 Pro performing Phase 1 of a Dopemux MCP/service architecture review.

Use Phase 0 output and `bundle-01-current-state.md`. Do not design the final target architecture yet. Build the most accurate current-state map.

## Required Output

1. Service Inventory Matrix:
   - service/server name
   - source path
   - compose wiring
   - registry/catalog wiring
   - consumer/client wiring
   - health surface
   - tests
   - classification: canonical/support/adapter/infra/duplicate/legacy/dead/unknown
   - evidence label
2. MCP Surface Matrix:
   - server
   - transport
   - tool count if known
   - tool source
   - generated config status
   - consumed by Claude/Codex/Cockpit/CLI/other
3. Shadow-Twin Map:
   - conceptual service
   - competing implementations
   - active runtime
   - stale or dead twin
   - recommended investigation before disposition
4. Current-State Diagram in Mermaid.
5. Unknowns Blocking Target Architecture.

Every row must use `OBSERVED`, `INFERRED`, or `UNKNOWN`. No roadmap yet.
