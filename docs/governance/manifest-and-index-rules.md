---
id: MANIFEST_AND_INDEX_RULES
title: Manifest And Index Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Manifest And Index Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Manifest and Index Rules

## Purpose

Define rules for manifests and indexes to ensure consistency and governance compliance.

## Manifest Rules

### 1. Manifest Purpose

Manifests serve as:
- **Inventory**: List of artifacts
- **Metadata**: Artifact properties
- **Governance**: Review readiness
- **Compliance**: Validation state

### 2. When Manifest is Required

Manifest required for:
- Substantive skill runs
- Governance review bundles
- Handoff to other skills
- Multi-phase executions

### 3. Manifest Fields

```json
{
  "bundle_id": "string",
  "run_id": "string",
  "skill": "string",
  "status": "string",
  "validation_state": "string",
  "created_at": "string",
  "authoritative_artifacts": "array",
  "supporting_artifacts": "array",
  "handoff_refs": "array",
  "parent_bundle_refs": "array",
  "review_order_hint": "integer",
  "chain_of_custody": "object"
}
```

### 4. Review Order

**review_order_hint**: Suggested review sequence

- `0`: Default (no specific order)
- `1`: First
- `2`: Second
- `...`: Sequential

### 5. Compliance

- Manifest must be present
- Manifest must be valid JSON
- Manifest must match actual artifacts
- Manifest must declare authoritative artifacts

## Index Rules

### 1. Index Purpose

Indexes serve as:
- **Discovery**: Find bundles
- **Navigation**: Review order
- **Governance**: Decision input
- **Compliance**: Validation state

### 2. Index Structure

```json
{
  "proof_bundle_index": {
    "metadata": {
      "generated": "ISO8601",
      "workstream": "string",
      "status": "string",
      "total_bundles": "integer",
      "organization": "string"
    },
    "bundles": [
      {
        "id": "string",
        "title": "string",
        "location": "string",
        "size": "string",
        "type": "string",
        "contents": "array",
        "purpose": "string",
        "status": "string"
      }
    ],
    "quick_access": {
      "governance_review": "string",
      "live_pilot": "string",
      "multi_tool_architecture": "string",
      "vibe_checkpoint_validation": "string",
      "vibe_guardrail_manifest": "string"
    },
    "usage": {
      "governance_review": "string",
      "detailed_pilot": "string",
      "architecture": "string",
      "vibe_validation": "string",
      "vibe_manifest": "string",
      "all_proof": "string"
    },
    "organization": {
      "pattern": "string",
      "structure": "string",
      "compliance": "string",
      "benefits": "string"
    },
    "status": {
      "generation": "string",
      "validation": "string",
      "chain_of_custody": "string",
      "ready_for_review": "string",
      "organization": "string"
    }
  }
}
```

### 3. Index Requirements

- One index per skill
- Index must be at skill root
- Index must list all bundles
- Index must declare review order

### 4. Review Order

**review_order_hint** in index:
- `1`: First to review
- `2`: Second to review
- `...`: Sequential

### 5. Compliance

- Index must be present
- Index must be valid JSON
- Index must list all bundles
- Index must declare review order

## Examples

### Minimal Manifest

```json
{
  "bundle_id": "TP-PRPS-008-001",
  "run_id": "pr-prep-20260314-001",
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
    "BRANCH_AUDIT_REPORT.json"
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

### Complete Index

```json
{
  "proof_bundle_index": {
    "metadata": {
      "generated": "2026-03-14T22:00:00Z",
      "workstream": "pr-prep-specialist",
      "status": "READY_FOR_REVIEW",
      "total_bundles": 5,
      "organization": "ONE_DIR_PER_TP"
    },
    "bundles": [
      {
        "id": "TP-PRPS-008-000-MASTER",
        "title": "Master Comprehensive Bundle",
        "location": "proof/pr_prep/TP-PRPS-008/TP-PRPS-008-000-MASTER-COMPREHENSIVE-BUNDLE.json",
        "size": "5.2KB",
        "type": "COMPREHENSIVE",
        "contents": [
          "Live pilot results (TP-PRPS-008)",
          "Multi-tool architecture (TP-PRPS-000)",
          "Governance inputs",
          "Verification checklist",
          "Complete artifact inventory"
        ],
        "purpose": "Single JSON with everything for governance review",
        "status": "READY"
      }
    ],
    "quick_access": {
      "governance_review": "proof/pr_prep/TP-PRPS-008/TP-PRPS-008-000-MASTER-COMPREHENSIVE-BUNDLE.json",
      "live_pilot": "proof/pr_prep/TP-PRPS-008/TP-PRPS-008-LIVE-PILOT-COMPREHENSIVE-BUNDLE.json",
      "multi_tool_architecture": "proof/pr_prep/TP-PRPS-000/TP-PRPS-000-SPECIFICATION-BUNDLE.json",
      "vibe_checkpoint_validation": "proof/pr_prep/TP-PRPS-000A/TP-PRPS-000A-VIBE-CHECKPOINT-VALIDATION.json",
      "vibe_guardrail_manifest": "proof/pr_prep/TP-PRPS-000A/TP-PRPS-000A-VIBE-GUARDRAIL-MANIFEST.json"
    },
    "usage": {
      "governance_review": "Start with MASTER bundle for complete overview",
      "detailed_pilot": "Use LIVE_PILOT bundle for execution details",
      "architecture": "Use MULTI_TOOL bundle for specification",
      "vibe_validation": "Use VIBE_CHECKPOINT bundle for Vibe-specific proof",
      "vibe_manifest": "Use VIBE_GUARDRAIL bundle for implementation details",
      "all_proof": "All bundles are self-contained single JSON files"
    },
    "organization": {
      "pattern": "ONE_DIR_PER_TP",
      "structure": "proof/pr_prep/TP-PRPS-<NUMBER>/<bundle_files>",
      "compliance": "FULL",
      "benefits": "Easy to find, consistent naming, no drift"
    },
    "status": {
      "generation": "COMPLETE",
      "validation": "VERIFIED",
      "chain_of_custody": "DOCUMENTED",
      "ready_for_review": "YES",
      "organization": "ONE_DIR_PER_TP"
    }
  }
}
```

## Compliance

All manifests and indexes must:
- Follow this schema
- Pass validation
- Declare authoritative artifacts
- Preserve chain of custody

Violations will be flagged and escalated.
