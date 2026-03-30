# PR Merge Flight Experience Improvements

## Objective
Enhance the `pr-merge flight` workflow to support CI remediation, improve validation failure handling, accurately track thread resolution metrics, and provide an interactive, granular thread resolution experience.

## Key Files & Context
- `src/dopemux_pr_merge_specialist/interactive.py` & `dashboard.py`: Controls the TUI interactive loop and user inputs.
- `src/dopemux_pr_merge_specialist/ux_engine.py`: Renders the terminal UI, including blockers, metrics, and prompts.
- `src/dopemux_pr_merge_specialist/queue_manager.py`: Parses CI and thread status.
- `src/dopemux_pr_merge_specialist/metrics.py`: Manages the telemetry and operational metrics.
- `src/dopemux_pr_merge_specialist/thread_resolution.py`: Handles the resolution of review threads.

## Implementation Steps

### 1. CI Remediation Integration
- **`src/dopemux_pr_merge_specialist/ux_engine.py`**:
  - Update the blocker text rendering. If CI is `FAILURE`, add a prompt to the "NEXT STEP" text: `Press [C] to invoke CI Remediation.`
- **`src/dopemux_pr_merge_specialist/interactive.py`**:
  - Add handling for the `C` key in the event loop.
  - When pressed, pause the flight TUI and execute the `ci-remediation-specialist` skill against the current branch/PR. Once complete, refresh the PR state.

### 2. Validation Failure Handling
- **`src/dopemux_pr_merge_specialist/ux_engine.py`**:
  - If local validation fails, update the UI to offer an automated fix action (e.g., `Press [F] to attempt auto-fix for validation failures.`).
- **`src/dopemux_pr_merge_specialist/interactive.py`**:
  - When validation fails after pressing `[V]`, don't just dump the user back. Present an interactive dialog asking if they want the agent to attempt to remediate the broken validation (leveraging the patch engine or a specific remediation skill).

### 3. Thread Metrics Tracking
- **`src/dopemux_pr_merge_specialist/metrics.py`**:
  - Update the metrics schema to include `resolved_threads_in_session: int`.
  - Update the `MetricsEngine` summary rollup to display this metric.
- **`src/dopemux_pr_merge_specialist/interactive.py` & `queue_drain.py`**:
  - Whenever threads are successfully applied and verified, record the delta (number of threads resolved) and log it via the `MetricsEngine`.

### 4. Interactive Thread Resolution
- **`src/dopemux_pr_merge_specialist/thread_resolution.py`**:
  - Refactor `decide_thread_disposition` and `apply_thread_dispositions` to allow a "dry-run" mode that generates the proposed fix without writing it to disk immediately.
- **`src/dopemux_pr_merge_specialist/interactive.py`**:
  - Enhance the `[T]` (Threads) keybind logic. Instead of automatically applying all thread dispositions, iterate through each unresolved thread.
  - Display the thread's comment text and the recommended code change (diff).
  - Prompt the user interactively: `[y] Fix  [n] Ignore  [e] Edit  [q] Quit`.
  - Apply the fix only if the user confirms.

## Verification & Testing
1. Run `dopemux pr-merge flight` on a test PR with a known CI failure and verify the `[C]` key triggers the remediation agent.
2. Introduce a syntax error, run validation `[V]`, and verify the system provides a clear path to auto-remediate.
3. Check the `METRICS_SUMMARY.json` and Ops HUD to ensure thread resolution counts update dynamically.
4. Open a test PR with multiple review comments and verify the interactive `[T]` flow presents each comment alongside its proposed solution, respecting user approvals.