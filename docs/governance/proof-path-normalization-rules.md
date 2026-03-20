---
id: PROOF_PATH_NORMALIZATION_RULES
title: Proof Path Normalization Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Proof Path Normalization Rules (explanation) for dopemux documentation and
  developer workflows.
---
# Proof Path Normalization Rules

## Purpose

Define canonical path patterns for proof artifacts to ensure deterministic location, easy discovery, and prevent ad-hoc folder proliferation.

## Canonical Path Structure

### Root Structure
```
proof/
├── pr_prep/
│   ├── <phase>/
│   │   ├── <run_id>/
│   │   │   ├── <bundle_id>.json
│   │   │   ├── <bundle_id>_MANIFEST.json
│   │   │   ├── <bundle_id>_HANDOFF.json
│   │   │   └── ...
│   │   └── ...
│   └── ...
├── pr_merge/
│   ├── <phase>/
│   │   ├── <run_id>/
│   │   │   ├── <bundle_id>.json
│   │   │   ├── <bundle_id>_MANIFEST.json
│   │   │   └── ...
│   │   └── ...
│   └── ...
├── governance/
│   ├── <bundle_type>/
│   │   ├── <bundle_id>.json
│   │   └── ...
│   └── ...
└── PROOF_INDEX.json
```

## Path Component Rules

### Skill Root
- **Pattern**: `proof/<skill>/`
- **Values**: `pr_prep`, `pr_merge`, `governance`
- **Rule**: One root per skill, no exceptions

### Phase/Domain
- **Pattern**: `proof/<skill>/<phase>/`
- **Examples**:
  - `pr_prep/TP-PRPS-008/` (TP-based)
  - `pr_prep/feature-branch/` (feature-based)
  - `pr_merge/PR-194/` (PR-based)
  - `governance/compliance/` (purpose-based)

### Run Identifier
- **Pattern**: `proof/<skill>/<phase>/<run_id>/`
- **Format**: `<skill>-<yyyymmdd>-<sequence>`
- **Examples**:
  - `pr_prep-20260314-001`
  - `pr_merge-20260314-001`
  - `gov-20260314-001`

### Bundle Filename
- **Pattern**: `<bundle_id>.json` or `<bundle_id>_<type>.json`
- **Examples**:
  - `TP-PRPS-008-001.json` (primary bundle)
  - `TP-PRPS-008-001_MANIFEST.json` (manifest)
  - `TP-PRPS-008-001_HANDOFF.json` (handoff)

## Normalization Rules

### Rule 1: No Ad-Hoc Folders
- ❌ `proof/temp/`
- ❌ `proof/misc/`
- ❌ `proof/debug/`
- ✅ Use canonical structure only

### Rule 2: Deterministic Naming
- ❌ `proof/pr_prep/my_run/`
- ❌ `proof/pr_prep/latest/`
- ✅ `proof/pr_prep/TP-PRPS-008/pr_prep-20260314-001/`

### Rule 3: Stable Run IDs
- ❌ `proof/pr_prep/TP-PRPS-008/run1/`
- ❌ `proof/pr_prep/TP-PRPS-008/current/`
- ✅ `proof/pr_prep/TP-PRPS-008/pr_prep-20260314-001/`

### Rule 4: Bundle Type Suffixes
- ❌ `manifest_TP-PRPS-008-001.json`
- ❌ `TP-PRPS-008-001_manifest_file.json`
- ✅ `TP-PRPS-008-001_MANIFEST.json`

## Path Validation Rules

### Automated Validation
1. **Skill Root Check**: Must be `pr_prep`, `pr_merge`, or `governance`
2. **Phase Check**: Must follow naming conventions
3. **Run ID Check**: Must match `<skill>-<yyyymmdd>-<sequence>`
4. **Filename Check**: Must match bundle ID patterns
5. **Depth Check**: Maximum 4 levels deep

### Validation Process
```
1. Parse path components
2. Validate skill root
3. Validate phase naming
4. Validate run ID format
5. Validate filename pattern
6. Check for prohibited folders
7. Approve or reject
```

## Migration Rules

### Legacy Path Migration
1. **Identify**: Find non-canonical paths
2. **Map**: Determine canonical equivalent
3. **Move**: Relocate to canonical path
4. **Update**: Fix all references
5. **Log**: Record migration in governance log
6. **Verify**: Confirm no broken references

