---
title: "Routing Policy and Cost"
plane: "pm"
component: "dopemux"
status: "skeleton"
---

# Model Routing, Plans, and Cost Optimization

## Purpose

How Supervisor chooses runner + model, using limits + preferences + cheap fallbacks.

## Scope

TODO: Define the scope of routing policy and cost management.

## Non-negotiable invariants

TODO: List routing invariants (e.g., "never exceed hard budget cap").

## FACT ANCHORS (Repo-derived)

TODO: Link to logic that maps stages to models and handles fallback.

## Open questions

TODO: List routing unknowns and how to resolve them.

## Preference ladder (policy)
1. Included plans (ChatGPT Plus / Anthropic Pro/Max / Copilot tier)
2. OpenAI Codex credits pool
3. API via OpenRouter/xAI/etc (region preference)
4. Cheapest stable fallback for bulk

TODO: Confirm the exact ladder and any exceptions.

## Stage-to-model mapping
- Preflight: Haiku
- Design/Arch/Audit: Opus
- Core implement: GPT-5.3-Codex
- Implement alt: Sonnet
- Git/admin/conport ops: mini
- Bulk/cheap: grok fast models

TODO: Replace with your actual supported model IDs and runner compatibility table.

## Where numbers come from

### Pricing sources

TODO: Store prices in config, not hard-coded.

### Limits sources

TODO: Identify limit scopes and reset signals.

### Quality sources
- pass rate
- rework count
- review delta

TODO: Define a v1 quality score.

## Long-term optimization loop

Record per run:
- tokens in/out
- wall time
- pass/fail
- rework count
- estimated cost

Policy v1:
- prefer lowest cost subject to pass rate >= threshold

TODO: Define thresholds and when to override for safety.

## Failure modes

TODO: limits mis-detected, cost overruns, wrong runner picked, quality collapse.

## Acceptance criteria

TODO: Provide 5 policy tests (synthetic scenarios) and expected routing choices.
