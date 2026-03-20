---
id: CHECKPOINT_SEQUENCE
title: Checkpoint Sequence
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Checkpoint Sequence (explanation) for dopemux documentation and developer
  workflows.
---
# Vibe Adapter Checkpoint Sequence

## Mandatory Checkpoints

### 1. PLAN_COMPLETE
**Phase**: PLAN
**Required Artifact**: `PLAN-ONLY-DOCUMENT.md`
**Human Summary**: Complete plan output with all phases defined
**Review Gate**: Operator approves plan before execution
**Allowed Next**: Wait for execution packet
**Forbidden**: Begin implementation, skip to execution

### 2. INTAKE_CHECKPOINT
**Phase**: EXECUTION
**Required Artifact**: `BRANCH_STATE.json`
**Human Summary**:
```
Branch: {current_branch}
Base: {base_branch}
Worktree: {clean/dirty}
Prep Posture: {NORMAL/CAUTION/BLOCK}
```
**Review Gate**: "Does branch/base detection look correct?"
**Allowed Next**: Proceed to AUDIT_CHECKPOINT
**Forbidden**: Skip to DRAFTING, create PR early

### 3. AUDIT_CHECKPOINT
**Phase**: EXECUTION
**Required Artifact**: `BRANCH_AUDIT_REPORT.json`
**Human Summary**:
```
Ambiguity Score: {0-100}
Stash Overlaps: {count}
Sibling Branch Overlaps: {count}
Uncommitted Changes: {count}
Adjacent Work Decision: {PROCEED/CAUTION/BLOCK}
```
**Review Gate**: "Does adjacent work audit cover all risks?"
**Allowed Next**: Proceed to OBLIGATION_CHECKPOINT
**Forbidden**: Skip to VALIDATION, hide ambiguity

### 4. OBLIGATION_CHECKPOINT
**Phase**: EXECUTION
**Required Artifact**: `CHANGESET_OBLIGATION_REPORT.json`
**Human Summary**:
```
Docs Required: {YES/NO}
Docs Present: {YES/NO}
Changelog Required: {YES/NO}
Changelog Present: {YES/NO}
Migration Notes Required: {YES/NO}
Migration Notes Present: {YES/NO}
Blockers: {count}
Warnings: {count}
```
**Review Gate**: "Are obligation requirements accurate?"
**Allowed Next**: Proceed to DRAFT_CHECKPOINT
**Forbidden**: Mark obligations complete without evidence

### 5. DRAFT_CHECKPOINT
**Phase**: EXECUTION
**Required Artifacts**: `PR_DRAFT_PACKAGE.json`, `PR_BODY_RENDERED.md`
**Human Summary**:
```
Title: {pr_title}
Body Sections: {count}
Warnings: {list}
Draft Posture: {CREATE_READY/DRAFT_RECOMMENDED/BLOCKED}
Risk Hint: {LOW/MEDIUM/HIGH}
```
**Review Gate**: "Is PR body truthful and complete?"
**Allowed Next**: Proceed to VALIDATION_CHECKPOINT
**Forbidden**: Handoff early, fabricate verification

### 6. VALIDATION_CHECKPOINT
**Phase**: EXECUTION
**Required Artifact**: `FINAL_PREP_DECISION.json`
**Human Summary**:
```
Final Decision: {CREATE_READY/DRAFT_RECOMMENDED/BLOCKED}
Blocked Reasons: {list}
Warnings: {list}
Deterministic Gate: {PASS/FAIL}
Consensus Invoked: {YES/NO}
```
**Review Gate**: "Are blockers and warnings correct?"
**Allowed Next**: Proceed to CREATION_CHECKPOINT
**Forbidden**: Bypass blocked state, silent progression

### 7. CREATION_CHECKPOINT
**Phase**: EXECUTION
**Required Artifacts**: `PR_CREATION_REPORT.json`, `PR_HANDOFF_BUNDLE.json`
**Human Summary**:
```
Creation Mode: {PACKAGE_ONLY/DRAFT_FIRST/SUPERVISED_FINAL}
PR Created: {YES/NO}
PR URL: {url_or_null}
Handoff Complete: {YES/NO}
Warnings: {list}
```
**Review Gate**: "Is handoff bundle truthful and complete?"
**Allowed Next**: Complete execution
**Forbidden**: Finalize without review, modify bundle

