---
id: ARCHITECTURE_MAPS
title: Architecture Maps
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Architecture Maps (explanation) for dopemux documentation and developer workflows.
---
# Dopemux System Architecture Maps

This document provides high-level and detailed architectural views of the Dopemux ecosystem.

## 1. High-Level Modular Overview (The "Planes")

Dopemux operates on a **Two-Plane Architecture**: the **Project Management (PM) Plane** and the **Cognitive (ADHD) Plane**.

```mermaid
graph TD
    User([User]) <--> CLI[Dopemux CLI]

    subgraph PM_Plane [Project Management Plane]
        Leantime[Leantime PM] <--> MySQL[(MySQL)]
        TM[Task-Master AI] <--> Leantime
    end

    subgraph Cognitive_Plane [Cognitive / ADHD Plane]
        ConPort[ConPort Knowledge Graph] <--> Postgres[(Postgres + AGE)]
        ADHD[ADHD Engine] <--> ConPort
        Serena[Serena Implementation Agent] <--> ConPort
        Context[Dope-Context Semantic Search] <--> Qdrant[(Qdrant Vector DB)]
    end

    subgraph Intelligence_Layer [Intelligence & Routing]
        LiteLLM[LiteLLM Proxy] --> Anthropic[Anthropic API]
        LiteLLM --> OpenAI[OpenAI API]
        PAL[PAL API Documentation MCP] <--> LiteLLM
    end

    CLI <--> Cognitive_Plane
    CLI <--> PM_Plane
    Cognitive_Plane <--> Intelligence_Layer
```

---

## 2. Extraction & Repo-Truth Flow (The "Intelligence Tree")

The Repo-Truth stack transforms raw source code into structured "Ground Truth" for LLMs.

```mermaid
graph LR
    Source[(Source Code)] --> A[Phase A: Repo Control Plane]
    Source --> C[Phase C: Code Surfaces]

    A --> D[Phase D: Docs Pipeline]
    C --> D

    D --> S[Phase S: System Truths Synthesis]

    S --> TruthPack[Final Truth Pack Bundle]

    TruthPack --> Claude[Claude Code Context]
```

---

## 3. Modular Container Deployment

Dopemux uses a fragmented deployment strategy to optimize for machine resources.

```mermaid
graph TD
    subgraph Core [Core Stack - 8GB]
        Postgres
        Redis
        Qdrant
        ConPort
        Orchestrator
    end

    subgraph Research [Research Stack - +2GB]
        GPT-Researcher
        Exa
    end

    subgraph Full [Full Stack - +6GB]
        Leantime
        LiteLLM
        Desktop-Commander
        Webhooks
    end

    Installer -->|Choice 1| Core
    Installer -->|Choice 2| Core + Research
    Installer -->|Choice 3| Core + Research + Full
```
