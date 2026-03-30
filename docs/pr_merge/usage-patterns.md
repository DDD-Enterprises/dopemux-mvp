---
id: USAGE_PATTERNS
title: Usage Patterns
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-27'
next_review: '2026-06-15'
prelude: Usage Patterns (explanation) for dopemux documentation and developer workflows.
---
# PR Merge Specialist — Usage Patterns

## Quick Start

```bash
# Check environment is ready
python -m dopemux_pr_merge_specialist.cli self-check

# Scan the PR queue (read-only)
python -m dopemux_pr_merge_specialist.cli queue-scan --limit 10

# Plan for a specific PR (read-only)
python -m dopemux_pr_merge_specialist.cli pr-plan --id 42

# Apply fixes to a PR (mutating, requires --execute)
python -m dopemux_pr_merge_specialist.cli pr-apply --id 42 --execute

# Merge a PR if all gates pass (mutating)
python -m dopemux_pr_merge_specialist.cli pr-merge --id 42 --execute

# Process the entire queue
python -m dopemux_pr_merge_specialist.cli queue-drain --execute --max-prs 5
```

`queue-drain` does not treat a PR as queued or merge-ready merely because local validation passed. Required GitHub check failures still block the PR until the remote checks clear.

For explicitly mapped required checks, `pr-apply` and `queue-drain` can now attempt a fail-closed local reproduction before invoking automated CI remediation. These mappings live in `config/pr_merge_specialist/policy.yaml` under `remote_check_repro.steps`. Unmapped required-check failures remain blocked by design.

When queue-wide CI failures repeat across multiple PRs, `queue-drain` now falls back to remote fingerprint harvesting if a local validation fingerprint is not available. The first pass is intentionally narrow:

- local validation fingerprints still win when a failing step was reproduced in the worktree
- remote clustering only applies to GitHub Actions-backed required checks that expose a `detailsUrl`
- the shared `global-ci-fix` PR path only engages when the failing required check has both a stable log-derived fingerprint and an explicit reproduction command in `remote_check_repro.steps`
- unsupported providers, ambiguous logs, or unmapped checks remain fail-closed and continue down the existing per-PR path

When `pr-apply` produces a passive `queued_for_merge` result after rebasing and validation, `queue-drain` now still executes the merge handoff step so GitHub receives the actual `gh pr merge` or auto-merge enqueue command for that PR.

For headless `queue-drain` runs, the canonical real-time execution stream now lives in `proof/pr_merge/<run-id>/LIVE_LOG.txt`. Use that file to tail pass progress, tactic selection, shared global-fix activity, and final run summary lines while the queue is still active.

`LIVE_LOG.txt` is additive:

- `COMMANDS_RUN.txt` remains per-command evidence
- `STATE.json` remains per-PR state authority
- `RUN_SUMMARY.md` remains the final human rollup

=======
>>>>>>> codex/pr-merge-queue-unblockers
=======
When `pr-apply` produces a passive `queued_for_merge` result after rebasing and validation, `queue-drain` now still executes the merge handoff step so GitHub receives the actual `gh pr merge` or auto-merge enqueue command for that PR.

>>>>>>> codex/pr-merge-queued-handoff
=======
>>>>>>> wt-collect-dopemux-pr321-20260330023335
## Common Workflows

### 1. Safe Review Cycle (Non-Mutating)
```bash
# Step 1: Scan queue
python -m dopemux_pr_merge_specialist.cli queue-scan

# Step 2: Review plan for top-priority PR
python -m dopemux_pr_merge_specialist.cli pr-plan --id 42

# Step 3: Inspect artifacts
cat proof/pr_merge/<run-id>/pr/42/PLAN.json | jq .lifecycle_state
```

### 2. Targeted PR Processing
```bash
# Only process specific PRs
python -m dopemux_pr_merge_specialist.cli queue-drain --execute --only 42,43,44

# Prioritize specific PRs (process first, then others)
python -m dopemux_pr_merge_specialist.cli queue-drain --execute --prioritize 42
```

For bounded live runs, use `--max-prs` to stop the execute loop after a fixed number of PRs:

```bash
python -m dopemux_pr_merge_specialist.cli queue-drain --execute --max-prs 3 --max-passes 1
```

This is the safest way to validate queue behavior against live GitHub state without mutating the full backlog in one run.

### 3. Custom Policy
```bash
# Use a custom policy file
python -m dopemux_pr_merge_specialist.cli queue-drain --policy ./my-policy.yaml --execute
```

### 4. Health Monitoring
```bash
# Check system health and scale-gate decision
python -m dopemux_pr_merge_specialist.cli health

# JSON output for monitoring tools
python -m dopemux_pr_merge_specialist.cli health --json
```

### 5. Programmatic Integration
```bash
# All commands support --json for machine-readable output
python -m dopemux_pr_merge_specialist.cli self-check --json
python -m dopemux_pr_merge_specialist.cli health --json
```

## Agent Integration

External agents can consume PRMS artifacts:

1. **Read artifacts**: All outputs are deterministic JSON in `proof/pr_merge/<run-id>/`
2. **Check lifecycle state**: Parse `PLAN.json` → `lifecycle_state` field
3. **Read blockers**: Parse `PLAN.json` → `blockers` array
4. **Closed-loop traces**: Parse `CLOSED_LOOP_TRACE.json` for tactic selection rationale

See `docs/pr_merge/output-contract.md` for full artifact schema.

## Artifact Directory Structure

```
proof/pr_merge/<run-id>/
├── POLICY_EFFECTIVE.json
├── COMMANDS_RUN.txt
├── RUN_MANIFEST.json
├── RUN_SUMMARY.md
├── QUEUE_REPORT.json
├── BASE_REBASE_UPDATES.json
├── CHECK_WAIT_REPORT.json
├── ops/
│   ├── cases.jsonl
│   ├── signoffs.jsonl
│   └── safety_log.jsonl
├── queue/
│   ├── QUEUE_SNAPSHOT.json
│   └── ORDERING_PLAN.json
└── prs/
    └── <pr-id>/
        ├── INTAKE.json
        ├── REVIEW_THREADS.json
        ├── PLAN.json
        ├── CLOSED_LOOP_TRACE.json
        ├── IMPLICIT_ACTION_LOG.json
        ├── STATE_RECOMPUTE_REPORT.json
        └── NEXT_ACTION_SELECTION_REPORT.json
```
