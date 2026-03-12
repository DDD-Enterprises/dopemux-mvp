---
id: DESIGN_EVOLUTION_2026
title: Design Evolution 2026
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Design Evolution 2026 (explanation) for dopemux documentation and developer
  workflows.
---
# Dopemux-MVP: Master Design & Evolution Document

**Generated:** 2026-02-05
**Scope:** Comprehensive history of features, architecture, and design evolution across the entire service ecosystem.

---

## Verification Status (Code-Truth, 2026-02-06)

- Implemented: DopeconBridge event-bus runtime, Task-Orchestrator core runtime, agent module files, and UI fallback paths are present.
- Partially Implemented: Several components in this history are implemented but not fully production-hardened (agent readiness, workflow automation depth, naming migration from Zen -> PAL).
- Planned: Future trajectory items are roadmap targets, not current production guarantees.
- Unverified Claims: Performance/SLO assertions without repeatable benchmark tests are treated as targets, not certified guarantees.

---

## 🚀 Executive Summary

Dopemux-MVP has evolved from a simple tmux-based workspace manager into a sophisticated **Cognitive Augmentation Platform** for ADHD developers. The evolution follows a clear trajectory from scripts to a distributed, event-driven microservices architecture dubbed the **"Two-Plane Architecture"**.

**Key Evolutionary Themes:**
1. **From Reactive to Proactive**: Initially reacting to user commands (tmux scripts), now anticipating needs (ML Risk Assessment, Background Prediction Service).
1. **Two-Plane Architecture**: Explicit separation between the **Human Plane** (Leantime, CLI) and the **Intelligence Plane** (ConPort KG, AI Agents, Taskmaster).
1. **Event-Driven Coordination**: Moving from direct API calls to an asynchronous **Redis Streams Event Bus** (DopeconBridge).
1. **Cognitive Load Management**: "ADHD-First" isn't just a label—it's implemented via **Progressive Disclosure**, strictly typed **API Contracts** for context snapshots, and **Visual Indicators** (sparklines, color coding).

---

## 📚 Service Master Index

Clickable index of deep-dive history for every service component.

| Service Group | Components | Description |
|:--------------|:-----------|:------------|
| [1. ConPort](../../archive/services/history/CONPORT_MASTER_HISTORY.md) | `conport`, `postgresql` | Context Portal & Knowledge Graph. |
| [2. ADHD Engine](../../archive/services/history/ADHD_ENGINE_MASTER_HISTORY.md) | `adhd_engine` | Proactive state tracking & risk assessment. |
| [3. Task Orchestrator](../../archive/services/history/TASK_ORCHESTRATOR_MASTER_HISTORY.md) | `task-orchestrator` | PM Plane connector (Leantime <-> AI). |
| [4. Serena](../../archive/services/history/SERENA_MASTER_HISTORY.md) | `serena` | Cognitive Assistant & LSP Server. |
| [5. DopeconBridge](../../archive/services/history/DOPECON_BRIDGE_MASTER_HISTORY.md) | `dopecon-bridge` | Central Event Bus (Redis Streams). |
| [6. Working Memory](../../archive/services/history/WORKING_MEMORY_ASSISTANT_MASTER_HISTORY.md) | `wma` | Snapshotting & Context Recovery. |
| [7. Session Manager](../../archive/services/history/SESSION_DASHBOARD_MASTER_HISTORY.md) | `session-manager` | Multi-AI Layout & TUI. |
| [8. Dope Context](../../archive/services/history/DOPE_CONTEXT_MASTER_HISTORY.md) | `dope-context` | Semantic search & indexing. |
| [9. Genetic Agent](../../archive/services/history/GENETIC_ML_SERVICES_MASTER_HISTORY.md) | `genetic`, `ml-risk` | Code repair eugenics & risk modeling. |
| [10. Monitoring](../../archive/services/history/MONITORING_MASTER_HISTORY.md) | `monitoring`, `grafana` | Prometheus/Grafana stack. |
| [11. Intelligence](../../archive/services/history/INTELLIGENCE_SUPPORT_MASTER_HISTORY.md) | `brain`, `prediction` | Meta-prompting & load prediction. |
| [12. Task Execution](../../archive/services/history/TASK_EXECUTION_MASTER_HISTORY.md) | `agents`, `router` | Infrastructure agents & routing. |
| [13. Environment](../../archive/services/history/ENVIRONMENT_SERVICES_MASTER_HISTORY.md) | `watcher`, `desktop` | Workspace sensory layer. |
| [14. Integrations](../../archive/services/history/INTEGRATION_SERVICES_MASTER_HISTORY.md) | `slack`, `litellm` | External world connectors. |
| [15. Data & Query](../../archive/services/history/DATA_QUERY_SERVICES_MASTER_HISTORY.md) | `dddpg`, `kg-ui` | Multi-workspace recall & TUI. |
| [16. Notifications](../../archive/services/history/NOTIFICATIONS_UI_MASTER_HISTORY.md) | `notifier`, `dashboard` | User Interface & interruptions. |

