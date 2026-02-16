---
id: TASK_ORCHESTRATOR_MASTER_HISTORY
title: Task Orchestrator Master History
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Task Orchestrator Master History (explanation) for dopemux documentation
  and developer workflows.
---
# Task Orchestrator: Master History & Feature Catalog

**Service ID**: `task_orchestrator`
**Role**: Tactical Execution Controller / PM Plane Hub
**Primary Owner**: @hu3mann
**Latest Version**: V2 (Un-deprecated & Restored)

---

## 1. Executive Summary & Evolution

The Task Orchestrator is the tactical "Traffic Controller" of the Dopemux ecosystem. It sits between the **Strategic Layer** (Leantime) and the **Execution Layer** (AI Agents, Morph, Playwright), ensuring that high-level goals are broken down into manageable, ADHD-safe units of work.

**Evolutionary Phases:**
*   **Phase 1 (SuperClaude Era)**: Originally designed as `SuperClaude` - a wrapper to give the Claude CLI "superpowers" (session management, tools).
*   **Phase 2 (The Deprecation Crisis)**: Renamed to `Task-Orchestrator`. Nearly deleted in "Decision #140" under the false assumption it was empty architecture stubs. A critical audit revealed 5,577 lines of functional code (ML risk, workflow automation) were about to be lost.
*   **Phase 3 (PM Plane - Current)**: Fully restored ("Un-deprecated"). Now acts as the central hub for the "PM Plane", coordinating multi-model consensus (Claude, Gemini, Grok) and managing developer attention.

---

## 2. Feature Catalog (Exhaustive)

### Core Orchestration
*   **Task Decomposition**: Breaks natural language tasks into 3-5 subtasks (Max 3 concurrent).
*   **Multi-Model Consensus**: Uses "Zen Consensus" to resolve architectural disputes between models (e.g., Claude vs Gemini on JWT vs Sessions).
*   **Tactical Routing**: Assigns tasks based on model strength:
  * *Research* → Gemini 2.5 Pro (1M Context)
  * *Architecture* → Claude Sonnet (Reasoning)
  * *Code Gen* → Grok Code Fast (Speed/Cost)

### The "PM Plane" Capabilities
*   **Strategic Sync**: Synchronizes with Leantime tickets.
*   **Risk Assessment**: Contains a specialized ML engine (`PredictiveRiskAssessmentEngine`) that predicts:
  * `COGNITIVE_OVERLOAD`
  * `HYPERFOCUS_BURNOUT`
  * `TIMELINE_SLIPPAGE`
*   **Deployment Orchestration**: Automated workflows for deployment.

### ADHD Optimizations
*   **Subtask Limiter**: Hard limit of 3 concurrent subtasks to prevent overwhelm.
*   **Auto-Checkpoint**: Saves state every 30 seconds to ConPort.
*   **Energy-Aware Suggestions**: Recommends tasks based on current energy (read from ADHD Engine).
  * *Example*: "Energy is Low. Do 'Write Integration Tests' (Complexity 0.3)."

### TUI Dashboard (Mission Control)
*   Visualizes "Sprint Overview" and "System Health" in a dedicated tmux pane.
*   Displays real-time "Phase Progress" (Research → Plan → Implement).

---

## 3. Architecture Deep Dive

### The "Two-Plane" Architecture
Task Orchestrator defines the boundary between:
1.  **Human Plane**: Leantime (Strategy), Dashboard (Monitoring).
2.  **Intelligence Plane**: ConPort (Memory), Agents (Execution), DopeconBridge (Events).

### Integration Logic
*   **Input**: Natural Language or Leantime Ticket.
*   **Processing**:
    1.  `Plan`: Decompose (with Claude).
    2.  `Validate`: Check constraints (with Gemini).
    3.  `Execute`: Dispatch to Morph/Agents.
*   **Output**: Unified Status Update -> ConPort -> Leantime.

---

## 4. Validated Status (Audit Results)

**✅ Working / Production Ready:**
*   **Subtask Decomposition**: Verified.
*   **ConPort Connectivity**: Verified (syncs decisions/artifacts).
*   **Risk Assessment Engine**: Code exists and is functional (562 lines).
*   **Un-Deprecation Status**: Fully restored after ADR-203.

**⚠️ Gaps / Known Issues:**
*   **"SuperClaude" Legacy**: Some internal variable names or older docs still reference `superclaude` or `/sc:` commands.
*   **Dashboard Integration**: While the TUI exists, the HTTP-based dashboard (port 8097) connection is sometimes flaky.

---

## 5. Integration Points

*   **Leantime**: Inbound (strategic goals).
*   **ConPort**: Bidirectional (reads context, writes decisions).
*   **Zen MCP**: Outbound (requests for consensus/reasoning).
*   **Morph**: Outbound (requests for file edits).

---

*Sources: `DOPEMUX-MULTI-AI-ORCHESTRATOR-DESIGN.md`, `ADR-203-task-orchestrator-un-deprecation.md`, `CRITICAL-task-orchestrator-deprecation-review.md`, `task-orchestrator-dopemux.md` Blueprint.*
