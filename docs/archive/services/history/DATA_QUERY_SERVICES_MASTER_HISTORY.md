---
id: DATA_QUERY_SERVICES_MASTER_HISTORY
title: Data Query Services Master History
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Data Query Services Master History (explanation) for dopemux documentation
  and developer workflows.
---
# Data & Query Services: Master History & Feature Catalog

**Services**: `dddpg`, `dope-query`, `conport_kg_ui`
**Role**: The Memory & Recall Layer
**Status**:
*   DDD-PG: Week 4 Implementation (Solid Foundation)
*   Dope-Query: Production (Multi-workspace)
*   KG-UI: Production (TUI)

---

## 1. Executive Summary

The **Data & Query Services** operate on the "Intelligence Plane" to manage the long-term memory of the system. While ConPort is the database, these services are the *lens* through which that data is viewed and manipulated.

**Key Innovation**: **DDD-PG** (Decision-Driven Development Portal Graph) introduces "Multi-Instance" support, allowing a single developer to run multiple isolated workspaces (e.g., `dopemux-mvp` and `dopemux-legacy`) without decision collision, while still allowing cross-workspace queries.

---

## 2. Feature Catalog

### 🏛️ DDD-PG (`services/dddpg`)
*   **Hybrid Storage**: Uses SQLite for fast, offline-capable local reads and PostgreSQL AGE for powerful graph queries.
*   **Multi-Instance**: Supports Git worktrees by tagging every decision with `workspace_id` and `instance_id`.
*   **ADHD Optimization**: Enforces "Top-3 Pattern" in API design—never show more than 3 items by default to prevent overwhelm.

### 🔍 Dope-Query (`services/dope-query`)
*   **Cross-Workspace Search**: "Show me all auth decisions across *all* my projects."
*   **Genealogy**: Traces decision lineage (e.g., "This Refactor supersedes That Migration").
*   **Unified Context**: Merges context from code (AST) and decisions (KG).

### 🖥️ ConPort KG UI (`services/conport_kg_ui`)
*   **TUI**: A Terminal User Interface for graph exploration (built with `ink` & React).
*   **Progressive Disclosure**:
  * **Tier 1**: Top-3 recent decisions.
  * **Tier 2**: 1-hop neighbors (what did this decision impact?).
  * **Tier 3**: Full context and metadata.
*   **Visuals**: Color-coded cognitive load indicators.

---

## 3. Architecture Deep Dive

### The Recall Loop
```
[User Queries TUI] -> [KG-UI]
                         |
                         v
                  [Dope-Query Service]
                         |
      +------------------+------------------+
      |                                     |
[Local SQLite Cache]                [Global Postgres Graph]
(Fast, Offline)                     (Complex Relations)
```

### Integration Points
*   **DDD-PG** captures data from *all* other agents (Serena, Task Orchestrator).
*   **KG-UI** is the primary way for humans to "browse" their external brain.

---

## 4. Validated Status (Audit Results)

**✅ Operational:**
*   **DDD-PG**: Core models and SQLite backend are production-ready. 100% test coverage on KG integration.
*   **Dope-Query**: Multi-workspace guide confirms functionality.
*   **KG-UI**: `npm run demo` confirmed working.

**🚧 In Progress:**
*   **Semantic Search**: Embedding-based retrieval is planned for "Week 5".
*   **EventBus Integration**: Publishing change events is specified but pending implementation.

---

*Sources: `dddpg/DEEP_ANALYSIS_CURRENT_STATE.md`, `dope-query/MULTI_WORKSPACE_GUIDE.md`, `conport_kg_ui/README.md`.*
