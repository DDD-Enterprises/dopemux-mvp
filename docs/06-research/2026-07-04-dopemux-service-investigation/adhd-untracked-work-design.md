---
id: adhd-untracked-work-design
title: ADHD Untracked Work Design
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: ADHD Untracked Work Design (reference) for dopemux documentation and developer
  workflows.
---
# ADHD + Serena/F001 + Task Orchestrator + Cockpit Integration Design

## Current Truth

### ADHD Engine

- OBSERVED: `services/adhd_engine/main.py` creates a FastAPI service and FastMCP app named `ADHD-Engine`.
- OBSERVED: ADHD Engine exposes HTTP root, `/health`, `/metrics`, `/api/v1/*`, `/mcp`, and stdio MCP via `services/adhd_engine/mcp_stdio.py`.
- OBSERVED: `services/adhd_engine/api/routes.py` exposes cognitive state, task assessment, activity, break, hook, WebSocket, trust, and dashboard-friendly endpoints.
- OBSERVED: ADHD Engine uses Redis/cache/in-memory state, bridge projections, and event helper modules. A single durable ADHD ledger is not proven.
- CONCLUSION: ADHD Engine owns current support-state and recommendations only. It does not own PM truth, workflow transitions, chronicle, ConPort, dope-context, or bridge authority.

### Serena/F001

- OBSERVED: `services/serena/untracked_work_detector.py` implements base and enhanced detection through `detect()` and `detect_with_enhancements()`.
- OBSERVED: Enhanced F001 components exist: false-starts aggregation, design-first detection, revival suggestions, and prioritization context.
- OBSERVED: `services/serena/mcp_server.py` implements `detect_untracked_work_enhanced_tool()`.
- OBSERVED: `detect_untracked_work_enhanced` is not registered in `list_tools()` and is not routed in `call_tool()`.
- CONCLUSION: Enhanced F001 is implemented but not currently callable through Serena MCP by the expected tool name.

### Task Orchestrator / PM Authority

- OBSERVED: Task Orchestrator is canonical for workflow-significant transitions and workflow views.
- OBSERVED: ConPort is canonical for structured decisions/progress/custom data.
- OBSERVED: Serena currently uses ConPort-shaped custom-data/progress calls for F001 records.
- CONCLUSION: F001 can recommend or request tracking, but final workflow item creation/transition needs Task Orchestrator/ConPort authority boundaries.

### Cockpit / Dashboard

- OBSERVED: Cockpit render modes are deterministic, guarded, and no-write.
- OBSERVED: ADHD dashboard/backend and `ui-dashboard` consume ADHD Engine state separately.
- UNKNOWN: A live Cockpit data source for Serena F001 or ADHD Engine state is not proven.
- CONCLUSION: Cockpit should become the unified operator surface for F001/service awareness, but action execution should remain gated and receipt-based.

## Intended Final Design

### Data Flow

```text
workspace/git state
  -> Serena F001 detector
  -> ConPort custom_data: untracked_work
  -> Cockpit service/F001 data source
  -> operator quick action
  -> Task Orchestrator or ConPort canonical writer
  -> receipt mirrored to dope-memory where appropriate

activity/window/git/hook signals
  -> workspace-watcher/activity-capture/ADHD hooks
  -> ADHD Engine current state and recommendations
  -> dashboard/Cockpit cognitive-state panel
  -> non-authoritative suggestions only
```

### Authority Rules

- Serena detects and explains. It does not own PM truth.
- ADHD Engine assesses cognitive state and suggests accommodations. It does not own PM truth.
- Cockpit displays, asks, gates, and receipts. It does not silently mutate.
- Task Orchestrator owns workflow transitions and next-work state.
- ConPort owns structured progress, decisions, custom data, and F001 record persistence.
- dope-memory owns historical receipts, not current PM state.
- dopecon-bridge transports/proxies and must carry provenance.

### F001 Enhanced Tool Contract

PROPOSED MCP tool:

```text
detect_untracked_work_enhanced(session_number: int = 1, show_details: bool = false)
```

Minimum response requirements:

- `status`: `all_clear | untracked_work_detected | degraded | error`
- `work_summary`: name, branch, files changed, confidence, threshold
- `false_starts_dashboard`: total unfinished, snoozed, abandoned, message, provenance
- `design_first_recommendation`: optional, with reasons and document type
- `revival_suggestions`: optional, max 3
- `prioritization_context`: active counts and risk level
- `suggested_actions`: inspect, track, design_first, resume_abandoned, snooze, ignore
- `provenance`: tool version, workspace id, ConPort availability, fallback flags

The existing implementation already produces most content, but the MCP registration and degraded provenance need hardening.

## Implementation Gaps

1. F001 Enhanced tool is not registered/callable through Serena MCP.
2. F001 fallback behavior returns empty/mock-like summaries without a strong degraded flag.
3. Cockpit does not have a proven live F001/ADHD/service-state data source.
4. ADHD dashboard and Cockpit are separate UX surfaces with no shared service-state model.
5. Service aliases are not normalized into one operator-facing model.
6. Task Orchestrator integration for F001 quick actions is not clearly defined as a gated write path.

## Proposed Integration Slices

1. Register and test `detect_untracked_work_enhanced` in Serena MCP.
2. Add explicit degraded/provenance fields to F001 responses when ConPort or pattern history is unavailable.
3. Add a read-only Cockpit data source for service inventory, ADHD state, and F001 summary.
4. Add Cockpit UI rows for untracked work: inspect, copy evidence, create Task Packet prompt, and open safe action gate.
5. Add gated action adapters for track/snooze/ignore/design-first with ConPort/Task Orchestrator receipts.
6. Add dashboard/Cockpit shared display contract so the web dashboard and terminal Cockpit present the same cognitive/F001 truth states.

## Safety Constraints

- No implicit PM writes.
- No silent conversion of `UNKNOWN` to OK.
- No content-bearing hook payloads into ADHD Engine.
- No bridge-owned authority claims.
- No service start/stop from Cockpit without typed service id, explicit consent, and proof receipt.
