---
id: DOPE-MEMORY-DEEP-DIVE
title: Dope Memory Deep Dive
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-09'
last_review: '2026-02-09'
next_review: '2026-05-10'
prelude: Dope Memory Deep Dive (explanation) for dopemux documentation and developer
  workflows.
---
# Deep Component Research: Dope-Memory

## 1. Executive Summary & Strategic Intent

**Component**: `dope-memory`
**Type**: MCP Service
**Status**: **Implementation Active** (Housed in `services/working-memory-assistant`)
**Health**: **Critical Issues Detected** (Runtime Missing, Environment Mismatch)

**Strategic Intent**:
Dope-Memory is the "Temporal Spine" of Dopemux, answering "What happened, when, and why?". It replaces ad-hoc memory solutions with a deterministic, local-first chronicle of events, decisions, and work logs. It sits alongside **DopeQuery** (Structural Truth) and **DopeContext** (Semantic History).

**Current State**:
-   **Implementation**: Fully implemented in `services/working-memory-assistant/`.
-   **Entry Point**: `dope_memory_main.py` (Port 3020).
-   **Storage**: SQLite Canonical Ledger (`chronicle/store.py`).
-   **Confusion Point**: The directory name `working-memory-assistant` is a legacy artifact; the running service is `dope-memory`.

---

## 2. Architecture & Core Components (Validated)

### 2.1 Core Responsibilities
1.  **Chronicle Store**: Immutable ledger managed by `ChronicleStore` class.
    -   `raw_activity_events`: Short retention (7 days), strictly redacted.
    -   `work_log_entries`: Durable, curated, high-signal entries.
2.  **MCP Server**: `DopeMemoryMCPServer` (FastAPI) exposing standard tools.
3.  **Promotion Engine**: Logic to promote raw events to work logs (seen in `promotion/`).
4.  **Trajectory Manager**: Boosts relevance based on recent activity (`trajectory/`).

### 2.2 Data Stores
-   **SQLite (Canonical)**: `chronicle/schema.sql` defines `work_log_entries`, `raw_activity_events`, `issue_links`, `reflection_cards`.
-   **Redis (EventBus)**: `eventbus_consumer.py` manages ingestion.
-   **Postgres (Mirror)**: `postgres_mirror_sync.py` handles replication.

### 2.3 Key Contracts (MCP)
-   `memory_store`: Implemented in `dope_memory_main.py`.
-   `memory_search`: Implemented with boost re-ranking.
-   `memory_recap`: Implemented with "Top-3" logic.
-   `memory_mark_issue`: Implemented.

---

## 3. Gap Analysis (Spec vs. Reality)

| Feature | Spec Status | Implementation Status | Notes |
| :--- | :--- | :--- | :--- |
| **Service Scaffold** | Defined | **Found** | `services/working-memory-assistant/` |
| **Chronicle Store** | SQLite Schema Defined | **Found** | `chronicle/store.py` matches spec. |
| **Event Ingestion** | Redis Stream Consumer | **Found** | `eventbus_consumer.py`. |
| **Promotion Logic** | Rules Defined | **Found** | `promotion/` directory. |
| **MCP Tools** | Contracts Defined | **Found** | `dope_memory_main.py` implements all. |

---

## 4. Critical Findings (Action Required)

### 4.1 Runtime Absence
The service is **NOT** present in `docker-compose.master.yml`. It is defined in `services/registry.yaml` (Port 3020) but never orchestrated.
-   **Impact**: The system has no memory continuity currently.
-   **Fix**: Add `dope-memory` service definition to `docker-compose.master.yml` pointing to `services/working-memory-assistant` Dockerfile.

### 4.2 Environment Mismatch (Python 3.10 vs 3.9)
The source code uses Python 3.10+ syntax (e.g., `str | Path` union types), but the environment/tests are running on Python 3.9.6.
-   **Evidence**: `TypeError: unsupported operand type(s) for |: 'type' and 'type'` during tests.
-   **Fix**: Update Dockerfile/Runtime to Python 3.10+ or downgrade syntax to `Union[str, Path]`.

## 5. Next Steps
1.  **Rename Directory**: Move `services/working-memory-assistant` back to `services/dope-memory` to match registry and intent.
2.  **Fix Python Version**: ensure Dockerfile uses python:3.11-slim.
3.  **Orchestrate**: Add to `docker-compose.master.yml`.
4.  **Verify**: Run `test_dope_memory.py` in the corrected environment.

---

## 4. Precursor Analysis: Working Memory Assistant

*Investigation in progress: checking `services/working-memory-assistant` for reusable patterns or migration data.*

---

## 5. Next Steps
1.  **Scaffold Service**: Create `services/dope-memory` based on `docker/mcp-servers/` templates.
2.  **Schema Migration**: Implement SQLite schema from `02_data_model_sqlite.md`.
3.  **MCP Implementation**: Implement the tools defined in `07_mcp_contracts.md`.
