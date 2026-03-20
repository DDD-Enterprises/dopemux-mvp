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
# PR-PREP-SPECIALIST Operator Contract

## Purpose

Define the canonical behavior contract for pr-prep-specialist across all AI platforms.

## Core Principles

### 1. Single Source of Truth
- This contract is the authoritative definition of pr-prep-specialist behavior
- All platform adapters must conform to this contract
- No platform-specific logic may override contract requirements

### 2. Behavioral Consistency
- Identical workflow sequence across all platforms
- Consistent decision logic and gate criteria
- Uniform handoff contract to pr-merge-specialist

### 3. Platform Portability
- Adapters may vary instruction format but not behavior
- Tool-specific optimizations must preserve contract compliance
- Migration between platforms requires no behavior changes

## Contractual Obligations

### Workflow Sequence (MANDATORY)

All implementations MUST execute these steps in exact order:

```
1. INSPECT_BRANCH_STATE → BRANCH_STATE.json
2. AUDIT_ADJACENT_WORK → BRANCH_AUDIT_REPORT.json
3. DETECT_OBLIGATIONS → CHANGESET_OBLIGATION_REPORT.json
4. DRAFT_PR_FROM_TEMPLATE → PR_DRAFT_PACKAGE.json, PR_BODY_RENDERED.md
5. RUN_DETERMINISTIC_VALIDATION → FINAL_PREP_DECISION.json
6. CREATE_PR_UNDER_POSTURE → PR_CREATION_REPORT.json
7. HANDOFF_TO_PRMS → PR_HANDOFF_BUNDLE.json
```

### Decision Logic (MANDATORY)

#### Branch State Inspection
- MUST detect: current branch, base branch, commit count, file changes
- MUST classify: feature/hotfix/bugfix based on branch name
- MUST validate: branch naming convention compliance

#### Adjacent Work Audit
- MUST check: open PRs targeting same base branch
- MUST detect: overlapping file changes
- MUST assess: merge conflict risk

#### Obligation Detection
- MUST identify: required changelog updates
- MUST detect: required documentation updates
- MUST flag: required test updates
- MUST check: required version bump

#### PR Drafting
- MUST use: canonical PR template
- MUST include: all detected obligations
- MUST generate: both JSON package and rendered markdown

#### Deterministic Validation
- MUST apply: identical validation gates across platforms
- MUST enforce: same blocking criteria
- MUST produce: consistent pass/fail decisions

#### PR Creation
- MUST respect: governing posture (GO_DRAFT_FIRST, etc.)
- MUST create: PR with exact specified content
- MUST handle: all GitHub API requirements

#### Handoff to PRMS
- MUST emit: identical handoff bundle structure
- MUST include: all authoritative artifacts
- MUST document: complete chain of custody

### Handoff Contract (MANDATORY)

The handoff bundle MUST contain:
```json
{
  "handoff_id": "TP-PRPS-<number>-HANDOFF-<sequence>",
  "source_skill": "pr-prep-specialist",
  "target_skill": "pr-merge-specialist",
  "run_id": "<skill>-<yyyymmdd>-<sequence>",
  "repo": "<repository_name>",
  "branch": "<branch_name>",
  "base_branch": "<base_branch>",
  "pr_number": <pr_number>,
  "governing_posture": "<GO_DRAFT_FIRST|GO_DIRECT|AWAIT_REVIEW>",
  "recommended_next_step": "<AWAIT_REVIEW|MERGE_READY|BLOCKED>",
  "authoritative_artifacts": [
    "BRANCH_STATE.json",
    "BRANCH_AUDIT_REPORT.json",
    "CHANGESET_OBLIGATION_REPORT.json",
    "PR_DRAFT_PACKAGE.json",
    "PR_BODY_RENDERED.md",
    "FINAL_PREP_DECISION.json",
    "PR_CREATION_REPORT.json"
  ],
  "supporting_artifacts": [],
  "warnings": [],
  "blocking_reasons": [],
  "chain_of_custody": {
    "parent_bundle_ids": [],
    "created_at": "<iso8601_timestamp>",
    "skill_version": "<version>"
  }
}
```

