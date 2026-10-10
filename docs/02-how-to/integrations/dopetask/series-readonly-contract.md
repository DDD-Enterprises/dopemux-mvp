---
id: series-readonly-contract
title: Series Readonly Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-27'
last_review: '2026-03-27'
next_review: '2026-06-25'
prelude: Series Readonly Contract (explanation) for dopemux documentation and developer
  workflows.
---
# read-only Series Contract (TP-DSER-003)

## Status
- **Scope**: Read-Only
- **Supported Version**: `dopetask==0.5.1`
- **Date**: 2026-03-27

## Objective
This contract establishes how `dopemux` consumes Task Packet series metadata from `dopetask` without triggering execution or event orchestration.

## No-Execution Boundary
**CRITICAL**: The methods introduced in this TP (`from_series_id`, `from_series_state_path`) are strictly for loading and normalizing state. They do NOT invoke `scripts/dopetask tp series exec` or any other modifying command.

## Data Model
Series state is modeled using the following entities in `dopetask_series_models.py`:
- `DopetaskSeriesResult`: The top-level normalized artifact.
- `DopetaskPacketRecord`: Individual Task Packets within the series, including their `depends_on` relationships.
- `SeriesStatus` / `PacketStatus`: Enums reflecting the state of the series and its components.

## Schema Expectations
The adapter expects the following JSON structure from `dopetask tp series status`:
```json
{
  "series_id": "string",
  "project_id": "string",
  "status": "VALIDATED|IN_PROGRESS|FAILED|...",
  "packets": [
    {
      "tp_id": "string",
      "status": "VALIDATED|PLANNED|SKIPPED|...",
      "depends_on": ["tp_id_ref"],
      "is_final": boolean
    }
  ]
}
```

## Governance
Governance is aggregated across the series using an intersection strategy based on the global posture. If a series is `VALIDATED` and the posture is `GO_SUPERVISED_ONLY`, the series allowed actions will include `APPLY_FIX`.
