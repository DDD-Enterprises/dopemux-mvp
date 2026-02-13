---
title: "ADHD Execution Model"
plane: "pm"
component: "dopemux"
status: "skeleton"
---

# ADHD Cognitive Loop and UX Contracts

## Purpose

Dopemux UX constraints that preserve focus, reduce decision fatigue, and checkpoint progress.

## Scope

TODO: Define the scope of the ADHD execution model and UX constraints.

## Non-negotiable invariants

TODO: List UX invariants (e.g., "no long-running silent commands").

## FACT ANCHORS (Repo-derived)

TODO: Link to code that handles checkpointing and disclosure rules.

## Open questions

TODO: List ADHD/UX unknowns and how to resolve them.

## Focus windows and checkpointing
- 25 minute focus blocks
- checkpoint prompts at boundaries
- “pause and checkpoint” behavior

TODO: Define checkpoint artifact format.

## Progressive disclosure rules
- default outputs are short
- provide one recommended next step and 2 alternates max
- expand only on request

TODO: Define exact caps per output type.

## Complexity score gating
- define complexity score range 0..1
- example: >= 0.6 means chunk smaller and suggest scheduling focus

TODO: Define how complexity is computed and what inputs are allowed.

## Result caps
- search top_k default
- file diff caps
- plan step caps

TODO: Set defaults and override policy.

## Supervisor behavior from ADHD signals
- chunk size decreases as load increases
- verbosity reduces when tired or limits are low
- automatic “pause and checkpoint”

TODO: Define what signals exist today vs planned.

## Failure modes

TODO: too much output, too many choices, context switching loops.

## Acceptance criteria

TODO: Define 5 measurable UX success signals.
