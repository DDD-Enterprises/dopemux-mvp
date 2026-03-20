---
id: USER_JOURNEY
title: User Journey
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: User Journey (explanation) for dopemux documentation and developer workflows.
---
# Dopemux User Journey & Workflow Map

This document outlines the end-to-end user experience for developers adopting Dopemux, from initial installation to daily high-performance workflows.

## 1. Onboarding Path (The First 5 Minutes)

### Phase A: Discovery & Bootstrap
- **Trigger**: User discovers Dopemux and wants to supercharge their Claude Code experience.
- **Action**: Runs `./install.sh`.
- **UX**:
  - Dynamic platform detection (macOS/Linux).
  - Pre-flight hardware validation (RAM/CPU checks).
  - Clear progress bars and "ADHD-friendly" visual status.
- **Outcome**: Isolated `venv` created, `dopemux` CLI aliased, `.env` secured.

### Phase B: Project Initialization
- **Trigger**: User enters a new or existing project directory.
- **Action**: Runs `dopemux init`.
- **UX**:
  - Auto-detection of project type (Python, Node, etc.).
  - Interactive profile selection (e.g., `python-ml`).
  - Automatic creation of `.dopemux/` and `.claude/` configs.
- **Outcome**: Project is "Dope-ready."

### Phase C: The "Soft Landing"
- **Trigger**: Installation completes.
- **Action**: User follows the "Next Step" suggestion.
- **Outcome**: User runs `source ~/.zshrc && dopemux start`.

---

## 2. Daily Workflow (The Hyperfocus Loop)

### Path 1: Quick Fix (Standard Mode)
- **Action**: `dopemux start --role quickfix`
- **Focus**: Targeted debugging and small changes.
- **Isolation**: Minimal MCP overhead.

### Path 2: Architectural Deep-Dive (Research Mode)
- **Action**: `dopemux start --role research`
- **Focus**: Complex system understanding.
- **Tooling**: Connects GPT-Researcher and Exa for deep-web and repo-wide knowledge.

### Path 3: The Multi-Instance Sprint
- **Action**: Running `dopemux start` in multiple terminal tabs or worktrees.
- **Isolation**: Automated git worktree creation per instance (`Instance A`, `Instance B`).
- **Context**: ConPort preserves the "Mental Map" across branch switches.

---

## 3. Maintenance & Health

### Health Checks
- **Action**: `dopemux verify` or `dopemux mcp status`.
- **Outcome**: Visual confirmation that all 17+ containers are healthy.

### Updates
- **Action**: `dopemux upgrades apply`.
- **Outcome**: Graceful migration of configurations and service definitions.

---

## 4. Advanced Intelligence (The Repo-Truth Stack)

### Action: `dopemux extractor trace`
- **Purpose**: Generates a comprehensive "Ground Truth" bundle of the repository.
- **Workflow**:
  1. **A**: Repo Control Plane (Mapping the core).
  2. **C**: Code Surfaces (Identifying entry points).
  3. **D**: Docs Pipeline (Syncing truth).
  4. **S**: System Truths (LLM-driven synthesis).
- **Outcome**: A branching tree of "Truth Trace" files used for perfect LLM context.
