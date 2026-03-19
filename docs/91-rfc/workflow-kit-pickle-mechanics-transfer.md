---
id: workflow-kit-pickle-mechanics-transfer
title: Workflow Kit Pickle Mechanics Transfer
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-03-19'
last_review: '2026-03-19'
next_review: '2026-06-19'
prelude: RFC-level transfer matrix for adopting useful workflow mechanics from the Pickle Rick extension into Dopemux without importing its brand voice or provider-specific assumptions.
---
# Workflow Kit Pickle Mechanics Transfer

## Context

This RFC captures how useful mechanics from `/Users/hue/code/pickle-rick-extension` should map into Dopemux. It is intentionally explicit so later work does not accidentally import gimmicks, franchise language, or provider-specific assumptions.

## Transfer Matrix

| Source capability | Decision | Dopemux translation |
| --- | --- | --- |
| Hook-based workflow continuity | Adopt | Use Claude native hooks to inject context, log tool activity, and guard stop behavior |
| Explicit phase checkpoints | Adopt | Standardize on `<workflow-checkpoint ... />` tokens and persisted checkpoint history |
| Manager and worker split | Adopt | `workflow-manager` validates state while `workflow-executor` handles one task in isolation |
| Workspace and cwd reattachment | Adopt | Resolve workflows by workspace ancestry, family root, instance id, and recency |
| Per-task worktree isolation | Adopt | Reuse Dopemux instance and tmux orchestration instead of custom spawn scripts |
| Research and plan review gates | Adopt | Enforce `research_review` and `plan_review` before implementation |
| Provider-agnostic orchestration | Adapt | Keep state and skills provider-neutral while using Claude hooks first because Dopemux already ships them |
| Batch queue or jar execution | Adapt later | Keep out of the first wave until the single-workflow path is stable |
| Rich diff and PR preview UI | Adapt later | Add only after the kernel, hooks, and validation flows are stable |
| Overnight autonomous multi-task execution | Adapt later | Defer until safety and visibility are stronger |
| Rick and Morty persona voice | Reject | Replace with Dopemux ritual-daemon voice and calm aftercare |
| Insult or compliance framing | Reject | Never ship coercive or abusive user copy |
| Gemini-only command layer | Reject | Keep runtime-neutral abstractions and Dopemux-native CLI surfaces |
| Local markdown ticket system as authority | Reject | Dopemux PM systems remain canonical; local mirrors are temporary fallbacks only |
| Default infinite stop blocking loops | Reject | Block stop only when workflow state is active and no valid checkpoint or completion token exists |
| Toybox or novelty features | Reject | Keep the workflow kit focused on delivery quality and operator clarity |

## First-Wave Scope

The first wave should include:

- workflow kernel and persisted state
- CLI for `init`, `status`, `resume`, `cancel`, and `inspect`
- manager and executor roles plus persona assets
- workflow skill pack
- hook integration for continuity and bounded stop behavior

The first wave should not include:

- queue runners
- provider-specific command wrappers
- playful imported personas
- unrelated dashboard polish

## Policy Guardrail

Any future change that imports direct references to franchise names, Gemini extension commands, or local markdown ticket authority as canonical workflow truth should be treated as a design regression and reviewed against this RFC before merge.