### 🕵️‍♀️ Archaeology & Vaporware

| Report | Description |
|:-------|:------------|
| [Unbuilt Features](UNBUILT_FEATURES_AND_ROADMAP.md) | The "Lost Futures" (Agents, Workflow, Auto-Resume). |
| [Project Archaeology](PROJECT_ARCHAEOLOGY_REPORT.md) | The "Deleted Civilizations" (Zen Server, Personas). |

## 🏗️ Architecture Evolution

### Phase 1: The Script Era (v0.1)
- **Design**: Collection of Shell and Python scripts.
- **State**: Ephemeral (tmux session state).
- **Communication**: Direct process execution.
- **Key Components**: `tmux/controller.py`, simple `dopemux` CLI.

### Phase 2: The Service Mesh (v0.2)
- **Design**: Specialized services running in Docker.
- **State**: Redis for event bus, SQLite for local storage.
- **Communication**: HTTP APIs + Redis Pub/Sub.
- **Key Components**: ADHD Engine (Reactive), ConPort (v1).

### Phase 3: The Intelligent Ecosystem (v0.3 - Current)
- **Design**: **Two-Plane Architecture** with MCP Agents.
- **State**: Enterprise-grade (PostgreSQL, Qdrant, Redis Streams).
- **Communication**: **DopeconBridge** (Async Event Bus) + MCP (stdio).
- **Key Components**:
- **PM Plane**: Leantime (Human) ↔ Task Orchestrator ↔ ConPort (AI).
- **Proactive Engine**: ML-driven background predictions.
- **Session Manager**: Multi-AI orchestration via tmux.

---

## 🧩 Service Evolution & History

### 1. ConPort (Context Portal)
*The evolution of memory and context management.*

| Feature | V1 (Legacy) | V2 (Current) |
|---------|-------------|--------------|
| **Backend** | SQLite | **PostgreSQL + Qdrant** |
| **Search** | Keyword (SQL LIKE) | **Semantic (Vector) + Hybrid FTS5** |
| **Workspaces** | Single Root | **Multi-Workspace / Worktree Support** |
| **Performance** | Synchronous | **Async Pipeline + Redis Caching** |

**Key Milestone: V2 Architecture Redesign**
- Moved to **AsyncDatabase** pattern.
- Implemented **Intelligent TTL Strategy** for caching.
- Introduced **Embedding Pipeline** processing 50 texts/sec with batching.
- **Multi-Workspace**: Added `DOPE_CONTEXT_WORKSPACES` support for unified querying across projects.
- **Evolution Source**: `docs/systems/conport/v2-architecture.md`, `dope-query/MULTI_WORKSPACE_GUIDE.md`.

### 2. The ADHD Dashboard
*From status bar to command center.*

**Evolutionary Path:**
1. **Tmux Status Line**: Simple bash scripts showing CPU/Mem.
1. **Compact Dashboard**: 3-line Python script (Rich library) showing Energy, Warnings, Tasks.
1. **Full Interactive Dashboard**: Textual-based TUI with sparklines, modal drill-downs, and keyboard navigation.

