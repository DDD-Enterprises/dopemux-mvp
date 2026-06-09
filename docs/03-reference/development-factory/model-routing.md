---
id: model-routing
title: Model Routing
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
last_review: '2026-06-06'
next_review: '2026-09-04'
prelude: Model Routing (reference) for dopemux documentation and developer workflows.
---
# Model Routing Policy

> **Note:** The formal versioned policy YAML/schema is deferred to `TP-DMX-MODEL-ROUTING-POLICY-001`.
> This document captures the design intent and stage-based routing contract.

---

## Stage-Based Model Split

Each stage of the factory pipeline is assigned a model tier chosen to balance cost, accuracy, and
role-separation requirements. Stages are discrete — a model assigned to one stage does not inherit
privileges of another.

| Stage key | Purpose | Model tier |
|---|---|---|
| `cheap_read` | grep, status, housekeeping, file existence | Fast/cheap (haiku-class) |
| `investigation` | Evidence gathering, path tracing, authority checks | Mid-tier |
| `planner_strong` | Architecture, scope design, packet authoring | Strong (GPT-5.5 / Opus) |
| `plan_challenge` | Adversarial challenge of planner output | Strong independent model |
| `implementer_standard` | Code writing, file editing | Mid-tier (sonnet-class) |
| `slice_review` | Per-file code review within packet | Mid-tier |
| `judge_strong` | Overall packet verdict, go/no-go | Strong (GPT-5.5 / Opus) |
| `self_audit` | NOT ALLOWED — implementer cannot self-audit | n/a |

**cheap eyes → strong brain → decent hands → strong judge → independent audit**

---

## Boundaries for `cheap_read` Stage

`cheap_read` models MUST NOT be used for:

- Architecture decisions
- Authority boundary checks
- Security analysis
- Workflow legality verification
- Task scope decisions

They are appropriate ONLY for deterministic read operations: `grep`, `ls`, `git status`, file
existence checks, port checks, and other operations where the answer is a mechanical fact with no
interpretive weight.

> **Root cause note:** Cheap models making architecture decisions is a documented root cause of
> hallucinated authority. The `cheap_read` stage exists to reduce per-run cost on the routine
> mechanical checks that precede every meaningful stage — it is not a general-purpose reasoning
> stage.

---

## Stage Independence and Model Selection

The `plan_challenge` stage MUST use a model that is independent of the `planner_strong` stage — not
the same model instance, and preferably a different provider. The purpose is genuine adversarial
challenge, not self-validation.

The `judge_strong` verdict is final within a capsule. It may not be appealed by the implementer.
Only the supervisor or Factory Controller may override a `judge_strong` NO-GO.

`self_audit` is not a valid routing target. If an implementer requests to audit its own output, the
Factory Controller rejects the capsule step and logs an obligation of class `AUTHORITY_CONFLICT`.

---

## Per-Capsule Overrides

Individual execution capsules may override the default model for any stage via the
`model_routing.stage_overrides` field. Overrides require supervisor sign-off when the stage is
`judge_strong` or `plan_challenge`. No override may assign a cheap/fast model to `judge_strong`,
`plan_challenge`, or `planner_strong`.

See [execution-capsule.md](execution-capsule.md) for the `model_routing` field definition.
