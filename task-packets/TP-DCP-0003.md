---
id: TP-DCP-0003
title: DCP Proof-Family Dispatcher And Proof Pointer Reader
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-06-04'
last_review: '2026-06-04'
next_review: '2026-09-02'
prelude: Bounded local-only implementation packet for DCP proof-family dispatch and
  proof pointer reading.
---
# TP-DCP-0003 - DCP Proof-Family Dispatcher And Proof Pointer Reader

**Packet ID**: TP-DCP-0003
**Project**: DCP - Data Control Plane
**Target**: `dcp/proof-family-dispatch-tp-0003`
**Implementer**: Codex
**Auditor**: distinct auditor required before final proof
**Status**: IN_PROGRESS
**Base**: `origin/main`

## Objective

Implement local DCP proof-family dispatch, proof pointer reading, and local proof artifact inspection so later DCP packets can consume proof artifacts without assuming a single proof shape.

## Scope

In scope:

- local proof-family classification
- local `DCP_PROOF_POINTER` reading
- local `PROOF.json`, `AUDIT.md`, and `MERGE_READINESS.json` inspection
- local SHA freshness classification
- explicit provenance labels: `OBSERVED`, `CLAIMED`, `INFERRED`, `UNKNOWN`, `CONFLICTING`
- fail-closed handling for missing, malformed, stale, conflicting, unknown, or live-write-shaped artifacts
- local deterministic tests and fixtures
- proof and audit artifacts for this packet

Out of scope:

- live adapters
- GitHub API reads or writes beyond branch push / PR creation
- merge automation
- Dopetask execution
- Task-Orchestrator, ConPort, dope-memory, dope-context, or dopecon-bridge reads or writes
- cockpit or web Palette work
- PR Steward implementation
- `LIVE_WRITE_READY` definition or endpoint promotion

## Allowed Files

```text
src/dopemux/dcp/__init__.py
src/dopemux/dcp/proof_family.py
src/dopemux/dcp/proof_pointer_reader.py
tests/dcp/test_dcp_0003_proof_family_dispatch.py
tests/dcp/fixtures/tp_dcp_0003_valid_proof_pointer.json
tests/dcp/fixtures/tp_dcp_0003_valid_proof_bundle.json
tests/dcp/fixtures/tp_dcp_0003_valid_merge_readiness.json
tests/dcp/fixtures/tp_dcp_0003_unknown_family.json
tests/dcp/fixtures/tp_dcp_0003_stale_sha.json
tests/dcp/fixtures/tp_dcp_0003_conflicting_artifacts.json
task-packets/TP-DCP-0003.md
proof/TP-DCP-0003/PROOF.json
proof/TP-DCP-0003/AUDIT.md
proof/TP-DCP-0003/MERGE_READINESS.json
```

Optional documentation path if needed:

```text
schemas/dcp/README.md
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

## Implementation Steps

1. Confirm current `origin/main` contains TP-DCP-0001 and TP-DCP-0002 artifacts.
2. Inspect existing DCP schemas, fixtures, tests, proof, and packet conventions.
3. Add failing local-only tests for proof-family dispatch and pointer reading.
4. Implement the minimal local parser/classifier under `src/dopemux/dcp`.
5. Run required validation commands and record outputs with exit codes in `proof/TP-DCP-0003/PROOF.json`.
6. Run an embedded distinct-auditor review and record it in `proof/TP-DCP-0003/AUDIT.md`.
7. Commit a single packet-sized change.

## Acceptance Criteria

- Current branch is `dcp/proof-family-dispatch-tp-0003`.
- TP-DCP-0001 and TP-DCP-0002 artifacts are present on current `origin/main`.
- Unknown proof family fails closed.
- Malformed JSON fails closed.
- Missing artifacts return `UNKNOWN`.
- Stale SHA returns `STALE`.
- Conflicting SHA fields return `CONFLICTING`.
- Missing fields are marked `UNKNOWN`.
- Local artifact inspection handles `PROOF.json`, `AUDIT.md`, and `MERGE_READINESS.json`.
- Remote URL references are not followed.
- `LIVE_WRITE_READY` remains `UNDEFINED_AND_BLOCKING`.
- Merge-seam red line remains preserved.
- No forbidden files are touched.
- No external writes or live adapters exist.
- Required tests, compile check, JSON proof parse, `git diff --check`, and forbidden-file checks pass.

## Validation Commands

```bash
python3 -m pytest tests/dcp/test_dcp_0003_proof_family_dispatch.py -q
python3 -m pytest tests/dcp -q
python3 -m compileall -q src tests
python3 -m json.tool proof/TP-DCP-0003/PROOF.json >/dev/null
git diff --check
git diff --name-only | grep -E '^(src/dopemux_pr_merge_specialist/|dopemux_pr_merge_specialist/|scripts/batch_resolve_and_merge.py|\.github/workflows/|scripts/dopetask|scripts/taskx)' && exit 1 || true
rg -n "gh pr merge|dopetask tp|scripts/dopetask|scripts/taskx|mem\\.upsert|memory_store|/api/(decisions|progress|custom_data)|/tools/memory_store|/api/workflow|/api/pm|queue_drain|batch_resolve_and_merge" src/dopemux/dcp tests/dcp || true
git status --short
git diff --stat
git diff
```

## Rollback

```bash
git restore src/dopemux/dcp tests/dcp/test_dcp_0003_proof_family_dispatch.py tests/dcp/fixtures/tp_dcp_0003_*.json task-packets/TP-DCP-0003.md proof/TP-DCP-0003
git status --short
```
