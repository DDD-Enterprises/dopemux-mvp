# Dopemux MVP: Features, Benefits, and Architecture

Dopemux is not a unified monolithic "AI Brain." It is an **operator-centric control workspace** that coordinates a distributed multi-plane architecture. By explicitly separating execution, memory, project management, and cognitive support, Dopemux guarantees that context is preserved exactly where it belongs, decisions are logged structurally, and workflows execute deterministically.

## Core Capabilities and Advantages

### 1. Deterministic Multi-Plane Architecture
**What it is:** Dopemux splits authority across isolated planes. PM metadata lives in Leantime; workflow transitions live in task-orchestrator; structured progress lives in ConPort; and historical evidence lives in the dope-memory chronicle.
**Why it matters:** It prevents the compounding corruption found in monolithic LLM wrappers. When an agent fails or a service degrades, the state of the workspace is preserved exactly where it stopped. There is no silent drift.

### 2. Evidence-Preserving Chronicle Memory
**What it is:** The `dope-memory` ledger acts as a permanent, append-only historical receipt store for PM progress and architectural decisions, running entirely independent of the active structured context (ConPort).
**Why it matters:** You can always reconstruct the *why* and the *how* of a codebase. The memory system proves what happened, enabling high-fidelity rollback and context restoration across sessions and agent boundaries.

### 3. Structured Decision and Progress Context
**What it is:** The `ConPort` integration allows developers and agents to inject structured, semantic decision logs and project tracking metadata directly into the system, proxy-routed safely via `dopecon-bridge`.
**Why it matters:** AI agents and human operators share the exact same structured context. When you switch tasks or environments, your reasoning graph travels with you, eliminating the "blank slate" problem in subsequent sessions.

### 4. Bridge-Mediated Integration
**What it is:** `dopecon-bridge` serves as an event transport and compatibility router. It normalizes communication without assuming ownership of the underlying data, acting strictly as a safe routing layer for PM reads/writes and knowledge graph proxying.
**Why it matters:** It forces compliance. Agents cannot hallucinate workflow transitions or bypass PM validation rules, because the bridge routes operations only to authorized upstream systems.

### 5. Operator-Support Surfaces (ADHD Engine)
**What it is:** A dedicated service layer (`ADHD Engine`) that provides cognitive-state, workload tracking, and break accommodation surfaces, independent of the core execution and PM state.
**Why it matters:** It provides real-time, terminal-native feedback on energy and attention without holding your project data hostage. It supports the operator's focus without entangling it with code execution logic.

### 6. Repo-Truth Extraction and Audit
**What it is:** A specialized extraction plane (`repo-truth-extractor` v5) that inspects the runtime codebase and generates evidence-backed artifacts about system boundaries and architecture.
**Why it matters:** The system's architecture is self-documenting based on runtime reality, not outdated aspirational prose. It makes structural drift visible, forcing engineering accountability.

## Who It Is For

Dopemux is built for **system operators, deeply integrated engineering teams, and developers** who rely on rigorous, repeatable context switching and multi-agent workflows. 

It is for users who demand to know exactly *which* service owns their data, and who refuse to surrender control of their local environment to a black-box platform. If you want a workspace where execution is deterministic, memory is structurally preserved, and workflow boundaries are enforced by strict routing, Dopemux is your stack.
