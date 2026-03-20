---
id: OUTPUT_CONTRACT
title: Output Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Output Contract (explanation) for dopemux documentation and developer workflows.
---
# PR Merge Specialist — Output Contract

## Artifact Schema

All artifacts are written to `--out-dir` (default: `proof/pr_merge/`).

### Core Artifacts

| Artifact | Format | Producer | Description |
|----------|--------|----------|-------------|
| `PR_PLAN.json` | JSON | `pr-plan` | Decision-complete plan for one PR |
| `QUEUE_SCAN.json` | JSON | `queue-scan` | Queue state snapshot with ordering layers |
| `QUEUE_DRAIN_MANIFEST.json` | JSON | `queue-drain` | Orchestration manifest for full queue processing |
| `COMMANDS_LOG.jsonl` | JSONL | All mutating commands | Append-only log of every subprocess invocation |
| `VALIDATION_REPORT.json` | JSON | `pr-apply` | Results of local validation commands |
| `VALIDATION_REPORT.md` | Markdown | `pr-apply` | Human-readable validation summary |
| `CONFLICT_ANALYSIS.md` | Markdown | `pr-plan` | Conflict analysis with strategy recommendation |
| `RUN_MANIFEST.json` | JSON | `queue-drain` | Run metadata, phases, and resumability info |

### Consensus Artifacts (when consensus engine is invoked)

| Artifact | Format | Description |
|----------|--------|-------------|
| `CONSENSUS_DECISION.json` | JSON | Final arbitrated merge strategy decision |
| `MERGE_EXECUTION_PLAN.json` | JSON | Ordered steps for executing the selected strategy |

### Dopetask Adapter Artifacts

| Artifact | Format | Description |
|----------|--------|-------------|
| `ADAPTER_RESULT.json` | JSON | Normalized dopetask integration result |

## JSON Schema Shapes

### PR_PLAN.json

```json
{
  "run_id": "string",
  "pr_state": { "PullRequestState fields" },
  "lifecycle_state": "PRState enum value",
  "apply_actions": ["string"],
  "merge_decision": { "action": "MergeActionType", "command": [], "reason": "string" },
  "blockers": [{ "type": "string", "source": "string", "name": "string" }],
  "warnings": [{ "kind": "warning", "finding_type": "string", "message": "string" }],
  "observations": [{ "kind": "observation", "finding_type": "string", "message": "string" }],
  "truth_sources": [{ "name": "string", "status": "string" }],
  "precedence_order": ["string"],
  "decision_basis": {},
  "validation_report": { "status": "passed|failed|not_executed", "steps": [] },
  "thread_dispositions": [{ "thread_id": "string", "disposition": "string", "applied": false }],
  "fingerprint": { "input_fingerprint": "string", "valid_for_sha": "string" },
  "artifacts": { "key": "path" }
}
```

### QUEUE_SCAN.json

```json
{
  "meta": { "ArtifactMeta fields" },
  "snapshot": [{ "PullRequestState fields" }],
  "ordering": [{ "layer": 1, "pr_ids": [123, 456] }]
}
```

### ThreadDisposition

```json
{
  "thread_id": "string (GitHub node ID)",
  "disposition": "implement | decline_with_rationale | auto_resolve_outdated | escalate",
  "reason": "string",
  "path": "string (file path)",
  "applied": false,
  "escalation_needed": false
}
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Blockers found or operation failed |
| 2 | Preflight checks failed |

## Versioning

- `artifact_version`: Current schema version for all JSON artifacts (see `schema.ARTIFACT_VERSION`)
- `tool_version`: Current CLI tool version (see `schema.TOOL_VERSION`)
- `policy_schema_version`: Policy file schema version (see `schema.POLICY_SCHEMA_VERSION`)

All artifacts include these version fields in their metadata for forward compatibility checking.
