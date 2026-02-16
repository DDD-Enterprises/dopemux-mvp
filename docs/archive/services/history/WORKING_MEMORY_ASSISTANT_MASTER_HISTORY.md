---
id: WORKING_MEMORY_ASSISTANT_MASTER_HISTORY
title: Working Memory Assistant Master History
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Working Memory Assistant Master History (explanation) for dopemux documentation
  and developer workflows.
---
# Working Memory Assistant: Master History & Feature Catalog

**Service ID**: `working-memory-assistant` (WMA)
**Role**: Short-Term Memory Extension / Interrupt Recovery System
**Primary Owner**: @hu3mann
**Latest Version**: 2.0.0 (Implementation Phase)
**Port**: 8096

---

## 1. Executive Summary & Evolution

The Working Memory Assistant (WMA) is designed to address the #1 ADHD productivity killer: **Working Memory Limitations**. ADHD developers often lose context completely after interruptions (phone calls, slack, context switches), taking 10-15 minutes to recover.

WMA solves this by automatically "snapshotting" the developer's mental and digital state every few minutes or upon interruption. It enables **<2 second recovery** (20-30x faster than baseline) via a "Progressive Disclosure" UI that reminds the user *what* they were doing, *why*, and *where* they left off.

**Evolutionary Phases:**
*   **Phase 1 (Concept)**: Identified as "F-NEW-10" to solve the "Where was I?" problem.
*   **Phase 2 (Design)**: Defined the "Snapshot Engine" and "Recovery Engine" architecture.
*   **Phase 3 (Implementation)**: Current phase. Core FastAPI service built with Redis/PostgreSQL backend.

---

## 2. Feature Catalog (Exhaustive)

### Core Capabilities
*   **Auto-Snapshotting**: Captures context triggers (File Save, ADHD Event, Time-based) in <200ms.
*   **Instant Recovery**: Restores context in <2s with "Progressive Disclosure" (Essential -> Detailed -> Complete).
*   **Smart Resume**: Suggests the exact line of code and "Next Action" based on previous intent.
*   **Mental Model Inference**: Infers goals (e.g., "Refactoring Auth") from file patterns and search history.

### Context Layers
1.  **Development Context**: Open files, cursor positions, git branch, tmux pane state.
2.  **Cognitive Context**: Inferred goals, recent decisions, "Thought Process" notes.
3.  **ADHD Context**: Energy level, attention span remaining, break recommendations (via ADHD Engine).

### Interfaces
*   **SnapshotEngine**: Capture logic (`captureSnapshot`).
*   **RecoveryEngine**: Restoration logic (`initiateRecovery`).
*   **MemoryManager**: Storage optimization (compression, LRU eviction).

---

## 3. Architecture Deep Dive

### The "Stack" Model
WMA functions like a computer's stack but for human thought:
*   **Push**: Auto-saves state to Redis (Hot Cache) when working.
*   **Pop**: Retrieves state from Redis when returning.
*   **Archive**: Moves older states to PostgreSQL for long-term pattern analysis.

### Integration Points
*   **Desktop Commander**: Detects "App Switch" or "Screen Lock" as interruption triggers.
*   **Serena**: Provides LSP-level context (function signatures, complexity).
*   **ConPort**: Links snapshots to long-term "Decisions" and "Knowledge Graph" nodes.
*   **ADHD Engine**: Modifies recovery strategy based on current energy levels (e.g., "Gentle" recovery for low energy).

---

## 4. Validated Status (Audit Results)

**🏗️ Implementation Phase / Early Alpha:**
*   **Service**: FastAPI service initialized (`services/working-memory-assistant`).
*   **Endpoints**: `/snapshot`, `/recover`, `/preferences` defined.
*   **Storage**: Redis + PostgreSQL schema designed.
*   **Status**: **NOT yet widely deployed** to all workflows like ConPort/Serena. It is functional but in active development.

**Performance Targets (Design Goals):**
*   Snapshot Capture: <200ms
*   Recovery Time: <2s
*   Memory Footprint: <50MB

---

*Sources: `f-new-10-working-memory-assistant.md`, `working-memory-assistant.md`, `README.md`.*
