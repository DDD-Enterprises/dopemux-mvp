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

When `pr-apply` produces a passive `queued_for_merge` result after rebasing and validation, `queue-drain` now still executes the merge handoff step so GitHub receives the actual `gh pr merge` or auto-merge enqueue command for that PR.

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
