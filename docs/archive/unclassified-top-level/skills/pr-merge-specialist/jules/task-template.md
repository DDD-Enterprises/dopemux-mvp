---
id: TASK_TEMPLATE
title: Task Template
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Task Template (explanation) for dopemux documentation and developer workflows.
---
# Jules Task Template: PR Remediation

## Task: Resolve PR Blockers
**ID**: `TP-PRMS-JULES-001`
**Trigger**: New review submitted or PR blocked in queue.

## When to Use
- Automated PR remediation loops.

## When NOT to Use
- Design from scratch.
- Bypassing approvals.

## Ordered Workflow
1. Inspect state via `pr-fix`.
2. Map verification requests.
3. Apply safe patches.
4. Finalize resolution.

## Prompt
"Act as the PR Merge Specialist. Ingest feedback using the `pr-fix` CLI, classify items as `MUST_FIX` or `QUESTION`, and run the `RemediationOrchestrator`. Only resolve threads where `ThreadResolutionGuard` provides a `True` disposition. Report final `READINESS_DECISION.json`."

## Output Requirements
- Audit trail of all `ReviewReplyAction` items.
- Link to `PR_BODY_ENFORCEMENT_SUMMARY.json`.
- Refusal rationale for any unresolved threads.
