---
id: CHAIN_OF_CUSTODY_RULES
title: Chain Of Custody Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Chain Of Custody Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Chain of Custody Rules

## Purpose

Define rules for preserving chain of custody across proof artifacts to ensure auditability and governance compliance.

## Rules

### 1. Metadata Requirements

Every proof artifact must include:
- **bundle_id**: Unique identifier
- **run_id**: Execution identifier
- **skill**: Originating skill
- **created_at**: ISO8601 timestamp
- **source_version**: Skill version

### 2. Parent/Child Linkage

Every bundle must declare:
- **parent_bundle_ids**: Upstream bundle references
- **child_bundle_ids**: Downstream bundle references

### 3. Handoff Preservation

Every handoff must preserve:
- Source skill and version
- Target skill
- Run identity
- Governance posture
- Chain of custody metadata

### 4. Review Documentation

Every review must document:
- Reviewer identity
- Review timestamp
- Decision (VERIFY/STOP/ESCALATE/RETRY/OVERRIDE)
- Rationale
- Signature

### 5. Mutation Rules

- No silent mutations
- All changes must be auditable
- Original artifacts preserved
- New versions clearly marked

## Compliance

### Enforcement

- Validate chain of custody on every bundle
- Reject bundles with missing metadata
- Flag bundles with broken chains
- Escalate violations to governance

### Audit

- Generate chain of custody reports
- Verify parent/child linkages
- Confirm handoff preservation
- Validate review documentation

## Examples

### Complete Chain of Custody

```json
{
  "bundle_id": "TP-PRPS-008-001",
  "run_id": "pr-prep-20260314-001",
  "skill": "pr-prep-specialist",
  "created_at": "2026-03-14T22:00:00Z",
  "source_version": "1.0.0",
  "parent_bundle_ids": ["TP-PRPS-007-001"],
  "child_bundle_ids": ["TP-PRPS-009-001"],
  "chain_of_custody": {
    "documented": true,
    "parent_bundle_ids": ["TP-PRPS-007-001"],
    "child_bundle_ids": ["TP-PRPS-009-001"],
    "reviews": [
      {
        "reviewer": "operator-001",
        "timestamp": "2026-03-14T22:30:00Z",
        "decision": "VERIFY",
        "rationale": "All validation gates passed",
        "signature": "op-001"
      }
    ]
  }
}
```

### Broken Chain (Violation)

```json
{
  "bundle_id": "TP-PRPS-008-002",
  "run_id": "pr-prep-20260314-002",
  "skill": "pr-prep-specialist",
  "created_at": "2026-03-14T22:00:00Z",
  "source_version": "1.0.0",
  "parent_bundle_ids": [],  // ❌ Missing parent
  "child_bundle_ids": [],
  "chain_of_custody": {
    "documented": false,  // ❌ Not documented
    "parent_bundle_ids": [],
    "child_bundle_ids": []
  }
}
```

## Policy

### Retention

- Chain of custody: Permanent
- Review records: 1 year
- Violation reports: 90 days

### Access

- Governance: Full access
- Execution: Skill-specific access
- Audit: Read-only access

### Compliance

All artifacts must:
- Preserve chain of custody
- Document reviews
- Pass validation

Violations will be flagged and escalated.
