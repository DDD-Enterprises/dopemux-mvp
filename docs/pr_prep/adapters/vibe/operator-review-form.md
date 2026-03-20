---
id: OPERATOR_REVIEW_FORM
title: Operator Review Form
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Operator Review Form (explanation) for dopemux documentation and developer
  workflows.
---
# Vibe Adapter Operator Review Form

## Purpose
Standardized form for operator review at each Vibe checkpoint.

## Review Process

### 1. Checkpoint Identification
**Checkpoint**: [INTAKE / AUDIT / OBLIGATIONS / DRAFT / VALIDATION / CREATION]
**Phase**: [PLAN / EXECUTION]
**Timestamp**: [ISO8601]

### 2. Artifact Verification

**Required Artifacts Present**:
- [ ] BRANCH_STATE.json (INTAKE)
- [ ] BRANCH_AUDIT_REPORT.json (AUDIT)
- [ ] CHANGESET_OBLIGATION_REPORT.json (OBLIGATIONS)
- [ ] PR_DRAFT_PACKAGE.json (DRAFT)
- [ ] PR_BODY_RENDERED.md (DRAFT)
- [ ] FINAL_PREP_DECISION.json (VALIDATION)
- [ ] PR_CREATION_REPORT.json (CREATION)
- [ ] PR_HANDOFF_BUNDLE.json (CREATION)

**Artifact Quality**:
- [ ] Valid JSON format
- [ ] Matches expected schema
- [ ] No missing required fields
- [ ] No corrupted data
- [ ] Timestamps present
- [ ] Checksums valid (if applicable)

### 3. Truth Verification

**Branch/Base Truth**:
- [ ] Current branch correctly identified
- [ ] Base branch correctly identified
- [ ] Worktree state accurate (clean/dirty)
- [ ] No branch identity conflicts

**Adjacent Work Risks**:
- [ ] Stash overlaps documented
- [ ] Sibling branch overlaps documented
- [ ] Uncommitted changes documented
- [ ] Ambiguity score calculated
- [ ] Missing work risks disclosed

**Obligation Accuracy**:
- [ ] Docs requirement correct
- [ ] Docs presence correct
- [ ] Changelog requirement correct
- [ ] Changelog presence correct
- [ ] Migration notes requirement correct
- [ ] Migration notes presence correct
- [ ] No false obligation claims

**PR Body Truthfulness**:
- [ ] Title accurate
- [ ] Summary section truthful
- [ ] Context section truthful
- [ ] Verification section truthful
- [ ] Risks section truthful
- [ ] Rollback section truthful
- [ ] Reviewer notes truthful
- [ ] Checklist items accurate

**Validation Decisions**:
- [ ] Deterministic gate status correct
- [ ] Consensus invocation correct
- [ ] Final decision accurate
- [ ] Blocked reasons truthful
- [ ] Warnings complete
- [ ] No hidden blockers

**Handoff Completeness**:
- [ ] All artifacts included
- [ ] Metadata complete
- [ ] Warnings preserved
- [ ] Decisions preserved
- [ ] Truthful evidence chain
- [ ] No fabrication

### 4. Risk Assessment

**Ambiguity Level**: [LOW / MEDIUM / HIGH]
**Confidence Level**: [0-100%]
**Risk Factors**:
- [ ] Dirty worktree
- [ ] High ambiguity score
- [ ] Missing obligations
- [ ] Blocked validation
- [ ] High-risk changes
- [ ] Missing evidence

### 5. Operator Decision

**Decision**: [VERIFY / STOP / ESCALATE / RETRY / OVERRIDE]

**Rationale**:
```
[Detailed explanation of decision]
[Reference to specific artifacts or concerns]
[Justification for override if applicable]
```

**Next Action**:
- VERIFY: Proceed to next checkpoint
- STOP: Abort execution immediately
- ESCALATE: Route to high-risk arbitration lane
- RETRY: Re-run current checkpoint with corrections
- OVERRIDE: Force progression (requires governance approval)

### 6. Signature

**Operator Name**: [Full Name]
**Operator Role**: [Maintainer / Reviewer / Governance]
**Timestamp**: [ISO8601]
**Decision**: [VERIFY / STOP / ESCALATE / RETRY / OVERRIDE]
**Signature**: [Electronic Signature or Initials]

### 7. Audit Trail

**Previous Checkpoint**: [Name or "N/A"]
**Previous Decision**: [VERIFY / STOP / ESCALATE / RETRY / OVERRIDE / "N/A"]
**Cumulative Warnings**: [Count]
**Cumulative Blockers**: [Count]
**Escalation History**: [List of escalations if any]

### 8. Checkpoint-Specific Questions

**INTAKE Checkpoint**:
- Does branch/base detection look correct? [YES/NO]
- Are there any branch identity concerns? [YES/NO]
- Should we proceed to audit? [YES/NO]

**AUDIT Checkpoint**:
- Does adjacent work audit cover all risks? [YES/NO]
- Are ambiguity scores reasonable? [YES/NO]
- Should we proceed to obligations? [YES/NO]

**OBLIGATIONS Checkpoint**:
- Are obligation requirements accurate? [YES/NO]
- Are any obligations incorrectly marked? [YES/NO]
- Should we proceed to drafting? [YES/NO]

**DRAFT Checkpoint**:
- Is PR body truthful and complete? [YES/NO]
- Are all warnings documented? [YES/NO]
- Should we proceed to validation? [YES/NO]

**VALIDATION Checkpoint**:
- Are blockers and warnings correct? [YES/NO]
- Is validation decision accurate? [YES/NO]
- Should we proceed to creation? [YES/NO]

**CREATION Checkpoint**:
- Is handoff bundle truthful and complete? [YES/NO]
- Are all artifacts included? [YES/NO]
- Should we complete execution? [YES/NO]

### 9. Compliance Certification

**Operator Certification**:
- [ ] I have reviewed all required artifacts
- [ ] I have verified truthfulness
- [ ] I understand the risks
- [ ] I accept responsibility for this decision
- [ ] I have followed all review procedures

**Policy Compliance**:
- [ ] Checkpoint sequence followed
- [ ] No checkpoints skipped
- [ ] All artifacts verified
- [ ] Decision logged
- [ ] No policy violations

### 10. Notes

**Additional Context**:
```
[Any additional information]
[References to external discussions]
[Links to related artifacts]
```

**Action Items**:
- [ ] Follow-up investigations needed
- [ ] Documentation updates required
- [ ] Policy changes recommended
- [ ] Governance review requested

---

## Review Form Usage

### When to Use
- Required at every Vibe checkpoint
- Must be completed before progression
- Must be signed by authorized operator

### How to Use
1. Fill out checkpoint identification
2. Verify all artifacts present and valid
3. Assess truthfulness of each section
4. Make explicit decision
5. Provide rationale
6. Sign and timestamp
7. Submit for audit trail

### Decision Matrix

| Decision | Meaning | Next Action |
|----------|---------|-------------|
| VERIFY | Approve progression | Proceed to next checkpoint |
| STOP | Reject progression | Abort execution immediately |
| ESCALATE | High-risk detected | Route to arbitration lane |
| RETRY | Corrections needed | Re-run current checkpoint |
| OVERRIDE | Emergency bypass | Requires governance approval |

### Audit Requirements
- All forms must be retained
- Electronic signatures required
- Timestamp must be ISO8601
- Rationale must be specific
- Compliance certification required

### Policy Owner
- **Owner**: pr-prep-specialist maintainer
- **Enforcement**: CI/CD + operator review
- **Updates**: Require governance approval
