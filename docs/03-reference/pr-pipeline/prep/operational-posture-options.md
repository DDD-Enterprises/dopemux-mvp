---
id: OPERATIONAL_POSTURE_OPTIONS
title: Operational Posture Options
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Operational Posture Options (explanation) for dopemux documentation and developer
  workflows.
---
# Operational Posture Options

## Available Postures

### GO_PACKAGE_ONLY

**Description**: Most conservative posture. Skill generates PR packages but does not create PRs.

**Use Case**:
- Initial deployment
- Low-risk environments
- Testing and validation

**Capabilities**:
- ✅ Branch state inspection
- ✅ Adjacent work audit
- ✅ Obligation detection
- ✅ PR drafting
- ✅ Validation
- ❌ PR creation
- ✅ Handoff to PRMS

**Risk Level**: LOW

**Next Steps**:
- Gather final creation evidence
- Monitor draft quality
- Consider GO_DRAFT_FIRST

### GO_DRAFT_FIRST

**Description**: Balanced posture. Skill creates PRs in draft state for review.

**Use Case**:
- Production deployment
- Moderate-risk environments
- Supervised automation

**Capabilities**:
- ✅ Branch state inspection
- ✅ Adjacent work audit
- ✅ Obligation detection
- ✅ PR drafting
- ✅ Validation
- ✅ PR creation (draft state)
- ✅ Handoff to PRMS

**Risk Level**: MODERATE

**Requirements**:
- Draft quality: HIGHLY_USEFUL or USEFUL_WITH_CAVEATS
- Validation: SUFFICIENT_WITH_GAPS or better
- Operator acceptance: ≥ 70%
- Incident rate: < 5%

**Next Steps**:
- Monitor final creation attempts
- Gather operational evidence
- Consider GO_SUPERVISED_FINAL

### GO_SUPERVISED_FINAL_CREATION

**Description**: Expanded posture. Skill creates PRs ready for merge with supervision.

**Use Case**:
- Mature deployment
- Low-risk environments
- High operator confidence

**Capabilities**:
- ✅ Branch state inspection
- ✅ Adjacent work audit
- ✅ Obligation detection
- ✅ PR drafting
- ✅ Validation
- ✅ PR creation (merge-ready)
- ✅ Handoff to PRMS

**Risk Level**: CALCULATED

**Requirements**:
- All domains: High quality
- Operational evidence: Strong
- Operator acceptance: ≥ 85%
- Incident rate: < 2%
- Final creation samples: ≥ 5

**Next Steps**:
- Maintain monitoring
- Address incidents promptly
- Consider TP-PRPS-010

### NO_GO_LIMIT_TO_ARTIFACTS_ONLY

**Description**: Restrictive posture. Skill limited to artifact generation only.

**Use Case**:
- Quality issues identified
- High-risk environments
- Safety concerns

**Capabilities**:
- ✅ Branch state inspection
- ✅ Adjacent work audit
- ✅ Obligation detection
- ❌ PR drafting
- ❌ Validation
- ❌ PR creation
- ❌ Handoff to PRMS

**Risk Level**: MINIMAL

**Next Steps**:
- Address quality issues
- Re-test and re-evaluate
- Re-attempt higher posture

### ROLLBACK_TO_HUMAN_PREP

**Description**: Emergency posture. All automation disabled.

**Use Case**:
- Critical failures
- Governance violations
- Safety incidents

**Capabilities**:
- ❌ All automation disabled
- Manual prep only

**Risk Level**: NONE (manual)

**Next Steps**:
- Redesign and retest
- Address root causes
- Re-evaluate gradually

## Posture Comparison

| Posture | Risk | Automation | PR Creation | Requirements |
|---------|------|-------------|-------------|--------------|
| GO_PACKAGE_ONLY | LOW | Partial | ❌ | Structural validation |
| GO_DRAFT_FIRST | MODERATE | Most | Draft | Medium evidence |
| GO_SUPERVISED_FINAL | CALCULATED | Full | Final | Strong evidence |
| NO_GO_ARTIFACTS | MINIMAL | Minimal | ❌ | Quality issues |
| ROLLBACK | NONE | None | ❌ | Critical failures |

## Decision Factors

### Favor GO_PACKAGE_ONLY when:
- Final creation unproven
- Thin operational sample
- Conservative approach preferred

### Favor GO_DRAFT_FIRST when:
- Draft quality proven
- Final creation thin sample
- Balanced risk approach

### Favor GO_SUPERVISED_FINAL when:
- Final creation proven
- Strong operational evidence
- High operator confidence

### Favor NO_GO or ROLLBACK when:
- Quality issues identified
- Safety concerns
- Governance violations

## Governance Requirements

### Posture Changes
- Require governance approval
- Document rationale
- Specify evidence
- Define monitoring

### Monitoring
- Track incident rates
- Measure operator acceptance
- Log overrides
- Validate handoff quality

### Rollback
- Define rollback criteria
- Document rollback procedure
- Test rollback path

## Implementation Requirements

### For All Postures
- Canonical contract compliance
- Governance integration
- Proof emission
- Chain of custody

### For Automated Postures
- Validation gates
- Escalation protocol
- Incident handling
- Operator override

### For Supervised Postures
- Additional monitoring
- Incident thresholds
- Rollback triggers
- Audit logging

## Next Packet Recommendations

### After GO_PACKAGE_ONLY
- TP-PRPS-009 evaluation
- Gather final creation evidence
- Re-evaluate posture

### After GO_DRAFT_FIRST
- TP-PRPS-009 evaluation
- Monitor operations
- Consider GO_SUPERVISED_FINAL

### After GO_SUPERVISED_FINAL
- TP-PRPS-010 operationalization
- Maintain monitoring
- Address incidents

### After NO_GO or ROLLBACK
- Address issues
- Re-test
- Re-evaluate
