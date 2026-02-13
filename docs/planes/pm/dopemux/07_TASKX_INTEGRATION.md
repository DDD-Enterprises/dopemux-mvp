---
title: "TaskX Integration"
plane: "pm"
component: "dopemux"
status: "skeleton"
---

# TaskX Integration Contract

## Purpose

The seam between deterministic engine and stateful runtime.

## Scope

TODO: Define the integration boundary between Dopemux and TaskX.

## Non-negotiable invariants

- TaskX stays deterministic and "boring".
- No policy, memory, or MCP management in TaskX.

## FACT ANCHORS (Repo-derived)

TODO: Link to TaskX wrapper and orchestration logic.

## Open questions

TODO: List integration unknowns and how to resolve them.

## TaskX responsibilities (must stay boring)
- deterministic artifacts
- refusal plans
- runner exclusivity (one runner per run)
- manual handoff chunks
- no policy, no memory, no MCP management

TODO: Insert the exact TaskX invariants list from the Brain Dump.

## Dopemux responsibilities (stateful runtime)
- generate packets
- provide policy inputs
- persist memory
- optimize costs
- manage MCP lifecycle and mandates

## Interface
- taskx orchestrate
- artifact dir consumption contract

## Artifacts
- ROUTE_PLAN.json
- RUN_REPORT.json or REFUSAL_REPORT.json
- ARTIFACT_INDEX.json

TODO: Define schema pointers and stable field ordering requirements.

## Key rule: no editing history

Dopemux never edits history. It creates new packets and new TaskX runs.

TODO: Define how supersession chains are represented.

## Failure modes

TODO: kernel scope creep, non-deterministic artifacts, leaky responsibilities.

## Acceptance criteria

TODO: Provide 5 “boundary enforcement” tests.
