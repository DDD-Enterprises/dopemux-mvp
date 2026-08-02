---
id: db-defragmentation-2026-08-01
title: Orchestrator DB Defragmentation 2026-08-01
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-01'
last_review: '2026-08-02'
next_review: '2026-10-30'
status: active
tags:
  - orchestrator
  - task-orchestrator
  - defragmentation
  - load-plan
prelude: Record of the 2026-08-01 task-orchestrator instance-database defragmentation, its root cause, and the detection recipe for misfiled work items.
---
# Orchestrator DB Defragmentation (2026-08-01)

## Why

Multiple task-packet programs were recorded in load plans and session notes as
"loaded into task-orchestrator" while being unqueryable from the dopemux-mvp MCP
server. The recurring conclusion — that the packets were stranded on unmerged
branches or never loaded — was wrong. They were loaded, into the wrong instance
database.

## Root cause

Task-orchestrator v3 runs with `TASK_ORCHESTRATOR_STATE_SCOPE=per-repo`. Each
project gets its own SQLite instance under
`~/.local/share/dopemux-mission-control/task-orchestrator/<project>-<hash>/current-tasks.db`,
and a given MCP server reads **only** its own instance.

Instance selection follows the workspace the server was launched against. Loading
dopemux-mvp packets during a session rooted in another workspace writes them to
that workspace's instance. Because each server is blind to every other instance,
the result is not a visible error but silent invisibility.

The `dnh_crm-9a4e9aa8a329cdd5` instance had accumulated work from three projects.
Of its 812 items only 292 (36%) were dNh_CRM work.

## What was done

Containers were stopped, then whole subtrees were moved with `ATTACH` +
`INSERT ... SELECT`, preserving original UUIDs, timestamps, roles, parent links,
notes, dependencies and role transitions. FTS indexes rebuilt via the existing
`work_items_fts_*` table triggers.

| Target instance | Before | After | Change |
| --- | ---: | ---: | --- |
| `dopemux-mvp-2e346e2084bca021` | 500 | 783 | +261 re-homed, +22 newly loaded |
| `adops-78854735f2d1eae5` | 13 | 266 | +253 re-homed |
| `dnh_crm-9a4e9aa8a329cdd5` | 812 | 309 | −520 re-homed out, +17 recovered in |
| `firestick-control-a3fce4918082f41f` | 78 | 84 | +6 re-homed |

Net 1420 → 1442 (+22 = 2 roots + 20 packets from two never-loaded series).
Zero cross-group dependencies, zero UUID collisions, zero item loss. All four
instances verify `integrity_check=ok`, 0 foreign-key violations, 0 orphan parents,
and FTS row counts equal to item counts.

Program roots restored to dopemux-mvp visibility: `7212c3b8` (RTE-TRUTH, 129),
`af10eefd` (DMX-MCPINT, 56, including `b5de7373` P7's 18 HRD packets),
`f64aa1a9` (DMX-SVCFEAT, 29), `3ad40a72` (DMX-SVCFIN, 25),
`ea969afa` (DCP-MCP-RO remainder, 9).

Two series that genuinely had never been loaded — matching their own
`PENDING_LOAD` / `NOT_PERFORMED` flags — were created: `TO-CANON` (8 packets) and
`DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED` (12 packets).

An orphaned v2-schema instance (`dnh_crm__recovery_20260504t060227z-...`, workspace
no longer on disk) had its 17-item tree migrated into dNh canonical and was moved
to `task-orchestrator-retired/`.

Pre-change backups: `~/.local/share/dopemux-mission-control/task-orchestrator-backups/2026-08-01-pre-defrag/`.

## Detection recipe

When a load plan asserts `children_created: N PASS` but the packets are not
queryable, **search other instances by root UUID before concluding it was never
loaded**:

```bash
D=~/.local/share/dopemux-mission-control/task-orchestrator
for f in $D/*/current-tasks.db; do
  n=$(sqlite3 "$f" "select count(*) from work_items
      where lower(hex(id)) like '<8hex>%' or lower(hex(parent_id)) like '<8hex>%'")
  [ "$n" != "0" ] && echo "$f -> $n"
done
```

Census every instance rather than trusting the one your server reads:

```bash
for f in $D/*/current-tasks.db; do
  printf '%s %s\n' "$(sqlite3 "$f" 'select count(*) from work_items')" "$f"
done | sort -rn
```

## Verification pitfall

Matching packets by ID string produces **false negatives**. Loaded titles
routinely drop the series prefix — P7 children are titled
`MCPINT-HRD-REPORT-001`, not `DMX-MCPINT-HRD-REPORT-001`. An initial ID-grep in
this incident reported 56 missing packets that were all present. Match
prefix-tolerantly, and corroborate against a second independent signal (the load
plan's own `loaded` flag, or the root-UUID subtree count) before reporting a gap.

## Known latent issue (not the cause of this incident)

`compose.yml` defines the Python `task-orchestrator` service with a fixed
`container_name: task-orchestrator` — a host singleton — while passing
per-project identity `WORKSPACE_ID=${DOPEMUX_WORKSPACE_ID:-/app}`. Whichever
project starts it first stamps its workspace onto the container all projects
share; it was observed running with `WORKSPACE_ID=/Users/hue/code/dNh_CRM`.

This service holds no task database (verified: no `*.db` anywhere in its
filesystem), so it did **not** cause the misfiling above. It is recorded here
because the same host-singleton-with-per-project-identity shape can contaminate
services that *do* hold state. Correcting it changes shared-service identity
semantics and warrants its own task packet rather than an incidental edit.
