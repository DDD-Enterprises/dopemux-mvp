---
id: WORKSPACE-WATCHER-DEEP-DIVE
title: Workspace Watcher Deep Dive
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-09'
last_review: '2026-02-09'
next_review: '2026-05-10'
prelude: Workspace Watcher Deep Dive (explanation) for dopemux documentation and developer
  workflows.
---
# Workspace Watcher: Deep Technical Analysis

## SECTION 1: TECHNICAL REPORT

### Executive Summary & Strategic Intent
**Workspace Watcher** is a peripheral monitoring service designed to detect "context switches" by observing active applications and file system changes. It feeds this data into the **Cognitive Plane** (ADHD Engine) to enable automatic session tracking and interruption detection—critical features for the ADHD-assistive capabilities of Dopemux.

### Architecture & Core Components (Validated)
The service is a standalone Python application intended to run as a background agent.

*   **Service Type**: Background Agent (Python)
*   **Location**: `services/workspace-watcher`
*   **Orchestration**:
  * **Master**: *Missing* from `docker-compose.master.yml`.
  * **Local**: Defined in `services/adhd_engine/docker/mcp-servers/docker-compose.yml`.
*   **Dependencies**: Redis (for event emission), OS-level APIs (`osascript`, `wmctrl`).

**Core Modules**:
1.  **`main.py`**: Entry point. Runs an asyncio event loop that polls `AppDetector`.
2.  **`app_detector.py`**: Uses platform-specific commands (AppleScript on macOS) to find the focused window/app.
3.  **`workspace_mapper.py`**: Maps application names (e.g., "VS Code") to specific project paths via `config.json`.
4.  **`event_emitter.py`**: Pushes `workspace.switched` events to Redis Streams.

### Failure & Drift Analysis
**Status**: **Not Running / Fragmented Orchestration**.

**Findings**:
1.  **Orchestration Drift**: The README claims it runs via `docker-compose.master.yml`, but it is actually only defined in a nested, likely obsolete, `services/adhd_engine/docker/mcp-servers/docker-compose.yml`.
2.  **Containerization Challenge**: The service relies on `osascript` to query the macOS Window Server. This works natively on the host but **will fail inside a standard Docker container** unless specifically configured with access to the host's windowing system (which is non-trivial and often brittle).
3.  **Documentation Gap**: The `README.md` instructions are misleading regarding the Docker startup method.

### Integration Patterns & Data Flow
1.  **Input**: Polls OS for active window title/process name.
2.  **Logic**: Checks `config.json` to see if the active app corresponds to a known workspace.
3.  **Output**: Emits `workspace.switched` event to Redis -> Consumed by `Activity Capture` -> Processed by `ADHD Engine`.

### Testing, Performance, Limitations & Opportunities
*   **Testing**: "No visible test coverage" (confirmed by Audit Reports).
*   **Limitations**:
  * **Host Dependency**: Highly coupled to the host OS.
  * **Polling**: Uses a 5s polling interval, which might miss rapid switches or add latency.
*   **Opportunities**:
  * **Refactor to Host Agent**: Officially designate this as a "Host Agent" that should be run via `systemd` or `launchd` rather than Docker, and update documentation/scripts (`start-all.sh`) to reflect this.

## SECTION 2: EVIDENCE TRAIL

### Inventory Evidence (Phase 1)
*   **Source Code**: `services/workspace-watcher`.
*   **Configuration**: `config.json` (mappings), `services/adhd_engine/docker/mcp-servers/docker-compose.yml` (legacy docker config).

### Failure & Drift Findings (Phase 2)
*   **Drift**: Service is referenced in "Environment" reports but missing from the master orchestration file.
*   **Code**: `AppDetector` explicitly checks for `darwin` (macOS) and uses `osascript`, confirming the host dependency.

## SECTION 3: LIVING DOCUMENTATION METADATA
* Last Validated: 2026-02-09
* Confidence Level: 90% (Source and Docs validated; Runtime not active but logic is clear)
* Evidence Quality Score: High (Code analysis + Config trace)
* Evolution Log:
  * 2026-02-09: Initial Deep Dive. Identified orchestration drift and host-dependency constraints.
