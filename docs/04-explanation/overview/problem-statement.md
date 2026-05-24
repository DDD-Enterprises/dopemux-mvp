---
id: problem-statement
title: Problem Statement
type: explanation
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Problem statement for Dopemux documentation and split-authority operations.
---
# Problem Statement

Dopemux solves an operator problem: development work spans execution, PM,
context, memory, retrieval, service startup, and audit trails, but those domains
do not have one trustworthy owner in this repository. The system needs a control
surface that can route work across those domains while preserving which service
is authoritative for each slice.

The main documentation risk is false unification. If docs describe Dopemux as a
single assistant, a single PM platform, a bridge-owned control plane, or a
unified memory layer, operators can send writes to the wrong surface and treat
derived views as truth.

## Observed Tensions

| Tension | Repo-grounded impact |
| --- | --- |
| PM is split | Metadata, workflow transitions, decision/progress context, and historical receipts have different writers. |
| Memory is split | ConPort structured context and dope-memory chronology are adjacent but not interchangeable. |
| Retrieval is derived | dope-context and ConPort retrieval output can support investigation but cannot override source files. |
| Bridge routes look authoritative | dopecon-bridge exposes PM/KG-like routes while its runtime states it is adapter/proxy only. |
| Runtime packaging drift remains | task-orchestrator and some MCP surfaces have old port/path assumptions beside newer compose defaults. |
| Agent ownership is unresolved | Multiple agent families exist, and no single runtime authority is proven. |

## Desired Operator Outcome

An operator should be able to:

1. Identify the source of truth for the action they are taking.
2. Start from `dopemux` for operator control without making `dopemux` the owner
   of every domain.
3. Route PM writes to the correct canonical writer.
4. Treat retrieval and extraction outputs as evidence instead of final truth.
5. Preserve `UNKNOWN` and drift until validation closes it.
6. Produce proof that names changed files, validations, residual risks, and
   exact blockers.

## Non-Goals

- Do not flatten Dopemux into a monolithic assistant.
- Do not promote dopecon-bridge into PM, workflow, decision, progress, or
  memory authority.
- Do not treat dope-context retrieval or Repo Truth Extractor artifacts as
  stronger than runtime code.
- Do not claim runtime drift is closed from docs-only work.
