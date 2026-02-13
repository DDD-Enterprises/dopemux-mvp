---
title: "Instance and Worktree Isolation"
plane: "pm"
component: "dopemux"
status: "skeleton"
---

# Instance Isolation and Workspace Identity

## Purpose

Mechanics and invariants: port offsets, workspace_id, worktree safety.

## Scope

TODO: Define the scope of instance isolation and workspace management.

## Non-negotiable invariants

TODO: List isolation invariants (e.g., "no cross-worktree filesystem access").

## FACT ANCHORS (Repo-derived)

TODO: Link to worktree management and workspace identity implementations.

## Open questions

TODO: List isolation unknowns and how to resolve them.

## Worktree identity rules
- how workspace_id is derived
- where it is stored
- how it is propagated

TODO: Define canonical workspace_id contract and collision avoidance.

## Per-worktree MCP isolation
- context isolation rules
- tool access boundaries

TODO: Define what can be shared and what cannot.

## Port offset scheme
- multi-instance port mapping
- reserved ranges

TODO: Document the exact scheme once verified.

## Cleanup and recovery
- safe cleanup of a broken instance
- recovery steps without data contamination

TODO: Provide an operator playbook section and a scripted checklist.

## Failure modes

TODO: port collisions, cross-worktree reads, stale workspace_id, shared caches.

## Acceptance criteria

TODO: Provide test scenarios for isolation boundaries.
