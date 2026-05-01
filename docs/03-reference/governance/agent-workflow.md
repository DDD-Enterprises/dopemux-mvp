---
id: AGENT_WORKFLOW
title: Deterministic Agent Workflow
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-30'
last_review: '2026-04-30'
next_review: '2026-07-30'
prelude: Deterministic helper-agent workflow for Dopemux Copilot agent specs.
---
# Deterministic Agent Workflow

## Purpose

This document defines the deterministic handoff workflow for the Dopemux Copilot helper agents in `.github/agents/`.

Agents are helpers, not authorities. They do not own PM truth, memory truth, retrieval truth, bridge authority, workflow truth, runtime truth, or repository truth. Repository authority remains in runtime code, schemas, tests, configs, and tracked truth references. Task packets define edit scope.

## Agent Chain

The normal chain is:

1. `dopemux-planner`
2. `dopemux-implementer`
3. `dopemux-reviewer`
4. `dopemux-testgen` when test proof is missing or the task packet requires test work

The reviewer may hand back to the implementer for corrections. The implementer may hand to testgen when proof is missing. Testgen may hand back to the implementer only when a required production change is explicitly allowed by the task packet.

## Handoff Limits

Each agent spec must expose no more than two or three handoffs. Handoffs must be narrowly scoped:

- planner -> implementer
- planner -> reviewer
- implementer -> reviewer
- implementer -> testgen
- reviewer -> implementer
- reviewer -> testgen
- testgen -> implementer
- testgen -> reviewer

Do not create broad handoff meshes. Do not use agents to bypass task-packet allowlists, repository identity checks, or proof requirements.

## Tool Boundaries

`dopemux-planner`:
- tools: `read`, `search`
- must not edit
- must not execute commands

`dopemux-reviewer`:
- tools: `read`, `search`
- must not edit
- must not execute commands

`dopemux-implementer`:
- tools: `read`, `edit`, `search`, `execute`
- may edit only files listed in the active task packet allowlist
- must verify repo identity, branch, marker, and allowlist before edits

`dopemux-testgen`:
- tools: `read`, `edit`, `search`, `execute`
- may edit tests only by default
- may edit production code only when the task packet explicitly allowlists the production file and explicitly requires testgen to make that production change

## Authority Boundaries

All agents must preserve the authority split documented by tracked repo references:

- PM authority is split and must not be unified by an agent.
- `dopecon-bridge` routes are adapter, proxy, event, and compatibility surfaces; they are not canonical task, workflow, decision, progress, PM, memory, or retrieval truth.
- Retrieval output is derived evidence and must point back to source artifacts.
- Mirror receipts are evidence of mirroring, not canonical state, unless the canonical writer is named and the mirror role is explicit.
- Agent system ownership remains `UNKNOWN` unless runtime evidence resolves it.

No agent may promote bridge, retrieval, mirror, memory, or PM surfaces beyond their observed authority.

## Stop Conditions

Any agent must stop and report a blocker when:

- the task packet is missing, malformed, or incompatible with the repository identity
- the requested edit is outside the task-packet allowlist
- branch, marker, or origin identity checks fail
- planner or reviewer work would require edit or execute tools
- canonical writer or reader ownership is unclear for a contract-sensitive surface
- validation fails and the cause is not understood
- required proof cannot be produced truthfully
- a handoff would hide unresolved `UNKNOWN`, split authority, or drift

## Proof Requirements

Before a task-packet change is treated as ready for commit or PR, the agent chain must provide:

- task-packet id, branch, and allowlist
- files changed
- authority used
- commands run
- validation results
- diff inspection summary
- residual uncertainty, drift, or risk

For docs-only or agent-spec packets, minimum proof is:

- all packet-declared files exist
- agent frontmatter includes `description`, `tools`, and scoped `handoffs`
- planner and reviewer specs do not include edit or execute tools
- implementer and testgen specs enforce task-packet allowlists
- workflow documentation states that agents are helpers, not authorities

No proof artifact may claim completion when required evidence is missing.