**Design Philosophy (ADHD-Optimized):**
- **Miller's Law**: Status bar limited to 7±2 items.
- **Color Psychology**: Catppuccin Mocha palette (Green=Safe, Red=Action, no jarring blinks).
- **Progressive Disclosure**: Tier 1 (Status) → Tier 2 (Pane) → Tier 3 (Popups).
- **Evolution Source**: `TMUX_DASHBOARD_DESIGN.md`.

### 3. ADHD Engine
*From monitoring to prediction.*

**Phase 2 (Reactive)**:
- Monitored energy levels via simple API inputs.
- Basic break reminders.

**Phase 3 (Proactive)**:
- **Background Prediction Service**: Scans users every 5 mins to predict energy dips.
- **ML Integration**: `ml_prediction` field in API responses giving confidence scores.
- **Redis Caching**: Endpoint-specific TTLs (documented `<100ms` latency target; benchmark evidence pending).
- **Evolution Source**: `adhd_engine/docs/PHASE_3_IMPLEMENTATION.md`.

### 4. Task Orchestrator (The PM Plane)
*The coordination hub.*

**History**:
- **Oct 2025**: Deprecated (Decision #140) in favor of "SuperClaude".
- **Oct 16, 2025**: **Un-Deprecated** (ADR-203). Systematic audit proved uniqueness.
- **Capabilities**: ML Risk Assessment (blocker prediction), Multi-team coordination.
- **Current Role**: Central node in the **PM Plane**.
- Connects **Leantime** (Human Project Management) with **ConPort** (Knowledge Graph).
- Routes tasks to specialized agents (Serena, PAL/Zen-legacy lineage, Taskmaster family).
- **Evolution Source**: `task-orchestrator/docs/pm-plane-architecture.md`, `ADR-203`.

### 5. DopeconBridge
*The nervous system.*

**Design**:
- **Redis Streams** based Event Bus.
- **Events**: `tasks_imported`, `session_started`, `progress_updated`, `decision_logged`.
- **Latency**: <10ms publishing, <50ms end-to-end.
- **Goal**: Decouple services so failure in one doesn't cascade (ADHD Resilience).
- **Evolution Source**: `dopecon-bridge/README.md`.

### 6. Working Memory Assistant (WMA)
*The save state for your brain.*

**Core Contract**:
- **DevelopmentSnapshot**: Captures open files, cursor positions, tmux state, AND cognitive context (thought process, energy level).
- **Performance**: Target `<200ms` capture time (production benchmark certification pending).
- **Recovery**: "Instant Recovery" with progressive disclosure to help users resume flow after interruptions.
- **Evolution Source**: `working-memory-assistant/docs/api_contracts.md`.

### 7. Session Manager
*Multi-AI Orchestration.*

**Design**:
- Runs multiple AI CLI instances (Claude, Gemini, Grok) in separate tmux panes.
- **Chat-Driven Control**: Natural language interface to orchestrate the AIs.
- **Adaptive Interface**: Adjusts pane layout based on user energy state.
- **Evolution Source**: `session-manager/README.md`.

---

## 🏷️ Naming & Terminology Evolution

| Old Term | New Term | Context |
|----------|----------|---------|
| `context_portal` | **ConPort** | Shortened for CLI/Branding solidity. |
| `SuperClaude` | **Code/Task Orchestrator** | "SuperClaude" was an abstract concept; replaced by concrete services. |
| `TaskMaster` | **Task Orchestrator** | Renamed (mostly) to avoid conflicts; "Taskmaster AI" exists as a sub-component. |
| `Status Line` | **Dashboard (Tier 1)** | Rebranded as the first tier of the dashboard system. |
| `Event Bus` | **DopeconBridge** | The concrete implementation of the system's event bus. |

---

## 🔮 Future Trajectory

Based on the latest implementation plans:
1. **Full "Zen" Mode**: Deep integration of "Flow State" metrics into IDEs.
1. **Autonomous Context**: `autonomous-indexing-daemon` implies self-healing/self-updating context without user intervention.
1. **Bio-Feedback Integration**: Placeholders in ADHD engine suggest future hardware integration for energy monitoring.
1. **Two-Plane Maturity**: Deeper integration between the Human Plane (Leantime) and AI Plane (ConPort) to fully automate project management overhead.

---

*This document compiles insights from across the entire `services/` directory and `System_Archive`.*
