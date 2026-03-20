---
id: OPERATOR_CONTRACT
title: Operator Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Operator Contract (explanation) for dopemux documentation and developer workflows.
---
# PR-MERGE-SPECIALIST Operator Contract

## Purpose

Define the canonical behavior contract for pr-merge-specialist across all AI platforms and execution contexts.

## Core Principles

### 1. Single Source of Truth
- This contract is the authoritative definition of pr-merge-specialist behavior
- All execution contexts must conform to this contract
- No context-specific logic may override contract requirements

### 2. Behavioral Consistency
- Identical workflow sequence across all execution modes
- Consistent decision logic and gate criteria
- Uniform handoff contracts and artifact emission

### 3. Context Portability
- Different execution contexts (CLI, API, interactive) may vary in invocation
- Context-specific optimizations must preserve contract compliance
- Migration between contexts requires no behavior changes

### 4. Governance Integration
- All decisions must be auditable and traceable
- Proof bundles emitted for every execution
- Chain of custody maintained throughout workflow

## Contractual Obligations

### Workflow Sequence (MANDATORY)

All implementations MUST execute these steps in exact order:

```
1. INTAKE_HANDOFF → HANDOFF_VALIDATION.json
2. TRIAGE_STATE → TRIAGE_REPORT.json
3. SCORE_PRIORITY → PRIORITY_SCORE.json
4. CONFLICT_ANALYSIS → CONFLICT_ANALYSIS.json
5. VERIFY_READINESS → READINESS_DECISION.json
6. PLAN_REMEDIATION → REMEDIATION_PLAN.json
7. EXECUTE_FIXES → FIX_EXECUTION_REPORT.json
8. VALIDATE_OUTCOME → VALIDATION_REPORT.json
9. EMIT_PROOF → PROOF_BUNDLE.json
10. HANDOFF_COMPLETE → HANDOFF_COMPLETE.json
```

### Decision Logic (MANDATORY)

#### Handoff Validation
- MUST validate: handoff bundle structure
- MUST verify: all required artifacts present
- MUST check: chain of custody integrity
- MUST assess: governing posture compatibility

#### State Triage
- MUST detect: CI status (SUCCESS/FAILURE/PENDING)
- MUST classify: conflict type (MECHANICAL/GENERATED/SEMANTIC)
- MUST assess: mergeability state
- MUST count: unresolved feedback threads

#### Priority Scoring
- MUST calculate: composite priority score
- MUST consider: PR age, CI status, conflict risk
- MUST apply: anti-starvation bonuses
- MUST normalize: score range [0.0, 1.0]

#### Conflict Analysis
- MUST identify: file-level conflicts
- MUST classify: conflict resolution strategy
- MUST assess: auto-resolvability
- MUST document: conflict evidence

#### Readiness Verification
- MUST apply: uniform readiness gates
- MUST check: all blocking criteria
- MUST generate: binary ready/not-ready decision
- MUST justify: decision with evidence

#### Remediation Planning
- MUST create: structured remediation plan
- MUST prioritize: by criticality and dependency
- MUST include: verification requirements
- MUST document: rollback procedures

#### Fix Execution
- MUST execute: approved remediation steps
- MUST capture: command outputs and exit codes
- MUST handle: partial failures gracefully
- MUST emit: execution trace

#### Outcome Validation
- MUST verify: all readiness criteria met
- MUST confirm: no new blockers introduced
- MUST validate: proof bundle completeness
- MUST assess: final merge readiness

### Artifact Emission (MANDATORY)

All implementations MUST emit these artifacts:

```json
{
  "run_id": "<yyyymmdd_hhmmss>",
  "pr_id": "<pr_number>",
  "source_skill": "pr-merge-specialist",
  "execution_context": "<CLI|API|INTERACTIVE>",
  "governing_posture": "<GO_SUPERVISED_ONLY|GO_AUTONOMOUS|GO_MANUAL>",
  "initial_state": {
    "ci_status": "<SUCCESS|FAILURE|PENDING>",
    "mergeable": <boolean>,
    "conflict_count": <number>,
    "thread_count": <number>
  },
  "triage_results": [],
  "priority_score": <number>,
  "conflict_analysis": {},
  "readiness_decision": {
    "status": "<merge_ready|not_ready|blocked>",
    "reason": "<string>",
    "blockers": [<blocker_list>]
  },
  "remediation_plan": {},
  "execution_report": {},
  "validation_report": {},
  "final_status": "<merged|merge_ready|blocked|escalated>",
  "chain_of_custody": {
    "parent_bundle_ids": [<parent_ids>],
    "created_at": "<iso8601_timestamp>",
    "skill_version": "<version>"
  }
}
```

