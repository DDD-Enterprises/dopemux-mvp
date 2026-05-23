---
id: PROOF_BUNDLE_SCHEMA
title: Proof Bundle Schema
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Proof Bundle Schema (explanation) for dopemux documentation and developer
  workflows.
---
# Proof Bundle Schema

## Purpose

Define the canonical schema for proof bundles to ensure consistency and validation.

## Schema Requirements

### Minimal Bundle

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

## Field Definitions

### bundle_id (string, required)

Unique identifier for the bundle.

**Format**: `TP-PRPS-<number>-<purpose>-<sequence>`

**Example**: `TP-PRPS-008-MASTER-001`

### run_id (string, required)

Execution identifier.

**Format**: `<skill>-<timestamp>-<sequence>`

**Example**: `pr-prep-20260314-001`

### skill (string, required)

Name of the skill that generated the bundle.

**Values**: `pr-prep-specialist`, `pr-merge-specialist`, `governance`, etc.

### status (string, required)

Current status of the bundle.

**Values**:
- `PLAN_ONLY`
- `SPECIFICATION_COMPLETE`
- `IMPLEMENTATION_STARTED`
- `IMPLEMENTATION_COMPLETE`
- `READY_FOR_REVIEW`
- `VERIFIED`
- `BLOCKED`

### validation_state (string, required)

Validation result.

**Values**:
- `NOT_STARTED`
- `IN_PROGRESS`
- `PASSED`
- `FAILED`
- `PARTIAL`

### created_at (string, required)

ISO8601 timestamp of creation.

**Format**: `YYYY-MM-DDTHH:MM:SSZ`

**Example**: `2026-03-14T22:00:00Z`

### authoritative_artifacts (array, required)

List of authoritative artifacts.

**Items**: Strings (filenames)

**Example**: `["FINAL_PREP_DECISION.json", "PR_HANDOFF_BUNDLE.json"]`

### supporting_artifacts (array, optional)

List of supporting artifacts.

**Items**: Strings (filenames)

**Example**: `["BRANCH_STATE.json", "BRANCH_AUDIT_REPORT.json"]`

### handoff_refs (array, optional)

References to handoff bundles.

**Items**: Strings (bundle IDs)

**Example**: `["TP-PRPS-008-HANDOFF-001"]`

### parent_bundle_refs (array, optional)

References to parent bundles.

**Items**: Strings (bundle IDs)

**Example**: `["TP-PRPS-008-001"]`

### review_order_hint (integer, optional)

Suggested review order.

**Range**: `0` to `N`

**Default**: `0`

### chain_of_custody (object, required)

Provenance information.

**Fields**:
- `documented` (boolean): Whether chain is documented
- `source_version` (string): Skill version
- `parent_bundle_ids` (array): Upstream bundle IDs
- `created_at` (string): ISO8601 timestamp

## Validation Rules

### Required Fields

- `bundle_id`
- `run_id`
- `skill`
- `status`
- `validation_state`
- `created_at`
- `authoritative_artifacts`
- `chain_of_custody`

### Type Constraints

- `bundle_id`: string
- `run_id`: string
- `skill`: string
- `status`: enum
- `validation_state`: enum
- `created_at`: ISO8601 string
- `authoritative_artifacts`: array of strings
- `supporting_artifacts`: array of strings
- `handoff_refs`: array of strings
- `parent_bundle_refs`: array of strings
- `review_order_hint`: integer
- `chain_of_custody`: object

### Enum Values

**status**:
- `PLAN_ONLY`
- `SPECIFICATION_COMPLETE`
- `IMPLEMENTATION_STARTED`
- `IMPLEMENTATION_COMPLETE`
- `READY_FOR_REVIEW`
- `VERIFIED`
- `BLOCKED`

**validation_state**:
- `NOT_STARTED`
- `IN_PROGRESS`
- `PASSED`
- `FAILED`
- `PARTIAL`

## Examples

### Minimal Compliant Bundle

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
    "source_version": "1.0.0",
    "parent_bundle_ids": [],
    "created_at": "2026-03-14T22:00:00Z"
  }
}
```

### Handoff Bundle

```json
{
  "handoff_id": "TP-PRPS-008-HANDOFF-001",
  "source_skill": "pr-prep-specialist",
  "target_skill": "pr-merge-specialist",
  "run_id": "pr-prep-20260314-001",
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

All bundles must:
- Follow this schema
- Pass validation
- Declare authoritative artifacts
- Preserve chain of custody

Violations will be flagged and escalated.
