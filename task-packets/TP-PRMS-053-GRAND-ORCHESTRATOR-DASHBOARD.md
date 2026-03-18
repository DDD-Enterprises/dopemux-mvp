---
id: TP-PRMS-053-GRAND-ORCHESTRATOR-DASHBOARD
title: Tp Prms 053 Grand Orchestrator Dashboard
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Tp Prms 053 Grand Orchestrator Dashboard (explanation) for dopemux documentation
  and developer workflows.
---
# TP-PRMS-053-GRAND-ORCHESTRATOR-DASHBOARD

## Summary
Implement a persistent, live-updating terminal dashboard (`dopemux pr-merge flight`) that tracks PR progress through the queue in real-time, combining the global queue view with the interactive tactical cockpit into a single, cohesive "Stateful Redraw Loop".

## Why Now
The current CLI forces the operator into a disjointed workflow (run health, run scan, run interactive, exit, repeat). A true "Flight Deck" should provide a continuous, unified view where the operator can see the whole queue, drill down into specific PRs, apply tactics, and watch the queue state update live without ever leaving the dashboard.

## Goals
- Replace the prompt-and-exit loop with a persistent, stateful application loop.
- Implement a split-pane UI:
    - **Top**: Global Queue Status (Live Table).
    - **Bottom**: Active PR Tactical Cockpit (The current `InteractiveMergeWizard` view).
- Implement non-blocking or managed input handling to allow the dashboard to refresh while waiting for operator commands.
- Provide real-time feedback on long-running tasks (e.g., "Synthesizing patch...", "Running CI...").

## Deliverables
- `src/dopemux_pr_merge_specialist/dashboard.py` (New module for the stateful loop).
- Updates to `src/dopemux_pr_merge_specialist/cli.py` (new `flight` command).
- Updates to `src/dopemux_pr_merge_specialist/ux_engine.py` (for full-screen layout rendering).

## Ordered Steps

### 1. The Stateful Redraw Architecture
Create a new `Dashboard` class in `dashboard.py`:
-   **State**: Define an `AppState` dataclass to hold the current queue (list of PRs), the index of the active PR, and global status messages.
-   **Loop**: Implement a `run()` method that uses a `while not exit:` loop. Inside the loop, clear the screen, render the full UI (Queue + Cockpit), and wait for input.

### 2. Refactor Input Handling
-   Move away from blocking `Prompt.ask()` calls for the main command loop.
-   Implement a command listener that reads standard input. For standard tactical commands (`[A]`, `[P]`, `[I]`, `[T]`, `[S]`, `[Q]`), map the keystroke directly to the corresponding engine action.

### 3. Implement the Split-Pane UI
Update `RichTerminalRenderer`:
-   Add a `render_dashboard_layout(queue_state, active_pr_state)` method.
-   The top half is a `rich.table.Table` showing PR#, Title, Current Step, Status, and Elapsed Time. Highlight the row corresponding to the active PR.
-   The bottom half renders the existing `mission_header_card`, `blocker_table`, and `next_action_card` for the active PR.

### 4. Wire the `flight` Command
In `cli.py`:
-   Add the `flight` subcommand.
-   The command should initialize the `QueueManager`, perform an initial `queue_scan` to populate the `AppState`, and then hand control over to `Dashboard.run()`.

### 5. Asynchronous Operations (Stretch/Optional for MVP)
-   For operations that take time (like LLM synthesis or CI verification), update the `AppState` status message to "Working..." and force a UI redraw before executing the blocking task.

## Implementation Requirements
- Stick to `rich` for rendering to maintain consistency and avoid the massive overhead of a full `Textual` rewrite. The "clear and redraw" loop is sufficient for a CLI tool.
- Ensure the terminal is properly restored to its normal state when the user quits (`[Q]`).

## Acceptance Checks
- Running `dopemux-pr-merge flight` launches a persistent, full-screen (or large panel) interface.
- The top half displays multiple PRs; the bottom half displays details for one PR.
- Pressing `S` skips to the next PR, updating both the top table highlight and the bottom details panel immediately.
- Applying a tactic updates the PR's status in the top table.

## Exit Criteria
Complete when an operator can run a single command and manage the entire queue from a persistent, live-updating dashboard interface.
