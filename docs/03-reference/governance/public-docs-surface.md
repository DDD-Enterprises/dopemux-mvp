---
id: public-docs-surface
title: Public Docs Surface
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Defines the maintained public-facing and AI-readable docs surface for Dopemux.
---
# Public Docs Surface

This document defines the smallest maintained public-facing documentation surface for humans and AI tools.

It does not change authority order. Runtime code, config, compose wiring, tests, active entrypoints, and stronger governance docs remain higher authority than public-facing summaries.

## Purpose

The public docs surface should answer three questions quickly:

1. What is Dopemux?
2. What problem does it solve?
3. Where should a reader or AI tool go next for architecture, product framing, and governance limits?

## Included Files

The maintained public docs surface currently includes:

- `README.md`
- `QUICK_START.md`
- `llms.txt`
- `docs/INDEX.md`
- `docs/00-MASTER-INDEX.md`
- `PROJECT.md`
- `ARCHITECTURE.md`
- `PM_PLANE.md`
- `docs/04-explanation/overview/project-overview.md`
- `docs/04-explanation/overview/problem-statement.md`
- `docs/04-explanation/overview/system-map.md`
- `docs/04-explanation/architecture/dopemux-architecture.md`
- `docs/04-explanation/architecture/data-and-control-flow.md`
- `docs/04-explanation/product/positioning.md`
- `docs/04-explanation/product/homepage-copy.md`
- `docs/04-explanation/product/audience-personas.md`
- `docs/04-explanation/product/elevator-pitches.md`
- `docs/04-explanation/product/features-and-benefits.md`
- `docs/04-explanation/product/faq.md`
- `docs/04-explanation/product/public-copy-variants.md`
- `docs/03-reference/governance/dopemux-documentation-source-map.md`
- `docs/03-reference/governance/documentation-gap-register.md`
- `docs/03-reference/governance/doc-trust-map.md`
- `docs/03-reference/governance/authority-boundaries.md`
- `docs/03-reference/governance/governance-model.md`
- `docs/03-reference/systems/system-boundaries.md`
- `docs/03-reference/instructions/ai-agent-handoff-guide.md`
- `docs/06-research/extraction/rte-provider-structured-output-baseline.md`

## Authority Rules

- Public docs must not overclaim beyond active runtime and source truth.
- `UNKNOWN` remains `UNKNOWN` until verified.
- `NEEDS_REPO_VERIFICATION` remains open until repo inspection or runtime validation closes it.
- Retrieval output, bridge routes, mirrors, generated summaries, and audit artifacts must not be promoted into source truth.
- Public copy must preserve split authority across control, execution, workflow, PM metadata, decisions/progress/context, chronicle history, retrieval, bridge transport, operator support, and repo audit.
- External research can inform public docs, but it is advisory unless separately verified against repo/runtime behavior.

## Claim Guardrails

Use:

- operator control surface
- composed multi-system workspace
- split-authority development workflow
- derived retrieval
- bridge/proxy/event transport
- evidence artifact
- current-state, repo-grounded

Avoid unless stronger evidence is added:

- unified control plane
- one AI brain
- autonomous development platform
- unified PM platform
- unified memory system
- production-ready by default
- fully local and private by default
- bridge-owned truth
- retrieval as source truth

## llms.txt Rules

- Keep `llms.txt` curated and small.
- Prefer repo-relative links while GitHub is the primary public surface.
- Every link in `llms.txt` must point to an existing maintained file.
- `llms.txt` is a map, not a second README and not a full architecture explainer.
- If a standalone docs site becomes canonical, migrate links in a separate packet.

## Maintenance Rules

Review this surface when any of the following changes:

- project identity or architecture changes
- PM authority changes
- service ownership changes
- product docs or homepage copy change
- `README.md`, `docs/INDEX.md`, or `docs/docs_index.yaml` changes
- new public-facing docs are added
- new AI-facing docs surfaces such as `llms-full.txt` are introduced
- external RTE/provider assumptions are recrawled or implemented

## Review Checklist

Before closing a public-docs change:

- confirm that the opener still describes Dopemux as an operator-facing, split-authority workspace
- confirm that no claim silently upgrades a proxy, bridge, retrieval system, mirror, generated artifact, or audit report into source truth
- confirm that `UNKNOWN` and `NEEDS_REPO_VERIFICATION` markers are preserved where required
- confirm that `llms.txt` links still resolve
- confirm that docs indexes expose the public docs surface
- confirm that public docs remain consistent with `PROJECT.md`, `ARCHITECTURE.md`, `PM_PLANE.md`, and `docs/03-reference/systems/system-boundaries.md`
- confirm that the change did not touch runtime or service code unless separately authorized

## Not Run By This Surface

Maintaining the public docs surface does not by itself run:

- live Docker startup
- live provider calls
- live RTE extraction
- live service health checks

Those validations must be reported separately when performed.
