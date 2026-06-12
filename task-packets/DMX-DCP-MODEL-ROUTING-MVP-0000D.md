---
id: DMX-DCP-MODEL-ROUTING-MVP-0000D
title: Dmx Dcp Model Routing Mvp 0000D
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-10'
last_review: '2026-06-10'
next_review: '2026-09-08'
prelude: Dmx Dcp Model Routing Mvp 0000D (explanation) for dopemux documentation and
  developer workflows.
---
# Task Packet: `DMX-DCP-MODEL-ROUTING-MVP-0000D` · DCP · Worktree + Red-Lane Reconciliation

════════════════════════════════════════════════════════════

## Objective

Separate useful routing work from scratch trash and red-lane poison in the current dirty worktree. The 0000B ledger shows 9 tracked modifications, 24 untracked files, and a dirty red-lane workflow file (`gemini-review.yml`).

**Runner**: Claude Code Sonnet
**Audit**: AGY/Sonnet or Claude Code Sonnet
**Mode**: mostly read-only, with optional cleanup only after operator approval

────────────────────────────────────────────────────────────

## Scope

### IN

* `git status`
* Dirty file classification
* Red-lane file classification
* Stale scratch identification
* Preservation plan for intended routing work
* Cleanup packet if needed

### OUT

* No workflow edits
* No code implementation
* No routing changes
* No `git reset --hard`
* No deleting files without operator approval
* No merge/repair tooling

────────────────────────────────────────────────────────────

## Exact Commands

```bash
set -euo pipefail

pwd
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short --branch
git diff --name-only
git diff --stat

git diff -- .github/workflows/gemini-review.yml > /tmp/dmx_0000d_gemini_review_diff.patch || true
git diff -- .claude/claude.md .claude/claude_config.json .claude/llms.md > /tmp/dmx_0000d_claude_config_diff.patch || true
git diff -- compose.yml src/dopemux/cli.py src/dopemux/roles/catalog.py src/dopemux/claude/configurator.py > /tmp/dmx_0000d_routing_code_diff.patch || true

find . -maxdepth 3 -type f -o -type d \
  | grep -E 'dcp_tp_0001_0002_planning_inputs_temp|ddf_commit_diff.patch|docs/plans|llm-plans|test_gemini_|inspect_pal_registry|list_gemini_models|src/proof|task-packets/DMX-DCP-MODEL-ROUTING-MVP-0000' \
  | sort > /tmp/dmx_0000d_untracked_routing_related.txt || true
```

────────────────────────────────────────────────────────────

## Required Artifacts

```
proof/DMX-DCP-MODEL-ROUTING-MVP-0000D/
  PROOF.json
  AUDIT.md
  COMMAND_LOG.md
  DIRTY_FILE_DECISION_LEDGER.md
  RED_LANE_RECONCILIATION_PLAN.md
  CLEANUP_PACKET_IF_NEEDED.md
```

────────────────────────────────────────────────────────────

## Decision Classes

```text
KEEP_ROUTING_RELEVANT
MOVE_TO_PROOF
DELETE_SCRATCH_WITH_APPROVAL
REVERT_WITH_APPROVAL
BLOCKED_RED_LANE
UNKNOWN_NEEDS_SUPERVISOR
```

────────────────────────────────────────────────────────────

## Validation Gates

* Every dirty tracked file classified
* Every untracked file classified
* `.github/workflows/gemini-review.yml` classified as red-lane
* No cleanup performed unless operator explicitly approves
* No claim of clean baseline unless `git status` proves it

────────────────────────────────────────────────────────────

## Stop Conditions

* Red-lane diff cannot be explained
* Any file contains secret-looking material
* Any cleanup would destroy potentially useful work
* Operator approval missing for writes

────────────────────────────────────────────────────────────

## Expected Output

A precise action ledger that tells 0001 exactly which files are safe to keep, which must be reverted, and which red-lane conflict must be resolved before any routing implementation can claim a clean baseline.
