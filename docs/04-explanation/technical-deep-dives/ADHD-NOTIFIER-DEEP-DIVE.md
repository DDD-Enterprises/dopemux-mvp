---
id: ADHD-NOTIFIER-DEEP-DIVE
title: ADHD Notifier Deep Dive
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-09'
last_review: '2026-02-09'
next_review: '2026-05-10'
prelude: ADHD Notifier Deep Dive (explanation) for dopemux documentation and developer
  workflows.
---
# ADHD Notifier: Deep Technical Analysis

## SECTION 1: TECHNICAL REPORT

### Executive Summary & Strategic Intent
**ADHD Notifier** is the feedback loop of the ADHD intelligence stack. It delivers intelligent, context-aware notifications (break reminders, hyperfocus alerts) across multiple channels (OS native, TTS, Mobile Push). Its intent is to minimize burnout by interrupting hyperfocus and encouraging breaks based on real-time activity metrics.

### Architecture & Core Components (Validated)
The service is a Python application primarily configured as a background monitor.

*   **Service Type**: Daemon / Monitor
*   **Port**: 8098 (FastAPI-ready, but primarily a polling daemon)
*   **Location**: `services/adhd-notifier`
*   **Orchestration**: Resides in `services/adhd_engine/docker/mcp-servers/docker-compose.yml` (Legacy).

**Core Modules**:
1.  **`main.py`**: Entry point that starts the monitoring loop.
2.  **`monitor.py`**: Orchestrates state checks. It polls **Activity Capture** (`8096/metrics`) and subscribes to `dopemux:events` for break suggestions.
3.  **`notify.py`**: Low-level OS integration for macOS (`osascript`/`say`) and Linux (`notify-send`).
4.  **`mobile_push.py`**: Multi-provider support for **Ntfy**, **Pushover**, and **Happy**.
5.  **`daily_reporter.py`**: Summarization logic for activity logs.

### Failure & Drift Analysis
**Status**: **Un-orchestrated in Master Stack**.

**Findings**:
1.  **Documentation Drift**: README claims it's in `docker-compose.master.yml`, which matches previous audits but is incorrect in the current state.
2.  **Hardcoded Dependencies**:
  * Polls `localhost:8096`. This will fail in Docker unless `network_mode: host` or correct internal aliases are used.
  * Subscribes to `localhost:6379` (Redis).
3.  **Pathing Fragility**: Imports `EventBus` using a relative path that expects `services/mcp-dopecon-bridge`. If this folder is renamed or moved (e.g., to `dopecon-bridge`), the service will crash on startup.
4.  **TTS Limitation**: Voice notifications are macOS-only.

### Integration Patterns & Data Flow
1.  **Poll**: Checks Activity Capture for session duration.
2.  **Listen**: Subscribes to Redis for `break.suggestion` events.
3.  **Context**: Fetch ADHD state if needed.
4.  **Execute**: Trigger OS notifications + TTS + Mobile Push if thresholds (25m/60m) are met.

### Testing, Performance, Limitations & Opportunities
*   **Testing**: Unit tests exist in `services/adhd-notifier/tests`.
*   **Opportunity**:
  * **Unified Push**: Centralize mobile push logic into a shared utility.
  * **Standardize Orchestration**: Bring into `docker-compose.master.yml` with correct network aliases.

## SECTION 2: EVIDENCE TRAIL

### Inventory Evidence (Phase 1)
*   **Source Code**: `services/adhd-notifier`.
*   **Structure**: Robust multi-channel notification logic detected.

### Failure & Drift Findings (Phase 2)
*   **Orchestration**: Confirmed as "orphaned" from the main master stack.
*   **Dependencies**: Validated logic for port 8096 and 6379 polling.

## SECTION 3: LIVING DOCUMENTATION METADATA
* Last Validated: 2026-02-09
* Confidence Level: 100%
* Evidence Quality Score: High
* Evolution Log:
  * 2026-02-09: Initial Deep Dive. Found robust notification implementation but deployment-level architecture drift.
