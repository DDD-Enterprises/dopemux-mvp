---
id: DOPEMUX_COCKPIT_TUI_DESIGN_SYSTEM_UI_KIT_README
title: Cockpit UI Kit
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-27'
last_review: '2026-04-27'
next_review: '2026-06-15'
prelude: CDN-dependent React reference render for the Surface-A cockpit composition.
---
# Cockpit UI Kit

CDN-dependent React+Babel visual reference for the dopemux cockpit TUI
primitive set. It mirrors the intended shape of `src/dopemux/ui/cockpit/`
seed data, but this package does not contain runtime proof that it renders
in a terminal.

This directory is reference-only until package-contained browser evidence
or runtime renderer evidence is added.

## Files

- `index.html` — visual reference cockpit, default 120x40, with a size
  toggle for 100x32 and 80x24; requires unpkg React/ReactDOM/Babel
- `Primitives.jsx` — the cockpit primitives: `Frame`, `Pane`, `PaneHeader`,
  `Rule`, `Row`, `ServiceRow`, `RunRow`, `ModeBar`, `Inspector`, `Chip`,
  `Src`, `Selector`, `CommandRail`, `StatusRail`, `HintRail`
- `Cockpit.jsx` — composed screen + size-switch shell
- `seed.js` — deterministic seed data (mirrors `seed.py`)
- `cockpit.css` — styling layer; consumes `colors_and_type.css`

## Component contract

Every component enforces:
- closed chip set: `LIVE | BLOCKER | OVERRIDE | LOGGED | AFTERCARE | EDGE`
- each logical data/provenance record carries `SRC=<service>` once
- panes declare `domain:`, `authority:`, `role:`, and `next_action:` in
  their header
- chrome rows carry no `SRC=`
- bridge / proxy actions live in their own pane, labeled `Bridge adapter/proxy: dopecon-bridge`

## Not included

By contract:
- no hover states (this is a TUI; the keyboard is the input)
- no mouse handlers beyond the size switcher
- no animations
- no chat / chat composer / unified PM record
- no new chips, modes, or status tokens beyond the closed set
