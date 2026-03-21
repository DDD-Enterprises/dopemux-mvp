---
id: workflow-kit-architecture
title: Workflow Kit Architecture
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-03-19'
last_review: '2026-03-19'
next_review: '2026-06-19'
prelude: Design rationale for the Dopemux workflow kit, including phase gates, manager and executor lanes, and hook-driven continuity.
---
# Workflow Kit Architecture

The workflow kit brings a bounded, stateful execution model into Dopemux without importing the brand voice or command surface of the upstream extension that inspired it.

## Why Dopemux Needed It

Dopemux already had strong primitives for tmux isolation, roles, and hook registration. What it was missing was a shared workflow state machine that could:

- survive worktree and instance switches
- force research and plan reviews before coding
- keep manager and executor responsibilities separate
- preserve continuity through Claude stop hooks

## Core Design

### Stateful Kernel

The workflow kernel stores state under `.dopemux/workflows/<workflow_id>/state.json` and keeps a history of prompts, tool usage, checkpoints, and phase changes. This gives the manager lane a durable record instead of relying on conversation memory alone.

### Manager and Executor Split

The manager lane owns workflow state, gate enforcement, and worker validation. The executor lane owns one task at a time inside an isolated worktree or instance. This keeps task scope narrow and makes checkpoint review deterministic.

### Review-Gated Lifecycle

The lifecycle is intentionally strict:

`brief -> breakdown -> research -> research_review -> plan -> plan_review -> implement -> refactor -> complete`

Every transition after `research` requires proof, not intent. That constraint is the main quality upgrade over ad hoc agent loops.

### Hook-Driven Continuity

Claude native hooks inject workflow context at session start, record tool activity, and block stop attempts when a workflow is still active without a valid checkpoint. This protects the run from disappearing into a vague "I think I'm done" state.

## What Was Kept and What Was Rewritten

Kept:

- stateful progression
- explicit phase checkpoints
- manager and worker isolation
- workspace-aware resume behavior
- hook-based continuity

Rewritten for Dopemux:

- tone and persona
- skill language
- PM authority rules
- stop semantics
- provider-neutral runtime assumptions

Rejected outright:

- imported franchise persona voice
- insult-based compliance framing
- Gemini-specific command surfaces
- toybox features unrelated to engineering quality

## Brand Alignment

The workflow kit follows Dopemux's evidence-first and ADHD-aware rules:

- explain before acting
- keep verification explicit
- avoid cognitive sprawl
- provide calm aftercare instead of hype

That translation matters because the mechanics are useful, but the imported personality would dilute the Dopemux product voice.
