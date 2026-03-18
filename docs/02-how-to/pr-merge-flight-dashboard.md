---
id: pr-merge-flight-dashboard
title: PR Merge Flight Dashboard
type: how-to
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-18'
last_review: '2026-03-18'
next_review: '2026-06-18'
prelude: PR Merge Flight Dashboard (how-to) for dopemux documentation and developer workflows.
---
# PR Merge Flight Dashboard Quickstart

The PR Merge Flight Dashboard (`dopemux-pr-merge flight`) is a persistent TUI for managing the pull request queue in real-time. It provides a visual representation of the queue and a tactical cockpit for active PR remediation.

## Launching

Run the following command from the repository root:

```bash
dopemux-pr-merge flight
```

## Dashboard Layout

- **Header**: Live mission timer and `[LIVE]` status chip.
- **Queue Status**: Scrollable list of PRs in the current run, highlighting the active PR with a Neon Cyan background.
- **Mission Intelligence**: Strategy, rationale, and metadata for the active PR.
- **Tactical Insights**: Real-time blocker status and automated check results.
- **Tactical Controls**: Keymap for operator actions.

## Controls

The dashboard features non-blocking input handling. Simply press the corresponding key to trigger an action:

- **[A] Approve**: Approve the current PR strategy and advance.
- **[P] Patch**: Trigger a codebase patch for the active PR.
- **[I] Implement**: Run implementation-specialist automation.
- **[T] Threads**: View or resolve discussion threads.
- **[V] Verify**: Run verification pipeline on the active PR.
- **[S] Skip**: Skip to the next PR in the queue.
- **[Q] Quit**: Gracefully exit the dashboard and restore terminal state.

## ADHD Optimization

The dashboard is designed for focus and clarity:
- **Visual Contrast**: High-contrast NEON and HOUSE themes (defined in `DOPE_LAYOUT_COLORS.md`).
- **Real-time Feedback**: Status messages update instantly upon keypress.
- **Non-blocking Loop**: The UI continues to refresh while waiting for operator input.
