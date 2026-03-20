---
id: ADR-205-systematic-audit-methodology
title: Adr 205 Systematic Audit Methodology
type: adr
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Adr 205 Systematic Audit Methodology (adr) for dopemux documentation and
  developer workflows.
status: proposed
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# ADR-205: Systematic Code Audit Methodology Standard

**Date**: 2025-10-16
**Status**: Accepted
**Decision Makers**: Claude Code (Based on audit learnings)
**Tags**: [methodology, quality-assurance, systematic-analysis, zen-mcp]

---

## Context

During 2025-10-16 code audit, comparison between "rush review" and "systematic Zen analysis" revealed **critical value of methodical investigation**.

**Case Study - ADHD Engine**:
- **Rush review** (10 min): "8.5/10, no issues, ship immediately"
- **Zen systematic** (1.5h): "7/10, 2 MEDIUM issues found"
- **Issues caught**: Database boundary violations, missing authentication

**Result**: Systematic analysis prevented shipping with security gaps.

---

## Decision

**Establish systematic audit methodology** as standard for all future code reviews, using Zen MCP thinkdeep for multi-step investigation.

**Mandatory for**:
- Production readiness assessments
- Security audits
- Deprecation decisions
- Architecture reviews

---

## Rationale

### Evidence: Rush Reviews Miss Critical Issues

**ADHD Engine Rush Review**:
```
✅ Pydantic validation
✅ Parameterized queries
✅ Clean code
→ Conclusion: 8.5/10, ship now
→ MISSED: Database writes, missing auth
```

**ADHD Engine Systematic Analysis**:
```
✅ Pydantic validation
✅ Parameterized queries
⚠️ Database writes (found via _get_connection tracing)
⚠️ Missing auth (found via deployment analysis)
→ Conclusion: 7/10, deployment restrictions
→ CAUGHT: Real security/architecture issues
```

**Time Investment**: 1.5 hours
**Value**: Prevented production security incident

### Evidence: Prevents Major Mistakes

**Task-Orchestrator Deprecation**:
- **Initial belief**: "Stubs, safe to delete"
- **Systematic analysis**: "5,577 lines production code, unique ML"
- **Result**: Reversed incorrect deprecation, saved valuable functionality

---

## Systematic Methodology

### 5-Step Investigation Process

**Step 1: Architecture Discovery**
- Map component structure
- Identify dependencies
- Understand scope

**Step 2: Security Deep-Dive**
- Search for SQL injection patterns
- Verify input validation
- Check authentication/authorization
- Scan for common vulnerabilities

**Step 3: Implementation Verification**
- Verify claims with evidence
- Check for TODOs/stubs
- Validate operational status
- Review git history

**Step 4: Integration & Edge Cases**
- Check service boundaries
- Verify deployment security
- Assess integration points
- Test edge cases

**Step 5: Synthesis & Recommendations**
- Aggregate all findings
- Assess production readiness
- Provide actionable recommendations
- Document with confidence levels

### Tools Required

**Zen MCP thinkdeep**:
- Multi-step investigation
- Hypothesis-driven analysis
- Evidence tracking
- Confidence scoring

**Supporting Tools**:
- Serena-v2: Code navigation
- Grep: Pattern matching
- Git: History analysis
- ConPort: Decision logging

---

## Consequences

### Positive

✅ **Prevents Incidents**: Catches issues before production
✅ **Prevents Mistakes**: Validates deprecation decisions
✅ **Builds Knowledge**: ConPort decisions create audit trail
✅ **Improves Quality**: Systematic rigor raises standards
✅ **Verifiable**: Confidence levels track certainty

### Negative

⚠️ **Time Investment**: 1.5-3h per service vs 10-min rush review
⚠️ **Requires Discipline**: Easy to skip when pressed for time
🟢 **Worth It**: ROI is preventing production incidents

---

## Standards

### Minimum Requirements for Production Reviews

1. **Use Zen thinkdeep** (not rush review)
1. **Minimum 3 investigation steps**
1. **Evidence-based findings** (no assumptions)
1. **Confidence levels** (exploring → certain)
1. **Log in ConPort** (build knowledge graph)

