---
id: rfc-0015
title: UX Phase Tracker & Preset Layouts for Workflow States
type: rfc
status: draft
author: @hu3mann
created: 2025-09-21
last_review: 2025-09-21
sunset: 2025-10-21
feature_id: feat-docs-governance
tags: [ux, workflow, layout, productivity, rails]
links:
  related_adrs: []
  related_rfc: []
---

## Problem

Developers often lose track of which phase of the workflow they're in (brainstorm, defining, designing, implementing, shipping).
Without visual cues or structured layouts, docs / design / review tend to overlap or diverge incorrectly, leading to wasted time, duplicated work, and unclear status.

## Context

- We already enforce doc intents (Diátaxis), ADRs, and manifest metadata.
- We use tmux, slash-commands, Claude Code, and MCP tools.
- Several ideas discussed: Double-Diamond rails (Discover → Define → Develop → Deliver), preset working layouts in the terminal / Claude Code.
- There is no formal UX system yet to reflect phases; dev flow currently relies on manual context.

## Options

| Option | Pros | Cons |
|---|---|---|
| No change ‒ rely on developers to self-track | Zero cost, simplicity | Prone to drift; inconsistent phase tracking; docs / ADRs might be created at wrong time; overhead on reviews |
| UI/CLI prompts & manual selection of phase | Gives explicit anchor; low overhead | Still manual; might be ignored; complexity in implementing prompts |
| **UX rails + preset layouts + automatic phase tags** | High guidance; helps alignment; reduces ambiguity; easier to enforce flows; better onboarding / visibility | More implementation work; sometimes forced structure; edge cases where phase boundaries are blurred |

## Proposed Direction

Adopt **UX rails** representing phases:
- **Discover / Brainstorm** → diverging ideas & raw research
- **Define** → decisions / ADR / refined design
- **Develop** → implementation / how-to / reference updating
- **Deliver / Ship / Operate** → shipping, runbooks, monitoring

Implement the following features:
1. Prompt when starting new RFC or Feature Hub to pick current phase, stored in metadata (e.g. `phase: define`).
2. Slash-commands/layouts in Claude Code or terminal: e.g. `/layout:discover`, `/layout:develop` that set up panes/tools (e.g. context pull, research panel) appropriate for the phase.
3. UI badge / indicator in Feature Hub / ARC42 / docs header: show current phase.
4. Possibly enforce rules per phase (via lint or CI): e.g., in Discover, no ADR allowed; in Deliver, each Feature Hub must have runbooks and updated reference docs.

## Open Questions

- What is the authoritative list of phases (names, number)? Are four enough or need more fine-grained?
- Do phases overlap or can someone be in multiple at once?
- What layouts / presets are most useful (terminal splits, window/tab setups)?
- How to store the "phase" metadata without polluting docs?
- How strict should enforcement be (warning vs blocking)?

## Risks

- Developers may find the phase prompts / layouts too restrictive or overhead heavy.
- Ambiguity when features don't follow clean sequential phases.
- Extra tooling burden (layout definitions, state management).
- Cognitive friction if the phase is wrong or mis-set.

## Timeline

1. Week 1: Prototype `phase` metadata + layout presets + CLI / slash commands for switching.
2. Week 2: Get feedback from team; define layout presets.
3. Week 3: Accept or reject RFC → if accepted, promote to ADR.
4. Week 4: Begin implementing badge/headers + enforcing rules in pre-commit or CI.

## Reviewers

- @hu3mann
- @team
- UX / Developer Experience stakeholder
- Possibly someone from UX or PM side