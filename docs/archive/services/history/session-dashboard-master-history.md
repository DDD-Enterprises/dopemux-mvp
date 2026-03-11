---
id: SESSION_DASHBOARD_MASTER_HISTORY
title: Session Dashboard Master History
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Session Dashboard Master History (explanation) for dopemux documentation
  and developer workflows.
---
# Session Manager & Dashboard: Master History & Feature Catalog

**Service ID**: `session-dashboard` (TUI Layer)
**Role**: ADHD-Optimized Metrics Display & Layout Manager
**Primary Owner**: @hu3mann
**Latest Version**: 2.1 (Compact Dashboard Complete)
**Port**: 8097 (Dashboard Metrics API)

---

## 1. Executive Summary & Evolution

The "Dopemux Dashboard" is not just a UI; it is an ADHD-assistive interface designed to combat time blindness and working memory deficits. It uses a "Progressive Disclosure" philosophy to show critical info (Energy, Attention, Next Task) without overwhelming the user.

**Evolutionary Phases:**
*   **Phase 1 (Scripts)**: loose collection of scripts (`check_energy.sh`).
*   **Phase 2 (Rich/Textual)**: Development of a proper TUI using Python's `rich` and `textual` libraries.
*   **Phase 3 (Compact Mode)**: Creation of the "Compact Dashboard" (3-line summary) specifically for tmux top panes, which is now considered **Production Ready**.

---

## 2. Feature Catalog (Exhaustive)

### Core Components
*   **Three-Tier Display System**:
    1.  **Tier 1 (Status Bar)**: Always visible, 0% CPU. Shows Energy (⚡), Attention (🧠), and Break Timer.
    2.  **Tier 2 (TUI Pane)**: Toggleable Rich/Textual dashboard. Shows deep metrics, sparklines, and task lists.
    3.  **Tier 3 (Popups)**: On-demand keyboard-driven details (e.g., `M-d` for detailed task view).

### Capabilities
*   **ADHD State Visualization**: Color-coded indicators (Green/Yellow/Red) for Energy and Attention.
*   **Untracked Work Detection**: visually alerts on uncommitted files or stale branches.
*   **Real-Time Metrics**: Polling (1s/30s/60s) from ADHD Engine, ConPort, and Prometheus.
*   **Session Management**: Tracks "Flow State" duration and session counts.

### Key Scripts
*   `dopemux_dashboard.py`: The main TUI application.
*   `dopemux-compact-dashboard.py`: The light-weight 3-line version for tmux.
*   `orchestrator_dashboard.py`: Specialized view for the Task Orchestrator.

---

## 3. Architecture Deep Dive

### Data Flow
```
[ADHD Engine] -> [Redis] -> [Dashboard API (8097)] -> [TUI / Tmux Status]
```
*   **Why an API?**: Decouples the UI from the heavy engines. The Dashboard API caches metrics to ensure the TUI is instantly responsive (<100ms) even if the backend is crunching numbers.

### Integration
*   **Tmux**: Integrated via `status-left` and `status-right` or dedicated panes.
*   **Monitoring**: Exports its own health metrics to Prometheus.

---

## 4. Validated Status (Audit Results)

**✅ Compact Dashboard - COMPLETE:**
*   A 3-line ultra-compact summary is deployed and working.
*   Integrates: Cognitive State, Untracked Work, Active Tasks.

**🏗️ Full Dashboard - Implementation Phase:**
*   **Status**: "Phase 1: Basic Setup" complete.
*   **Pending**: Full deployment of the interactive Textual app as the default right-pane.
*   **Performance**: Verified <5% CPU usage.

---

*Sources: `metric-dashboards.md`, `tmux-dashboard-design.md`, `COMPACT-DASHBOARD-COMPLETE.md`, `TMUX_DASHBOARD_README.md`.*
