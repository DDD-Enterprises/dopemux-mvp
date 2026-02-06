---
id: ADHD_ENGINE_MASTER_HISTORY
title: Adhd Engine Master History
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Adhd Engine Master History (explanation) for dopemux documentation and developer
  workflows.
---
# ADHD Engine: Master History & Feature Catalog

**Service ID**: `adhd_engine`
**Role**: Proactive Cognitive Support System
**Primary Owner**: @hu3mann
**Current Version**: Phase 3 (Proactive Intelligence)

---

## 1. Executive Summary & Evolution

The ADHD Engine is the "heart" of Dopemux, designed to adapt the development environment to the user's fluctuating cognitive state. Unlike traditional tools that assume linear productivity, the Engine actively monitors energy, attention, and cognitive load to provide real-time accommodations.

**Evolutionary Phases:**
*   **Phase 1 (Reactive)**: Simple API endpoints where users manually reported energy levels. Basic break timers.
*   **Phase 2 (Analysis)**: Introduction of the "3-Layer Architecture" (Monitor → Analyze → Intervene). Integration with ConPort for pattern storage.
*   **Phase 3 (Proactive - Current)**: ML-driven prediction. The system now *anticipates* energy crashes and proactively suggests interventions before burnout occurs.

---

## 2. Feature Catalog (Exhaustive)

### Core Monitoring (The "Four Signals")
Real-time energy assessment based on:
1.  **Task Completion Rate**: High velocity = High Energy.
2.  **Context Switching Freq**: >5 switches/hour = Scattered Attention / Low Energy.
3.  **Break Compliance**: Skipping breaks = Impending Crash.
4.  **Time Sine Last Break**: >60 mins = Depletion Risk.

### Cognitive Accommodations
*   **Hyperfocus Guard**:
    *   **25min**: Gentle reminder.
    *   **60min**: Warning.
    *   **90min**: Mandatory break enforcement (Auto-save & Lock).
*   **Energy-Aware Task Routing**: Matches task complexity (0.0-1.0) to current capacity.
    *   *Example*: "Your energy is Low (0.3). Here is a documentation task (0.2) instead of the refactor (0.8)."
*   **Procrastination Detection**: Detects "spinning" (reading without writing) and offers "Micro-tasks" to break inertia.
*   **Wind Down Ritual**: End-of-day summary of "Quick Wins" to combat negative self-talk.

### API Capabilities (15+ Endpoints)
*   `POST /assess-task`: Returns complexity score and recommended chunking.
*   `GET /energy-level`: Returns status + ML confidence score.
*   `GET /attention-state`: Focused / Scattered / Hyperfocus.
*   `POST /recommend-break`: Zen-AI integrated suggestions (e.g., "Stretch" vs "Meditate").
*   `POST /voice/command`: "How is my focus?" (Voice assistant).
*   `POST /notifications/test`: Multi-channel alerts (Terminal, System, Mobile).

### Gamification & Psychology
*   **Momentum Badges**: Awarded for completing micro-tasks.
*   **Positive Reinforcement**: "Celebrate Completion" patterns to counter internal criticism.
*   **Social Battery Monitor**: Tracks drain from meetings vs coding time.

---

## 3. Architecture Deep Dive

### Three-Layer Architecture
1.  **Layer 1: Real-Time Monitoring**: Redis-backed state tracking (<5ms latency).
2.  **Layer 2: Analysis & Decision**: Cognitive Load Calculation logic.
3.  **Layer 3: Intervention**: UI adaptations, Toast notifications, Task re-routing.

### Storage Strategy
*   **Redis**: Real-time state (Energy, Attention, Session Timers). TTLs: 5m (Energy), 1m (Breaks).
*   **ConPort** (SQLite/PG): Long-term pattern storage. Used for profile learning.

### The "Background Monitors"
Six async tasks run continuously:
*   `_energy_level_monitor` (5 min)
*   `_attention_state_monitor` (2 min)
*   `_break_timing_monitor` (1 min)
*   `_hyperfocus_protection_monitor` (1 min)
*   `_cognitive_load_monitor` (1 min)
*   `_context_switch_analyzer` (5 min)

---

## 4. Validated Status (Audit Results)

**✅ Working / Production Ready:**
*   **Task Assessment API**: Fully implemented with ML integration.
*   **Energy/Attention APIs**: Redis caching and ConPort persistence working.
*   **User Profiles**: Advanced customization active.
*   **Break Logic**: Zen-AI integration verified.

**⚠️ Gaps / Incomplete:**
*   **Dashboard UI (Status: MISSING)**: The `adhd-dashboard` service (port 8097) is referenced but code is missing. There is no visual frontend for the data.
*   **Background Services**: The framework exists (`monitoring_tasks.py`), but the actual service implementation in `services/adhd_engine` directory was flagged as "Partially Implemented" in audits.
*   **Cognitive Load**: Implementation is "simplified" compared to the complex multi-factor model described in docs.

---

## 5. Known Integration Points

*   **ConPort**: Reads "Task Completion" validation; Writes "Break History".
*   **Serena**: Receives "Navigation Patterns" to detect context switching.
*   **DopeconBridge**: Publishes `session.started`, `break.recommended` events.
*   **Zen AI**: Calls for intelligent break activity suggestions.

---

*Sources: `adhd-engine-deep-dive.md`, `adhd-engine-api.md`, `phase3-adhd-engine-feature-analysis.md`, `services/adhd_engine/README.md`.*
