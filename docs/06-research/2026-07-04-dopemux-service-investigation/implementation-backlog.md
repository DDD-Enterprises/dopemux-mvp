---
id: implementation-backlog
title: Implementation Backlog
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Implementation Backlog (reference) for dopemux documentation and developer
  workflows.
---
# Implementation Backlog

This backlog is ordered to reduce authority drift before adding richer UX. Each item is commit-sized and Task-Packet-ready.

## P0: Correctness And Exposure

### TP-DMX-F001-ENHANCED-MCP-REGISTER-001

- Goal: Make the already-implemented Serena enhanced untracked-work detector callable through MCP.
- Scope: `services/serena/mcp_server.py`, Serena MCP tests.
- Changes:
  - Add `detect_untracked_work_enhanced` to `list_tools()`.
  - Add dispatch to `call_tool()`.
  - Update tool grouping metadata.
  - Add tests proving list and call dispatch.
- Validation:
  - `pytest -q services/serena/tests/test_mcp_server_local.py services/serena/test_f001_enhanced.py`
- Risk:
  - Current implementation may expose degraded ConPort fallback too optimistically; pair with next packet before UX surfacing.

### TP-DMX-F001-PROVENANCE-DEGRADED-001

- Goal: Make F001 fallback/degraded states explicit.
- Scope: Serena F001 detector/storage/aggregator output shapes and tests.
- Changes:
  - Add `provenance` and `degraded` fields to enhanced detection responses.
  - Distinguish `no data` from `ConPort unavailable`.
  - Ensure mock/empty dashboard summaries are never rendered as healthy history.
- Validation:
  - Serena F001 unit tests plus response-shape regression test.

### TP-DMX-SERVICE-MODEL-ALIASES-001

- Goal: Create a normalized service inventory model that groups directory, compose, registry, and catalog aliases.
- Scope: new read-only model under `src/dopemux/ui` or `src/dopemux/orchestrator/ui`.
- Changes:
  - Group aliases: `qdrant/mcp-qdrant`, `gptr-mcp/gpt-researcher`, `adhd_engine/adhd-engine`, `dope-memory/working-memory-assistant`, `conport-http/conport-mcp/conport`.
  - Expose classification and action policy.
- Validation:
  - Unit tests for alias grouping and classification.

## P1: Cockpit Read-Only Integration

### TP-DMX-COCKPIT-SERVICE-DATA-SOURCE-001

- Goal: Add a read-only Cockpit data source for service inventory and status provenance.
- Scope: Cockpit data-source layer and services mode.
- Changes:
  - Read compose/registry/catalog without starting services.
  - Display active, support, adapter, duplicate, legacy, unknown.
  - Preserve `UNKNOWN` and `NOT_PROBED`.
- Validation:
  - Cockpit render-mode tests and data-source unit tests.

### TP-DMX-COCKPIT-F001-PANEL-001

- Goal: Surface F001 untracked-work summary in Cockpit without writes.
- Scope: Cockpit events/services/implementer mode read-only panel.
- Changes:
  - Call Serena enhanced MCP when available.
  - Show degraded state when tool is missing or ConPort is unavailable.
  - Provide inspect/copy-evidence/copy-task-prompt actions only.
- Validation:
  - Unit tests for all-clear, detected, degraded, and unavailable states.

### TP-DMX-COCKPIT-ADHD-STATE-PANEL-001

- Goal: Surface ADHD Engine cognitive state in Cockpit as advisory support.
- Scope: Cockpit data source and render surface.
- Changes:
  - Read ADHD Engine health/state when available.
  - Never treat cognitive state as workflow authority.
  - Show stale/unavailable with explicit timestamp and source.
- Validation:
  - Unit tests using mocked ADHD Engine responses.

## P2: Gated Actions And Receipts

### TP-DMX-F001-TRACK-WORK-GATE-001

- Goal: Convert F001 track/snooze/ignore/design-first into safe action gates.
- Scope: Cockpit safe action gate, Serena action adapters, ConPort/Task Orchestrator receipts.
- Changes:
  - Require explicit operator confirmation.
  - Write only through canonical writer for each action.
  - Return receipts with source, destination, id, timestamp, and rollback/undo guidance.
- Validation:
  - Unit tests for receipt shape and blocked writes.

### TP-DMX-F001-TASK-ORCH-ESCALATION-001

- Goal: Escalate detected untracked work into Task Orchestrator when the operator chooses to track work as workflow.
- Scope: Task Orchestrator client adapter and F001 action flow.
- Changes:
  - Map F001 detection to a work item draft.
  - Keep ConPort custom-data as detection record, not workflow authority.
  - Link Task Orchestrator item id back to F001 record.
- Validation:
  - Adapter tests with fake Task Orchestrator.

## P3: Gorgeous Seamless UX

### TP-DMX-DASHBOARD-COCKPIT-SHARED-STATE-001

- Goal: Align web dashboard and terminal Cockpit display semantics.
- Scope: shared status model, dashboard mapping, Cockpit rendering.
- Changes:
  - Shared state labels: `LIVE`, `DEGRADED`, `NOT_PROBED`, `UNKNOWN`, `BLOCKED`.
  - Common colors/tokens with low cognitive load and no false green.
  - F001 summary and ADHD advisory state share provenance language.
- Validation:
  - UI tests for mapping, accessibility, and no misleading success state.

### TP-DMX-IMPLICIT-SESSION-START-SURFACING-001

- Goal: At session start, gently surface current untracked work and service drift without blocking.
- Scope: Dopemux startup/Cockpit session view.
- Changes:
  - Show max three high-signal items.
  - Avoid shame language and avoid modal interruption.
  - Offer one keystroke to inspect, not mutate.
- Validation:
  - Snapshot tests for clean slate, one untracked work item, many false-starts, and unavailable MCP.

## Deferred / Needs Decision

- Whether `activity-capture`, `workspace-watcher`, `adhd-dashboard`, and `adhd-notifier` should be promoted into canonical compose/registry.
- Whether source-only service directories should be archived after alias model lands.
- Whether web dashboard should remain separate from Cockpit or become a Cockpit web surface.