## Allowed Variations

### Instruction Format
- Platform-specific instruction syntax (YAML/JSON/Markdown)
- Tool-specific invocation methods
- Platform-optimized prompting strategies

### Integration Method
- Skills (Codex)
- Subagents (Claude)
- Rules (Cursor)
- Hooks (Claude)
- Custom agents (Copilot)
- Task templates (Gemini, Jules)
- Agent templates (Vibe)

### Metadata and UI
- Platform-specific metadata fields
- Tool-specific configuration options
- UI/UX adaptations
- Platform branding

## Forbidden Variations

### Workflow Changes
- ❌ Modifying step sequence
- ❌ Skipping required steps
- ❌ Adding platform-specific steps
- ❌ Changing step outputs

### Decision Logic
- ❌ Platform-specific gate criteria
- ❌ Tool-specific validation rules
- ❌ Inconsistent blocking conditions
- ❌ Different obligation detection

### Handoff Contract
- ❌ Modified handoff structure
- ❌ Missing required fields
- ❌ Inconsistent artifact lists
- ❌ Broken chain of custody

## Compliance Requirements

### Validation Gates
All implementations MUST pass these gates:
1. **Workflow Sequence Gate**: Exact 7-step sequence executed
2. **Output Validation Gate**: All required outputs produced
3. **Handoff Structure Gate**: Identical handoff bundle format
4. **Decision Consistency Gate**: Same decisions for same inputs
5. **Artifact Completeness Gate**: All authoritative artifacts present

### Proof Requirements
All implementations MUST emit:
- Complete proof bundles under governance contract
- Valid handoff bundles to pr-merge-specialist
- Chain of custody documentation
- Compliance reports

## Escalation Protocol

### Non-Compliance Detection
1. Automated validation fails
2. Handoff structure mismatch
3. Decision inconsistency detected
4. Missing required artifacts

### Escalation Path
1. **Level 1 - Warning**: First offense, minor violation
2. **Level 2 - Block**: Repeat offense, moderate violation
3. **Level 3 - Governance Review**: Severe violation, contract breach

### Remediation
- Immediate correction required
- Governance approval for exceptions
- Documentation in conflict ledger

## Governance Integration

### Compliance Monitoring
- Automated schema validation
- Handoff structure verification
- Decision consistency checking
- Artifact completeness validation

### Reporting
- Weekly compliance reports
- Monthly governance audits
- Quarterly full reviews
- Annual external audit (if required)

## Contract Versioning

### Version Format
`<major>.<minor>.<patch>`
- Major: Breaking changes to contract
- Minor: Backward-compatible additions
- Patch: Clarifications and fixes

### Change Process
1. Propose change via governance packet
2. Impact analysis
3. Governance team review
4. Approval and version bump
5. Documentation update
6. Adapter migration plan

## Implementation Requirements

### For Contract
- Single canonical contract file
- Versioned contract definition
- Complete workflow specification
- Decision logic documentation
- Handoff contract template

### For Adapters
- Platform-specific README
- Instruction files
- Configuration templates
- Integration guides
- Compliance documentation

### For Validation
- Automated validation suite
- Compliance test coverage
- Handoff verification
- Decision consistency tests
- Artifact completeness checks

## Exit Criteria

Contract implementation is complete when:
1. ✅ Canonical contract files created
2. ✅ All platform adapters implemented
3. ✅ Validation suite passes 100%
4. ✅ Handoff contract identical across adapters
5. ✅ All adapters documented equally
6. ✅ Governance compliance verified
7. ✅ Chain of custody documented

## Compliance Statement

By implementing pr-prep-specialist, I agree to:
- Follow this canonical contract exactly
- Preserve behavioral consistency across platforms
- Maintain identical handoff contracts
- Submit to governance validation
- Document all deviations
- Participate in compliance monitoring

**This contract is binding and enforceable under TP-GOV-001 governance rules.**
