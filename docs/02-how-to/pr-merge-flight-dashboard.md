---
id: pr-merge-flight-dashboard
title: PR Merge Flight Dashboard
type: how-to
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-18'
last_review: '2026-03-27'
next_review: '2026-06-27'
prelude: PR Merge Flight Dashboard (how-to) for dopemux documentation and developer workflows.
---
# PR Merge Flight Dashboard Quickstart

The PR Merge Flight Dashboard (`dopemux-pr-merge flight`) is the authoritative interactive executor for PR merge operations. It provides a persistent TUI for queue management, tactical remediation, approval, validation, and merge-queue handoff.

`dopemux-pr-merge flight-deck` is a compatibility entry point that now delegates to this same dashboard so both surfaces share the same execution path and autopilot behavior.

## Launching

Run the following command from the repository root:

```bash
dopemux-pr-merge flight
```

To launch the same dashboard through the legacy flight-deck entry point and engage autopilot immediately:

```bash
dopemux-pr-merge flight-deck --auto-pilot
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
If multiple PRs fail CI with the same error, the orchestrator identifies a stable failure fingerprint and routes them through a shared remediation path instead of fixing each PR independently. The authority order is local-first:

- if a PR already produced a failing local validation step, the global blocker fingerprint comes from that local validation output
- otherwise, the queue can harvest GitHub Actions job logs for failed required checks and derive a remote fingerprint from the underlying failing test or error signature
- when two or more PRs share that fingerprint and the failing required check has an explicit reproduction command, PRMS opens or reuses a single `global-ci-fix` PR against `main`

Important constraint:

- branches with failing required GitHub checks remain blocked even when local validation passes
- auto-merge-enabled PRs are still treated as blocked if the required remote checks are red
- bounded dry or execute runs respect `--max-prs`, so operator test runs can sample the queue without draining the whole backlog
- explicitly mapped required checks can be reproduced locally before CI remediation runs; unmapped remote failures still fail closed
- remote fingerprint harvesting is GitHub Actions-only in the first pass; non-Actions check URLs and ambiguous log output do not trigger shared remediation
- headless queue runs append real-time progress to `proof/pr_merge/<run-id>/LIVE_LOG.txt`; this is the canonical artifact to tail while `queue-drain` is still running

Important constraint:

- branches with failing required GitHub checks remain blocked even when local validation passes
- auto-merge-enabled PRs are still treated as blocked if the required remote checks are red
- bounded dry or execute runs respect `--max-prs`, so operator test runs can sample the queue without draining the whole backlog
=======
>>>>>>> codex/remote-required-check-repro
=======
If multiple PRs fail CI with the same error, the orchestrator identifies a stable failure fingerprint from the failing validation step and error output. Instead of fixing each PR individually, it invokes the `ci-remediation-specialist` against `main` and opens or reuses a single `global-ci-fix` PR. Other failing PRs wait on that shared fix path instead of duplicating remediation.
>>>>>>> wt-collect-dopemux-pr321-20260330023335

### Optimistic Lifecycle
The dashboard uses a state model that distinguishes local proof from GitHub lag:

- `🟡` validation pending: local verification still required
- `🟣` approval required: reviewer consent is the remaining gate
- `🔵` queued: local work is done and GitHub is handling the final queue/check path
- `🟢` ready or merged: no local blocker remains

Required-check failures are not treated as queue lag. If GitHub still reports failing required checks, the PR remains blocked even when local validation is green.

## Controls

The dashboard features non-blocking input handling. Simply press the corresponding key to trigger an action:

- **[A] Approve**: Approve the current PR strategy and advance.
- **[P] Patch**: Trigger a codebase patch for the active PR.
- **[I] Implement**: Run implementation-specialist automation.
- **[T] Threads**: View or resolve discussion threads.
- **[V] Verify**: Run verification pipeline on the active PR.
- **[S] Skip**: Skip to the next PR in the queue.
- **[Q] Quit**: Gracefully exit the dashboard and restore terminal state.

Navigation behavior:

- **Up / Down Arrow**: Move between PRs in the queue without exiting the dashboard.
- **Kitty and other application-cursor terminals**: Arrow-key navigation accepts both CSI (`Esc [ A/B`) and SS3 (`Esc O A/B`) cursor sequences.
- **Bare `Esc`**: Quit only when no cursor-key suffix arrives. Unrecognized escape suffixes are ignored instead of forcing a quit.

## Verification

After launching the dashboard:

1. Confirm the queue viewport follows the active PR instead of truncating unexpectedly.
1. Confirm validation-only PRs appear as `🟡` rather than queued.
1. Confirm approval-only PRs appear as `🟣`.
1. Confirm already queued auto-merge PRs appear as `🔵`.
1. Confirm PRs with failing required GitHub checks remain blocked instead of flipping to queued-for-merge after a local pass.
=======
1. Confirm PRs with failing required GitHub checks remain blocked instead of flipping to queued-for-merge after a local pass.
>>>>>>> codex/pr-merge-queue-unblockers
1. Confirm Up/Down arrow navigation works in your terminal emulator, including Kitty.
=======
>>>>>>> wt-collect-dopemux-pr321-20260330023335

## ADHD Optimization

The dashboard is designed for focus and clarity:
- **Visual Contrast**: High-contrast NEON and HOUSE themes (defined in `DOPE_LAYOUT_COLORS.md`).
- **Real-time Feedback**: Status messages update instantly upon keypress.
- **Non-blocking Loop**: The UI continues to refresh while waiting for operator input.
