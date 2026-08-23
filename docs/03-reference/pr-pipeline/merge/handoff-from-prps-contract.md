---
id: HANDOFF_FROM_PRPS_CONTRACT
title: Handoff From Prps Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Handoff From Prps Contract (explanation) for dopemux documentation and developer
  workflows.
---
# PR-MERGE-SPECIALIST Handoff Contract (from PR-PREP-SPECIALIST)

## Purpose

Define the canonical contract for receiving handoffs from PR-PREP-SPECIALIST to ensure consistent, predictable transitions into the PR-MERGE-SPECIALIST workflow.

This is the receiving side of
[`../prep/operator-contract.md`](../prep/operator-contract.md) §9 (Handoff V2). It
consumes the `schema_version: "2.0.0"` bundle, not the legacy fixed
seven-artifact / `TP-PRPS-<n>-HANDOFF-<seq>` bundle this file previously
described.

Note: the actual wired `pr-merge-specialist` implementation
(`src/dopemux_pr_merge_specialist/**`) does not consume this document or any
field defined here — confirmed by direct grep, zero hits for `source_skill`,
`handoff_id`, or PRPS-specific tokens in that package. This is reference
documentation describing the intended contract, not a code adapter.

## Contract Principles

### 1. Single Handoff Structure
- Identical bundle format expected from all PR-PREP-SPECIALIST instances
- No fixed artifact count — `authoritative_artifacts` and `supporting_artifacts` reflect whatever the run actually produced
- Uniform metadata structure

### 2. Complete Provenance
- Full chain of custody documentation required
- Parent bundle references must be valid
- Timestamp continuity must be maintained

### 3. Behavioral Guarantees
- Predictable intake regardless of source platform
- Standardized validation procedures
- Consistent error handling

### 4. Governance Continuity
- Chain of custody extended seamlessly
- All governance requirements preserved
- Proof bundles linked appropriately

## Expected Handoff Bundle Structure

### Mandatory Structure

```json
{
  "schema_version": "2.0.0",
  "handoff_id": "<id>",
  "source_skill": "pr-prep-specialist",
  "target_skill": "pr-merge-specialist",
  "run_id": "<run-id>",
  "repo": "DDD-Enterprises/dopemux-mvp",
  "branch": "<branch>",
  "base_branch": "main",
  "governing_posture": "<prep-state>",
  "recommended_next_step": "<action>",
  "task_packet": {
    "id": "<packet-id>",
    "path": "<path-or-null>"
  },
  "risk_lane": "L0|L1|L2|L3",
  "heads": {
    "live_main": "<sha>",
    "merge_base": "<sha>",
    "content_head": "<sha-or-null>",
    "proof_head": "<sha-or-null>",
    "current_pr_head": "<sha-or-null>"
  },
  "pr": {
    "number": "<integer-or-null>",
    "state": "<state-or-null>",
    "draft": "<boolean-or-null>"
  },
  "scope": {
    "allowlist_status": "PASS|FAIL|UNKNOWN|NOT_RUN",
    "changed_files_artifact": "<path-or-null>"
  },
  "drift": {
    "classification": "IDENTICAL|SUBSET|SUPERSET|COMPATIBLE|CONFLICTING|UNKNOWN",
    "blocking": "<boolean>"
  },
  "validation": {
    "pre_push": "<status>",
    "focused_tests": "<status>",
    "relevant_suite": "<status>",
    "precommit": "<status>",
    "secret_scan": "<status>"
  },
  "audit": {
    "required": "<boolean>",
    "content_head": "<sha-or-null>",
    "verdict": "PASS|PASS_WITH_RISKS|FAIL|NEEDS_SUPERVISOR|SKIPPED|NOT_REQUIRED|NOT_RUN"
  },
  "proof": {
    "status": "<status>",
    "path": "<path-or-null>"
  },
  "ci": {
    "status": "<status>"
  },
  "pr_steward": {
    "status": "READY|NOT_READY|NEEDS_IMPLEMENTER|NEEDS_SUPERVISOR|BLOCKED|NOT_RUN",
    "head_sha": "<sha-or-null>",
    "merge_readiness_path": "<path-or-null>"
  },
  "authoritative_artifacts": [],
  "supporting_artifacts": [],
  "warnings": [],
  "blocking_reasons": [],
  "unknowns": [],
  "operator_authority": {
    "merge": false,
    "close_pr": false,
    "mark_ready": false,
    "force_push": false,
    "delete_branch": false
  },
  "chain_of_custody": {
    "parent_bundle_ids": [],
    "created_at": "<iso8601>",
    "skill_version": "2.0.0"
  }
}
```

## Field Specifications

### schema_version (string, required)
- **Value**: `2.0.0`
- **Validation**: Must match; a mismatched major version is a structure-invalid intake failure.

### handoff_id (string, required)
- **Purpose**: Unique identifier for the handoff bundle. No fixed format is mandated.

### source_skill (string, required)
- **Value**: Must be exactly `pr-prep-specialist`
- **Validation**: Case-sensitive exact match

### target_skill (string, required)
- **Value**: Must be exactly `pr-merge-specialist`
- **Validation**: Case-sensitive exact match

