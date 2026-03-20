---
id: PROOF_DIRECTORY_RULES
title: Proof Directory Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Proof Directory Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Proof Directory Rules

## Purpose

Establish canonical directory structure for proof artifacts to ensure consistency and easy discovery.

## Directory Structure

### Root

```
proof/<skill>/<domain_or_tp>/<run_id>/...
```

### Examples

```
proof/pr_prep/TP-PRPS-000/<run_id>/...
proof/pr_prep/TP-PRPS-000A/<run_id>/...
proof/pr_prep/TP-PRPS-008/<run_id>/...
proof/pr_merge/<domain>/<run_id>/...
proof/governance/<domain>/<run_id>/...
```

## Path Rules

### Canonical Patterns

**Preferred**:
- `proof/<skill>/TP-PRPS-<number>/<run_id>/...`
- `proof/<skill>/<domain>/<run_id>/...`

**Tolerated (Deprecated)**:
- `proof/<skill>/<phase>/<run_id>/...`
- `proof/<skill>/<tranche>/<run_id>/...`

**Non-Compliant**:
- `proof/<skill>/temp/...`
- `proof/<skill>/misc/...`
- `proof/<skill>/ad-hoc/...`

## Naming Rules

### Bundle Files

**Pattern**: `TP-PRPS-<NUMBER>-<PURPOSE>-BUNDLE.json`

**Examples**:
- `TP-PRPS-000-SPECIFICATION-BUNDLE.json`
- `TP-PRPS-008-MASTER-COMPREHENSIVE-BUNDLE.json`
- `TP-PRPS-000A-VIBE-CHECKPOINT-VALIDATION.json`

### Manifest Files

**Pattern**: `TP-PRPS-<NUMBER>-<PURPOSE>-MANIFEST.json`

**Examples**:
- `TP-PRPS-000-SPECIFICATION-MANIFEST.json`
- `TP-PRPS-000A-VIBE-GUARDRAIL-MANIFEST.json`

### Index Files

**Pattern**: `PROOF_BUNDLE_INDEX.json`

**Location**: `proof/<skill>/PROOF_BUNDLE_INDEX.json`

## Run ID Rules

### Format

**Pattern**: `<skill>-<timestamp>-<sequence>`

**Examples**:
- `pr-prep-20260314-001`
- `pr-merge-20260314-001`
- `governance-20260314-001`

### Requirements

- Unique per skill
- Sortable by timestamp
- Predictable sequence

## Compliance

### Enforcement

- Paths must follow canonical patterns
- Non-canonical paths must be reported
- Deprecated paths must be migrated
- Non-compliant paths must be rejected

### Audit

- Generate path normalization report
- Identify canonical paths
- Flag deprecated paths
- Reject non-compliant paths

## Examples

### Canonical Structure

```
proof/pr_prep/
├── PROOF_BUNDLE_INDEX.json
├── TP-PRPS-000/
│   ├── TP-PRPS-000-SPECIFICATION-BUNDLE.json
│   └── TP-PRPS-000-SPECIFICATION-MANIFEST.json
├── TP-PRPS-000A/
│   ├── TP-PRPS-000A-VIBE-CHECKPOINT-VALIDATION.json
│   └── TP-PRPS-000A-VIBE-GUARDRAIL-MANIFEST.json
└── TP-PRPS-008/
    ├── TP-PRPS-008-MASTER-COMPREHENSIVE-BUNDLE.json
    └── TP-PRPS-008-LIVE-PILOT-COMPREHENSIVE-BUNDLE.json
```

### Non-Compliant Structure

```
proof/pr_prep/
├── PROOF_BUNDLE_INDEX.json
├── temp/
│   └── random-bundle.json  ❌ Non-compliant
└── misc/
    └── another-bundle.json  ❌ Non-compliant
```

## Migration

### From Deprecated to Canonical

1. **Identify**: Find deprecated paths
2. **Report**: Generate normalization report
3. **Move**: Relocate to canonical paths
4. **Update**: Fix references
5. **Verify**: Confirm compliance

### Automation

- Pre-commit hooks
- CI/CD validation
- Linter rules
- Compliance checks

## Policy

### Retention

- Canonical paths: Permanent
- Deprecated paths: 30 days
- Non-compliant paths: Reject immediately

### Access

- Read: All team members
- Write: Skill maintainers
- Delete: Governance only

## Compliance

All paths must:
- Follow canonical patterns
- Be auditable
- Be predictable
- Be documented

Violations will be flagged and escalated.
