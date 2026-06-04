---
id: TP-DCP-0004
title: DCP Core Local Control Snapshot Generator
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-06-04'
last_review: '2026-06-04'
next_review: '2026-09-02'
prelude: Local-only DCP control snapshot generator using existing proof-family readers.
---
# TP-DCP-0004 - DCP Core Local Control Snapshot Generator

**Packet ID**: TP-DCP-0004
**Project**: DCP - Data Control Plane
**Target**: `dcp/local-control-snapshot-tp-0004`
**Implementer**: Codex
**Auditor**: distinct auditor required before final proof
**Status**: IN_PROGRESS
**Base**: `origin/main`

## Objective

Implement a local-only DCP control snapshot generator that reads repo-local
DCP schemas, task packets, proof bundles, audit artifacts, merge-readiness
artifacts, and red-line status inputs, then emits a deterministic derived
`DCP_CONTROL_SNAPSHOT` object for downstream inspection.

The snapshot is evidence-labeled, provenance-preserving, fail-closed, and
strictly local. It does not perform live reads, live writes, external writes,
or merge automation.

## Schema Convention Decision

- `CLAIMED/OBSERVED_BY_IMPLEMENTER`: Existing DCP control snapshot schema convention is `schemas/dcp/dcp_control_snapshot.schema.json`.
- `DECISION_APPLIED`: TP-DCP-0004 extends existing schema convention and does not introduce `schemas/dcp/dcp_control_snapshot.v0.schema.json`.
- `RATIONALE`: Repo-local convention outranks packet-preferred path when the packet explicitly required stop-and-report on naming mismatch.

## Scope

In scope:

- local control snapshot generation under `src/dopemux/dcp`
- use of TP-DCP-0003 proof-family / proof-pointer reader
- source artifact inventory
- packet states for TP-DCP-0001 through TP-DCP-0004
- guard summary
- endpoint certainty summary
- readiness summary
- residual risk and stop-condition preservation
- local deterministic tests and fixtures
- proof and audit artifacts for this packet

Out of scope:

- live adapters
- GitHub API reads or writes
- Dopetask execution
- Task-Orchestrator, ConPort, dope-memory, dope-context, dopecon-bridge reads or writes
- cockpit work
- `LIVE_WRITE_READY`
- merge automation
- forbidden-file edits

## Allowed Files

```text
src/dopemux/dcp/__init__.py
src/dopemux/dcp/control_snapshot.py
schemas/dcp/dcp_control_snapshot.schema.json
schemas/dcp/README.md
tests/dcp/test_dcp_0004_control_snapshot.py
tests/dcp/fixtures/tp_dcp_0004_valid_snapshot_inputs/**
tests/dcp/fixtures/tp_dcp_0004_missing_tp0003/**
tests/dcp/fixtures/tp_dcp_0004_conflicting_proof/**
tests/dcp/fixtures/tp_dcp_0004_live_write_detected/**
tests/dcp/fixtures/tp_dcp_0004_stale_proof/**
task-packets/TP-DCP-0004.md
proof/TP-DCP-0004/**
```

## Forbidden Files And Paths

Do not edit, import, call, wrap, invoke, or wire into:

```text
src/dopemux_pr_merge_specialist/queue_drain.py
dopemux_pr_merge_specialist/queue_drain.py
scripts/batch_resolve_and_merge.py
.github/workflows/*
scripts/dopetask
scripts/taskx
services/task-orchestrator/**
services/dopecon-bridge/**
services/dope-context/**
services/working-memory-assistant/**
docker/mcp-servers-source/conport/**
src/conport/**
```

## Validation Commands

```bash
python3 -m pytest tests/dcp/test_dcp_0004_control_snapshot.py -q
python3 -m pytest tests/dcp -q
python3 -m compileall -q src tests
python3 -m json.tool proof/TP-DCP-0004/PROOF.json >/dev/null
test -f schemas/dcp/dcp_control_snapshot.schema.json && python3 -m json.tool schemas/dcp/dcp_control_snapshot.schema.json >/dev/null || true
git diff --check
git diff --name-only | grep -E '^(src/dopemux_pr_merge_specialist/|dopemux_pr_merge_specialist/|scripts/batch_resolve_and_merge.py|\.github/workflows/|scripts/dopetask|scripts/taskx|services/task-orchestrator/|services/dopecon-bridge/|services/dope-context/|services/working-memory-assistant/|docker/mcp-servers-source/conport/|src/conport/)' && exit 1 || true
rg -n "gh pr merge|dopetask tp|scripts/dopetask|scripts/taskx|mem\\.upsert|memory_store|/api/(decisions|progress|custom_data)|/tools/memory_store|/api/workflow|/api/pm|queue_drain|batch_resolve_and_merge|requests\\.|httpx\\.|urllib|subprocess" src/dopemux/dcp tests/dcp || true
```

## Rollback

```bash
git restore src/dopemux/dcp/__init__.py src/dopemux/dcp/control_snapshot.py schemas/dcp/dcp_control_snapshot.schema.json schemas/dcp/README.md tests/dcp/test_dcp_0004_control_snapshot.py task-packets/TP-DCP-0004.md
rm -rf tests/dcp/fixtures/tp_dcp_0004_* proof/TP-DCP-0004
```
