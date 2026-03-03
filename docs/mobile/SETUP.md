---
id: SETUP
title: Setup
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-03'
last_review: '2026-03-03'
next_review: '2026-06-01'
prelude: Setup (explanation) for dopemux documentation and developer workflows.
---
# Mobile-First Dopemux Setup (Blink Shell / iOS)

This guide details how to set up and use the mobile-optimized `tmux` environment for Dopemux.

## Prerequisites

- **tmux** (2.6+ recommended).
- **Docker** (to run ConPort/Task Orchestrator).
- **iOS Device** with **Blink Shell** or **Termux**.

## Deployment Steps

1.  **Clone the Repository** (on the remote host):
    ```bash
    git clone https://github.com/dopemux/dopemux-mvp.git
    cd dopemux-mvp
    ```

2.  **Installation**:
    Install Dopemux in editable mode to register the `dopemux-mobile` command:
    ```bash
    pip install -e .
    ```

3.  **Configuration**:
    The mobile environment uses `configs/mobile/tmux.mobile.conf` automatically.

## Blink Shell Configuration (iOS)

To make the connection seamless, update your Host configuration in Blink Shell:

1.  **RemoteCommand**: `~/bin/dopemux-mobile`
2.  **RequestTTY**: `Yes`
3.  **ServerAliveInterval**: `60`
4.  **Clipboard**: Ensure `OSC 52` is enabled in Blink settings.

## Window Topology & Navigation

Once connected, use **F1-F7** (via Smart Keys or keyboard) to jump between domains:

- **F1 (0): Control** - Orchestration and quick commands.
- **F2 (1): Status** - Real-time health and repository dashboard.
- **F3 (2): Logs** - Dedicated log buffer.
- **F4 (3): Claude** - AI-assisted development.
  - **Top Pane (Supervisor)**: High-level context (Branch, TP status).
  - **Bottom Pane (Implementer)**: Claude Code or your editor.
  - **Ctrl+\**: Toggle focus between panes.
  - **Ctrl+Z**: Zoom/unzoom active pane (critical for narrow screens).
- **F5 (4): Tasks** - Planning and Task Packet management.
- **F6 (5): Editor** - Fast access to Neovim.
- **F7 (6): Monitor** - System resource monitoring (`top`/`btop`).

## Productivity Keys (Zero Chord)

- **Ctrl+Z**: Zoom active pane.
- **Ctrl+]**: Next window.
- **Ctrl+[**: Previous window.
- **Ctrl+\**: Toggle panes in window 3.

## Troubleshooting

Run the verification script from the repo root:
```bash
./scripts/mobile/verify-setup.sh
```
