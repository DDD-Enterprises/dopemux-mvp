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
- **Queue Status**: Dynamic viewport that follows the active PR as you scroll.
- **Mission Intelligence**: Strategy, rationale, and metadata for the active PR.
- **Tactical Insights**: A requirements checklist showing progress (CI, Validation, Conflicts, Threads).
- **Tactical Controls**: Keymap for operator actions.

## Advanced Orchestration

### Speculative Rebase Train (Merge Train)
The dashboard automatically attempts to "ignite" a speculative rebase train for all `READY` PRs at the start of a pass. Instead of rebasing one-by-one, it rebases them in a chain (e.g., PR B onto PR A). This allows multiple PRs to pass CI and merge simultaneously, significantly increasing integration velocity.

### Global CI Remediation
If multiple PRs fail CI with the same error, the orchestrator identifies the "Failure Fingerprint". Instead of fixing each PR individually, it spawns a `ci-remediation-specialist` to fix the issue in `main` and opens a single `global-ci-fix` PR. Other failing PRs will wait for this fix to merge, then automatically rebase and heal.

### Optimistic Lifecycle
The dashboard uses an "optimistic" state model. If local validation passes, the PR is marked as `READY` (🟢) in the UI immediately, even if GitHub's CI status is still lagging or pending.

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