### run_id (string, required)
- **Purpose**: Execution identifier. No fixed format is mandated.

### repo (string, required)
- **Example**: `DDD-Enterprises/dopemux-mvp`

### branch (string, required)
- **Validation**: Valid Git branch name format

### base_branch (string, required)
- **Value**: `main` in this repository

### governing_posture (string, required)
- **Values**: one of the prep states in §6 of the canonical contract (e.g. `PREP_COMPLETE_AWAITING_STEWARD`, `PREP_READY_FOR_OPERATOR_DECISION`)

### recommended_next_step (string, required)
- **Purpose**: Recommended action for PR-MERGE-SPECIALIST, consistent with `governing_posture`

### task_packet (object, required)
- **Fields**: `id`, `path` (nullable)

### risk_lane (string, required)
- **Values**: `L0` | `L1` | `L2` | `L3` — see canonical contract §4

### heads (object, required)
- **Fields**: `live_main`, `merge_base`, `content_head`, `proof_head`, `current_pr_head`
- **Semantics**: `content_head` is the frozen `C1` from canonical contract §5; `proof_head` is the proof-only successor `C2` from §7 when it exists

### pr (object, required)
- **Fields**: `number`, `state`, `draft` (all nullable when no PR exists yet)

### scope (object, required)
- **Fields**: `allowlist_status`, `changed_files_artifact`

### drift (object, required)
- **Fields**: `classification` (one of `IDENTICAL|SUBSET|SUPERSET|COMPATIBLE|CONFLICTING|UNKNOWN`, canonical contract §1), `blocking`

### validation (object, required)
- **Fields**: `pre_push`, `focused_tests`, `relevant_suite`, `precommit`, `secret_scan` — each a status string, never a silently-invented `PASS`

### audit (object, required)
- **Fields**: `required`, `content_head`, `verdict`
- **Verdict values**: `PASS|PASS_WITH_RISKS|FAIL|NEEDS_SUPERVISOR|SKIPPED|NOT_REQUIRED|NOT_RUN` (canonical contract §6)
- Only `PASS` or `PASS_WITH_RISKS` may support downstream readiness claims when `required: true`

### proof (object, required)
- **Fields**: `status`, `path`

### ci (object, required)
- **Fields**: `status`

### pr_steward (object, required)
- **Fields**: `status` (`READY|NOT_READY|NEEDS_IMPLEMENTER|NEEDS_SUPERVISOR|BLOCKED|NOT_RUN`), `head_sha`, `merge_readiness_path`
- Only current PR Steward evidence on the same current head may support `governing_posture: PREP_READY_FOR_OPERATOR_DECISION`

### authoritative_artifacts / supporting_artifacts (array, required/optional)
- **No fixed list.** Contents reflect what the run actually produced. Do not require exactly seven, or any specific fixed set of filenames.

### warnings / blocking_reasons / unknowns (array, optional)
- Non-empty strings when present

### operator_authority (object, required)
- **Fields**: `merge`, `close_pr`, `mark_ready`, `force_push`, `delete_branch` — all booleans, all `false` unless the operator has explicitly authorized the corresponding mutation. `pr-merge-specialist` must never treat a `true` value here as self-granted; it reflects operator authorization recorded elsewhere, not PRPS authority.

### chain_of_custody (object, required)
- **Fields**: `parent_bundle_ids`, `created_at`, `skill_version`

## Intake Validation Rules

### Structure Validation
1. **Schema Version**: `schema_version` present and major-version-compatible
2. **Field Presence**: All required fields present
3. **Type Correctness**: Fields match specified types
4. **Format Validation**: IDs and timestamps valid

### Content Validation
1. **Consistency Check**: `risk_lane`, `audit`, and `governing_posture` mutually consistent (e.g. `L2`/`L3` with `audit.required: false` is a structure violation)
2. **Decision Validation**: `governing_posture` justified by `validation`, `audit`, `proof`, `ci`, and `pr_steward` fields
3. **Merge-readiness guard**: `pr-merge-specialist` MUST NOT treat `governing_posture: PREP_READY_FOR_OPERATOR_DECISION` as a substitute for its own current PR Steward evidence — re-verify PR Steward status on the same head before acting
4. **Conflict Assessment**: `drift.classification` and `drift.blocking` reasonable and documented

### Provenance Validation
1. **Chain of Custody**: Complete and documented
2. **Parent References**: All parents valid and accessible
3. **Timestamp Order**: Temporally consistent (no future dates)
4. **Version Tracking**: `skill_version` recorded and valid

## Consumption Contract

### PR-MERGE-SPECIALIST Responsibilities
1. **Validate Structure**: Verify handoff bundle format and `schema_version` completely
2. **Check Artifacts**: Confirm listed artifacts actually exist and are valid — do not assume a fixed count
3. **Assess State**: Review `governing_posture`, `risk_lane`, and `recommended_next_step`
4. **Re-verify PR Steward**: Never substitute the handoff's `pr_steward` snapshot for a fresh check on the same head
5. **Preserve Provenance**: Extend chain of custody appropriately
6. **Emit Proof**: Generate intake validation proof bundle
7. **Handle Errors**: Escalate according to escalation protocol

