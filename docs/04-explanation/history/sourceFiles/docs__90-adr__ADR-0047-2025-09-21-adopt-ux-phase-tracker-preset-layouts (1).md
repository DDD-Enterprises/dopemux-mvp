---
id: adr-0047
title: Adopt UX Phase Tracker & Preset Layouts
type: adr
status: proposed
date: 2025-09-21
author: @hu3mann
derived_from: rfc-0015
tags: [ux, workflow, layout]
---

## Context & Problem Statement

Developers sometimes lose track of which phase of the workflow they are in (Brainstorm/Discover, Define, Develop, Deliver). Without explicit structure, things can overlap incorrectly, documentation can get ahead of decisions, and the transitions between phases are fuzzy. We've discussed Double-Diamond style rails and various layouts/tools, but there's no formal decision yet.

## Decision Drivers

- Need for clarity in phase boundaries to avoid mixed work or misaligned expectations.
- Desire for consistency and better UX in dev flow.
- Want tooling/layouts to align with phases (so documentation, design, implementation follow predictable patterns).
- Better onboarding / visibility for new features / devs.

## Considered Options

| Option | Pros | Cons |
|---|------|-------|
| Do nothing / keep status quo | Zero cost; minimal friction | High risk of drift; inconsistent workflows; more confusion in reviews |
| Manual phase selection + minimal prompts | Some clarity; low cost to implement | May be ignored; still manual; no layout support; weak enforcement |
| **UX phase rails + presets/layouts + automatic phase metadata** | Clear guidance; enforced structure; better alignment; helps automation and reviews | Higher upfront work; may annoy devs in edge cases; need to maintain presets and layouts; special cases |

## Decision Outcome

Chosen option: **UX phase rails + presets/layouts + automatic phase metadata**

- Introduce a `phase:` field in front-matter for RFCs, Feature Hubs, or documents.
- Create CLI/slash commands/layout presets: e.g. `/layout:discover`, `/layout:define`, `/layout:develop`, `/layout:deliver` that configure the workspace (context panels, research panel, code view, etc.).
- Add a visual badge or UI indicator in Feature Hub docs to show current phase.
- Enforce rules per phase via lint or CI: e.g., allow ADR only in Define or later; require reference docs in Deliver; restrict raw research to Discover.

## Consequences

- **Positive**: Increased clarity of workflow; better visibility for team; less drift/misaligned docs; improves consistency.
- **Negative**: More upfront workload: defining presets/layouts; devs may feel constrained; potential edge cases where phases overlap.
- Need ongoing maintenance of layout definitions and guardrails.
- Might require some refactoring of existing docs to include phase metadata and badge UI.

## Implementation Steps / Follow-Ups

1. Define canonical list of phases (names, order).
2. Build preset layouts in Claude Code / terminal tabs / tmux.
3. Update slash commands `/rfc:new`, `/doc:new`, etc., to accept `--phase` param.
4. Update front-matter templates to include optional `phase:` field.
5. Add checks: docs lint, CI gates for phase rules.
6. Update arc42:
   - §4 Solution Strategy: include phase rails decision
   - §6 Runtime View: scenarios showing phase transitions
   - §8 Cross-cutting Concepts: phase metadata, presets layouts.

## Validation

We will consider the decision successfully implemented and useful if:

- At least 80% of new RFCs/Feature Hubs have `phase:` front-matter set.
- Code reviews / PRs detect when phase rules aren't followed (e.g. ADR created in Discover).
- Team finds the layout presets usable.
- Internal feedback shows less drift / fewer "missing context" complaints in features.