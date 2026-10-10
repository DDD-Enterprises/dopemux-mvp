---
id: ENFORCEMENT_EDIT_RULES
title: Enforcement Edit Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Enforcement Edit Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Enforcement Edit Rules

## Purpose

Define how governance violations are detected, escalated, and remediated through enforcement edits.

## Detection Rules

### Automated Detection

**Schema Validation**:
- Trigger: Bundle emission
- Check: JSON Schema validation
- Action: Block emission on failure
- Log: `proof/governance/validation_failures/<bundle_id>.json`

**Path Compliance**:
- Trigger: File creation in `proof/`
- Check: Canonical path pattern
- Action: Warning + move to correct location
- Log: `proof/governance/path_violations/<timestamp>.json`

**Field Completeness**:
- Trigger: Bundle finalization
- Check: Required fields present
- Action: Block finalization on missing fields
- Log: `proof/governance/field_violations/<bundle_id>.json`

### Manual Detection

**Governance Review**:
- Frequency: Weekly
- Scope: Sample of recent bundles
- Check: Compliance with all rules
- Log: `proof/governance/manual_reviews/<timestamp>.json`

**Incident Response**:
- Trigger: Reported violation
- Process: Immediate investigation
- Log: `proof/governance/incidents/<incident_id>.json`

## Escalation Rules

### Escalation Levels

**Level 1 - Warning**:
- First offense
- Minor violation
- No impact on chain of custody
- Action: Warning + 7-day fix

**Level 2 - Block**:
- Repeat offense
- Moderate violation
- Potential custody impact
- Action: Block new emissions until fixed

**Level 3 - Governance Review**:
- Severe violation
- Custody chain broken
- Security implications
- Action: Full governance review + corrective plan

### Escalation Process

1. **Detection**: Automated or manual
2. **Logging**: Create violation record
3. **Notification**: Alert responsible party
4. **Assessment**: Determine severity level
5. **Action**: Apply appropriate response
6. **Resolution**: Track remediation
7. **Closure**: Document in conflict ledger

## Remediation Rules

### Automated Remediation

**Schema Fixes**:
- Missing fields: Add defaults where safe
- Type mismatches: Coerce if unambiguous
- Pattern violations: Reject with clear error

**Path Normalization**:
- Wrong location: Move to canonical path
- Wrong naming: Rename to canonical pattern
- Update all references in manifests

**Field Completion**:
- Add missing required fields with defaults
- `created_at`: Use current timestamp
- `validation_state`: Set to `NOT_STARTED`
- `chain_of_custody.documented`: Set to `false`

### Manual Remediation

**Governance Approval Required**:
- Changing bundle IDs
- Modifying chain of custody
- Redacting sensitive data post-emission
- Deleting bundles

**Remediation Process**:
1. Create remediation plan
2. Get governance approval
3. Execute changes
4. Validate compliance
5. Update manifests
6. Log in conflict ledger

## Enforcement Edit Types

### Type 1 - Schema Enforcement
```json
{
  "edit_type": "schema_enforcement",
  "bundle_id": "<bundle_id>",
  "violation": "missing_required_field",
  "field": "chain_of_custody",
  "action": "add_default",
  "applied_at": "2026-03-14T23:00:00Z",
  "result": "success"
}
```

### Type 2 - Path Normalization
```json
{
  "edit_type": "path_normalization",
  "bundle_id": "<bundle_id>",
  "old_path": "proof/temp/bundle.json",
  "new_path": "proof/pr_prep/TP-PRPS-008-001/bundle.json",
  "action": "move",
  "applied_at": "2026-03-14T23:00:00Z",
  "result": "success"
}
```

### Type 3 - Field Completion
```json
{
  "edit_type": "field_completion",
  "bundle_id": "<bundle_id>",
  "fields_added": ["created_at", "validation_state"],
  "action": "add_defaults",
  "applied_at": "2026-03-14T23:00:00Z",
  "result": "success"
}
```

### Type 4 - Governance Override
```json
{
  "edit_type": "governance_override",
  "bundle_id": "<bundle_id>",
  "violation": "chain_of_custody_break",
  "action": "manual_repair",
  "approved_by": "governance-team",
  "approved_at": "2026-03-14T23:00:00Z",
  "result": "success",
  "notes": "Repaired broken custody chain"
}
```

