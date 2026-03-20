---
id: PM_PLANE_PHASE0_SCOPE_LOCK_OPUS
title: Pm Plane Phase0 Scope Lock Opus
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Pm Plane Phase0 Scope Lock Opus (explanation) for dopemux documentation and
  developer workflows.
---
# PM / Task Management Plane — Phase 0 Scope Lock

### Ready-to-run prompt for Opus (Investigator / Architect)

════════════════════════════════════════════════════════════

## Role

You are operating as the Investigator / Architect for the PM / Task Management plane of Dopemux.

You are not implementing code.
You are establishing current-state truth, boundaries, success criteria, and an evidence plan.

You must follow:

* .claude/PROJECT_INSTRUCTIONS.md (authority)
* .claude/PRIMER.md (phased investigation protocol)

────────────────────────────────────────────────────────────

## Mission

Produce Phase 0 only:

* Scope IN / OUT
* Success criteria
* Stop conditions
* Evidence plan (what to read/run first)

Do not proceed to Phase 1 in this run.

────────────────────────────────────────────────────────────

## Target Plane Definition (PM / Task Management)

This plane covers:

* Task creation, representation, and lifecycle
* Work planning and decomposition
* Tracking: status, ownership, dependencies
* Bridging external systems (Leantime, Task Master AI, etc.)
* Any CLI/agent interface that creates or mutates task state
* Project-level decision logs and how they relate to tasks

This plane does not include:

* Memory promotion semantics (unless tasks write to memory)
* Search ranking (unless search is used to manage tasks)
* UI aesthetics (unless it affects determinism or state truth)

────────────────────────────────────────────────────────────

## Required Outputs (Phase 0)

### A) Scope (IN / OUT)

Define with explicit bullets.

### B) Success Criteria

Define as testable statements, for example:

* There is exactly one authoritative task truth store per project (or explicitly justified split).
* Task lifecycle transitions are explicit, auditable, and replayable.
* External PM tools are either authoritative or mirrors, never both without a contract.
* Agents cannot silently mutate task truth without logging.

### C) Stop Conditions

Define what evidence gaps block Phase 1.

Examples:

* Cannot identify where tasks are stored or how they are keyed.
* Cannot locate command surfaces that create/update tasks.
* Conflicting definitions of task identity across components.

### D) Evidence Plan

List exact repo paths and exact commands to run next.

Your plan must include:

* Where tasks are defined (schemas, models)
* Where tasks are created/updated (CLI commands, services)
* Where external sync is implemented (bridges)
* Any docs that claim PM semantics (PRDs, guides)

────────────────────────────────────────────────────────────

## Output Format

Use:

* Findings (Phase 0 only)
* Risks
* Decision (Scope lock)
* Next Evidence Plan
* Stop Conditions

Do not write code. Do not draft ADRs. Do not write task packets yet.
