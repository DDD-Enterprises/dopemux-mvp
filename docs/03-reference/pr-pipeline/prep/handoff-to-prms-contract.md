---
id: HANDOFF_TO_PRMS_CONTRACT
title: Handoff To Prms Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Handoff To Prms Contract (explanation) for dopemux documentation and developer
  workflows.
---
# PR-PREP-SPECIALIST to PR-MERGE-SPECIALIST Handoff Contract

## Purpose

Define the canonical handoff contract between pr-prep-specialist and pr-merge-specialist to ensure consistent, predictable transitions.

## Contract Principles

### 1. Single Handoff Structure
- Identical bundle format across all platforms
- Consistent artifact naming and organization
- Uniform metadata structure

### 2. Complete Provenance
- Full chain of custody documentation
- Parent bundle references
- Timestamp preservation

### 3. Behavioral Guarantees
- Identical handoff regardless of source platform
- Predictable artifact locations
- Consistent validation state

## Handoff Bundle Specification

### Mandatory Structure

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
  "warnings": [<warning_list>],
  "blocking_reasons": [<blocking_reason_list>],
  "chain_of_custody": {
    "parent_bundle_ids": [<parent_bundle_ids>],
    "created_at": "<iso8601_timestamp>",
    "skill_version": "<version>"
  }
}
```

## Field Specifications

### handoff_id (string, required)
- **Format**: `TP-PRPS-<number>-HANDOFF-<sequence>`
- **Example**: `TP-PRPS-008-HANDOFF-001`
- **Purpose**: Unique identifier for handoff bundle

### source_skill (string, required)
- **Value**: `pr-prep-specialist`
- **Purpose**: Identify source skill

### target_skill (string, required)
- **Value**: `pr-merge-specialist`
- **Purpose**: Identify target skill

### run_id (string, required)
- **Format**: `<skill>-<yyyymmdd>-<sequence>`
- **Example**: `pr-prep-20260314-001`
- **Purpose**: Execution identifier

### repo (string, required)
- **Example**: `dopemux-mvp`
- **Purpose**: Repository name

### branch (string, required)
- **Example**: `feat/extraction-wizard-cli`
- **Purpose**: Source branch name

### base_branch (string, required)
- **Example**: `main`
- **Purpose**: Target base branch

### pr_number (integer, required)
- **Example**: `194`
- **Purpose**: Pull request number

### governing_posture (string, required)
- **Values**: `GO_DRAFT_FIRST`, `GO_DIRECT`, `AWAIT_REVIEW`
- **Purpose**: Governance posture for PR

### recommended_next_step (string, required)
- **Values**: `AWAIT_REVIEW`, `MERGE_READY`, `BLOCKED`
- **Purpose**: Recommended action for PRMS

### authoritative_artifacts (array, required)
- **Items**: Exact 7 artifacts in specified order
- **Purpose**: Primary artifacts for PRMS consumption

### supporting_artifacts (array, optional)
- **Items**: Additional context artifacts
- **Purpose**: Supplementary information

### warnings (array, optional)
- **Items**: Warning messages
- **Purpose**: Non-blocking issues

### blocking_reasons (array, optional)
- **Items**: Blocking reason strings
- **Purpose**: Issues preventing merge

### chain_of_custody (object, required)
- **Fields**: parent_bundle_ids, created_at, skill_version
- **Purpose**: Provenance tracking

## Artifact Specifications

### BRANCH_STATE.json
```json
{
  "branch_name": "<branch_name>",
  "base_branch": "<base_branch>",
  "commit_count": <number>,
  "changed_files": [<file_list>],
  "branch_type": "<feature|hotfix|bugfix>",
  "naming_valid": <boolean>,
  "timestamp": "<iso8601_timestamp>"
}
```

### BRANCH_AUDIT_REPORT.json
```json
{
  "open_prs": [<pr_list>],
  "overlapping_files": [<file_list>],
  "conflict_risk": "<low|medium|high>",
  "related_work": [<pr_list>],
  "dependencies": [<pr_list>],
  "timestamp": "<iso8601_timestamp>"
}
```

### CHANGESET_OBLIGATION_REPORT.json
```json
{
  "changelog_required": <boolean>,
  "documentation_required": <boolean>,
  "tests_required": <boolean>,
  "version_bump": "<major|minor|patch|none>",
  "breaking_changes": <boolean>,
  "obligations_valid": <boolean>,
  "timestamp": "<iso8601_timestamp>"
}
```

### PR_DRAFT_PACKAGE.json
```json
{
  "pr_title": "<generated_title>",
  "pr_body": "<generated_body>",
  "template_used": "<template_name>",
  "obligations_included": <boolean>,
  "validation_passed": <boolean>,
  "timestamp": "<iso8601_timestamp>"
}
```

### PR_BODY_RENDERED.md
```markdown
# <PR Title>

## Description
<Generated description>

## Changes
- Change 1
- Change 2

## Obligations
- ✅ Changelog updated
- ✅ Documentation updated
- ✅ Tests added

