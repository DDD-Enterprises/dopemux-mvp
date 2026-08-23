---
id: TRUTH_GAPS
title: Truth Gaps
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-07-01'
prelude: Truth Gaps (reference) for dopemux documentation and developer workflows.
---
# TRUTH_GAPS

Method:
- Drift and risk items are grouped by category.
- Each item cites exact repo paths.
- No destructive commands were used in this pass.

## Boundary Violations

- `[LOCAL_PATH_REDACTED]`
  - Observed contract says bridge must not be canonical task, workflow, decision, or progress authority.
  - Risk:
    - downstream operators may still treat bridge endpoints as authoritative because they expose `/kg/*`, `/ddg/*`, and PM routing surfaces.
- `[LOCAL_PATH_REDACTED]`
  - Observed authority split across Leantime, task-orchestrator, ConPort, and dope-memory mirror receipts.
  - Risk:
    - any service that begins owning more than its declared slice will create silent contract drift.

## Duplicate Responsibilities

- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
  - Multiple memory-related surfaces exist with overlapping names but different transport/runtime status.
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
  - Serena implementation and deployment surfaces overlap without a single declared canonical writer/runtime.
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
  - Agent responsibilities are duplicated across at least three families.

## Unresolved Canonicality

- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
  - Runtime authority points in conflicting directions.
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
  - Canonical Serena surface remains `UNKNOWN`.
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
  - Naming suggests related retrieval families, but only ConPort shows active authority.

## Naming Ambiguity

- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
  - Runtime is `dopetask`; operator language still says TaskX in code and tests.
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
  - Hyphen/underscore duplicate family.
- `[LOCAL_PATH_REDACTED]`
  - Maps `serena-v2`, `serena`, and `dopemux-serena`, indicating ongoing alias sprawl.

## Interface Inconsistency

- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
  - Observed inconsistent launch methods and endpoint assumptions for Serena and Dope-Context.
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
  - Dope-memory adapter uses `8096`, while registry and compose use `3020`.
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
  - `truth` shortcut and `extractor/upgrades` commands lead to different extraction engines.

## Dead / Stub / Hard-Failing Paths

- `[LOCAL_PATH_REDACTED]`
  - Hard-fails and says not to use it as runtime authority.
- `[LOCAL_PATH_REDACTED]`
  - Likely stale because its target port does not match observed runtime config.
- `[LOCAL_PATH_REDACTED]`
  - No active runtime entrypoint found in this pass.
- `[LOCAL_PATH_REDACTED]`
  - Refer to missing `[LOCAL_PATH_REDACTED]`.

## Docs vs Repo Risk

- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
  - README mentions `dopetask==0.2.0`; repo pin and dependency declarations show `0.5.1`.
- `[LOCAL_PATH_REDACTED]`
  - `dopemux rte` is the canonical operator command family, `dopemux upgrades` is a legacy compatibility alias, and `dopemux truth` now refuses with guidance to use `dopemux rte`.
- RTE operator docs
  - Older docs may still carry stale command examples; current docs should classify `dopemux upgrades`, `dopemux extractor`, `dopemux truth`, direct runner calls, and legacy scan paths according to runtime evidence.
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
  - Registry and runtime module disagree on task-orchestrator port.

## Drift in Operator / Dev Workflow Surfaces

- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
  - Developer workflow branding and actual runtime diverge.
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
  - MCP/operator launch surfaces are not aligned on actual service entrypoints.
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
- `[LOCAL_PATH_REDACTED]`
  - Provider/model/server naming and aliasing appear broader than the currently consistent runtime set.

## Commands Used

- `pwd`
- `find . -maxdepth 2 -type d | sort`
- `rg --files ...`
- `rg -n ...`
- `sed -n 'start,endp' ...`
- `ls -la ...`
- `ls -l scripts/taskx scripts/dopetask .dopetaskroot .taskxroot`
- `cat .dopetask-pin`
- `find services/dope-query -maxdepth 3 -type f | sort`
- `mkdir -p [LOCAL_PATH_REDACTED]`

Validation note:
- This pass validated by repository inspection and artifact review only.
- No destructive commands were run.
- No commits were created.
