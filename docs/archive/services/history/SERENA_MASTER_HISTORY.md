---
id: SERENA_MASTER_HISTORY
title: Serena Master History
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Serena Master History (explanation) for dopemux documentation and developer
  workflows.
---
# Serena: Master History & Feature Catalog

**Service ID**: `serena` (v2)
**Role**: Cognitive Assistant / Code Intelligence Authority
**Primary Owner**: @hu3mann
**Latest Version**: V2.0.0-phase2e
**Status**: Production Ready (Quality Score 8.5/10)

---

## 1. Executive Summary & Evolution

Serena is the **"LSP for Thoughts"**—a cognitive layer that sits between the developer and the codebase. Its primary mission is to reduce cognitive load by filtering code through an "ADHD Lens".

**Evolutionary Phases:**
* **Phase 1 (The Duplication Crisis)**: Initially planned to duplicate `claude-context`'s vector search.
* **Pivot (Sep 2025)**: Decision #84 reframed Serena as an *integration* layer. Instead of storing vectors itself, it uses a "Hybrid Architecture":
  * **Semantic Search**: Via `claude-context` (Milvus).
  * **Structural Intelligence**: Via internal LSP + Tree-sitter engines.
* **Phase 2 (The Intelligence Layer)**: Added PostgreSQL for "Adaptive Learning" (learning user patterns) and "Complexity Scoring" (traffic light indicators).
* **Current State**: A production-grade service with 31 components, fully implemented and validated (ADR-202).

---

## 2. Feature Catalog (Exhaustive)

### Core Code Intelligence
* **Enhanced LSP Wrapper**: Manages Python (`pylsp`), TS (`ts-language-server`), and Rust (`rust-analyzer`) servers.
* **Tree-sitter Analyzer**: Structural parsing for deep complexity analysis.
* **Hybrid Search**: Merges semantic results (from `claude-context`) with structural symbols (LSP).

### ADHD Accommodations (The "Cognitive Plane")
* **Complexity Scoring**: Auto-scores every file/function from `0.0` (Simple) to `1.0` (Very Complex).
  * 🟢 Simple (0.0-0.3)
  * 🟡 Moderate (0.3-0.6)
  * 🟠 Complex (0.6-0.8)
  * 🔴 Very Complex (0.8+)
* **Progressive Disclosure**:
  * **Hard Limit**: Max 10 results per query.
  * **Focus Modes**: Light (10 items), Medium (7 items), Deep (5 items).
* **Fatigue Detection**: Monitors query patterns to detect "Scattered" or "Fatigued" states and auto-simplifies results.
* **Guilt-Free Abandonment**: Tracks untracked work (git branches) and offers non-judgmental "Snooze" or "Track" options.

### Adaptive Learning
* **Pattern Recognition**: Learns developer navigation habits (e.g., "Always goes from `test_*.py` to `src/*.py`").
* **Reading Order Suggestions**: `get_reading_order` reorders file lists from Simplest -> Most Complex.
* **Next Step Prediction**: `suggest_next_step` based on historical probability.

---

## 3. Architecture Deep Dive

### Components
* **Database**: PostgreSQL (`serena_intelligence`) for patterns and relationships.
* **Caching**: Redis for hot navigation results (1.18ms hit time).
* **Compute**: Python AsyncIO server with `mcp-proxy`.

### Performance Metrics (Validated)
* **Startup**: <1ms (Lazy Loading).
* **Navigation Query**: 78.7ms avg (<200ms target).
* **DB Query**: 0.78ms avg.

### Integration Points
* **Inbound**: MCP Requests from Claude/Zen.
* **Outbound**:
  * `claude-context` (HTTP) for vectors.
  * `conport` (HTTP) for linking code to decisions.

---

## 4. Validated Status (Audit Results)

**✅ Working / Production Ready:**
* **Assessment**: "Highest quality service audited" (ADR-202).
* **Security**: Parameterized queries everywhere (No SQLi).
* **Feature Completeness**: All 58 files implemented (0 TODOs).
* **Stability**: Continuous operation verified (21+ hours).

**⚠️ Gaps:**
* **Documentation**: The 31 MCP tools need a consolidated user guide (currently scattered).
* **Metrics Dashboard**: Level 3 dashboard (Time Series) integration is pending.

---

*Sources: `serena-v2-technical-deep-dive.md`, `ADR-202-serena-v2-production-validation.md`, `serena-v2-mcp-tools.md`.*
