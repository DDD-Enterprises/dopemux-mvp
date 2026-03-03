---
id: IMPLEMENTATION
title: Implementation
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-02'
last_review: '2026-03-02'
next_review: '2026-05-31'
prelude: Implementation (explanation) for dopemux documentation and developer workflows.
---
# Implementation Overview: Mobile-First tmux for Dopemux

This document outlines the architecture and components of the mobile-first tmux environment, optimized for **Blink Shell (iOS)** and intended for integration into the core `dopemux` platform.

## 1. Core Architecture

The system is designed around **hard isolation** and **deterministic layout**.

- **Isolated Server Socket:** Uses `tmux -L dopemux-mobile` to ensure mobile sessions never conflict with desktop tmux instances or configurations.
- **Dedicated Configuration:** A self-contained `tmux.mobile.conf` that ignores user globals, ensuring a consistent experience across all mobile clients.
- **Atomic Entry Point:** A unified CLI (`dopemux-mobile`) handles the lifecycle of the isolated server and session.

## 2. Component Breakdown

### 2.1. Infrastructure
- **Bootstrap Script (`scripts/mobile/dopemux-mobile.sh`):**
    - Checks for session existence on the `dopemux-mobile` socket.
    - If missing, creates a detached session with 7 deterministic windows.
    - Configures the **Supervisor/Implementer split** in the Claude window.
    - Uses `exec tmux attach-session` to hand over control to the tmux client.
- **Configuration (`configs/mobile/tmux.mobile.conf`):**
    - Enables **OSC 52** clipboard support (essential for mobile).
    - Maps **F1-F7** to instant window jumps.
    - Binds `Ctrl+Z` to pane zoom (survival feature for narrow screens).
    - Binds `Ctrl+\` to toggle focus between Supervisor and Implementer panes.

### 2.2. Specialized Tooling
- **Status Dashboard (`scripts/mobile/status-dashboard.sh`):**
    - Runs in Window 1 (`Status`).
    - Surfaces live health metrics, Docker service status, and active Task Packet metadata.
- **Supervisor Context (`scripts/mobile/supervisor-context.sh`):**
    - Runs in the top pane of Window 3 (`Claude`).
    - Provides high-level project situational awareness (Branch, staged changes, TP intent) while the bottom pane executes code.

### 2.3. CLI Integration
- **Mobile Module (`src/dopemux/mobile/main.py`):**
    - A Click-based CLI providing `launch`, `attach`, `setup`, and `status` subcommands.
    - Designed to be exposed as a standalone entry point (`dopemux-mobile`) or integrated into the main `dopemux` command tree.

## 3. Window Topology (Indices 0-6)

| Index | Name | Purpose | Command |
|-------|------|---------|---------|
| 0 | Control | Orchestration | Default Shell |
| 1 | Status | Real-time Health | `status-dashboard.sh` |
| 2 | Logs | Operational Logs | Placeholder (Tail) |
| 3 | Claude | AI Development | **Split**: Supervisor / Implementer |
| 4 | Tasks | Planning | `ls workspace/handoff` |
| 5 | Editor | Config Edits | `nvim` |
| 6 | Monitor | Telemetry | `top` / `btop` |

## 4. Integration Instructions for LLM

When integrating this into `dopemux-mvp`:
1.  **Entry Points:** Add `dopemux-mobile` to `pyproject.toml` scripts or register the `mobile` group in `src/dopemux/cli.py`.
2.  **Dependencies:** Ensure `tmux` 2.6+ is available. The CLI relies on `click` and `os.execvp`.
3.  **Paths:** The scripts use `REPO_ROOT` relative resolution. Ensure they are placed in `scripts/mobile/` within the target repo.
4.  **Verification:** Use `scripts/mobile/verify-setup.sh` to smoke-test the environment post-integration.
