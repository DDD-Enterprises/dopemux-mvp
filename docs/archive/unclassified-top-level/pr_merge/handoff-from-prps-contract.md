---
id: HANDOFF_FROM_PRPS_CONTRACT
title: Handoff From Prps Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Handoff From Prps Contract (explanation) for dopemux documentation and developer
  workflows.
---
# PR-MERGE-SPECIALIST Handoff Contract (from PR-PREP-SPECIALIST)

## Purpose

Define the canonical contract for receiving handoffs from PR-PREP-SPECIALIST to ensure consistent, predictable transitions into the PR-MERGE-SPECIALIST workflow.

## Contract Principles

### 1. Single Handoff Structure
- Identical bundle format expected from all PR-PREP-SPECIALIST instances
- Consistent artifact naming and organization
- Uniform metadata structure

### 2. Complete Provenance
- Full chain of custody documentation required
- Parent bundle references must be valid
- Timestamp continuity must be maintained

### 3. Behavioral Guarantees
- Predictable intake regardless of source platform
- Standardized validation procedures
- Consistent error handling

### 4. Governance Continuity
- Chain of custody extended seamlessly
- All governance requirements preserved
- Proof bundles linked appropriately

## Expected Handoff Bundle Structure

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
- **Validation**: Must match pattern, unique per handoff

### source_skill (string, required)
- **Value**: Must be exactly `pr-prep-specialist`
- **Validation**: Case-sensitive exact match

### target_skill (string, required)
- **Value**: Must be exactly `pr-merge-specialist`
- **Validation**: Case-sensitive exact match

### run_id (string, required)
- **Format**: `<skill>-<yyyymmdd>-<sequence>`
- **Example**: `pr-prep-20260314-001`
- **Validation**: Valid date format, consistent sequencing

### repo (string, required)
- **Example**: `dopemux-mvp`
- **Validation**: Non-empty string, valid repository name

### branch (string, required)
- **Example**: `feat/extraction-wizard-cli`
- **Validation**: Valid Git branch name format

### base_branch (string, required)
- **Example**: `main`
- **Validation**: Valid Git branch name, must exist

### pr_number (integer, required)
- **Example**: `194`
- **Validation**: Positive integer, must correspond to existing PR

### governing_posture (string, required)
- **Values**: `GO_DRAFT_FIRST`, `GO_DIRECT`, `AWAIT_REVIEW`
- **Validation**: Must be one of enumerated values
- **Semantics**: Governance posture recommended by PR-PREP-SPECIALIST

### recommended_next_step (string, required)
- **Values**: `AWAIT_REVIEW`, `MERGE_READY`, `BLOCKED`
- **Validation**: Must be one of enumerated values
- **Semantics**: Recommended action for PR-MERGE-SPECIALIST

### authoritative_artifacts (array, required)
- **Items**: Exact 7 artifacts in specified order
- **Validation**: All must be present and valid
- **Contents**:
  - `BRANCH_STATE.json`
  - `BRANCH_AUDIT_REPORT.json`
  - `CHANGESET_OBLIGATION_REPORT.json`
  - `PR_DRAFT_PACKAGE.json`
  - `PR_BODY_RENDERED.md`
  - `FINAL_PREP_DECISION.json`
  - `PR_CREATION_REPORT.json`

### supporting_artifacts (array, optional)
- **Items**: Additional context artifacts
- **Validation**: If present, must be valid artifacts

### warnings (array, optional)
- **Items**: Warning message strings
- **Validation**: If present, non-empty strings

### blocking_reasons (array, optional)
- **Items**: Blocking reason strings
- **Validation**: If present, non-empty strings

### chain_of_custody (object, required)
- **Fields**: parent_bundle_ids, created_at, skill_version
- **Validation**: All fields required and valid
- **Semantics**: Provenance tracking from PR-PREP-SPECIALIST

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

## Intake Validation Rules

### Structure Validation
1. **Field Presence**: All required fields present
2. **Type Correctness**: Fields match specified types
3. **Format Validation**: IDs and timestamps valid
4. **Artifact Completeness**: All 7 authoritative artifacts included

### Content Validation
1. **Consistency Check**: Artifacts consistent with each other
2. **Decision Validation**: Final decision justified by artifacts
3. **Obligation Verification**: All obligations addressed appropriately
4. **Conflict Assessment**: Risk assessment reasonable and documented

### Provenance Validation
1. **Chain of Custody**: Complete and documented
2. **Parent References**: All parents valid and accessible
3. **Timestamp Order**: Temporally consistent (no future dates)
4. **Version Tracking**: Skill version recorded and valid

## Consumption Contract

### PR-MERGE-SPECIALIST Responsibilities
1. **Validate Structure**: Verify handoff bundle format completely
2. **Check Artifacts**: Confirm all artifacts present and valid
3. **Assess State**: Review governing posture and recommendations
4. **Preserve Provenance**: Extend chain of custody appropriately
5. **Emit Proof**: Generate intake validation proof bundle
6. **Handle Errors**: Escalate according to escalation protocol

