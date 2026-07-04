---
id: gpt55-mcp-architecture-bundle-05-operator-ux
title: GPT55 MCP Architecture Bundle 05 Operator UX
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Phase 5 input bundle for Cockpit and operator UX design.
---
# Bundle 05: Operator UX

## Purpose

Design the seamless operator experience after architecture and roadmap are stable.

## Required Uploads

1. `prompt-05-operator-ux.md`
2. Phase 0-4 GPT-5.5 outputs
3. `docs/06-research/2026-07-04-dopemux-service-investigation/ux-integration-spec.md`
4. `docs/06-research/2026-07-04-dopemux-service-investigation/adhd-untracked-work-design.md`

## Source Chunks

Chunk A, Cockpit:

- `src/dopemux/ui/cockpit/`
- `tests/unit/dopemux/ui/cockpit/`

Chunk B, dashboard:

- `ui-dashboard/`
- `services/adhd-dashboard/`
- `services/activity-capture/`

Chunk C, CLI/operator lifecycle:

- `src/dopemux/commands/mcp_commands.py`
- `src/dopemux/mcp/fleet_catalog.py`
- `scripts/mcp-wrappers/`

Chunk D, F001 and ADHD:

- `services/serena/mcp_server.py`
- `services/serena/untracked_work_detector.py`
- `services/serena/untracked_work_storage.py`
- `services/adhd_engine/api/routes.py`
- `services/adhd_engine/main.py`

## UX Requirements

- No fake green states.
- Preserve `UNKNOWN`, `NOT_PROBED`, `DEGRADED`, `BLOCKED`, `ADVISORY`, and `PROXY`.
- Mutating actions require explicit confirmation.
- Every action emits a receipt naming canonical writer and target id.
- Show max three high-signal recommendations by default.
- Surface F001 and ADHD as supportive, not authoritative.

## Expected GPT-5.5 Phase Output

- Cockpit state model
- dashboard state model
- implicit session-start flow
- F001 quick-action flow
- receipt model
- visual quality and accessibility requirements
- UX-specific implementation slices
