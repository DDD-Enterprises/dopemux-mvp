---
id: ACTIVITY-CAPTURE-DEEP-DIVE
title: Activity Capture Deep Dive
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-09'
last_review: '2026-02-09'
next_review: '2026-05-10'
prelude: Activity Capture Deep Dive (explanation) for dopemux documentation and developer
  workflows.
---
# Activity Capture: Deep Technical Analysis

## SECTION 1: TECHNICAL REPORT

### Executive Summary & Strategic Intent
**Activity Capture** is the ingestion engine for the ADHD intelligence stack. It listens to system-wide events (workspace switches, task updates) via Redis Streams and transforms them into structured activity data for the **ADHD Engine**. Its primary goal is to eliminate the cognitive load of manual time-tracking and activity logging.

### Architecture & Core Components (Validated)
The service is a Python-based FastAPI application that acts primarily as a Redis Stream consumer.

*   **Service Type**: Event Consumer / Backend API
*   **Port**: 8096
*   **Container**: `dopemux-activity-capture`
*   **Upstream**: ADHD Engine (`http://host.docker.internal:8095`), Redis (`dopemux-redis-events`)

**Core Modules**:
1.  **`EventSubscriber`**: Manages the Redis Consumer Group and acknowledges processed messages.
2.  **`ActivityTracker`**: Aggregates raw events into time-windowed summaries (default 300s) to reduce noise and API pressure on the ADHD Engine.
3.  **`ADHDEngineClient`**: Handles authenticated communication with the ADHD Engine's `/activity` endpoints.

### Failure Analysis: CRITICAL BUG IDENTIFIED
**Status**: **Unhealthy / Blocked**.

**Root Cause**:
There is a fundamental "blocking startup" bug in the service's lifecycle management.
*   **File**: `services/activity-capture/main.py`
*   **Issue**: The `lifespan` context manager awaits `event_subscriber.start()`. Since `start()` contains an infinite `while self.running` loop, the lifespan startup never completes.
*   **Impact**: Uvicorn never starts the HTTP server because it's waiting for the lifespan to finish. Consequently, the health check fails (`Empty reply from server`), and the container is marked as `unhealthy`.

**Drift Findings**:
*   The `ADHD_ENGINE_URL` in `docker-compose.master.yml` points to `host.docker.internal`, which is inconsistent with other services that use internal container networking (e.g., `http://adhd-engine:8095`).

### Integration Patterns & Data Flow
1.  **Subscribe**: Joins the `activity-capture` consumer group on the `dopemux:events` stream.
2.  **Aggregate**: Batches events over 5-minute windows.
3.  **Sync**: Sends summaries to `ADHD Engine -> /activity/batch`.

### Testing, Performance, Limitations & Opportunities
*   **Testing**: No automated tests found.
*   **Limitations**:
  * **Blocking Startup**: Prevents the service from serving API/Health requests.
  * **Statelessness**: Aggregated counts are lost if the container restarts before the window closes (though it tries to flush on shutdown).
*   **Opportunities**:
  * **Fix Startup**: Change `await event_subscriber.start()` to `asyncio.create_task(event_subscriber.start())`.
  * **Externalize Windowing**: Use Redis-side aggregation for better persistence.

## SECTION 2: EVIDENCE TRAIL

### Inventory Evidence (Phase 1)
*   **Source Code**: `services/activity-capture/`.
*   **Runtime**: Container `dopemux-activity-capture` is running but **unhealthy**.

### Failure & Drift Findings (Phase 2)
*   **Logs**: Verified that the service reaches "Starting event subscription" but never reaches "Activity Capture Service ready!".
*   **Networking**: Identified the port 8096 mismatch/blocking issue.

## SECTION 3: LIVING DOCUMENTATION METADATA
* Last Validated: 2026-02-09
* Confidence Level: 100% (Bug identified and root cause confirmed)
* Evidence Quality Score: High (Reproducible logic error)
* Evolution Log:
  * 2026-02-09: Initial Deep Dive. Found critical blocking loop in FastAPI lifespan.
