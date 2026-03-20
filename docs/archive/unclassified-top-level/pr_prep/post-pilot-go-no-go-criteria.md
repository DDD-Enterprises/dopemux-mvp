---
id: POST_PILOT_GO_NO_GO_CRITERIA
title: Post Pilot Go No Go Criteria
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Post Pilot Go No Go Criteria (explanation) for dopemux documentation and
  developer workflows.
---
# Post-Pilot Go/No-Go Criteria

## Decision Criteria

### GO_PACKAGE_ONLY

**Required**:
- Branch truth: TRUSTWORTHY
- Adjacent work: HIGH_SIGNAL or CONSERVATIVE_USEFUL
- Obligations: ACCURATE or CONSERVATIVE
- PR draft: HIGHLY_USEFUL or USEFUL_WITH_CAVEATS
- Validation: READY_FOR_DOWNSTREAM_USE or SUFFICIENT_WITH_GAPS
- Handoff: READY_FOR_DOWNSTREAM_USE or SUFFICIENT_WITH_GAPS
- Adapters: IDENTICAL or MINOR_VARIATIONS
- Vibe control: EFFECTIVE or PARTIAL
- Pilot: SUPERVISED_READY or better

**Confidence**: MEDIUM or HIGH

### GO_DRAFT_FIRST

**Required**:
- Branch truth: TRUSTWORTHY
- Adjacent work: CONSERVATIVE_USEFUL or better
- Obligations: CONSERVATIVE or better
- PR draft: USEFUL_WITH_CAVEATS or better
- Validation: SUFFICIENT_WITH_GAPS or better
- Handoff: SUFFICIENT_WITH_GAPS or better
- Adapters: MINOR_VARIATIONS or better
- Vibe control: PARTIAL or better
- Pilot: SUPERVISED_READY

**Confidence**: MEDIUM (thin sample on final creation)

### GO_SUPERVISED_FINAL_CREATION

**Required**:
- Branch truth: TRUSTWORTHY
- Adjacent work: HIGH_SIGNAL
- Obligations: ACCURATE
- PR draft: HIGHLY_USEFUL
- Validation: READY_FOR_DOWNSTREAM_USE
- Handoff: READY_FOR_DOWNSTREAM_USE
- Adapters: IDENTICAL
- Vibe control: EFFECTIVE
- Pilot: PRODUCTION_READY
- Operational sample: ≥ 5 successful final creations
- Operator acceptance: ≥ 85%
- Incident rate: < 2%

**Confidence**: HIGH

### NO_GO_LIMIT_TO_ARTIFACTS_ONLY

**Triggered by any**:
- Branch truth: NOISY or UNSAFE
- Adjacent work: OVERBLOCKING or UNDERDETECTING
- Obligations: NOISY or UNRELIABLE
- PR draft: LIMITED or MISLEADING
- Validation: INSUFFICIENT
- Handoff: INSUFFICIENT
- Adapters: SIGNIFICANT_GAPS or BROKEN
- Vibe control: INEFFECTIVE or UNPROVEN
- Pilot: DEVELOPMENT_ONLY or UNSAFE

**Confidence**: LOW or INSUFFICIENT_EVIDENCE

### ROLLBACK_TO_HUMAN_PREP

**Triggered by any**:
- Critical safety incidents
- Uncorrectable quality issues
- Governance violations
- Operator rejection > 50%
- Incident rate > 10%

**Confidence**: HIGH (negative evidence)

## Evidence Requirements

### Structural Validation (Minimum)
- Schema compliance: 100%
- Workflow verification: 100%
- Handoff structure: 100%
- Chain of custody: 100%

### Operational Evidence (Required for GO_DRAFT_FIRST+)
- Pilot runs: ≥ 3
- Operator feedback: ≥ 5 responses
- Incident logs: Complete
- Override logs: Complete

### Strong Operational Evidence (Required for GO_SUPERVISED_FINAL)
- Pilot runs: ≥ 5
- Operator acceptance: ≥ 85%
- Incident rate: < 2%
- Override rate: < 5%
- Final creation samples: ≥ 5

## Thin-Sample Rules

### When to Declare Thin Sample
1. < 3 operational samples
2. No live final creation evidence
3. Theoretical validation only
4. Unverified adapter behavior

### Thin-Sample Postures
- **GO_PACKAGE_ONLY**: Acceptable with thin sample
- **GO_DRAFT_FIRST**: Acceptable with explicit caveats
- **GO_SUPERVISED_FINAL**: Not acceptable with thin sample
- **Higher postures**: Require strong operational evidence

## Decision Flow

1. **Check structural validation** → If failed, NO_GO or ROLLBACK
2. **Check operational evidence** → If insufficient, note caveats
3. **Evaluate domain quality** → Assign quality bands
4. **Check thin-sample indicators** → Adjust confidence
5. **Apply decision matrix** → Determine posture
6. **Assign confidence level** → HIGH/MEDIUM/LOW/INSUFFICIENT
7. **Document caveats** → Explicit limitations

## Governance Requirements

### Mandatory Documentation
- Explicit posture recommendation
- Rationale with evidence
- Confidence level
- Sample-size caveats
- Major blockers
- Risk assessment

### Prohibited Actions
- Silent posture expansion
- Unjustified confidence
- Hidden caveats
- Ignored incidents
- Unverified assumptions

## Posture Transition Rules

### From GO_PACKAGE_ONLY
- **To GO_DRAFT_FIRST**: Requires draft quality evidence
- **To higher postures**: Requires final creation evidence

### From GO_DRAFT_FIRST
- **To GO_SUPERVISED_FINAL**: Requires strong operational evidence
- **To lower postures**: Requires quality degradation

### From GO_SUPERVISED_FINAL
- **To higher postures**: Not defined (max posture)
- **To lower postures**: Requires incident or quality issue

## Monitoring Requirements

### For GO_PACKAGE_ONLY
- Monitor draft quality
- Track operator acceptance
- Log all overrides

### For GO_DRAFT_FIRST
- Monitor final creation attempts
- Track incident rate
- Log override reasons
- Measure operator acceptance

### For GO_SUPERVISED_FINAL
- Monitor all PR creations
- Track incident rate (< 2%)
- Log override reasons
- Measure operator acceptance (≥ 85%)
- Validate handoff quality

## Rollback Criteria

### Immediate Rollback
- Critical safety incident
- Governance violation
- Uncorrectable quality issue

### Considered Rollback
- Incident rate > 5%
- Operator acceptance < 70%
- Override rate > 15%
- Quality degradation

## Next Packet Recommendations

### After GO_PACKAGE_ONLY
- Gather final creation evidence
- Pilot supervised final creation
- Re-evaluate for GO_DRAFT_FIRST

### After GO_DRAFT_FIRST
- Gather more operational evidence
- Monitor incident trends
- Consider GO_SUPERVISED_FINAL if evidence supports

### After GO_SUPERVISED_FINAL
- Maintain monitoring
- Address incidents promptly
- Consider TP-PRPS-010 operationalization

### After NO_GO or ROLLBACK
- Address quality issues
- Re-test and re-evaluate
- Re-attempt lower posture
