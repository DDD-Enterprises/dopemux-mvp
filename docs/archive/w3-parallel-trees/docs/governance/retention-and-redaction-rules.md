---
id: RETENTION_AND_REDACTION_RULES
title: Retention And Redaction Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Retention And Redaction Rules (explanation) for dopemux documentation and
  developer workflows.
---
# Retention and Redaction Rules

## Purpose

Define retention periods and redaction requirements for proof artifacts to prevent junk drawer accumulation while preserving chain of custody.

## Retention Rules

### Proof Bundle Retention

**Active Development (Current Branch)**:
- Retention: Indefinite
- Rationale: Active development requires full provenance
- Location: `proof/<skill>/<phase>/<run_id>/`

**Merged PRs**:
- Retention: 90 days post-merge
- Rationale: Sufficient for audit and rollback
- Location: `proof/<skill>/<phase>/<run_id>/`
- Archive: Compress to `.tar.gz` after 30 days

**Abandoned Branches**:
- Retention: 30 days after abandonment
- Rationale: Short-term debugging only
- Location: `proof/<skill>/<phase>/<run_id>/`
- Action: Delete entirely after retention period

**Governance Artifacts**:
- Retention: Indefinite
- Rationale: Governance decisions are permanent
- Location: `proof/governance/` and `docs/governance/`

### Handoff Bundle Retention

**Successful Handoffs**:
- Retention: Match target skill retention period
- Rationale: Handoff provenance must match downstream usage
- Location: Same as parent bundle

**Failed Handoffs**:
- Retention: 7 days
- Rationale: Short-term debugging only
- Location: Same as parent bundle
- Action: Delete after resolution or timeout

### Manifest Retention

**Run Manifests**:
- Retention: Match parent bundle retention
- Rationale: Manifest is part of bundle provenance
- Location: Same as parent bundle

**Top-Level Index**:
- Retention: Indefinite
- Rationale: Primary discovery mechanism
- Location: `proof/PROOF_INDEX.json`

## Redaction Rules

### Sensitive Data Redaction

**Never Store**:
- API keys
- Passwords
- Personal identifiable information (PII)
- Authentication tokens
- Private keys

**Redact Before Storage**:
- GitHub tokens → `[REDACTED_GITHUB_TOKEN]`
- Repository URLs with credentials → `[REDACTED_URL]`
- Environment variables → `[REDACTED_ENV_VAR]`
- Local file paths → `[REDACTED_PATH]`

### Redaction Process

**Automatic Redaction**:
- Implement in skill output filters
- Pattern-based replacement
- Validation before emission

**Manual Review**:
- Required for first emission of new artifact types
- Spot-check 10% of bundles weekly
- Full audit quarterly

## Archive Rules

### Archive Format
- Format: `.tar.gz`
- Naming: `<bundle_id>-<timestamp>.tar.gz`
- Location: `proof/archive/<skill>/<year>/`

### Archive Process
1. Validate bundle completeness
2. Generate manifest
3. Compress with `tar -czvf`
4. Verify archive integrity
5. Store in archive location
6. Update index with archive reference

### Restore Process
1. Locate archive via index
2. Extract to temporary location
3. Validate against manifest
4. Use for audit/debugging
5. Delete temporary extraction

## Compliance Monitoring

### Retention Compliance Checks
- Weekly scan for expired artifacts
- Automated deletion after retention period
- Log all deletion actions
- Escalate failures to governance team

### Redaction Compliance Checks
- Automated pattern scanning
- Block emission on sensitive data detection
- Manual override requires governance approval
- Audit trail for all redactions

## Enforcement

### Automated Enforcement
- Pre-commit hooks for redaction validation
- CI/CD gates for retention compliance
- Scheduled cleanup jobs

### Manual Enforcement
- Quarterly governance audits
- Incident response for violations
- Corrective action plans

## Chain of Custody Preservation

All retention and redaction operations must:
- Preserve original bundle IDs
- Maintain parent/child relationships
- Document operation in chain of custody
- Update manifests accordingly

## Violation Handling

**Minor Violations**:
- Warning issued
- 7-day remediation period
- Escalation if unresolved

**Major Violations**:
- Immediate block on new emissions
- Governance review required
- Corrective action plan mandatory
- Documentation in conflict ledger

## Audit Requirements

- Weekly: Retention compliance
- Monthly: Redaction effectiveness
- Quarterly: Full governance audit
- Annually: External review (if required)

## Implementation Requirements

1. Add redaction filters to all skill outputs
2. Implement retention cleanup scripts
3. Create archive/restore tooling
4. Add compliance checks to CI/CD
5. Document all processes in skill READMEs
