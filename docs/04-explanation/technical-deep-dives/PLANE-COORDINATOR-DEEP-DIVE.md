---
id: PLANE-COORDINATOR-DEEP-DIVE
title: Plane Coordinator Deep Dive
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-09'
last_review: '2026-02-09'
next_review: '2026-05-10'
prelude: Plane Coordinator Deep Dive (explanation) for dopemux documentation and developer
  workflows.
---
# Plane Coordinator: Deep Technical Analysis

## SECTION 1: TECHNICAL REPORT

### Executive Summary & Strategic Intent
The **Plane Coordinator** is a specialized orchestration service designed to bridge the "PM Plane" (Leantime, Jira, etc.) and the "Cognitive Plane" (ADHD Engine, biological state). Its primary role is to ensure that task execution is biologically attuned—meaning tasks are scheduled, batched, and blocked based on the user's real-time cognitive capacity (ADHD state) rather than just deadline priorities.

It implements the "Two-Plane Architecture" where the PM Plane provides the *what* (tasks) and the Cognitive Plane provides the *when* and *how* (capacity).

### Architecture & Core Components (Validated)
The service is a Python-based FastAPI/Uvicorn application running in a Docker container (`dopemux-plane-coordinator`).

* **Service Type**: Backend Service (FastAPI)
* **Port**: 8090
* **Container**: `dopemux-plane-coordinator`
* **Build Context**: `services/task-orchestrator` (shared with Task Orchestrator)

**Core Modules**:
1. **`TaskCoordinator`**: The central brain that batches tasks based on "Cognitive Load" scores vs. current user capacity.
2. **`CognitiveLoadBalancer`**: Algorithms for estimating energy cost of tasks.
3. **`ContextSwitchRecovery`**: Monitors context switching penalties and enforces breaks.
4. **`ConPortEventAdapter`**: Syncs coordination state back to the Knowledge Graph (ConPort).

### Failure Analysis: CRITICAL BUILD ERROR
**Status**: The service is currently **CRASHING** (`Restarting (1)`).

**Root Cause**:
The `Dockerfile.coordination` fails to copy the `task_orchestrator` package, which contains shared models used by the coordinator code.

* **Error Log**: `ModuleNotFoundError: No module named 'task_orchestrator'`
* **File Trace**: `services/task-orchestrator/app/services/task_coordinator.py` attempts to import `from task_orchestrator.models import ...`.
* **Docker Config**:
    ```dockerfile
    # Dockerfile.coordination
    COPY services/task-orchestrator/app /app/app
    COPY services/task-orchestrator/intelligence /app/intelligence
    # MISSING: COPY services/task-orchestrator/task_orchestrator /app/task_orchestrator
    ```

### Integration Patterns & Data Flow
1. **Input**: Receives tasks from `Task Orchestrator` (via ConPort sync or direct API).
2. **Modulation**: Queries `ADHD Engine` for current biological state (Energy, Attention).
3. **Logic**:
    * *High Energy* -> Prioritizes complex tasks.
    * *Low Energy* -> Recommend simple tasks or breaks.
    * *Scattered* -> Limits active tasks to 1.
4. **Output**: Dispatches "Sequenced Batches" back to agent actuators or user UI.

### Testing, Performance, Limitations & Opportunities
* **Testing**: Unit tests exist (`test_coordination_integration.py`), but the broken Docker build prevents integration testing.
* **Performance**: Lightweight, mainly I/O bound (Redis/HTTP).
* **Opportunities**:
    * **Fix the Build**: Immediate priority is to add the missing `COPY` instruction to `Dockerfile.coordination`.
    * **Shared Library**: The `task_orchestrator` package should likely be refactored into a shared `dopemux-common` library to avoid these copy-paste dependencies.

## SECTION 2: EVIDENCE TRAIL

### Inventory Evidence (Phase 1)
* **Source Code**: `services/task-orchestrator/app` (Coordinator specific code) and `services/task-orchestrator/task_orchestrator` (Shared models).
* **Runtime**: Container `dopemux-plane-coordinator` exists but is in a crash loop.

### Failure & Drift Findings (Phase 2)
* **[CRITICAL] Dependency Drift**: The code in `app/services/task_coordinator.py` drifted to rely on a shared package structure that the Dockerfile was not updated to reflect.
* **Configuration**: `docker-compose.master.yml` correctly maps the build context, but the internal Dockerfile logic is flawed.

## SECTION 3: LIVING DOCUMENTATION METADATA
- Last Validated: 2026-02-09
- Confidence Level: 100% (Root cause identified via logs and code analysis)
- Evidence Quality Score: High (Reproducible failure)
- Evolution Log:
    - 2026-02-09: Initial Deep Dive. Identified critical build failure preventing service startup.
