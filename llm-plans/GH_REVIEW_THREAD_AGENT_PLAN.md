# GH Review Thread Agent Implementation Plan

## Objective
Implement a deterministic GitHub review-thread automation path that fetches unresolved PR review threads, turns them into commit-sized execution slices, lets the Gemini CLI implement fixes, posts evidence-backed replies, and resolves threads ONLY after verification passes.

## Canonical Owner
The implementation will reside entirely within the `dopemux_pr_merge_specialist` subsystem, specifically leveraging the existing `thread_resolution.py` and `queue_drain.py` architectures.

## Risk Level
High - Workflow and API-sensitive.

## Authorized Scope
- `src/dopemux_pr_merge_specialist/schema.py`
- `src/dopemux_pr_merge_specialist/thread_resolution.py`
- `src/dopemux_pr_merge_specialist/queue_drain.py`
- Accompanying tests in `tests/test_dopemux_pr_merge_specialist/`
- Proof artifact generation path (`proof/gh_review_thread_agent.proof.json`)

## Commit-Sized Execution Slices

### Slice 1: Schema and Classification
**Objective:** Add the `AGENTIC_FIX` disposition to the thread schema and implement the classification logic.
**Files:**
- `src/dopemux_pr_merge_specialist/schema.py` (Update `ThreadDispositionType`)
- `src/dopemux_pr_merge_specialist/thread_resolution.py` (Update `decide_thread_disposition`)
**Behavior:**
- Distinguish between simple `IMPLEMENT` (regex match) and `AGENTIC_FIX` (complex/semantic comments).
- Threads that aren't exact regex matches but are clearly actionable requests (e.g., "please update the logic to handle X") receive `AGENTIC_FIX`.
**Verification:** Unit tests in `test_thread_resolution.py` proving accurate classification without false positives.

### Slice 2: Agentic Remediation Engine
**Objective:** Implement the `remediate_review_thread` runner.
**Files:**
- `src/dopemux_pr_merge_specialist/queue_drain.py`
**Behavior:**
- Build a function parallel to `remediate_ci_failure`.
- Formulate a precise "YOLO" prompt for the `gemini` CLI containing the thread context, affected file snippet, and instructions to fix the issue minimally.
- Execute within the isolated worktree using `_isolated_gemini_home_env`.
**Verification:** Unit/integration test ensuring the prompt generation and isolated execution call are correctly structured.

### Slice 3: Disposition Application and Orchestration
**Objective:** Wire the `AGENTIC_FIX` disposition into the orchestration loop.
**Files:**
- `src/dopemux_pr_merge_specialist/thread_resolution.py` (Update `apply_thread_dispositions`)
- `src/dopemux_pr_merge_specialist/queue_drain.py` (Update `pr_apply`)
**Behavior:**
- Modify `apply_thread_dispositions` to recognize `AGENTIC_FIX` and defer it or invoke a callback.
- In `pr_apply`, intercept `AGENTIC_FIX` dispositions, call `remediate_review_thread`, and mark them as applied *if* the agent exits successfully.
- Ensure the commit/push logic handles these new agentic modifications correctly.
**Verification:** Tests ensuring `AGENTIC_FIX` dispositions trigger the remediation engine and update the applied state.

### Slice 4: Verification Gate and Thread Resolution
**Objective:** Ensure threads are only resolved after successful local validation.
**Files:**
- `src/dopemux_pr_merge_specialist/thread_resolution.py` (Update `resolve_verified_threads`)
**Behavior:**
- Ensure `resolve_verified_threads` correctly posts an evidence-backed reply (mentioning the commit and verification run) before firing the GraphQL resolution mutation.
- Ensure failing validation leaves the thread unresolved so it can be handled or escalated.
**Verification:** Tests verifying the GraphQL calls are formatted correctly and only fire when the `applied` and validation flags are true.

### Slice 5: Proof Artifact and Finalization
**Objective:** Complete the packet requirements.
**Files:**
- `proof/gh_review_thread_agent.proof.json`
**Behavior:**
- Document all slice completions, verification results, and residual risks.
- Open PR for review.

## Exit Condition
The `dopemux extract truth-run` / `dopemux pr-merge` pipeline can autonomously fix review comments, verify them locally, push the commits, and correctly resolve the GitHub threads with detailed reply evidence.