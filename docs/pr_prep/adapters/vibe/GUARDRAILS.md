---
id: GUARDRAILS
title: Guardrails
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Guardrails (explanation) for dopemux documentation and developer workflows.
---
# Vibe Adapter Guardrails for PR-Prep-Specialist

## Purpose
Prevent Vibe from drifting out of plan mode and enforce checkpointed execution with operator review gates.

## Guardrail Rules

### 1. PLAN MODE IS TEXT-ONLY
- **No repo writes** allowed in plan mode
- **No implementation** allowed in plan mode
- **No phase progression** allowed in plan mode
- **Mandatory stop** after plan output
- **Wait for execution packet** required

### 2. EXECUTION IS CHECKPOINTED
Vibe **MUST** stop after each phase and emit:
- Required artifact references
- Human-readable phase summary
- Explicit next requested action
- Explicit review-gate requirement

### 3. ARTIFACT-FIRST TRANSITIONS
No phase transition allowed unless:
- Required artifacts exist
- Artifacts are recorded in checkpoint manifest
- Operator verification completed

### 4. PACKAGE-ONLY DEFAULT
- Default posture: **PACKAGE_ONLY**
- DRAFT_FIRST requires operator approval
- SUPERVISED_FINAL requires operator signoff + policy check

### 5. HUMAN REVIEW REQUIRED
Vibe **MUST** require operator review at each checkpoint before continuing.

## Checkpoint Sequence

### 1. Branch Intake Checkpoint
- **Phase**: INTAKE
- **Required Artifacts**: `BRANCH_STATE.json`
- **Human Summary**: Branch identity, base detection, worktree state
- **Review Gate**: Operator verifies branch/base truth
- **Allowed Next**: Proceed to adjacent-work audit
- **Forbidden**: Skip to drafting, create PR early

### 2. Adjacent-Work Audit Checkpoint
- **Phase**: AUDIT
- **Required Artifacts**: `BRANCH_AUDIT_REPORT.json`
- **Human Summary**: Stash/sibling branch analysis, ambiguity score
- **Review Gate**: Operator verifies missing work risk
- **Allowed Next**: Proceed to obligation detection
- **Forbidden**: Skip to validation, hide ambiguity

### 3. Obligation Detection Checkpoint
- **Phase**: OBLIGATIONS
- **Required Artifacts**: `CHANGESET_OBLIGATION_REPORT.json`
- **Human Summary**: Docs/changelog requirements, existing artifacts
- **Review Gate**: Operator verifies obligation correctness
- **Allowed Next**: Proceed to PR drafting
- **Forbidden**: Mark obligations complete without evidence

### 4. PR Drafting Checkpoint
- **Phase**: DRAFTING
- **Required Artifacts**: `PR_DRAFT_PACKAGE.json`, `PR_BODY_RENDERED.md`
- **Human Summary**: Title, body sections, warnings
- **Review Gate**: Operator verifies PR body truthfulness
- **Allowed Next**: Proceed to validation
- **Forbidden**: Handoff early, fabricate verification

### 5. Final Prep Decision Checkpoint
- **Phase**: VALIDATION
- **Required Artifacts**: `FINAL_PREP_DECISION.json`
- **Human Summary**: Decision, blockers, warnings
- **Review Gate**: Operator verifies blocker correctness
- **Allowed Next**: Proceed to creation/handoff
- **Forbidden**: Bypass blocked state, silent progression

### 6. Creation/Handoff Checkpoint
- **Phase**: HANDOFF
- **Required Artifacts**: `PR_CREATION_REPORT.json`, `PR_HANDOFF_BUNDLE.json`
- **Human Summary**: Creation mode, handoff completeness
- **Review Gate**: Operator verifies handoff truthfulness
- **Allowed Next**: Complete
- **Forbidden**: Finalize without review, modify bundle

## Operator Review Model

### Review Requirements
1. **Explicit Verification**: Operator must actively verify each checkpoint artifact
2. **Stop Authority**: Operator can STOP at any checkpoint
3. **Escalation Path**: Operator can ESCALATE to high-risk lane
4. **No Silent Progression**: Vibe must wait for operator response
5. **Timeout**: 300s max wait per checkpoint

### Operator Decisions
- **VERIFY**: Proceed to next checkpoint
- **STOP**: Abort execution immediately
- **ESCALATE**: Move to high-risk arbitration
- **RETRY**: Re-run current checkpoint
- **OVERRIDE**: Force progression (audit logged)

### Review Checklist
Operator must verify at each checkpoint:
- [ ] Branch/base truth accuracy
- [ ] Missing related work risk assessment
- [ ] Docs/changelog obligation correctness
- [ ] PR body truthfulness
- [ ] Verification truthfulness
- [ ] Blocker correctness
- [ ] Continue/stop/escalate decision

## Fail-Closed Policy

### Halt Conditions
Vibe **MUST** halt when:
- Required artifact missing → `MISSING_ARTIFACT.json`
- Required summary missing → `MISSING_SUMMARY.json`
- Checkpoint skipped → `CHECKPOINT_VIOLATION.json`
- Phase output ambiguous → `AMBIGUITY_THRESHOLD_BREACH.json`
- Confidence < 85% → `LOW_CONFIDENCE.json`
- Ambiguity > 50 → `HIGH_AMBIGUITY.json`
- Operator declines → `OPERATOR_STOP.json`

### Default Posture Downgrade
Automatic downgrade to **PACKAGE_ONLY** when:
- High ambiguity score detected
- Missing obligations found
- Blocked validation state
- Operator override requested

## Implementation Requirements

### Vibe-Specific Files
1. `docs/pr_prep/adapters/vibe/GUARDRAILS.md` (this file)
2. `docs/pr_prep/adapters/vibe/CHECKPOINT_SEQUENCE.md`
3. `docs/pr_prep/adapters/vibe/OPERATOR_REVIEW_FORM.md`
4. `docs/pr_prep/adapters/vibe/AGENT_TEMPLATE.md`

### Validation Artifacts
1. `proof/pr_prep/instructions/VIBE_CHECKPOINT_VALIDATION.json`
2. `proof/pr_prep/instructions/VIBE_GUARDRAIL_MANIFEST.json`

### Checkpoint Validation
Each checkpoint must define:
- `phase_name`
- `required_artifacts`
- `required_human_summary`
- `review_gate_question`
- `allowed_continue_condition`
- `must_halt_condition`
- `forbidden_next_actions`

## Compliance

### Enforcement
- Pre-commit hooks verify guardrail presence
- CI/CD validates checkpoint sequence
- Operator review required for bypass

### Violation Handling
1. Detect violation
2. Emit violation report
3. Halt execution
4. Escalate to operator
5. Log in audit trail

## Policy Owner
- **Owner**: pr-prep-specialist maintainer
- **Enforcement**: CI/CD + operator review
- **Updates**: Require governance approval
