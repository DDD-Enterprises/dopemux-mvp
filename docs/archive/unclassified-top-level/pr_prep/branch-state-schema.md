---
id: BRANCH_STATE_SCHEMA
title: Branch State Schema
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Branch State Schema (explanation) for dopemux documentation and developer
  workflows.
---
# Branch State Schema

## Definition
The `BRANCH_STATE.json` object is the canonical state representation for a branch undergoing PR preparation.

## Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "BranchState",
  "type": "object",
  "required": [
    "repo_root",
    "current_branch",
    "base_branch",
    "base_branch_confidence",
    "head_sha",
    "changed_files_total",
    "worktree_state",
    "change_profile",
    "risk_hint",
    "prep_posture"
  ],
  "properties": {
    "repo_root": { "type": "string" },
    "current_branch": { "type": "string" },
    "base_branch": { "type": "string" },
    "base_branch_confidence": {
      "enum": ["HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    },
    "merge_base": { "type": "string" },
    "head_sha": { "type": "string" },
    "base_sha": { "type": "string" },
    "changed_files_total": { "type": "integer" },
    "changed_files_by_category": {
      "type": "object",
      "properties": {
        "code": { "type": "integer" },
        "docs": { "type": "integer" },
        "tests": { "type": "integer" },
        "config": { "type": "integer" },
        "migrations": { "type": "integer" },
        "ci": { "type": "integer" },
        "other": { "type": "integer" }
      }
    },
    "worktree_state": {
      "type": "object",
      "properties": {
        "staged": { "type": "boolean" },
        "unstaged": { "type": "boolean" },
        "untracked": { "type": "boolean" },
        "clean": { "type": "boolean" }
      }
    },
    "change_profile": {
      "enum": [
        "DOCS_ONLY",
        "TEST_ONLY",
        "SMALL_CODE_CHANGE",
        "REFACTOR",
        "CONFIG_OR_INFRA",
        "MIGRATION_OR_SCHEMA",
        "PUBLIC_SURFACE_CHANGE",
        "MIXED_CHANGESET",
        "DIRTY_OR_AMBIGUOUS"
      ]
    },
    "risk_hint": {
      "enum": ["LOW", "MEDIUM", "HIGH", "UNKNOWN"]
    },
    "prep_posture": {
      "enum": ["NORMAL", "CAUTION", "BLOCK_UNTIL_CLEAN", "HIGH_RISK_ESCALATE"]
    },
    "warnings": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```
