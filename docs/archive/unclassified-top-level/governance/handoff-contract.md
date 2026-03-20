---
id: HANDOFF_CONTRACT
title: Handoff Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Handoff Contract (explanation) for dopemux documentation and developer workflows.
---
# Handoff Contract

## Purpose

Define the canonical contract for skill-to-skill handoff to ensure consistency and governance compliance.

## Contract Rules

### 1. Handoff Purpose

Handoff bundles serve as:
- **Evidence**: Verifiable record of skill execution
- **Governance**: Input for downstream decisions
- **Truth**: Preserved warnings and blockers
- **Continuation**: Next steps for receiving skill

### 2. Handoff Minimums

Every handoff must include:
- **Source Skill**: Originating skill
- **Target Skill**: Receiving skill
- **Run ID**: Execution identifier
- **Repo/Branch**: Context
- **Governing Posture**: Current posture
- **Recommended Next Step**: Action for receiver
- **Authoritative Artifacts**: Required artifacts
- **Supporting Artifacts**: Contextual artifacts
- **Warnings**: Current warnings
- **Blocking Reasons**: Current blockers
- **Chain of Custody**: Provenance

### 3. When Handoff is Mandatory

Handoff required when:
- Control passes to another skill
- PR creation occurs
- Governance decision required
- High-risk escalation
- Cross-skill dependency

### 4. Chain of Custody

Every handoff must preserve:
- Parent bundle references
- Source skill version
- Creation timestamp
- Downstream references

## Contract Requirements

### Minimal Handoff Bundle

```json
{
  "handoff_id": "string",
  "source_skill": "string",
  "target_skill": "string",
  "run_id": "string",
  "repo": "string",
  "branch": "string",
  "base_branch": "string",
  "governing_posture": "string",
  "recommended_next_step": "string",
  "authoritative_artifacts": "array",
  "supporting_artifacts": "array",
  "warnings": "array",
  "blocking_reasons": "array",
  "chain_of_custody": "object"
}
```

## Field Definitions

### handoff_id (string, required)

Unique identifier for the handoff.

**Format**: `TP-PRPS-<number>-HANDOFF-<sequence>`

**Example**: `TP-PRPS-008-HANDOFF-001`

### source_skill (string, required)

Originating skill name.

**Values**: `pr-prep-specialist`, `pr-merge-specialist`, etc.

### target_skill (string, required)

Receiving skill name.

**Values**: `pr-prep-specialist`, `pr-merge-specialist`, etc.

### run_id (string, required)

Execution identifier.

**Format**: `<skill>-<timestamp>-<sequence>`

**Example**: `pr-prep-20260314-001`

### repo (string, required)

Repository name.

**Example**: `dopemux-mvp`

### branch (string, required)

Branch name.

**Example**: `feat/extraction-wizard-cli`

### base_branch (string, required)

Base branch name.

**Example**: `main`

### governing_posture (string, required)

Current governance posture.

**Values**:
- `GO_DRAFT_FIRST`
- `GO_PACKAGE_ONLY`
- `GO_SUPERVISED_FINAL_CREATION`
- `NO_GO_LIMIT_TO_ARTIFACTS_ONLY`
- `ROLLBACK_TO_HUMAN_PREP`

### recommended_next_step (string, required)

Action for receiving skill.

**Values**:
- `AWAIT_REVIEW`
- `PROCEED_TO_MERGE`
- `ESCALATE_TO_GOVERNANCE`
- `BLOCK_AND_AWAIT_FIX`
- `CREATE_DRAFT_PR`
- `CREATE_FINAL_PR`

### authoritative_artifacts (array, required)

List of authoritative artifacts.

**Items**: Strings (filenames)

**Example**: `["PR_DRAFT_PACKAGE.json", "FINAL_PREP_DECISION.json"]`

### supporting_artifacts (array, optional)

List of supporting artifacts.

**Items**: Strings (filenames)

**Example**: `["PR_BODY_RENDERED.md", "BRANCH_STATE.json"]`

### warnings (array, optional)

Current warnings.

**Items**: Strings

**Example**: `["Changelog missing", "High ambiguity score"]`

### blocking_reasons (array, optional)

Current blockers.

**Items**: Strings

**Example**: `["Dirty worktree", "Missing docs"]`

### chain_of_custody (object, required)

Provenance information.

**Fields**:
- `parent_bundle_ids` (array): Upstream bundle IDs
- `created_at` (string): ISO8601 timestamp
- `skill_version` (string): Skill version

## Validation Rules

### Required Fields

- `handoff_id`
- `source_skill`
- `target_skill`
- `run_id`
- `repo`
- `branch`
- `base_branch`
- `governing_posture`
- `recommended_next_step`
- `authoritative_artifacts`
- `chain_of_custody`

### Type Constraints

- `handoff_id`: string
- `source_skill`: string
- `target_skill`: string
- `run_id`: string
- `repo`: string
- `branch`: string
- `base_branch`: string
- `governing_posture`: enum
- `recommended_next_step`: enum
- `authoritative_artifacts`: array of strings
- `supporting_artifacts`: array of strings
- `warnings`: array of strings
- `blocking_reasons`: array of strings
- `chain_of_custody`: object

### Enum Values

**governing_posture**:
- `GO_DRAFT_FIRST`
- `GO_PACKAGE_ONLY`
- `GO_SUPERVISED_FINAL_CREATION`
- `NO_GO_LIMIT_TO_ARTIFACTS_ONLY`
- `ROLLBACK_TO_HUMAN_PREP`

**recommended_next_step**:
- `AWAIT_REVIEW`
- `PROCEED_TO_MERGE`
- `ESCALATE_TO_GOVERNANCE`
- `BLOCK_AND_AWAIT_FIX`
- `CREATE_DRAFT_PR`
- `CREATE_FINAL_PR`

## Examples

### Minimal Compliant Handoff

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

### Blocked Handoff

```json
{
  "handoff_id": "TP-PRPS-008-HANDOFF-002",
  "source_skill": "pr-prep-specialist",
  "target_skill": "pr-merge-specialist",
  "run_id": "pr-prep-20260314-002",
  "repo": "dopemux-mvp",
  "branch": "feat/extraction-wizard-cli",
  "base_branch": "main",
  "governing_posture": "BLOCKED_DIRTY_WORKTREE",
  "recommended_next_step": "BLOCK_AND_AWAIT_FIX",
  "authoritative_artifacts": [
    "FINAL_PREP_DECISION.json"
  ],
  "supporting_artifacts": [
    "BRANCH_STATE.json",
    "WORKTREE_STATE.json"
  ],
  "warnings": [],
  "blocking_reasons": [
    "Dirty worktree detected",
    "Uncommitted changes present"
  ],
  "chain_of_custody": {
    "parent_bundle_ids": ["TP-PRPS-008-002"],
    "created_at": "2026-03-14T22:00:00Z",
    "skill_version": "1.0.0"
  }
}
```

## Compliance

All handoffs must:
- Follow this contract
- Preserve chain of custody
- Declare authoritative artifacts
- Pass validation

Violations will be flagged and escalated.
