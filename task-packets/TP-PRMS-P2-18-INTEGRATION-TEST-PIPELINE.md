---
id: TP-PRMS-P2-18-INTEGRATION-TEST-PIPELINE
title: Tp Prms P2 18 Integration Test Pipeline
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Tp Prms P2 18 Integration Test Pipeline (explanation) for dopemux documentation
  and developer workflows.
---
# TP-PRMS-P2-18-INTEGRATION-TEST-PIPELINE

## Summary
Create an end-to-end integration test that exercises the full pipeline (`queue_scan` -> `pr_plan` -> `pr_apply` -> `pr_merge`) using a mocked GitHub API and git operations, ensuring the complete state machine functions as a cohesive unit.

## Why Now
We currently have 120+ unit tests that verify individual functions, logic heuristics, and state transitions in isolation. However, the true value of the PR Merge Specialist is the orchestration of the full loop. Now that the `engine.py` split (P2-12) is complete and the module boundaries are stable, we can write robust, high-fidelity integration tests that prove the entire `queue_drain` orchestrator works end-to-end without brittle mocking.

## Goals
- Create a comprehensive integration test suite for the `queue_drain` orchestrator and its sub-commands.
- Mock all side-effect boundaries (GitHub API, Git CLI, filesystem mutations outside `tmp_path`).
- Verify the correct generation of proof artifacts (`PLAN.json`, `QUEUE_SNAPSHOT.json`, `CLOSED_LOOP_TRACE.json`).
- Ensure no real code is committed or pushed during the test.

## Deliverables
- `tests/pr_merge_specialist/test_integration_pipeline.py`

## Ordered Steps
1. **Setup Fixtures**: Create fixtures for `mock_github_client` (returning realistic, static PR JSON data), `run_dir` (using `tmp_path`), and `base_args` (a standard CLI namespace configured for dry runs).
2. **Implement API Mocking**: Patch `GitHubClient`, `run_command` (for git), `execute_or_dry_run`, `ci_status`, `thread_counters`, and `summarize_checks` at their new module locations (e.g., `dopemux_pr_merge_specialist.queue_drain.GitHubClient`).
3. **Write Pipeline Tests**:
    - `test_full_dry_run_pipeline`: Scan -> Plan.
    - `test_queue_scan_produces_ordering`: Verify dependency edges.
    - `test_pr_plan_green_pr_reaches_merge_ready`: Ideal path.
    - `test_pr_plan_failing_ci_reaches_apply_blocked`: CI failure path.
    - `test_pr_plan_with_conflicts_reaches_apply_blocked`: Conflict path.
    - `test_queue_drain_dry_run_processes_all`: Full loop simulation.
4. **Verify Artifacts**: Ensure `test_closed_loop_trace_written` and `test_artifacts_are_valid_json` confirm the integrity of the emitted JSON payloads in the temporary run directory.

## Implementation Requirements
- The test must never mutate the real repository or communicate with GitHub.
- Mock paths must align perfectly with the post-P2-12 module structure.
- Assertions should focus on generated JSON artifacts and state transitions (`lifecycle_state`), not just mock call counts.

## Acceptance Checks
- `pytest tests/pr_merge_specialist/test_integration_pipeline.py` passes 100%.
- Artifacts emitted during the test are strictly confined to the `tmp_path`.
- The test suite covers the "happy path" and at least two blocked paths (CI failure, Conflict).

## Exit Criteria
Complete when the integration test suite successfully exercises the full `queue_drain` loop with mocked API data and proves that all required artifacts are generated correctly.
