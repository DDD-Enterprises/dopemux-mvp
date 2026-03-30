---
id: EVIDENCE_PACK_MODEL
title: Evidence Pack Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Evidence Pack Model (explanation) for dopemux documentation and developer
  workflows.
---
# Evidence Pack Model

## Overview
The Arbitration Evidence Bundle is a canonical JSON object that reconstructs the full change context for high-risk integrations.

## Schema Structure

### 1. Identity and Lineage
- `merge_base_sha`: Common ancestor.
- `ours_sha`: Head of target branch.
- `theirs_sha`: Head of PR branch.

### 2. Change Surfaces
- `ours_files`: Files changed on target.
- `theirs_files`: Files changed on PR.
- `overlap_map`: Shared files and symbols.

### 3. Code Context (Excerpts)
- `hunks`: List of conflicting or overlapping regions.
- `excerpt`: Bounded surrounding text (default +/- 10 lines).
- `symbols`: Names of functions/classes touched in the hunk.

### 4. Governance and Enforcement
- `readiness`: Result from `READINESS_DECISION.json`.
- `feedback`: Categorized items from `FEEDBACK_INGEST_SNAPSHOT.json`.
- `verification`: Status from `VERIFICATION_EXECUTION_REPORT.json`.

## Constraints
- **Provenanced**: Every section must cite its source (Git, GraphQL, or Artifact).
- **Bounded**: Excerpts must be truncated according to `CONTEXT_BOUNDS.md`.
- **Deterministic**: Stable sorting for all lists.
