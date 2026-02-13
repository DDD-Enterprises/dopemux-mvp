---
title: "Supervisor Packet Format"
plane: "pm"
component: "dopemux"
status: "skeleton"
---

# Supervisor Packet Generation and Manual Model Switching

## Purpose

Formalize packet schema and the fewest-messages manual switching format.

## Scope

TODO: Define the scope of packet generation and model switching protocols.

## Non-negotiable invariants

TODO: List packet invariants (e.g., "required fields must be present").

## FACT ANCHORS (Repo-derived)

TODO: Link to packet generation logic and runner-specific wrappers.

## Open questions

TODO: List packet/switching unknowns and how to resolve them.

## Packet schema (minimal)

Required fields:
- id
- title
- objective
- scope (in/out)
- invariants
- plan steps
- exact commands
- output capture rules
- acceptance criteria
- rollback steps
- stop conditions

TODO: Decide YAML vs JSON vs Markdown frontmatter and pin it.

## Chunking format per step (manual mode)

Example slicing:
- CHUNK 1/3: Haiku preflight
- CHUNK 2/3: Opus design
- CHUNK 3/3: GPT-5.3-Codex implement

TODO: Specify exact chunk envelope format and filenames.

## Runner-specific wrappers
- claude-code formatting rules
- codex formatting rules
- copilot-cli formatting rules

TODO: Provide examples for each runner.

## Resume strategy
- how manual chunks advance
- sentinel files (STEP_ALPHA.DONE etc)
- exit code semantics (example: exit 2 means manual continuation required)

TODO: Pin the exact sentinel scheme.

## Failure modes

TODO: partial completion, chunk mismatch, wrong runner used.

## Acceptance criteria

TODO: Provide a complete example packet and manual run path.