## Logging Requirements

### Enforcement Log Structure
```json
{
  "enforcement_id": "ENF-<timestamp>-<sequence>",
  "bundle_id": "<bundle_id>",
  "skill": "<skill_name>",
  "run_id": "<run_id>",
  "violation_type": "<violation_type>",
  "severity": "warning|block|review",
  "detected_at": "<timestamp>",
  "action_taken": "<action>",
  "applied_at": "<timestamp>",
  "result": "success|failure|pending",
  "governance_approval": "required|not_required|granted",
  "notes": "<additional_context>"
}
```

### Log Locations
- Automated enforcement: `proof/governance/enforcement/<year>/<month>/`
- Manual enforcement: `proof/governance/manual_enforcement/<year>/<month>/`
- Escalations: `proof/governance/escalations/<year>/<month>/`

## Conflict Ledger Integration

All enforcement actions must be recorded in the conflict ledger:
- Location: `docs/03-reference/governance/conflict-ledger-2.md`
- Format: Markdown table with enforcement details
- Update frequency: Daily

## Compliance Reporting

### Enforcement Compliance Report
```json
{
  "report_id": "ENF-COMPLIANCE-<timestamp>",
  "period": "<start_date>-<end_date>",
  "total_violations": 0,
  "violations_by_type": {
    "schema": 0,
    "path": 0,
    "field": 0,
    "custody": 0
  },
  "enforcement_actions": 0,
  "success_rate": 100.0,
  "pending_actions": 0,
  "escalations": 0,
  "compliance_status": "FULLY_COMPLIANT"
}
```

## Implementation Requirements

1. **Automated Detection**:
   - Add validation hooks to bundle emission
   - Implement path compliance checks
   - Add field completeness validation

2. **Enforcement Engine**:
   - Schema validation and auto-fix
   - Path normalization
   - Field completion
   - Governance override support

3. **Logging Infrastructure**:
   - Enforcement log generation
   - Conflict ledger integration
   - Compliance reporting

4. **CI/CD Integration**:
   - Pre-commit hooks for detection
   - Build gates for compliance
   - Scheduled enforcement runs

5. **Monitoring**:
   - Dashboard for enforcement status
   - Alerts for severe violations
   - Trend analysis

## Governance Approval Requirements

### Actions Requiring Approval
- Bundle deletion
- Chain of custody modification
- Retention period changes
- Redaction of emitted data
- Major schema changes

### Approval Process
1. Submit request with justification
2. Governance team review
3. Approval or rejection
4. Documentation in conflict ledger
5. Implementation with audit trail

## Audit Requirements

- Daily: Enforcement log review
- Weekly: Compliance report generation
- Monthly: Governance team audit
- Quarterly: Full enforcement review

## Violation Examples and Responses

### Example 1 - Missing Field
**Violation**: Bundle missing `chain_of_custody`
**Detection**: Schema validation
**Action**: Add default with `documented: false`
**Log**: Enforcement log entry
**Result**: Bundle becomes compliant

### Example 2 - Wrong Path
**Violation**: Bundle in `proof/temp/`
**Detection**: Path compliance check
**Action**: Move to canonical location
**Log**: Path normalization entry
**Result**: Bundle in correct location

### Example 3 - Broken Custody Chain
**Violation**: Parent bundle reference invalid
**Detection**: Manual review
**Action**: Governance override to repair
**Log**: Governance override entry
**Result**: Chain restored with documentation

## Enforcement Edit Lifecycle

1. **Detection**: Violation identified
2. **Classification**: Determine type and severity
3. **Action Selection**: Choose appropriate response
4. **Approval**: Get governance approval if needed
5. **Execution**: Apply enforcement edit
6. **Validation**: Verify compliance achieved
7. **Logging**: Record all details
8. **Monitoring**: Track for recurrence

## Success Criteria

- 100% of bundles pass schema validation
- 0 violations in production bundles
- All enforcement actions logged
- Conflict ledger up to date
- Compliance reports show 100% compliance