### Quality Gates

**Before "Ship to Production"**:
- [ ] Systematic security analysis (SQL injection, auth, validation)
- [ ] Implementation verification (not stubs)
- [ ] Integration review (service boundaries)
- [ ] Edge case analysis (deployment, failure modes)
- [ ] ConPort decision logged

**Confidence Threshold**: VERY_HIGH or ALMOST_CERTAIN for production decisions

---

## Comparison: Rush vs Systematic

| Aspect | Rush Review | Systematic Analysis | Difference |
|--------|-------------|---------------------|------------|
| **Time** | 10 minutes | 1.5-3 hours | 9-17x longer |
| **Depth** | Surface level | Multi-step investigation | Much deeper |
| **Evidence** | Assumptions | Code verification | Verifiable |
| **Issues Found** | Miss critical | Catch hidden issues | **Better** |
| **Confidence** | Low (guessing) | High (verified) | **Better** |
| **Value** | Quick feedback | Prevent incidents | **Better** |

**ROI**: 1.5 hours prevents weeks of production firefighting

---

## Case Studies from 2025-10-16 Audit

### Success: ADHD Engine

**Rush Review Missed**:
- Database writes violating service boundaries
- Missing authentication on all 7 endpoints
- False "read-only" claim

**Systematic Analysis Caught**:
- All of the above through code tracing and deployment analysis

**Outcome**: Prevented shipping with security gaps

### Success: Task-Orchestrator

**Rush Assumption**:
- "Architectural stubs, safe to delete"

**Systematic Analysis Found**:
- 5,577 lines production code
- Unique ML capabilities
- Working service marked "complete"

**Outcome**: Prevented losing valuable functionality

### Success: ConPort KG

**Systematic Analysis Found**:
- 4 SQL injection vulnerabilities
- 1 ReDoS vulnerability
- N+1 query performance issue

**Outcome**: Fixed before production deployment

---

## Implementation

### For All Future Audits

**Use This Template**:
```python
# Step 1: Architecture
findings["architecture"] = investigate_structure()

# Step 2: Security
findings["security"] = check_sql_injection()
findings["security"] += check_authentication()
findings["security"] += check_input_validation()

# Step 3: Implementation
findings["implementation"] = verify_completeness()
findings["implementation"] += check_git_history()
findings["implementation"] += count_todos()

# Step 4: Integration
findings["integration"] = check_service_boundaries()
findings["integration"] += verify_deployment_security()

# Step 5: Synthesis
recommendation = synthesize(findings)
confidence = assess_confidence(findings)
log_to_conport(recommendation, confidence)
```

### Zen Thinkdeep Parameters

```python
mcp__zen__thinkdeep(
    step="Investigation step narrative",
    step_number=1-5,
    total_steps=3-5,
    next_step_required=True/False,
    findings="Evidence-based discoveries",
    confidence="exploring → certain",
    files_checked=[list of examined files],
    model="gpt-5-mini"  # Fast model for efficiency
)
```

---

## Validation

### Audit Session Metrics (2025-10-16)

**Services Reviewed**: 7
**Time**: 10 hours (systematic)
**Issues Found**: 10 (3 critical, 4 medium, 3 minor)
**Critical Discoveries**: 2 (un-deprecation, methodology value)
**Rush Reviews Prevented**: 1 (ADHD Engine)
**Incidents Prevented**: 3+ (security + deprecation)

**ROI**: 10h investment prevented weeks of production issues

---

## Related Decisions

- **Application**: All ADRs 201-204 used this methodology
- **ConPort Decisions**: #1-#7 logged via systematic process
- **Success Stories**: ADHD Engine, Task-Orchestrator
- **Git Commits**: All audit commits include systematic analysis evidence

---

## Status

**Accepted**: 2025-10-16
**Mandatory For**: Production reviews, security audits, deprecation decisions
**Quality Standard**: VERY_HIGH or ALMOST_CERTAIN confidence required
**Tool**: Zen MCP thinkdeep (primary), supporting tools (Serena, Grep, Git)
