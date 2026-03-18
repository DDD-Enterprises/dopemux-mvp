---
id: TP-PRMS-052-GRAND-ORCHESTRATOR-COCKPIT
title: Tp Prms 052 Grand Orchestrator Cockpit
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Tp Prms 052 Grand Orchestrator Cockpit (explanation) for dopemux documentation
  and developer workflows.
---
# TP-PRMS-052-GRAND-ORCHESTRATOR-COCKPIT

## Summary
Implement a unified, single-command entry point (`flight` or `orchestrate`) that ties together the entire PR Merge Specialist lifecycle: Health Check -> Tactical Queue Scan -> Interactive Cockpit Loop -> Post-Mission Report.

## Why Now
Currently, the operator experience is highly disjointed. A user must remember to run `health`, then `queue-scan` to see the queue, then launch `interactive`, and manually enter PR IDs. For a system that acts as a "Flight Deck," the operator should have one button to start the mission and be guided through the queue sequentially.

## Goals
- Create a single CLI entry point (`dopemux-pr-merge flight`).
- Automate the transitions between pre-flight health checks, queue discovery, and the interactive remediation loop.
- Refactor `InteractiveMergeWizard` to accept an ordered list of PRs directly from the `QueueManager`, replacing the raw `gh pr list` call.
- Provide a summary of actions taken across the entire session when the loop concludes.

## Deliverables
- Updates to `src/dopemux_pr_merge_specialist/cli.py` (new `flight` command).
- Updates to `src/dopemux_pr_merge_specialist/interactive.py` (`InteractiveMergeWizard` accepts an external queue).
- A new `SessionReporter` in `ops_engine.py` to aggregate stats across the loop.

## Ordered Steps

### 1. Refactor `InteractiveMergeWizard` Initialization
Modify `InteractiveMergeWizard` to accept an optional `pr_queue: List[Dict[str, Any]]` during initialization or via a new method `run_queue(pr_queue)`.
Remove the hardcoded `_get_scan_data()` reliance on raw `gh` commands when an orchestrated queue is provided.

### 2. Implement the `flight` Command
In `cli.py`, add a new command that orchestrates the following:
1.  **Pre-flight**: Call the `health` reporting logic to show the current `Scale Gate Decision` and `Signoff Compliance`.
2.  **Scan**: Call the internal logic of `queue_scan` (via `QueueManager`) to fetch the priority-ordered list of PRs.
3.  **Handoff**: Pass the resulting ordered PR list to `InteractiveMergeWizard.run_queue()`.

### 3. Upgrade the Cockpit Loop
Within the wizard:
-   Instead of asking "Enter PR ID", automatically present the first PR in the prioritized queue.
-   If the user selects `[S]kip`, move to the next PR in the queue.
-   If the user selects `[A]pprove`, `[P]atch`, `[I]mplement`, etc., stay on the PR until it is resolved or skipped.
-   If the user selects `[Q]uit`, safely break the loop and proceed to the final report.

### 4. Post-Mission Briefing
When the queue is drained or the user quits:
-   Print a summary table: "PRs Reviewed", "Patches Applied", "Threads Resolved", "Total Time".
-   Optionally, re-run the `health` check to show how the session improved the fleet metrics.

## Implementation Requirements
- Do not duplicate the logic in `queue_drain.py`; import and reuse the core `QueueManager` flow.
- Ensure that quitting the interactive mode (`[Q]`) gracefully drops the user into the final summary, rather than a hard `sys.exit(0)`.

## Acceptance Checks
- Running `dopemux-pr-merge flight` executes health, scan, and interactive mode sequentially.
- The interactive mode automatically presents PRs in the order determined by the queue scan priority layers.
- Quitting the interactive mode displays a session summary.

## Exit Criteria
Complete when an operator can run a single command to perform a full, guided shift of PR remediation without needing to memorize PR IDs or run discrete CLI steps.
