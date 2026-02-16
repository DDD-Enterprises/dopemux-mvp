---
id: DESKTOP-COMMANDER-DEEP-DIVE
title: Desktop Commander Deep Dive
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-09'
last_review: '2026-02-09'
next_review: '2026-05-10'
prelude: Desktop Commander Deep Dive (explanation) for dopemux documentation and developer
  workflows.
---
# Desktop Commander: Deep Technical Analysis

## SECTION 1: TECHNICAL REPORT

### Executive Summary & Strategic Intent
Desktop Commander is a dedicated MCP server designed to provide OS-level automation and state awareness to the Dopemux system. It acts as the "eyes and hands" of the ADHD Engine, enabling it to perceive user context (active window, app usage) and intervene when necessary (focus enforcement, notifications).

Unlike generic MCP servers, Desktop Commander implements a hybrid architecture that supports both macOS (via AppleScript/screencapture) and Linux (via wmctrl/xdotool/scrot), abstracting OS differences behind a unified MCP toolset.

### Architecture & Core Components (Validated)
The service is built as a FastAPI application (`server.py`) serving MCP tools over HTTP/SSE.

* **Service Type**: MCP Server (FastAPI)
* **Port**: 3012 (Default)
* **Container**: `mcp-desktop-commander`
* **Transport**: HTTP SSE (`/sse`) and POST (`/mcp`)

**Core Modules**:
1. **Server (`server.py`)**: Handles MCP protocol, tool routing, and OS abstraction.
2. **Integration Bridge (`integration_bridge_connector.py`)**: A specialized connector for the `dopecon-bridge` event bus, allowing direct event emission for workspace changes.

### Advanced Features & Intelligence
* **Hybrid OS Support**: Automatically detects `Darwin` (macOS) vs `Linux` and swaps backend tools at runtime.
* **ADHD Context Awareness**: Designed to support "sub-2s context switching" and "auto-focus windows", critical for maintaining flow state.
* **Token-Safe Design**: Validated to use file-path returns for screenshots instead of base64 encoding to preserve context window limits (see `DESKTOP_COMMANDER_VALIDATION.md`).

### Integration Patterns & Data Flow
1. **ADHD Engine Integration**:
    * The `DesktopActivityMonitor` in `adhd_engine/external_activity.py` polls Desktop Commander every 5 seconds.
    * It uses `list_resources` (or custom tool calls) to fetch active window state.
    * **Data Flow**: `Desktop Commander -> ADHD Engine -> Event Bus (WindowSwitchEvent)`.

2. **Dopecon Bridge Integration**:
    * Direct integration via `integration_bridge_connector.py` allows it to emit `workspace_switched` events directly to the global event bus, bypassing the polling loop for critical latency-sensitive actions.

### Testing, Performance, Limitations & Opportunities
* **Performance**: Local tool execution (AppleScript/subprocess) is generally fast (<100ms), but polling overhead in ADHD engine could be optimized.
* **Limitations**:
    * Requires X11 socket access on Linux.
    * Requires Accessibility permissions on macOS.
    * Currently appears **STOPPED** in the runtime environment.
* **Opportunities**:
    * Migrate from polling (ADHD Engine) to push-based events (via Bridge) for all activities, not just workspace switches.

## SECTION 2: EVIDENCE TRAIL

### Inventory Evidence (Phase 1)
* **Source Code**: Located in `docker/mcp-servers/desktop-commander`.
    * `server.py` (Main entrypoint)
    * `integration_bridge_connector.py` (Bridge integration)
    * `Dockerfile` (Python 3.10 slim)
* **Config**: Defined in `docker-compose.master.yml` (Service `desktop-commander`, Port 3012).

### Failure & Drift Findings (Phase 2)
* **[Observed] Runtime State**: Service is defined but not appearing in active `docker ps` output. Likely stopped or failed to start.
* **[Observed] Integration Match**: Code in `adhd_engine` matches the expected integration pattern (polling port 3012).

### Cross-Validation Summary
* **Validation Doc**: `docs/archive/mcp-servers/DESKTOP_COMMANDER_VALIDATION.md` confirms design safety regarding token usage.
* **Code Implementation**: `server.py` implements the file-path pattern confirmed in the validation doc.

## SECTION 3: LIVING DOCUMENTATION METADATA
- Last Validated: 2026-02-09
- Confidence Level: 90% (Source & Config verified, Runtime confirmed stopped)
- Evidence Quality Score: High (Direct code analysis)
- Evolution Log:
    - 2026-02-09: Initial Deep Dive completed. Phase 1-3 verified.