## Allowed Variations

### Execution Context
- CLI vs API vs Interactive invocation methods
- Context-specific user interface adaptations
- Platform-specific authentication methods
- Environment-specific configuration

### Performance Optimization
- Parallel vs sequential execution strategies
- Caching and memoization approaches
- Resource allocation strategies
- Batch processing vs individual PR handling

### Monitoring and Observability
- Context-specific logging formats
- Platform-specific metrics emission
- Environment-specific tracing
- Custom dashboard integrations

## Forbidden Variations

### Workflow Changes
- ❌ Modifying step sequence or order
- ❌ Skipping required steps
- ❌ Adding context-specific steps
- ❌ Changing step outputs or contracts

### Decision Logic
- ❌ Context-specific gate criteria
- ❌ Different scoring algorithms
- ❌ Inconsistent blocking conditions
- ❌ Platform-specific readiness definitions

### Artifact Structure
- ❌ Modified artifact schemas
- ❌ Missing required fields
- ❌ Inconsistent naming conventions
- ❌ Broken chain of custody

## Compliance Requirements

### Validation Gates
All implementations MUST pass these gates:

1. **Workflow Sequence Gate**: Exact step sequence executed
2. **Artifact Completeness Gate**: All required artifacts emitted
3. **Decision Consistency Gate**: Same decisions for same inputs
4. **Proof Integrity Gate**: Complete chain of custody
5. **Governance Compliance Gate**: All governance rules followed

### Proof Requirements
All implementations MUST emit:

- Complete proof bundles under governance contract
- Valid handoff bundles when transitioning
- Chain of custody documentation
- Compliance reports and metrics

## Escalation Protocol

### Non-Compliance Detection
1. Automated validation failure
2. Artifact structure mismatch
3. Decision inconsistency detected
4. Missing required artifacts
5. Governance rule violation

### Escalation Path
1. **Level 1 - Warning**: First offense, minor violation
2. **Level 2 - Block**: Repeat offense, moderate violation
3. **Level 3 - Governance Review**: Severe violation, contract breach

### Remediation
- Immediate correction required
- Governance approval for exceptions
- Documentation in conflict ledger
- Full audit trail maintained

## Governance Integration

### Compliance Monitoring
- Automated schema validation
- Artifact completeness verification
- Decision consistency checking
- Chain of custody auditing

### Reporting
- Execution logs with timestamps
- Validation results and metrics
- Compliance reports
- Governance audit trails

## Contract Versioning

### Version Format
`<major>.<minor>.<patch>`
- Major: Breaking changes to workflow or contracts
- Minor: Backward-compatible additions
- Patch: Clarifications, bug fixes, documentation updates

### Change Process
1. Propose change via governance packet
2. Impact analysis and risk assessment
3. Governance team review and approval
4. Version bump according to semantic versioning
5. Documentation update
6. Migration guide for existing implementations

## Implementation Requirements

### For Contract
- Single canonical contract file
- Versioned contract definition
- Complete workflow specification
- Decision logic documentation
- Artifact schema definitions
- Governance integration guidelines

### For Implementations
- Platform-specific README
- Configuration templates
- Integration guides
- Compliance documentation
- Testing and validation suite

### For Validation
- Automated validation suite
- Compliance test coverage
- Decision consistency tests
- Artifact completeness verification
- Chain of custody validation

## Exit Criteria

Contract implementation is complete when:
1. ✅ Canonical contract files created and versioned
2. ✅ All execution contexts implement identical behavior
3. ✅ Validation suite passes 100% compliance
4. ✅ Proof bundles identical across contexts
5. ✅ All implementations fully documented
6. ✅ Governance compliance verified
7. ✅ Chain of custody documentation complete

## Compliance Statement

By implementing pr-merge-specialist, I agree to:
- Follow this canonical contract exactly
- Preserve behavioral consistency across all contexts
- Maintain identical artifact structures and contracts
- Submit to governance validation and auditing
- Document all deviations and exceptions
- Participate in compliance monitoring and reporting

**This contract is binding and enforceable under governance rules.**
