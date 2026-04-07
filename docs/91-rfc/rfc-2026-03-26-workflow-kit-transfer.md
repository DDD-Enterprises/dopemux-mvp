---
id: rfc-2026-03-26-workflow-kit-transfer
title: Workflow Kit Transfer from Pickle Rick Mechanics
type: rfc
status: draft
author: '@codex'
date: '2026-03-26'
created: 2026-03-26
updated: 2026-03-26
owner: dopemux
prelude: First-wave RFC for adopting, adapting, or rejecting imported workflow-kit
  mechanics into Dopemux.
derived_from:
- workflow-kit import analysis
summary: Classifies each imported Pickle Rick extension capability as adopt now, adapt
  later, or reject for the Dopemux internal workflow kit.
last_review: '2026-03-26'
next_review: '2026-06-24'
---
# Workflow Kit Transfer from Pickle Rick Mechanics

## Purpose

Freeze the first-wave transfer decisions for the Dopemux internal workflow kit so later iterations do not accidentally import Gemini-specific behavior, off-brand persona mechanics, or local markdown task authority.

## Adopt Now

- Stateful workflow phase progression persisted in `.dopemux/workflows/<workflow_id>/state.json`.
- Review-gated execution using explicit `research_review` and `plan_review` checkpoints.
- Hook-managed continuity for `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, and `SessionEnd`.
- Cwd-to-workflow resolution using workspace ancestry and instance ID.
- Manager/executor separation using `workflow-manager` and `workflow-executor` roles.
- Per-task executor launch planning built on existing Dopemux worktree and instance machinery.
- Concise workflow telemetry: phase, task, iteration budget, time budget, checkpoint status, missing artifacts.

## Adapt Later

- Queue or batch containers similar to Pickle Rick "jar" flows.
- PR preview UI and richer operator dashboards for workflow state.
- Long-running autonomous overnight multi-task runs.
- Expanded provider-specific wrappers once the provider-neutral workflow contract is stable.

## Reject

- Pickle Rick or Morty naming, voice, or insult-driven compliance patterns.
- Gemini-only command model and provider-coupled prompt structure.
- Infinite or default stop-looping behavior.
- Local markdown task files as canonical authority.
- Toybox, game, or gimmick workflow surfaces.

## Authority Rules

- Dopemux PM plane remains canonical for workflow task truth.
- Local workflow task data is a mirror and may not override PM state.
- Workflow hooks may enrich context and enforce gates, but they may not fabricate success.
- Completion requires both evidence and the configured completion token.

## Guardrails

- No implementation planning before approved research.
- No implementation execution before approved plan.
- No completion while required artifacts or workflow tasks remain incomplete.
- No persona transfer that conflicts with Dopemux brand or operator trust.