## Related Work
- #123
- #456
```

### FINAL_PREP_DECISION.json
```json
{
  "workflow_valid": <boolean>,
  "outputs_complete": <boolean>,
  "decisions_consistent": <boolean>,
  "blocking_issues": [<issue_list>],
  "warnings": [<warning_list>],
  "final_decision": "<APPROVE|REJECT|BLOCK>",
  "timestamp": "<iso8601_timestamp>"
}
```

### PR_CREATION_REPORT.json
```json
{
  "governing_posture": "<GO_DRAFT_FIRST|GO_DIRECT|AWAIT_REVIEW>",
  "pr_created": <boolean>,
  "pr_number": <number>,
  "pr_url": "<url>",
  "creation_success": <boolean>,
  "timestamp": "<iso8601_timestamp>"
}
```

## Handoff Validation Rules

### Structure Validation
1. **Field Presence**: All required fields present
2. **Type Correctness**: Fields match specified types
3. **Format Validation**: IDs and timestamps valid
4. **Artifact Completeness**: All 7 artifacts included

### Content Validation
1. **Consistency Check**: Artifacts consistent with each other
2. **Decision Validation**: Final decision justified by artifacts
3. **Obligation Verification**: All obligations addressed
4. **Conflict Assessment**: Risk assessment reasonable

### Provenance Validation
1. **Chain of Custody**: Complete and documented
2. **Parent References**: All parents valid
3. **Timestamp Order**: Temporally consistent
4. **Version Tracking**: Skill version recorded

## Consumption Contract

### PR-MERGE-SPECIALIST Responsibilities
1. **Validate Structure**: Verify handoff bundle format
2. **Check Artifacts**: Confirm all artifacts present
3. **Assess State**: Review governing posture and recommendations
4. **Process PR**: Execute merge workflow
5. **Emit Proof**: Generate merge proof bundles
6. **Update Custody**: Extend chain of custody

### Guarantees to PR-PREP-SPECIALIST
1. **Structure Preservation**: Handoff bundle unchanged
2. **Artifact Integrity**: No modification of authoritative artifacts
3. **Provenance Continuity**: Chain of custody extended
4. **Feedback Loop**: Status updates provided
5. **Error Handling**: Clear error reporting

## Error Handling

### Handoff Failure Modes
1. **Structure Invalid**: Missing required fields
2. **Artifacts Missing**: Incomplete artifact list
3. **Inconsistent State**: Conflicting information
4. **Provenance Broken**: Invalid chain of custody

### Recovery Procedures
1. **Validation Failure**: Return detailed error report
2. **Artifact Missing**: Request specific artifact
3. **State Conflict**: Escalate to governance
4. **Custody Break**: Manual repair required

### Escalation Path
1. **Level 1 - Warning**: Minor format issues
2. **Level 2 - Block**: Missing artifacts
3. **Level 3 - Governance**: Structure violations

## Versioning and Compatibility

### Version Format
`<major>.<minor>.<patch>`
- Major: Breaking changes to structure
- Minor: Backward-compatible additions
- Patch: Clarifications and fixes

### Backward Compatibility
- New fields may be added
- Existing fields may not be removed
- Artifact list may be extended
- Structure must remain stable

### Migration Process
1. **Deprecation Notice**: Announce changes
2. **Grace Period**: Support old format
3. **Migration Window**: Dual support
4. **Cutover**: Full transition

## Implementation Requirements

### For PR-PREP-SPECIALIST
1. Emit identical handoff structure
2. Include all required artifacts
3. Validate before emission
4. Document chain of custody
5. Handle errors gracefully

### For PR-MERGE-SPECIALIST
1. Validate handoff structure
2. Process all artifacts
3. Extend chain of custody
4. Provide feedback
5. Escalate issues appropriately

## Testing and Validation

### Automated Tests
1. **Structure Validation**: JSON Schema validation
2. **Artifact Check**: Completeness verification
3. **Consistency Test**: Cross-artifact validation
4. **Provenance Test**: Chain of custody verification

### Integration Tests
1. **End-to-End Flow**: Full workflow execution
2. **Cross-Platform**: Multiple source platforms
3. **Error Cases**: Failure mode testing
4. **Recovery**: Error handling verification

## Governance Integration

### Compliance Monitoring
1. **Structure Validation**: Automated checks
2. **Artifact Tracking**: Completeness monitoring
3. **Provenance Auditing**: Chain verification
4. **Consumption Tracking**: PRMS usage logging

### Reporting
1. **Handoff Success Rate**: Monthly metrics
2. **Error Trends**: Pattern analysis
3. **Compliance Reports**: Quarterly reviews
4. **Improvement Plans**: Annual updates

## Exit Criteria

Handoff contract implementation complete when:
1. ✅ Canonical structure defined
2. ✅ All adapters emit identical format
3. ✅ Validation suite passes 100%
4. ✅ PRMS consumption verified
5. ✅ Governance compliance confirmed
6. ✅ Chain of custody documented
7. ✅ Error handling implemented

## Implementation Checklist

- [ ] Handoff structure specification
- [ ] Artifact specifications
- [ ] Validation rules
- [ ] Consumption contract
- [ ] Error handling procedures
- [ ] Versioning policy
- [ ] Testing suite
- [ ] Governance integration
- [ ] Documentation complete
- [ ] All adapters compliant

## Compliance Statement

By emitting handoff bundles, pr-prep-specialist agrees to:
- Follow this canonical contract exactly
- Include all required artifacts
- Maintain structure consistency
- Document provenance completely
- Submit to validation
- Participate in governance

By consuming handoff bundles, pr-merge-specialist agrees to:
- Validate structure completely
- Preserve artifact integrity
- Extend chain of custody
- Provide clear feedback
- Escalate issues appropriately
- Participate in governance

**This contract is binding and enforceable under TP-GOV-001 governance rules.**