### Guarantees to PR-PREP-SPECIALIST
1. **Structure Preservation**: Handoff bundle unchanged during validation
2. **Artifact Integrity**: No modification of authoritative artifacts
3. **Provenance Continuity**: Chain of custody extended seamlessly
4. **Feedback Loop**: Validation results provided
5. **Error Handling**: Clear error reporting with recovery paths
6. **Consistent Behavior**: Identical validation across all contexts

## Error Handling Procedures

### Validation Failure Modes
1. **Structure Invalid**: Missing required fields or invalid types
2. **Artifacts Missing**: Incomplete artifact list
3. **Inconsistent State**: Conflicting information between artifacts
4. **Provenance Broken**: Invalid chain of custody
5. **Content Invalid**: Artifact content doesn't match specifications

### Recovery Procedures
1. **Immediate Response**: Emit detailed validation failure artifact
2. **Notification**: Alert operator with specific issues
3. **Preservation**: Maintain handoff bundle for inspection
4. **Escalation**: Follow escalation protocol (typically Level 2 - BLOCK)
5. **Recovery**: Await corrected handoff from PR-PREP-SPECIALIST

### Specific Error Scenarios

#### Missing Artifacts
**Detection**: Authoritative artifact count < 7
**Response**:
1. List missing artifacts specifically
2. Emit BLOCK escalation
3. Provide recovery procedure
4. Await complete handoff

#### Invalid Chain of Custody
**Detection**: Parent references invalid or missing
**Response**:
1. Freeze intake immediately
2. Emit GOVERNANCE_REVIEW escalation
3. Preserve all state
4. Notify governance team

#### Inconsistent Artifact Data
**Detection**: Conflicting information between artifacts
**Response**:
1. Document specific inconsistencies
2. Emit BLOCK escalation
3. Request clarification from PR-PREP-SPECIALIST
4. Await corrected handoff

## Governance Integration

### Compliance Monitoring
- Automated structure validation on every intake
- Artifact completeness verification
- Chain of custody auditing
- Decision consistency tracking

### Reporting Requirements
- Intake validation metrics
- Error trends and patterns
- Recovery time statistics
- Governance compliance reports

### Audit Trail Requirements
- Complete intake history
- All validation artifacts preserved
- Operator actions logged
- Recovery procedures documented

## Context-Specific Adaptations

### CLI Context
- **Validation Output**: Structured console output
- **Error Handling**: Interactive prompts for recovery
- **Logging**: JSON-formatted validation logs

### API Context
- **Validation Output**: Structured API response
- **Error Handling**: Webhook notifications
- **Logging**: API-accessible validation logs

### Interactive Context
- **Validation Output**: Rich UI validation report
- **Error Handling**: Guided recovery workflow
- **Logging**: User action audit trail

## Validation Gates

### Intake Validation Gate
- ✅ Handoff bundle structure valid
- ✅ All required fields present
- ✅ All artifacts included and valid
- ✅ Chain of custody intact
- ✅ No critical inconsistencies

### Provenance Continuity Gate
- ✅ Parent references valid
- ✅ Timestamps consistent
- ✅ Skill version tracked
- ✅ Governance requirements met

## Implementation Requirements

### For Intake Validation
1. Complete schema validation
2. Artifact presence verification
3. Content consistency checking
4. Provenance auditing
5. Error handling procedures

### For Error Recovery
1. Detailed error reporting
2. Recovery procedure documentation
3. State preservation mechanisms
4. Operator notification
5. Governance escalation paths

### For Governance Integration
1. Compliance monitoring
2. Audit trail preservation
3. Reporting mechanisms
4. Validation metrics
5. Policy enforcement

## Exit Criteria

Handoff contract implementation complete when:
1. ✅ Canonical intake structure defined
2. ✅ Validation procedures implemented
3. ✅ Error handling operational
4. ✅ Governance integration complete
5. ✅ Cross-context consistency verified
6. ✅ All validation gates passing
7. ✅ Recovery procedures documented
8. ✅ Compliance monitoring operational

## Compliance Statement

By consuming handoff bundles, PR-MERGE-SPECIALIST agrees to:
- Validate structure completely and consistently
- Preserve artifact integrity absolutely
- Extend chain of custody appropriately
- Follow escalation protocol precisely
- Provide clear feedback to PR-PREP-SPECIALIST
- Document all intake validations and errors
- Participate in governance compliance monitoring

By emitting handoff bundles, PR-PREP-SPECIALIST agrees to:
- Follow canonical handoff structure exactly
- Include all required artifacts completely
- Maintain structure consistency absolutely
- Document provenance completely
- Submit to intake validation
- Participate in governance compliance

**This contract is binding and enforceable under governance rules.**
