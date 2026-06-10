# Task Packet: `DMX-DCP-MODEL-ROUTING-MVP-0000I` · DCP · Routing Classifier Golden Corpus Seed

════════════════════════════════════════════════════════════

## Objective

Create the first set of routing test fixtures (golden corpus) that any future classifier, lane engine, or router must pass before production use.

**Runner**: Codex or Claude Code Sonnet
**Audit**: AGY/Sonnet
**Mode**: fixture-only

────────────────────────────────────────────────────────────

## Scope

### IN

* JSON fixtures only
* README explaining expected labels
* Cases for safe, risky, forbidden, unknown, and conflicting tasks
* No production classifier code

### OUT

* No classifier implementation
* No runtime routing
* No model calls
* No runner execution

────────────────────────────────────────────────────────────

## Files Likely Touched

```
tests/fixtures/dcp/routing_corpus/README.md
tests/fixtures/dcp/routing_corpus/*.json
proof/DMX-DCP-MODEL-ROUTING-MVP-0000I/*
```

────────────────────────────────────────────────────────────

## Required Fixture Types

```text
safe_read_task.json
docs_only_task.json
domain_model_design_task.json
implementation_allowed_task.json
workflow_red_lane_task.json
secret_path_task.json
merge_tool_forbidden_task.json
dopetask_execution_forbidden_task.json
task_orchestrator_write_forbidden_task.json
opencode_authority_forbidden_task.json
pal_model_inventory_unknown_task.json
litellm_unhealthy_task.json
stale_alias_task.json
dopecode_legacy_serena_alias_task.json
agent_authority_unknown_task.json
```

────────────────────────────────────────────────────────────

## Validation Gates

* Every fixture has expected classification
* Every fixture has expected stop behavior
* Forbidden-action miss rate target set to zero
* Risk underclassification cases included
* No runtime code changed

────────────────────────────────────────────────────────────

## Expected Output

A seed corpus of 15+ labeled routing test cases that 0001+ can use to validate classifier and lane engine behavior.
