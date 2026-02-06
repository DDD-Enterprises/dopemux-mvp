---
id: GENETIC_ML_SERVICES_MASTER_HISTORY
title: Genetic Ml Services Master History
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Genetic Ml Services Master History (explanation) for dopemux documentation
  and developer workflows.
---
# Genetic Agent & ML Services: Master History & Feature Catalog

**Service ID**: `genetic-agent`, `ml-risk-assessment`
**Role**: Experimental Layer / Advanced Research
**Primary Owner**: @hu3mann
**Latest Version**: 1.5 (Research Prototype)

---

## 1. Executive Summary & Evolution

The **Experimental Plane** of Dopemux contains advanced AI research services designed to push the boundaries of "Self-Healing Code" and "Predictive Risk Assessment". These services are less critical than the Core Plane but provide powerful advanced capabilities.

**Evolutionary Phases:**
*   **Phase 1 (Vanilla)**: Iterative LLM repair loops (standard "AI coding agent").
*   **Phase 2 (Genetic)**: Introduction of **Genetic Programming (GP)** to evolve populations of code solutions, optimizing for multiple objectives (speed, size, memory) beyond just correctness.
*   **Phase 3 (ML Extraction)**: Separating the random-forest based Risk Assessment from the Task Orchestrator into a dedicated ML service.

---

## 2. Feature Catalog (Exhaustive)

### 🧬 Genetic Agent (Hybrid LLM + GP)
*   **Population Evolution**: Generates 15+ solution variants.
*   **Genetic Operators**: Uses Crossover (mixing two solutions) and Mutation (random changes) to explore the search space.
*   **Fitness Function**: Scores code based on `0.4*Success + 0.3*Size + 0.3*Quality`.
*   **Use Case**: Complex optimization (e.g., "Make this function 50% faster") or deep bug repair.

### 🤖 Vanilla Agent (Baseline)
*   **Iterative Repair**: Fast, feedback-based repair loop using compiler/test errors.
*   **Bluesky Mode**: Ideation -> Design -> Implementation pipeline.
*   **Status**: Active, used for quick fixes.

### 🔮 ML Risk Assessment
*   **Predictive Risk**: Scores tasks 0.0-1.0 on failure probability.
*   **ADHD Patterns**: Detects "Hyperfocus Burnout" and "Cognitive Overload" risks.
*   **Status**: Extracted standalone Python module (services/ml-risk-assessment).

---

## 3. Architecture Deep Dive

### The Genetic Pipeline
```
[Bug] -> [Zen Planner] -> [Initial Population (LLM)]
           |
           v
      [Evolution Loop] <--> [Serena (Fitness Analysis)]
           ^    |
           |    v
      [Crossover/Mutation]
           |
           v
      [Best Solution]
```

---

## 4. Validated Status (Audit Results)

**🧪 Experimental / Research:**
*   **Genetic Agent**: Functional but heavy. Contains "Technical Debt" (nested directories `genetic_agent/genetic_agent/...`).
*   **ML Risk**: Extracted code is safe and operational as a library, but lacks a full HTTP API wrapper (planned for future).

**Performance**:
*   **Vanilla**: 5-15s response.
*   **Genetic**: 30-120s response (computationally expensive).

---

*Sources: `genetic_agent_api.md`, `README-genetic.md`, `ADR-204-ml-risk-assessment-extraction.md`.*
