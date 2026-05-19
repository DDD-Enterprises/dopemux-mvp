---
id: public-copy-variants
title: Public Copy Variants
type: explanation
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Repo-faithful homepage, README, and launch-copy variants for the public documentation surface.
---
# Public Copy Variants

This document is a reusable copy source, not a runtime source.

Use these variants to keep the README, homepage, launch copy, product summaries, and AI-facing summaries aligned with repo truth. If runtime evidence does not support a phrase, remove the phrase instead of polishing around the gap.

## Guardrails

- Dopemux is an operator-facing control surface and composed multi-system workspace.
- Dopemux coordinates multiple systems without making one service the owner of every domain.
- Authority remains split across control, execution, workflow, PM metadata, decisions/progress/context, chronicle history, retrieval, bridge transport, operator support, and repo audit.
- Retrieval output, bridge routes, mirrors, and audit artifacts are evidence or transport surfaces, not source truth.
- Avoid production-readiness, autonomy, unified-platform, unified-PM, or unified-memory claims unless runtime validation proves them.
- Prefer exact language over impressive language.

## Technical Variant

### Homepage Headline

Operator control plane for split-authority development workflows

### Homepage Subheadline

Coordinate startup, execution handoff, workflow state, structured context, chronicle history, retrieval, routing, operator support, and repo audit without pretending one system owns it all.

### Support Bullets

- Route work across services while keeping ownership visible.
- Keep retrieval and audit output useful without letting them outrank source truth.
- Preserve `UNKNOWN`, drift, and runtime verification gaps until proof closes them.

### README Opening

Dopemux is an operator-facing workspace for development-control work across multiple systems. It starts with `dopemux`, but authority stays where the repository proves it: control, execution, workflow state, PM metadata, decisions/progress/context, chronicle history, retrieval, routing, operator support, and audit each live in their own lane.

## Founder / Operator Variant

### Homepage Headline

Coordinate the stack without lying about the source of truth

### Homepage Subheadline

Dopemux gives operators one control surface for a development stack that still has multiple owners. That is the architecture, not a copy problem.

### Support Bullets

- Make complex operator work visible instead of flattening it into one fake assistant.
- Route PM, context, history, retrieval, bridge, and audit work through the right authority slice.
- Keep proof and drift explicit instead of hiding them behind cleaner copy.

### README Opening

Most workflow tools flatten complexity into a cleaner story than the runtime deserves. Dopemux does the opposite. It helps operators move work across a multi-system stack while keeping ownership visible instead of pretending one service owns everything.

## Product Variant

### Homepage Headline

Control complex development workflows with visible authority boundaries

### Homepage Subheadline

Keep work moving across services, workflow state, context, history, retrieval, routing, and audit while staying explicit about which system owns what.

### Support Bullets

- One operator workspace for coordination, not one monolithic backend.
- Clear authority lanes for control, execution, workflow, context, retrieval, bridge transport, and evidence.
- Better handoffs, less silent drift, fewer truth mistakes.

### README Opening

Dopemux helps operators coordinate complex development work without losing the source of truth. It is a control surface, not a monolith: one workspace for routing the work, not one system claiming authority over every domain.

## Sharp Developer Variant

### Homepage Headline

Split-authority control for AI-assisted development work

### Homepage Subheadline

Dopemux keeps execution, PM, memory, retrieval, routing, and proof in their own lanes so operators can move faster without inventing a single owner.

### Support Bullets

- Bridges stay bridges.
- Retrieval stays derived.
- Proof does not outrank the runtime it describes.

## Anti-Claims

Do not use these in public copy:

- unified control plane
- one AI brain
- autonomous development company
- production-ready platform
- never fail
- all-in-one PM and memory system
- fully local and private by default
- bridge-owned truth
- retrieval as source truth

Each of those claims outruns current repo evidence.

## Usage Rule

If a surface needs more detail than these openers provide, link to `README.md`, `PROJECT.md`, `ARCHITECTURE.md`, `PM_PLANE.md`, `docs/03-reference/systems/system-boundaries.md`, and `docs/04-explanation/product/faq.md` instead of expanding a short opener into a miniature architecture manual.
