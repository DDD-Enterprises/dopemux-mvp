---
id: TP-GOV-001-PROOF-AND-HANDOFF-CONTRACT-HARDENING
title: Tp Gov 001 Proof And Handoff Contract Hardening
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Tp Gov 001 Proof And Handoff Contract Hardening (explanation) for dopemux
  documentation and developer workflows.
---
# TP-GOV-001: Proof and Handoff Contract Hardening

## Summary

Formalize and enforce canonical rules for proof placement, proof structure, handoff semantics, and enforcement edits across all skills.

## Why This Packet Exists

Current proof ecosystem is convention-driven and risks drifting from:
- "we always emit the right bundle"
- into "mostly"
- into "it's in a temp folder somewhere, good luck"

The proof index shows READY_FOR_REVIEW, VERIFIED, and chain_of_custody: DOCUMENTED, indicating mature proof discipline that needs standardization to prevent drift.

## Goals

1. Define one canonical proof directory contract
2. Define one canonical proof bundle contract
3. Define one canonical handoff bundle contract
4. Define manifest/index requirements
5. Define chain-of-custody requirements
6. Define enforcement edits for skill compliance
7. Make proof and handoff behavior consistent across skills

## Non-Goals

1. Redesigning substantive logic of skills
2. Changing governance decisions already made
3. Building UI/dashboard
4. Hiding detail behind "smart" abstraction
5. Inventing alternate proof layouts for different tools

## Deliverables

### Contract Documentation
1. `docs/governance/proof-contract.md` - Proof purpose and minimums
2. `docs/governance/proof-directory-rules.md` - Path and naming rules
3. `docs/governance/proof-bundle-schema.md` - Bundle structure contract
4. `docs/governance/handoff-contract.md` - Handoff requirements
5. `docs/governance/chain-of-custody-rules.md` - Custody requirements
6. `docs/governance/manifest-and-index-rules.md` - Manifest requirements
7. `docs/governance/retention-and-redaction-rules.md` - Retention policies

### Proof Artifacts
8. `proof/governance/PROOF_CONTRACT_REPORT.json` - Contract compliance
9. `proof/governance/HANDOFF_CONTRACT_REPORT.json` - Handoff compliance
10. `proof/governance/PROOF_PATH_NORMALIZATION_REPORT.json` - Path audit
11. `proof/governance/MANIFEST_COMPLIANCE_REPORT.json` - Manifest compliance
12. `proof/governance/HANDOFF_COMPLIANCE_REPORT.json` - Handoff compliance
13. `proof/governance/GOVERNANCE_ENFORCEMENT_EDITS.json` - Required edits
14. `proof/governance/PROOF_AND_HANDOFF_MANIFEST.json` - Complete manifest

## Core Design

### 1. Canonical Proof Root

Every skill writes proof into predictable root:
- `proof/pr_prep/...`
- `proof/pr_merge/...`
- `proof/governance/...`

**Rules**:
- No ad hoc temp directories
- No mystery subfolders
- Deterministic pathing
- Stable naming

### 2. Canonical Run-Level Structure

Each major run emits into stable run path:
- `proof/<skill>/<phase-or-domain>/<run_id>/...`
- Or standardized tranche pattern

**Requirements**:
- Deterministic pathing
- Stable naming
- Easy review order
- No ambiguity about "latest" vs "authoritative"

### 3. Canonical Top-Level Artifacts

Each run emits minimum:
- One primary report
- One manifest
- One warnings/failures artifact (if applicable)
- One handoff bundle (if handing off)
- Optional summary markdown for humans

### 4. Canonical Handoff Bundle

Every cross-skill handoff uses same skeleton:
```json
{
  "handoff_id": "",
  "source_skill": "",
  "target_skill": "",
  "run_id": "",
  "repo": "",
  "branch": "",
  "base_branch": "",
  "pr_number": null,
  "governing_posture": "",
  "recommended_next_step": "",
  "authoritative_artifacts": [],
  "supporting_artifacts": [],
  "warnings": [],
  "blocking_reasons": [],
  "chain_of_custody": {
    "parent_bundle_ids": [],
    "created_at": "",
    "skill_version": ""
  }
}
```

**Purpose**: Prevents downstream skills from re-discovering upstream truth

### 5. Canonical Manifest Requirements

Each bundle includes:
```json
{
  "bundle_id": "",
  "run_id": "",
  "skill": "",
  "status": "",
  "validation_state": "",
  "created_at": "",
  "authoritative_artifacts": [],
  "supporting_artifacts": [],
  "handoff_refs": [],
  "parent_bundle_refs": [],
  "review_order_hint": 0,
  "chain_of_custody": {
    "documented": true,
    "source_version": ""
  }
}
```

### 6. Canonical Index Behavior

Proof index must:
- Enumerate bundles
- Declare review order
- Show status
- Show validation state
- Show chain-of-custody state
- Link bundle roles

## Ordered Steps

### 1. Define Proof Contract

Write normative contract for:
- Proof purpose
- Proof minimums
- Path rules
- Naming rules
- Authoritative artifact rules
- Human vs machine artifact roles

### 2. Define Handoff Contract

Write normative contract for:
- When handoff bundle required
- Required fields
- Allowed next-step values
- How warnings/blockers preserved
- How target skills consume upstream artifacts

### 3. Define Chain-of-Custody Rules

Specify:
- Required metadata
- Parent/child bundle linkage
- Source skill version
- Run identity
- Mutation/append rules
- Reviewability expectations

### 4. Define Manifest/Index Rules

Specify:
- When manifests mandatory
- When top-level index mandatory
- How review order declared
- How "ready for review" represented
- How "verified" represented
- How compliance failures surfaced

### 5. Define Proof Path Normalization

Audit current proof paths and define:
- Canonical path patterns
- Deprecated path patterns
- Migration or alias rules if needed

### 6. Define Enforcement Edits

Identify required skill changes:
- Mandatory manifest emission
- Mandatory handoff bundle emission
- Mandatory warnings/failures artifact
- Mandatory run id and bundle id
- Mandatory authoritative artifact list
- Mandatory source/target skill fields on handoff

### 7. Emit Compliance Reports

Produce:
- Proof path normalization report
- Manifest compliance report
- Handoff compliance report
- Enforcement edits report

## Implementation Requirements

1. Contract is shared, not skill-specific
2. Handoff treated as first-class artifact
3. Every bundle declares what is authoritative
4. Every bundle declares upstream/downstream relationship
5. Deprecated layouts called out explicitly
6. No silent "support everything"
7. Normalize or mark non-compliant
8. Redaction/retention rules prevent junk drawer

## Exit Criteria

Complete when:
- Proof placement formalized
- Proof structure formalized
- Handoff semantics formalized
- Required enforcement edits identified
- Compliance reporting shows skill conformity
- Future skills follow one shared standard

## After TP-GOV-001

Next packet: TP-GOV-002-PROOF-AND-HANDOFF-ENFORCEMENT
- Add CI/CD gates
- Add pre-commit hooks
- Add compliance checks
- Enforce contract automatically
