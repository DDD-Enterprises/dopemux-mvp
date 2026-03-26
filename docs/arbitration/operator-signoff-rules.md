---
id: OPERATOR_SIGNOFF_RULES
title: Operator Signoff Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Operator Signoff Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Operator Sign-off Rules

## Overview
High-risk actions (Patching, Enqueuing) require formal operator sign-off. This document defines the rules for valid approval.

## Sign-off Requirements
1. **Evidence Verification**: The operator must confirm that they have reviewed the `ARBITRATION_EVIDENCE_BUNDLE.json`.
2. **Objection Resolution**: All Challenger objections in `CHALLENGE_REPORT.json` must be addressed or explicitly accepted as non-blocking.
3. **Plan Approval**: The `MERGE_EXECUTION_PLAN.json` must be reviewed for correctness and side-effects.
4. **Identity**: The sign-off must include the operator's identifier and a timestamp.
5. **Rationale**: A brief rationale for approval must be provided, especially for `HIGH_RISK` cases.

## Sign-off Command
Sign-offs are recorded via the CLI:
```bash
python3 -m src.dopemux_pr_merge_specialist.cli signoff --id <PR_ID> --run-id <RUN_ID> --action <ACTION> --rationale <TEXT>
```

## Audit Trail
All sign-offs are logged to `proof/pr_merge/arbitration/ops/OPERATOR_SIGNOFF_LOG.jsonl`.
