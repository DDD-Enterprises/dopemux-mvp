---
id: tui-framework-architecture
title: TUI Framework Architecture
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-19'
prelude: Normalized research summary for a tmux-first Dopemux Cockpit framework architecture.
last_review: '2026-05-19'
next_review: '2026-08-17'
---
# TUI Framework Architecture

Source: `/Users/hue/Downloads/deep-research-report 14.md`

SHA256:
`5757d34173f9931aeda6e33db8c3d0f89a984fca3f77c123bebed7843105dc6d`

Classification: research input. This document is not repo truth.

## OBSERVED

- The repo already has a Cockpit command surface that can render deterministic
  plain/audit output or launch a thin Textual shell.
- `src/dopemux/ui/cockpit/render.py` is the deterministic render layer. It
  declares `80x24` as the minimum supported viewport and produces ANSI-free,
  stable text for tests.
- `src/dopemux/ui/cockpit/app.py` is a thin Textual surface over the renderer.
- `src/dopemux/commands/cockpit_commands.py` exposes `120x40`, `100x32`, and
  `80x24` presets.
- Existing tests verify deterministic rendering, split authority labels,
  forbidden phrase exclusions, bridge collapse at `80x24`, and blocker behavior
  below minimum size.
- The repo already contains `docs/03-reference/python-tmux-research.md`, which
  records prior direction around libtmux plus Textual architecture.

## INFERRED

- The best architecture is a hybrid Python CLI plus deterministic renderer plus
  optional Textual shell plus tmux orchestration.
- Textual is a suitable richer shell because it fits the current Python runtime
  and test structure, but it must not become the source of truth.
- Rich is useful for presentation, not as the primary app framework.
- prompt_toolkit or plain deterministic text is the correct fallback for
  constrained mobile terminals.
- Bubble Tea, Lip Gloss, and Ratatui are credible terminal frameworks, but a Go
  or Rust cockpit rewrite would broaden the repo blast radius and duplicate
  current Python renderer work.
- Pure tmux scripting should remain orchestration only. Domain logic, proof
  display, adapters, and action contracts should not migrate into tmux snippets.

## CONFLICTING

- Current runtime blocks below `80x24`. The mobile-first research recommends
  a degraded under-70-column mode. That is a future runtime/prototype question,
  not a docs packet implementation change.
- Current design-system docs are `120x40` first. Mobile-first use requires
  inverting the layout priority for phone-sized clients while preserving the
  existing desktop contract.

## UNKNOWN

- There is no repo validation proving Textual, prompt_toolkit, Bubble Tea, and
  Ratatui behavior side by side inside Blink on iPhone portrait.
- Exact Unicode, glyph, terminal feature, and color behavior across Blink, tmux,
  SSH, Mosh, Textual, and fallback renderers remains unproven.
- The future runtime mapping between current safe-action tiers in
  `runtime_contract.py` and the more descriptive tier names documented in the
  mobile spec remains unresolved.

## Architecture Contract To Carry Forward

- Headless domain/adapters own state and actions.
- Deterministic renderer owns stable, testable snapshots.
- Textual owns optional richer interaction only.
- Plain/audit output must remain a guaranteed fallback.
- tmux owns session persistence, attach/detach, pane/window orchestration, and
  reconnect ergonomics.
- Adapters return immutable snapshot payloads plus proof/provenance metadata,
  never framework widgets.
- Bounded polling is preferred for mobile status. Stream only log-like data.
- Runtime validation should include deterministic renderer tests, Textual
  headless tests at `80x24`, `100x32`, and `120x40`, and isolated tmux
  integration only when runtime work is actually authorized.
