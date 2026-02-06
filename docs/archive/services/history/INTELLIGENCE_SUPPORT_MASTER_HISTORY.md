---
id: INTELLIGENCE_SUPPORT_MASTER_HISTORY
title: Intelligence Support Master History
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Intelligence Support Master History (explanation) for dopemux documentation
  and developer workflows.
---
# Intelligence Support Services: Master History & Feature Catalog

**Services**: `claude-brain`, `ml-predictions`, `session-intelligence`, `complexity-coordinator`
**Role**: Cognitive Plane Support Layer
**Latest Versions**:
*   Claude Brain: 1.0.0 (Phase 1 Complete)
*   Session Intelligence: Production
*   ML Predictions: v3.2 (LSTM Model)

---

## 1. Executive Summary

The **Intelligence Support** services provide the "higher-order" cognitive functions of Dopemux. Unlike the core ADHD Engine which tracks state, these services *process* information to optimize interactions. They handle prompt evolution, complex code analysis, and predictive load modeling.

**Evolutionary Themes:**
*   **From Static to Dynamic**: Moving from hardcoded prompts to "Self-Improving Meta-Prompts" (Claude Brain).
*   **From Reactive to Predictive**: Moving from tracking energy to *predicting* cognitive crash (LSTM Predictor).
*   **Unified Scoring**: Merging disparate complexity metrics into a single "Unified Complexity Score" (Complexity Coordinator).

---

## 2. Feature Catalog

### 🧠 Claude Brain (`services/claude_brain`)
*   **Meta-Prompting**: Recursive prompt optimization loop.
*   **Dynamic Formatting**: Adapts output verbosity based on user's current cognitive load (e.g., "High Load" -> "Bullet points only").
*   **Critique Analyzer**: Multi-dimensional quality assessment of AI responses.
*   **Architecture**: FastAPI service with Redis caching and multi-provider routing (Anthropic/OpenAI).

### 🔮 ML Predictions (`services/ml-predictions`)
*   **LSTM Model**: Long Short-Term Memory network to predict future cognitive load.
*   **Multi-Factor Confidence**: confidence score based on data quality (30%), stability (25%), and calibration (20%).
*   **Actionable Insights**: Returns specific recommendations like "Schedule break in 10m" based on predictions.
*   **Status**: Python module integration (not yet a standalone microservice).

### 🔄 Session Intelligence (`services/session-intelligence`)
*   **Continuity Engine**: "Pick up where you left off" suggestions.
*   **Boundary Detection**: Automatically identifies start/end of "Deep Work" sessions.
*   **Context Preservation**: Serializes detailed context to ConPort for recovery.

### 📐 Complexity Coordinator (`services/complexity_coordinator`)
*   **Hybrid Scoring**: `0.5*AST + 0.3*LSP + 0.2*ADHD_History`.
*   **Goal**: Prevent "Codebases that burn you out" by warning about objectively complex code relative to your current energy.
*   **Status**: Design Complete, Implementation Pending (Phase 1).

---

## 3. Architecture Deep Dive

### The "Brain" Loop
```
[User Request] -> [Claude Brain] -> [Meta-Prompt Gen]
                       ^
                       | (optimizes)
[ADHD Context] --------+
    ^
    | (predicts)
[ML Predictor] <- [Historical Data]
```

### Integration Points
*   **Claude Brain** wraps all LLM calls from the core system.
*   **ML Predictor** feeds data into the ADHD Engine.
*   **Session Intelligence** bridges the gap between the TUI (Dashboard) and the Knowledge Graph (ConPort).

---

## 4. Validated Status (Audit Results)

**✅ Operational:**
*   **Claude Brain**: Phase 1 complete, API endpoints functional.
*   **Session Intelligence**: Production ready, DopeconBridge adapter working.

**⚠️ Pending / Experimental:**
*   **Complexity Coordinator**: High-impact design, but implementation meant for "Next Sprint".
*   **ML Predictions**: Code exists (`lstm_cognitive_predictor.py`) but needs encapsulation into a proper service with API.

---

*Sources: `claude_brain/README.md`, `session-intelligence/README.md`, `lstm_cognitive_predictor.py`, `UNIFIED_COMPLEXITY_INTELLIGENCE.md`.*
