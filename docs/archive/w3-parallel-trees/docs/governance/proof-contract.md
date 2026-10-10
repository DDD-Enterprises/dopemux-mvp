---
id: PROOF_CONTRACT
title: Proof Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Proof Contract (explanation) for dopemux documentation and developer workflows.
---
# Proof Contract

## Purpose

Establish a canonical contract for proof artifacts across all skills to ensure consistency, auditability, and governance compliance.

## Contract Rules

### 1. Proof Purpose

Proof artifacts serve as:
- **Evidence**: Verifiable record of skill execution
- **Governance**: Input for governance decisions
- **Audit**: Chain of custody for compliance
- **Handoff**: Truthful evidence for downstream skills

### 2. Proof Minimums

Every substantive run must emit:
- **Primary Report**: Main execution results
- **Manifest**: Artifact inventory and metadata
- **Warnings/Blockers Artifact**: If non-empty
- **Handoff Bundle**: If handing off to another skill
- **Summary Markdown**: Optional human-readable summary

### 3. Authoritative vs Supporting Artifacts

**Authoritative**: Required for governance decisions
- Final decisions
- Blockers and warnings
- Validation results
- Handoff bundles

**Supporting**: Contextual evidence
- Audit reports
- Obligation reports
- Draft packages
- Intermediate artifacts

### 4. When Manifest is Mandatory

Manifest required for:
- Substantive skill runs
- Governance review bundles
- Handoff to other skills
- Multi-phase executions

### 5. When Handoff Bundle is Mandatory

Handoff bundle required when:
- Control passes to another skill
- PR creation occurs
- Governance decision required
- High-risk escalation

### 6. Review Order Declaration

Review order must be declared when:
- Multiple bundles require sequential review
- Governance decision depends on order
- Downstream skill needs specific sequence

## Compliance Requirements

### Field Requirements

Every proof bundle must include:
```json
{
  "bundle_id": "<unique_identifier>",
  "run_id": "<execution_identifier>",
  "skill": "<skill_name>",
  "status": "<current_status>",
  "validation_state": "<validation_result>",
  "created_at": "<ISO8601_timestamp>",
  "authoritative_artifacts": ["<list>"],
  "supporting_artifacts": ["<list>"],
  "handoff_refs": ["<list>"],
  "parent_bundle_refs": ["<list>"],
  "review_order_hint": <number>,
  "chain_of_custody": {
    "documented": true,
    "source_version": "<version>"
  }
}
```

### Status Values

- `PLAN_ONLY`: Text-only plan output
- `SPECIFICATION_COMPLETE`: Specification defined
- `IMPLEMENTATION_STARTED`: Implementation in progress
- `IMPLEMENTATION_COMPLETE`: Implementation finished
- `READY_FOR_REVIEW`: Ready for governance review
- `VERIFIED`: Validation passed
- `BLOCKED`: Blocked by dependencies

### Validation States

- `NOT_STARTED`: Validation not begun
- `IN_PROGRESS`: Validation underway
- `PASSED`: All validation gates passed
- `FAILED`: Validation failed
- `PARTIAL`: Some gates passed

## Chain of Custody

### Required Metadata

- `bundle_id`: Unique identifier
- `run_id`: Execution identifier
- `skill`: Originating skill
- `created_at`: ISO8601 timestamp
- `source_version`: Skill version
- `parent_bundle_ids`: Upstream bundle references
- `handoff_refs`: Downstream handoff references

### Provenance Rules

- Every bundle must declare its origin
- Every handoff must preserve chain of custody
- Every review must document decision
- Every modification must be auditable

## Enforcement

### Compliance Checks

- Manifest presence
- Handoff bundle presence (when required)
- Authoritative artifact declaration
- Chain of custody completeness
- Schema compliance

### Violation Handling

- Emit violation report
- Halt execution if critical
- Escalate to governance
- Log in audit trail

## Policy

### Retention

- Governance bundles: Permanent
- Execution bundles: 90 days
- Debug bundles: 30 days
- Temporary bundles: 7 days

### Redaction

- Remove sensitive data before storage
- Mask secrets in artifacts
- Anonymize personal data
- Preserve governance evidence

### Access

- Governance: Full access
- Execution: Skill-specific access
- Debug: Temporary access
- Audit: Read-only access

## Examples

### Minimal Compliant Bundle

```json
{
  "bundle_id": "TP-PRPS-008-001",
  "run_id": "exec-20260314-001",
  "skill": "pr-prep-specialist",
  "status": "READY_FOR_REVIEW",
  "validation_state": "PASSED",
  "created_at": "2026-03-14T22:00:00Z",
  "authoritative_artifacts": [
    "FINAL_PREP_DECISION.json",
    "PR_HANDOFF_BUNDLE.json"
  ],
  "supporting_artifacts": [
    "BRANCH_STATE.json",
    "BRANCH_AUDIT_REPORT.json",
    "CHANGESET_OBLIGATION_REPORT.json"
  ],
  "handoff_refs": [],
  "parent_bundle_refs": [],
  "review_order_hint": 1,
  "chain_of_custody": {
    "documented": true,
    "source_version": "1.0.0"
  }
}
```

### Handoff Bundle

```json
{
  "handoff_id": "TP-PRPS-008-HANDOFF-001",
  "source_skill": "pr-prep-specialist",
  "target_skill": "pr-merge-specialist",
  "run_id": "exec-20260314-001",
  "repo": "dopemux-mvp",
  "branch": "feat/extraction-wizard-cli",
  "base_branch": "main",
  "governing_posture": "GO_DRAFT_FIRST",
  "recommended_next_step": "AWAIT_REVIEW",
  "authoritative_artifacts": [
    "PR_DRAFT_PACKAGE.json",
    "FINAL_PREP_DECISION.json"
  ],
  "supporting_artifacts": [
    "PR_BODY_RENDERED.md",
    "BRANCH_STATE.json"
  ],
  "warnings": ["Changelog missing"],
  "blocking_reasons": [],
  "chain_of_custody": {
    "parent_bundle_ids": ["TP-PRPS-008-001"],
    "created_at": "2026-03-14T22:00:00Z",
    "skill_version": "1.0.0"
  }
}
```

## Compliance

All skills must:
- Follow this contract
- Emit required artifacts
- Declare authoritative artifacts
- Preserve chain of custody
- Pass compliance checks

Violations will be flagged and escalated.
