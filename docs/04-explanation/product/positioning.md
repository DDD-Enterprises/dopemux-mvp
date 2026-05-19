---
id: product-positioning
title: Product Positioning
type: explanation
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Repo-faithful positioning for Dopemux without monolithic assistant claims.
---
# Product Positioning

Dopemux is an operator-control plane for a split-authority development
workspace. It helps an operator coordinate startup, routing, execution handoff,
PM workflow, structured context, chronicle memory, retrieval, and repo-truth
audit surfaces without pretending those domains have one owner.

Dopemux is not a monolithic assistant. It is a control surface over multiple
systems with explicit authority boundaries.

## Positioning Statement

For operators and maintainers working across local services, PM tools, memory,
retrieval, and audit workflows, Dopemux provides a repo-grounded operator
workspace that routes work through the right authority slice and preserves
evidence about what is implemented, drifted, or UNKNOWN.

## Core Message

Dopemux turns a complex development-control stack into an operator-facing
workspace while keeping the source of truth visible. It coordinates the system;
it does not collapse task execution, PM state, memory, retrieval, bridge
routing, and repo audit into one brain.

## Claim Boundaries

| Claim class | Repo-faithful message | Evidence basis |
| --- | --- | --- |
| Implemented | `dopemux` is the operator CLI/control surface. | `pyproject.toml`, `src/dopemux/cli.py`, `README.md`, `ARCHITECTURE.md` |
| Implemented | Execution handoff goes through `scripts/taskx` to `scripts/dopetask` and then the external `dopetask` runtime. | `scripts/taskx`, `scripts/dopetask`, `.dopetask-pin`, `ARCHITECTURE.md` |
| Implemented | PM authority is split by write type. | `src/dopemux/pm/writes.py`, `PM_PLANE.md`, governance docs |
| Implemented | dopecon-bridge is proxy, routing, compatibility, and event transport only. | `services/dopecon-bridge/dopecon_bridge/routes.py`, system docs |
| Experimental | Some support and integration surfaces are active but drifted or unresolved. | `SERVICE_CATALOG.md`, system docs |
| Vision | A smoother operator experience can be built on top of these boundaries. | Inferred product direction, not runtime proof |
| UNKNOWN | A single repo-wide agent authority is not proven. | `AGENTS.md`, `truth-gaps.md`, component catalog |

## What To Say

- Dopemux is a split-authority operator workspace.
- Dopemux coordinates local services and workflow surfaces for development
  control.
- Dopemux preserves authority boundaries between PM metadata, workflow,
  decisions, progress, chronicle memory, retrieval, bridge routing, and repo
  audit.
- Dopemux can use retrieval and extraction outputs as evidence, but source files
  and runtime code remain stronger.

## What Not To Say

- Do not say Dopemux is a monolithic assistant.
- Do not say Dopemux is a unified PM platform.
- Do not say dopecon-bridge owns task, workflow, decision, progress, memory, or
  retrieval truth.
- Do not say dope-memory is all memory.
- Do not say dope-context retrieval output is source truth.
- Do not say Repo Truth Extractor artifacts outrank runtime.
- Do not claim production readiness or runtime drift closure from docs-only
  evidence.

## Short Description

Dopemux is an operator-facing control surface for a multi-system development
workspace. It routes work across execution, PM workflow, structured context,
chronicle memory, retrieval, bridge/proxy, ADHD support, and repo-truth audit
systems while keeping authority boundaries explicit.

## Tagline Candidates

- Control the workspace without losing the source of truth.
- A split-authority cockpit for development-control workflows.
- Repo-grounded coordination for complex operator workspaces.

These are positioning drafts, not additional runtime claims.