## Checkpoint Validation Matrix

| Checkpoint | Phase | Required Artifacts | Review Gate | Halt Conditions |
|------------|-------|-------------------|-------------|-----------------|
| PLAN_COMPLETE | PLAN | PLAN-ONLY-DOCUMENT.md | Operator approval | None (must stop) |
| INTAKE_CHECKPOINT | EXEC | BRANCH_STATE.json | Branch/base truth | Missing artifact, operator stop |
| AUDIT_CHECKPOINT | EXEC | BRANCH_AUDIT_REPORT.json | Missing work risk | Missing artifact, high ambiguity |
| OBLIGATION_CHECKPOINT | EXEC | CHANGESET_OBLIGATION_REPORT.json | Obligation correctness | Missing artifact, missing docs |
| DRAFT_CHECKPOINT | EXEC | PR_DRAFT_PACKAGE.json, PR_BODY_RENDERED.md | PR body truth | Missing artifact, low confidence |
| VALIDATION_CHECKPOINT | EXEC | FINAL_PREP_DECISION.json | Blocker correctness | Missing artifact, blocked state |
| CREATION_CHECKPOINT | EXEC | PR_CREATION_REPORT.json, PR_HANDOFF_BUNDLE.json | Handoff truth | Missing artifact, operator stop |

## Operator Review Form

### Checkpoint Review Template

**Checkpoint**: [INTAKE/AUDIT/OBLIGATIONS/DRAFT/VALIDATION/CREATION]

**Artifact Verification**:
- [ ] Required artifacts present
- [ ] Artifacts valid JSON
- [ ] Artifacts match expected schema
- [ ] No missing fields

**Truth Verification**:
- [ ] Branch/base identity accurate
- [ ] Adjacent work risks documented
- [ ] Obligations correctly detected
- [ ] PR body truthful
- [ ] Validation decisions accurate
- [ ] Handoff complete

**Operator Decision**:
- [ ] VERIFY - Proceed to next checkpoint
- [ ] STOP - Abort execution
- [ ] ESCALATE - High-risk arbitration
- [ ] RETRY - Re-run current checkpoint
- [ ] OVERRIDE - Force progression (reason required)

**Operator Notes**:
```
[Free-form notes on decision rationale]
```

**Signature**:
```
Operator: [name]
Timestamp: [ISO8601]
Decision: [VERIFY/STOP/ESCALATE/RETRY/OVERRIDE]
```

## Execution Flow

```
PLAN_MODE
  │
  ▼
PLAN_COMPLETE → [Operator Review] → EXECUTION_MODE
  │
  ▼
INTAKE_CHECKPOINT → [Operator Review] → AUDIT_CHECKPOINT
  │
  ▼
AUDIT_CHECKPOINT → [Operator Review] → OBLIGATION_CHECKPOINT
  │
  ▼
OBLIGATION_CHECKPOINT → [Operator Review] → DRAFT_CHECKPOINT
  │
  ▼
DRAFT_CHECKPOINT → [Operator Review] → VALIDATION_CHECKPOINT
  │
  ▼
VALIDATION_CHECKPOINT → [Operator Review] → CREATION_CHECKPOINT
  │
  ▼
CREATION_CHECKPOINT → [Operator Review] → COMPLETE
```

## Compliance Requirements

### Vibe Must
- Stop at each checkpoint
- Emit required artifacts
- Wait for operator review
- Respect operator decision
- Default to PACKAGE_ONLY
- Halt on violations

### Operator Must
- Review each checkpoint
- Verify artifacts
- Make explicit decision
- Sign review form
- Escalate on ambiguity

### System Must
- Log all decisions
- Enforce timeouts
- Prevent checkpoint skip
- Validate artifacts
- Emit violation reports
