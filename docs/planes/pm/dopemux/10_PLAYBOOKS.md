---
title: "Operational Playbooks"
plane: "pm"
component: "dopemux"
status: "skeleton"
---

# Operational Playbooks

## Purpose

How to run this when tired.

## Scope

TODO: Define the scope of operational playbooks for Dopemux.

## Non-negotiable invariants

TODO: List operational invariants (e.g., "always follow the startup checklist").

## FACT ANCHORS (Repo-derived)

TODO: Link to existing checklists and verification scripts.

## Open questions

TODO: List operational unknowns and how to resolve them.

## Start session checklist
- load workspace
- verify worktree identity
- verify MCP health
- verify limits mode
- set focus window

TODO: Provide a short and a long checklist.

## Build packet fast checklist
- define objective
- define scope
- define invariants
- define plan steps
- define commands
- define acceptance criteria and stop conditions

TODO: Provide template snippet.

## When MCP is down
- detect
- degrade path
- refuse if mandate cannot be met
- log to ConPort

TODO: Provide a decision tree.

## When tests fail (RCA loop)
- capture outputs
- isolate failure
- minimal diff fix
- rerun exact commands
- record results

TODO: Provide a hard “no skipping” rule list.

## When limits are low (cheap-mode)
- switch model ladder
- reduce verbosity
- increase chunking
- defer heavy work

TODO: Provide cheap-mode defaults.

## Acceptance criteria

TODO: Define how we know playbooks are usable (time-to-next-action, error rate).
