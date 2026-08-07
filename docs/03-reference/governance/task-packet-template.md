---
id: task-packet-template
title: Task Packet Template
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-02'
last_review: '2026-08-02'
next_review: '2026-10-31'
prelude: Task Packet Template (reference) for dopemux documentation and developer workflows.
---

# Task Packet Template

Every non-trivial repo-changing packet includes:

- identity, objective, repository/base policy
- `IN` / `OUT`, allowed and forbidden files
- invariants and stop conditions
- execution recommendation (live selectors only; use `UNKNOWN` when unverified)
- exact validation gates
- proof, audit, PR, rollback, and expected output
- resilient drift rules
- risk lane (`L0`–`L3`) and model-call budget

## Execution recommendation shape

```yaml
execution_recommendation:
  stage: investigation|planning|implementation|judgment|formal_audit|operations
  runner:
    preferred: <live runner>
    availability: PROVEN|PROPOSED|UNKNOWN
  agent:
    logical_role: <role>
    custom_agent: <exact agent or null>
    authority_ceiling: <scope>
  model:
    preferred: <exact live selector or UNKNOWN>
    effort: low|medium|high|xhigh|max|unknown
  fallback:
    runner: <runner or null>
    model: <exact selector or null>
    trigger: <condition>
  audit:
    required: true|false
    runner: <route or null>
    model: <selector or null>
    independence: PROVEN|LIMITED|UNKNOWN
```

Recommendations never grant authority.

## Economy rules

- L0: zero model calls; deterministic checks only.
- L1: at most one implementer model by default.
- L2/L3: one implementer + one final independent auditor after content head freeze.
- Do not audit intermediate commits.
- Do not spawn recursive packets for frontmatter/schema packaging fixes.

See `docs/03-reference/governance/evidence-economy.md`.
