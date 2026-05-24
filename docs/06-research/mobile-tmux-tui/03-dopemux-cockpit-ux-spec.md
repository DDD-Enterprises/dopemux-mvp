---
id: dopemux-cockpit-ux-spec-research
title: Dopemux Cockpit UX Spec Research
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-19'
prelude: Normalized research summary for a mobile-first tmux Cockpit UX specification.
last_review: '2026-05-19'
next_review: '2026-08-17'
---
# Dopemux Cockpit UX Spec Research

Source: `/Users/hue/Downloads/deep-research-report 13.md`

SHA256:
`e7550446b250eef4995dc605432342dc1c3c6a9010164479823e7e6105c809f2`

Classification: research input. This document is not repo truth.

## OBSERVED

- The repo authority model is already explicit: `dopemux` is operator control,
  `dopetask` is execution after handoff, task-orchestrator owns workflow
  transitions, Leantime owns PM metadata, ConPort owns decisions/progress,
  dope-memory owns chronicle receipts, dope-context owns retrieval, and
  dopecon-bridge is proxy/routing/event transport only.
- Existing Cockpit docs already require authority labels, pane declarations,
  bridge segregation, provenance labels, forbidden phrases, and blocker behavior
  below `80x24`.
- Existing Cockpit runtime already implements a deterministic static PM shell
  and tests architecture-safety constraints.
- Existing Command Palette, Settings/Admin/Runtime, Safe Action Gate, and
  Unknown/Drift surfaces are secondary surfaces, not top-level authority modes.

## INFERRED

- The mobile Cockpit should retain the authority contracts but invert layout
  priority: single-focus first, multi-pane only when viewport supports it.
- Command Palette and Safe Action Gate should be full-screen overlays on mobile.
- Breadcrumbs should show both route and authority, for example
  `Queue / TP-055 / detail / AUTH=task-orchestrator`.
- Search and filters should use shared prefixes across search and palette:
  `auth:`, `writer:`, `class:`, `place:`, `proof:`, `status:`, `coverage:`,
  `src:`, `tp:`, and `svc:`.
- Proof and evidence viewing must show artifact paths, validation status,
  receipt IDs, request correlation, and canonical writer. Absence of proof is
  visible state, not success.

## CONFLICTING

- Research recommends degrading below `80x24`; current runtime and design-system
  acceptance require a `[BLOCKER]` below `80x24`. The new repo-facing spec
  preserves this as a conflict and documents the mobile-first behavior as a
  future acceptance contract only.
- Research recommends avoiding F-key-only navigation and mouse-required
  controls. Existing mobile tmux config currently exposes F-key jumps and mouse
  support. The repo-facing spec treats these as optional conveniences, not core
  input contracts.

## UNKNOWN

- Canonical writers for several future actions are not proven until a concrete
  runtime action catalog exists.
- The exact safe-action tier mapping to current runtime tier constants is
  unresolved.
- Future proof bundle schemas for mobile UI actions are not implemented by this
  docs packet.
- Terminal diagnostics capability probing is not yet implemented.

## UX Rules To Carry Forward

- The Cockpit is a viewport over authoritative systems, not a canonical system.
- Every write/action names the upstream canonical writer or blocks as UNKNOWN.
- Bridge and retrieval outputs are visibly labeled derived/proxy output.
- Confirmation is intent evidence only. It is not completion proof.
- Proof must be file-backed and replayable.
- Dangerous or unknown actions fail closed.
- On mobile, overlays beat cramped multi-pane layout.
- Empty states and error states must name the authority or source they depend on.
