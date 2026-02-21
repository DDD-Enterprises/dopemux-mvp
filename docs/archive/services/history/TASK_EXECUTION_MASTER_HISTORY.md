---
id: TASK_EXECUTION_MASTER_HISTORY
title: Task Execution Master History
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Task Execution Master History (explanation) for dopemux documentation and
  developer workflows.
---
# Task Execution Services: Master History & Feature Catalog

**Services**: `agents`, `task-router`, `taskmaster`, `task-master-ai`
**Role**: Execution Layer & Routing
**Status**:
* MemoryAgent: Operational
* Task Router: Beta
* Infrastructure Agents: 1/7 Implemented

---

## 1. Executive Summary

The **Task Execution Layer** acts as the "Hands" of the system, whereas ConPort is the memory and ADHD Engine is the conscience. It consists of specialized agents that execute workflows while enforcing ADHD constraints (breaks, energy matching).

**Core Philosophy**: Agents aren't just for code; they are **Infrastructure Support** for the human's executive function.

---

## 2. Feature Catalog

### 🕵️ 7 Infrastructure Agents (`services/agents`)
A suite of 7 planned agents to support the "2-Plane Architecture":
1. **MemoryAgent** (✅ Implemented): Auto-saves context every 30s. Prevents "Where was I?" syndrome.
1. **CognitiveGuardian**: Enforces breaks and monitors attention drift.
1. **TwoPlaneOrchestrator**: Manages traffic between Leantime (PM) and ConPort (AI).
1. **TaskDecomposer**: Breaks PRDs into atomic, ADHD-sized tasks.
1. **DopemuxEnforcer**: Validates architecture rules (e.g., "No direct DB access").
1. **ToolOrchestrator**: Selects the right MCP tool for the job.
1. **WorkflowCoordinator**: Manages long-running multi-step processes.

### 🔀 Task Router (`services/task-router`)
* **Energy Matching**: Matches tasks to user's current energy (e.g., "High Energy" -> "Deep Work", "Low Energy" -> "Docs").
* **Complexity Routing**: Routes complex tasks to `o3-mini` and simple ones to `gpt-4o`.

### 🧩 Task Master AI (`docker/mcp-servers/task-master-ai`)
* **PRD Parser**: Converts structured requirements into task lists.
* **Decomposition Engine**: Recursively breaks tasks down until they are < 4 hours estimate.

---

## 3. Architecture Deep Dive

### The Agent Hierarchy
```
[User] -> [Task Router]
             |
             v
[Cognitive Guardian] --(checks energy)--> [Allowed?]
             |
             v
      [Memory Agent] --(saves context)--> [ConPort]
             |
             v
      [Specialized Execution Agent]
```

### Integration Points
* **MemoryAgent** wraps ConPort to ensure zero data loss during crashes or interruptions.
* **Task Master AI** sits as an MCP server, accessible by any agent to decompose big problems.

---

## 4. Validated Status (Audit Results)

**✅ Operational:**
* **MemoryAgent**: Tested connection to ConPort; auto-save interval validated.
* **Task Router**: API endpoints `/suggest-tasks` functional.

**⏳ Planned/Pending:**
* **Agents 2-7**: Detailed designs exist (Week 3-10 timeline) but code is pending.
* **Task Master Wrappers**: `server.py` exists to wrap the Node.js MCP server for Python consumers.

---

*Sources: `services/agents/README.md`, `router_api.py`, `task-master-ai/README.md`.*
