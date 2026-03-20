---
id: OPERATOR_ONBOARDING
title: Operator Onboarding
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Operator Onboarding (explanation) for dopemux documentation and developer
  workflows.
---
# Operator Onboarding: PR Merge Specialist

## Getting Started
Welcome to the PR Merge Specialist pilot. This tool is designed to assist you in remediating and merging Pull Requests safely.

### 1. The Dry-Run First Rule
Always start with a dry-run to see what the engine plans to do:
```bash
python3 -m src.dopemux_pr_merge_specialist.cli pr-fix --id <PR_ID>
```

### 2. Inspect the Artifacts
Review the generated evidence in `proof/pr_merge/PR-<ID>/<RUN_ID>/`:
- **READINESS_DECISION.json**: Why the PR is blocked or ready.
- **REMEDIATION_PLAN.json**: What the engine suggests fixing.
- **PR_BODY_MUTATION_PLAN.json**: Exact patches planned for the description.

### 3. Execution
If the plan looks correct, proceed with safe execution (if Tier 1+):
```bash
# In Tier 1, safe mutations happen by default if enabled in policy.
```

### 4. Escalation
If you see something confusing or contradictory in the logs, **stop** and resolve it manually. The engine is a specialist, but you are the authoritative owner.
