---
id: ADHD-DASHBOARD-DEEP-DIVE
title: ADHD Dashboard Deep Dive
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-09'
last_review: '2026-02-09'
next_review: '2026-05-10'
prelude: ADHD Dashboard Deep Dive (explanation) for dopemux documentation and developer
  workflows.
---
# ADHD Dashboard: Deep Technical Analysis

## SECTION 1: TECHNICAL REPORT

### Executive Summary & Strategic Intent
**ADHD Dashboard** is the primary visual interface for the ADHD intelligence stack. It provides real-time monitoring of energy levels, attention state, and cognitive load. Its strategic intent is to provide a "live" mirror of the user's cognitive state, enabling immediate awareness of hyperfocus or burnout risks.

### Architecture & Core Components (Validated)
The dashboard is a hybrid FastAPI application that serves a single-page HTML interface and provides a WebSocket-based data stream.

*   **Service Type**: Web Application / Monitoring Dashboard
*   **Port**: 8097
*   **Location**: `services/adhd-dashboard`
*   **Orchestration**: Resides in `services/adhd_engine/docker/mcp-servers/docker-compose.yml` (Legacy).

**Core Modules**:
1.  **`backend.py`**: The main FastAPI application.
    *   **WebSocket**: Manages live connections to the browser via `/ws/state`.
    *   **Redis Listener**: Subscribes to `adhd:state_changes:*` and broadcasts updates to all connected WebSockets.
    *   **HTML**: Embeds a modern, dark-themed CSS/JS dashboard directly in the code (lines 136-224).
2.  **`task_recommender.py`**: Intelligent logic for suggesting tasks based on current cognitive state (referenced but potentially elective).

### Failure & Drift Analysis
**Status**: **Un-orchestrated in Master Stack**.

**Findings**:
1.  **Documentation Drift**: README claims the service can be started via `docker-compose.master.yml`, but it is actually defined in the legacy ADHD engine compose file.
2.  **Networking Defaults**: The backend uses `localhost` defaults for `ACTIVITY_CAPTURE_URL` (8096) and `ADHD_ENGINE_URL` (8095). In a containerized stack, these must be overridden with service aliases (e.g., `http://activity-capture:8096`).
3.  **Security**: Implements an optional `X-API-Key` check, but it defaults to `None` (disabled) unless `DASHBOARD_API_KEY` is set.

### Integration Patterns & Data Flow
1.  **Ingress**: User accesses `http://localhost:8097`.
2.  **Stream**: Client opens a WebSocket to `/ws/state`.
3.  **Listen**: Backend listens to Redis Pub/Sub for state change events emitted by the ADHD Engine.
4.  **Broadcast**: State changes are pushed immediately to the browser.
5.  **Proxy**: The dashboard fetches initial state and historical metrics by proxying requests to ADHD Engine and Activity Capture.

### Testing, Performance, Limitations & Opportunities
*   **Testing**: Basic tests found in `services/adhd-dashboard/tests`.
*   **Limitations**:
    *   **Monolithic UI**: The UI is embedded in the Python file as a string. While simple, it limits development of a complex frontend.
    *   **State Dependency**: Relies heavily on healthy Activity Capture and ADHD Engine services.
*   **Opportunities**:
    *   **Componentize UI**: Move the HTML/CSS/JS to a standalone React/Next.js frontend in `ui-dashboard`.
    *   **Orchestrate**: Include in the unified dev stack to provide a "single pane of glass" for ADHD metrics.

## SECTION 2: EVIDENCE TRAIL

### Inventory Evidence (Phase 1)
*   **Source Code**: `services/adhd-dashboard`.
*   **Orchestration**: Found service definition in `adhd_engine/docker/mcp-servers/docker-compose.yml`.

### Failure & Drift Findings (Phase 2)
*   **Deployment Gap**: Verified the service is missing from `docker-compose.master.yml`.
*   **Config Drift**: Confirmed `ALLOWED_ORIGINS` in the master compose references port 8097, indicating intention but lack of implementation.

## SECTION 3: LIVING DOCUMENTATION METADATA
- Last Validated: 2026-02-09
- Confidence Level: 100%
- Evidence Quality Score: High
- Evolution Log:
    - 2026-02-09: Initial Deep Dive. Found robust real-time communication logic but orphaned deployment.
