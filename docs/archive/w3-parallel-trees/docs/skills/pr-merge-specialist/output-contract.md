---
id: OUTPUT_CONTRACT
title: Output Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Output Contract (explanation) for dopemux documentation and developer workflows.
---
# PR Merge Specialist: Output Contract

## Mandatory Reporting
Every execution of the PR Merge Specialist must conclude with a concise summary covering:

1. **Current PR State**: Title, ID, Readiness (READY/BLOCKED), and Priority Score.
2. **Blockers**: A categorized list of all current blockers (Comments, CI, Conflicts, Gaps).
3. **Actions Taken**: A summary of all automated changes, verification runs, and metadata updates performed.
4. **Remaining Decisions**: Explicit list of escalations or manual tasks required.
5. **Proof Artifacts**: Relative paths to the key JSON evidence generated during the run.

## Artifact Naming Conventions
- `QUEUE_STATE_SNAPSHOT.json`: Full technical state of the PR.
- `READINESS_DECISION.json`: The authoritative go/no-go logic result.
- `REMEDIATION_PLAN.json`: Planned (or completed) code and test fixes.
- `METRICS_SUMMARY.json`: Rollups for throughput, duration, and cost proxies.
- `SCENARIO_RESULTS.json`: Results of the automated validation matrix.
- `THREAD_DISPOSITIONS.json`: Categorized review feedback and resolution status.