### Migration Examples

**Example 1: Ad-Hoc Folder**
- Old: `proof/temp/debug_run.json`
- New: `proof/pr_prep/debug/pr_prep-20260314-001/TP-PRPS-DEBUG-001.json`

**Example 2: Poor Naming**
- Old: `proof/pr_prep/my_feature/bundle.json`
- New: `proof/pr_prep/feature-x/pr_prep-20260314-001/TP-PRPS-FEAT-001.json`

**Example 3: Missing Run ID**
- Old: `proof/pr_merge/PR-194/bundle.json`
- New: `proof/pr_merge/PR-194/pr_merge-20260314-001/TP-PRPS-PR194-001.json`

## Enforcement Rules

### Automated Enforcement
- **Pre-commit Hook**: Check all new proof files
- **CI/CD Gate**: Block on path violations
- **Scheduled Scan**: Weekly path compliance check
- **Auto-Correct**: Move files to canonical paths when safe

### Manual Enforcement
- **Governance Review**: Monthly path audit
- **Migration Plans**: For complex cases
- **Override**: Governance approval required

## Path Compliance Reporting

### Path Compliance Report Structure
```json
{
  "report_id": "PATH-COMPLIANCE-<timestamp>",
  "scan_date": "<timestamp>",
  "total_paths": 100,
  "compliant_paths": 95,
  "non_compliant_paths": 5,
  "compliance_rate": 95.0,
  "violations_by_type": {
    "wrong_skill_root": 0,
    "invalid_phase_name": 2,
    "bad_run_id_format": 1,
    "prohibited_folder": 2,
    "excessive_depth": 0
  },
  "migrations_performed": 3,
  "migrations_pending": 2,
  "compliance_status": "PARTIAL"
}
```

## Index Integration

### Proof Index Requirements
- Must enumerate all canonical paths
- Must exclude non-canonical paths
- Must show path compliance status
- Must link to migration reports

### Index Entry Structure
```json
{
  "bundle_id": "<bundle_id>",
  "path": "<canonical_path>",
  "path_compliant": true,
  "migration_history": [
    {
      "from": "<old_path>",
      "to": "<new_path>",
      "migrated_at": "<timestamp>",
      "reason": "<migration_reason>"
    }
  ]
}
```

## Implementation Requirements

1. **Path Validator**:
   - Implement canonical path checking
   - Add to pre-commit hooks
   - Integrate with CI/CD

2. **Migration Tool**:
   - Automated path normalization
   - Reference updating
   - Governance logging

3. **Compliance Scanner**:
   - Weekly path compliance checks
   - Report generation
   - Auto-correct where safe

4. **Documentation**:
   - Update skill READMEs
   - Add path examples
   - Document migration process

## Success Criteria

- 100% of new bundles use canonical paths
- 0 ad-hoc folders created
- All legacy paths migrated or documented
- Path compliance rate ≥ 95%
- Migration process documented and tested

## Examples

### Compliant Path Examples
```
✅ proof/pr_prep/TP-PRPS-008/pr_prep-20260314-001/TP-PRPS-008-001.json
✅ proof/pr_merge/PR-194/pr_merge-20260314-001/TP-PRPS-PR194-001.json
✅ proof/governance/compliance/gov-20260314-001/TP-PRPS-GOV-001-001.json
✅ proof/pr_prep/feature-x/pr_prep-20260314-001/TP-PRPS-FEAT-001_MANIFEST.json
```

### Non-Compliant Path Examples
```
❌ proof/temp/debug.json
❌ proof/pr_prep/latest/bundle.json
❌ proof/misc/stuff/TP-PRPS-008.json
❌ proof/pr_prep/TP-PRPS-008/run1/bundle.json
❌ proof/pr_merge/PR-194/current/result.json
```

## Governance Integration

- Path violations logged in conflict ledger
- Migration actions require governance approval
- Compliance reports part of governance reviews
- Path rules enforced through standard governance processes

## Audit Requirements

- Weekly: Path compliance scan
- Monthly: Migration status review
- Quarterly: Full path audit
- Annually: Path structure review and optimization

## Future Evolution

Path rules may evolve through:
- Governance decision (documented in conflict ledger)
- New skill requirements
- Tooling improvements
- All changes must maintain backward compatibility
