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

The PR Merge Flight Dashboard (`dopemux pr-merge flight`) is a persistent TUI for managing the pull request queue in real-time. It provides a visual representation of the queue and a tactical cockpit for active PR remediation, validation, approval, and merge-queue handoff.

## Launching

Run the following command from the repository root:

```bash
dopemux pr-merge flight
```

The package entrypoint remains available as a direct smoke path:

```bash
dopemux-pr-merge flight
```

## Dashboard Layout

- **Header**: Live mission timer and `[LIVE]` status chip.
- **Queue Status**: Dynamic viewport that follows the active PR as you scroll.
- **Mission Intelligence**: Strategy, rationale, and metadata for the active PR.
- **Tactical Insights**: A requirements checklist showing progress (CI, Validation, Approval, Conflicts, Threads).
- **Tactical Controls**: Keymap for operator actions.
- **Status Icons**: Distinct icons for validation-pending, approval-required, queued, blocked, and merged states.

## Advanced Orchestration

### Speculative Rebase Train (Merge Train)
The dashboard automatically attempts to "ignite" a speculative rebase train for merge-ready PRs at the start of a pass. Each candidate is rebased against the latest `origin/main`, then queued for GitHub auto-merge if the rebase succeeds.

Important behavior:

- the train does not treat another speculative branch as the base of truth
- a failed speculative rebase or push skips that PR and continues evaluating the remaining train candidates
- GitHub remains the final merge authority when auto-merge or merge queue is enabled

### Global CI Remediation
If multiple PRs fail CI with the same error, the orchestrator identifies a stable failure fingerprint from the failing validation step and error output. Instead of fixing each PR individually, it invokes the `ci-remediation-specialist` against `main` and opens or reuses a single `global-ci-fix` PR. Other failing PRs wait on that shared fix path instead of duplicating remediation.

### Optimistic Lifecycle
The dashboard uses a state model that distinguishes local proof from GitHub lag:

- `🟡` validation pending: local verification still required
- `🟣` approval required: reviewer consent is the remaining gate
- `🔵` queued: local work is done and GitHub is handling the final queue/check path
- `🟢` ready or merged: no local blocker remains

## Controls

The dashboard features non-blocking input handling. Simply press the corresponding key to trigger an action:

- **[A] Approve**: Approve the current PR strategy and advance.
- **[P] Patch**: Trigger a codebase patch for the active PR.
- **[I] Implement**: Run implementation-specialist automation.
- **[T] Threads**: View or resolve discussion threads.
- **[V] Verify**: Run verification pipeline on the active PR.
- **[S] Skip**: Skip to the next PR in the queue.
- **[Q] Quit**: Gracefully exit the dashboard and restore terminal state.

## Verification

After launching the dashboard:

1. Confirm the queue viewport follows the active PR instead of truncating unexpectedly.
1. Confirm validation-only PRs appear as `🟡` rather than queued.
1. Confirm approval-only PRs appear as `🟣`.
1. Confirm already queued auto-merge PRs appear as `🔵`.

## ADHD Optimization

The dashboard is designed for focus and clarity:
- **Visual Contrast**: High-contrast NEON and HOUSE themes (defined in `DOPE_LAYOUT_COLORS.md`).
- **Real-time Feedback**: Status messages update instantly upon keypress.
- **Non-blocking Loop**: The UI continues to refresh while waiting for operator input.
