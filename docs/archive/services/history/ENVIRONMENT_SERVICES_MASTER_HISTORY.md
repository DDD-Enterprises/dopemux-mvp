---
id: ENVIRONMENT_SERVICES_MASTER_HISTORY
title: Environment Services Master History
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Environment Services Master History (explanation) for dopemux documentation
  and developer workflows.
---
# Environment & Workspace Services: Master History & Feature Catalog

**Services**: `workspace-watcher`, `activity-capture`, `desktop-commander`, `voice-commands`
**Role**: Physical/Digital Environment Sensory Layer
**Status**:
*   Watcher: Production
*   Desktop Commander: Production (MCP)
*   Activity Capture: Production
*   Voice Commands: Beta

---

## 1. Executive Summary

The **Environment Services** form the "Senses" of the Dopemux system. They allow the system to "see" what the user is doing (Activity Capture), "watch" the files they touch (Workspace Watcher), "control" their window focus (Desktop Commander), and "hear" their commands (Voice).

**Key Synergy**: These services work together to create the "Zero-Friction Context Switch". When the user switches tasks in the TUI, Desktop Commander rearranges windows while Workspace Watcher loads the relevant files.

---

## 2. Feature Catalog

### 👀 Workspace Watcher (`services/workspace-watcher`)
*   **Real-Time Monitoring**: Detects file changes/creates/deletes.
*   **Intelligent Filtering**: Ignores `node_modules`, `.git`, `__pycache__` to reduce noise.
*   **Multi-Workspace**: Simultaneously monitors multiple project roots.
*   **Event Publishing**: Pushes `workspace:file_modified` to Redis Streams.

### 🎥 Activity Capture (`services/activity-capture`)
*   **Passive Logging**: No push-buttons. It infers activity from file edits and window switches.
*   **Session Tracking**: Groups rapid-fire events into "Focus Sessions".
*   **ADHD Engine Sync**: Feeds raw activity data into the ADHD Engine for metrics calculation.

### 🖥️ Desktop Commander (`docker/mcp-servers/desktop-commander`)
*   **Window Management**: `focus_window("code")`, `list_windows()`.
*   **Visual Context**: `screenshot()` capability for providing visual context to Vision LLMs.
*   **MCP Interface**: Exposes desktop control to any MCP-compliant agent.

### 🎙️ Voice Commands (`services/voice-commands`)
*   **Voice Decomposition**: "Break down the auth feature" -> [Audio] -> [TaskDecomposer].
*   **Hands-Free**: Integration with Zen for complex planning without typing.
*   **Bridge Adapter**: Direct integration with ConPort for storing voice-generated tasks.

---

## 3. Architecture Deep Dive

### The Sensory Loop
```
[User Types Code] -> [Workspace Watcher]
                          |
                          v
                   [Activity Capture] --(logs)--> [ADHD Engine]
                          |
                          v
[User Switches Task] -> [Desktop Commander] --(refocuses)--> [New Window]
```

### Integration Points
*   **Redis Streams** is the backbone here (`workspace:events`, `activity:events`).
*   **Desktop Commander** is an MCP Server, meaning it can be used by *Claude* or *Task Orchestrator* to control the screen.

---

## 4. Validated Status (Audit Results)

**✅ Operational:**
*   **Workspace Watcher**: Production ready, ignoring patterns works.
*   **Activity Capture**: Safely shutting down and flushing to ADHD Engine.
*   **Desktop Commander**: Validated with Docker/X11 forwarding.

**⚠️ Beta / Experimental:**
*   **Voice Commands**: Functional API (`voice_api.py`) but relies on external `ZEN_URL`.

---

*Sources: `workspace-watcher/README.md`, `activity-capture/main.py`, `desktop-commander/README.md`, `voice_api.py`.*