### Guarantees to PR-PREP-SPECIALIST
1. **Structure Preservation**: Handoff bundle unchanged during validation
2. **Artifact Integrity**: No modification of authoritative artifacts
3. **Provenance Continuity**: Chain of custody extended seamlessly
4. **Feedback Loop**: Validation results provided
5. **Error Handling**: Clear error reporting with recovery paths
6. **Consistent Behavior**: Identical validation across all contexts

## Error Handling Procedures

### Validation Failure Modes
1. **Structure Invalid**: Missing required fields, invalid types, or incompatible `schema_version`
2. **Artifacts Missing**: A referenced artifact path does not resolve
3. **Inconsistent State**: Conflicting information between `risk_lane`, `audit`, `governing_posture`
4. **Provenance Broken**: Invalid chain of custody
5. **Content Invalid**: Artifact content doesn't match specifications

### Recovery Procedures
1. **Immediate Response**: Emit detailed validation failure artifact
2. **Notification**: Alert operator with specific issues
3. **Preservation**: Maintain handoff bundle for inspection
4. **Escalation**: Follow escalation protocol (typically Level 2 - BLOCK)
5. **Recovery**: Await corrected handoff from PR-PREP-SPECIALIST

### Specific Error Scenarios

#### Missing Referenced Artifact
**Detection**: A path in `authoritative_artifacts` does not resolve
**Response**:
1. List the missing artifact specifically
2. Emit BLOCK escalation
3. Provide recovery procedure
4. Await complete handoff

#### Invalid Chain of Custody
**Detection**: Parent references invalid or missing
**Response**:
1. Freeze intake immediately
2. Emit GOVERNANCE_REVIEW escalation
3. Preserve all state
4. Notify governance team

#### Inconsistent Artifact Data
**Detection**: Conflicting information between fields
**Response**:
1. Document specific inconsistencies
2. Emit BLOCK escalation
3. Request clarification from PR-PREP-SPECIALIST
4. Await corrected handoff

## Governance Integration

### Compliance Monitoring
- Automated structure validation on every intake
- Referenced-artifact resolution verification
- Chain of custody auditing
- Decision consistency tracking

### Reporting Requirements
- Intake validation metrics
- Error trends and patterns
- Recovery time statistics
- Governance compliance reports

### Audit Trail Requirements
- Complete intake history
- All validation artifacts preserved
- Operator actions logged
- Recovery procedures documented

## Context-Specific Adaptations

### CLI Context
- **Validation Output**: Structured console output
- **Error Handling**: Interactive prompts for recovery
- **Logging**: JSON-formatted validation logs

### API Context
- **Validation Output**: Structured API response
- **Error Handling**: Webhook notifications
- **Logging**: API-accessible validation logs

### Interactive Context
- **Validation Output**: Rich UI validation report
- **Error Handling**: Guided recovery workflow
- **Logging**: User action audit trail

## Validation Gates

### Intake Validation Gate
- ✅ Handoff bundle structure valid, `schema_version` compatible
- ✅ All required fields present
- ✅ Referenced artifacts resolve and are valid
- ✅ Chain of custody intact
- ✅ No critical inconsistencies

### Provenance Continuity Gate
- ✅ Parent references valid
- ✅ Timestamps consistent
- ✅ Skill version tracked
- ✅ Governance requirements met

## Implementation Requirements

### For Intake Validation
1. Complete schema validation
2. Referenced-artifact resolution verification
3. Content consistency checking
4. Provenance auditing
5. Error handling procedures

### For Error Recovery
1. Detailed error reporting
2. Recovery procedure documentation
3. State preservation mechanisms
4. Operator notification
5. Governance escalation paths

### For Governance Integration
1. Compliance monitoring
2. Audit trail preservation
3. Reporting mechanisms
4. Validation metrics
5. Policy enforcement

## Exit Criteria

Handoff contract implementation complete when:
1. ✅ Canonical intake structure defined
2. ✅ Validation procedures implemented
3. ✅ Error handling operational
4. ✅ Governance integration complete
5. ✅ Cross-context consistency verified
6. ✅ All validation gates passing
7. ✅ Recovery procedures documented
8. ✅ Compliance monitoring operational

## Compliance Statement

By consuming handoff bundles, PR-MERGE-SPECIALIST agrees to:
- Validate structure completely and consistently
- Preserve artifact integrity absolutely
- Extend chain of custody appropriately
- Re-verify PR Steward status rather than trusting the handoff snapshot as final
- Follow escalation protocol precisely
- Provide clear feedback to PR-PREP-SPECIALIST
- Document all intake validations and errors
- Participate in governance compliance monitoring

By emitting handoff bundles, PR-PREP-SPECIALIST agrees to:
- Follow the canonical V2 handoff structure exactly
- Never claim merge readiness independently
- Maintain structure consistency absolutely
- Document provenance completely
- Submit to intake validation
- Participate in governance compliance

**This contract is binding and enforceable under governance rules.**
