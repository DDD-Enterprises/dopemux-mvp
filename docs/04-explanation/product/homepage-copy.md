---
id: homepage-copy
title: Homepage Copy
type: explanation
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Repo-faithful homepage copy drafts for Dopemux product positioning.
---
# Homepage Copy

## Purpose

This is copy source, not a published homepage and not runtime proof. It keeps
public-facing language aligned with repo evidence, split-authority boundaries,
and known drift.

The homepage should make the operator value legible before it lists systems.

## Primary Hero

### Headline

Operator control plane for split-authority development workflows

### Subheadline

Coordinate complex development work without losing the source of truth.
Dopemux gives operators a repo-grounded control surface for routing work across
multiple authority lanes while keeping proof, drift, and ownership visible.

### Primary Value

Move faster through the stack without flattening PM, memory, retrieval, bridge,
execution, and audit into one false owner.

## Proof Strip

| Proof point | Grounded copy | Boundary |
| --- | --- | --- |
| Operator entrypoint | `dopemux` is the operator control surface for startup, routing, MCP/server coordination, and downstream delegation. | It does not own every downstream truth domain. |
| Execution boundary | Local wrappers hand execution to the pinned external `dopetask` runtime. | The external runtime implementation is outside this repo. |
| Split PM authority | PM metadata, workflow transitions, decisions, progress, and historical receipts stay in separate authority lanes. | The repo does not prove one PM backend. |
| Derived retrieval | dope-context and ConPort help find source, docs, and structured context. | Retrieval output must be checked against source truth. |
| Evidence-first audit | Repo Truth Extractor produces evidence artifacts. | Artifacts do not outrank runtime code, config, tests, or active entrypoints. |

## What Dopemux Solves

Development-control work spans more than one system. Operators need to start
services, route execution, inspect PM state, preserve decisions, retrieve
context, keep history, and generate proof. The failure mode is not only slow
work; it is losing track of which system owns the claim.

Dopemux solves for current-state coordination with explicit authority
boundaries. It helps an operator move through the workflow while keeping the
source of truth visible.

## What Dopemux Is Not

Dopemux coordinates work across authority lanes. It does not collapse those
lanes into one owner.

It is not:

- one AI assistant
- one PM platform
- one memory system
- an unsupervised development system
- a guarantee of production readiness
- proof that all runtime drift is closed
- proof of fully local, private, or offline operation by default

## Section Blocks

### Keep Authority Visible

Route work through a single operator control surface while preserving separate
truth lanes for execution, PM metadata, workflow transitions, decisions,
progress, chronicle receipts, retrieval, bridge transport, operator support,
and repo audit.

### Treat Retrieval As Evidence

Use derived retrieval to find relevant source and documentation, then verify
claims against the runtime files, configs, tests, active entrypoints, and
stronger governance docs.

### Preserve Proof And Drift

Carry `UNKNOWN`, `NEEDS_REPO_VERIFICATION`, validation output, and residual
risk through handoff instead of turning unresolved runtime state into polished
certainty.

## Audience Snapshot

Dopemux is for operators and maintainers coordinating complex development work
across multiple repo-backed systems. It is especially useful when correctness
depends on choosing the right authority lane, preserving an audit trail, and
keeping current-state evidence separate from advisory or derived context.

## Messaging Rule

Public copy may simplify the route into Dopemux, but it must not simplify the
authority model. If a claim needs more than a short homepage section, link to
`README.md`, `PROJECT.md`, `ARCHITECTURE.md`,
`docs/03-reference/systems/system-boundaries.md`, and
`docs/04-explanation/product/faq.md`.
