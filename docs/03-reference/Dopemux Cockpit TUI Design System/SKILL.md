---
name: dopemux-cockpit-design
description: Use this skill to generate well-branded TUI / cockpit interfaces and
  assets for dopemux, either for production or throwaway prototypes/mocks/etc. Contains
  essential design guidelines, colors, type, fonts, assets, and the cockpit UI kit
  (frame, panes, status chips, mode bar, inspector, command/status rails) for terminal-native
  operator surfaces. Authority before aesthetics; closed chip set; 120x40 first.
user-invocable: true
id: skill
title: Skill
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-01'
last_review: '2026-05-01'
next_review: '2026-07-30'
prelude: Skill (reference) for dopemux documentation and developer workflows.
---
Read the `README.md` file within this skill, and explore the other available files.

If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out and create static HTML files for the user to view. If working on production code, you can copy assets and read the rules here to become an expert in designing with this brand.

If the user invokes this skill without any other guidance, ask them what they want to build or design, ask some questions, and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.

## Hard contract (do not violate)

- **Status chips are closed**: `LIVE | BLOCKER | OVERRIDE | LOGGED | AFTERCARE | EDGE`. Never invent new chips. Web variants map: `DEGRADED→OVERRIDE`, `FAILED→BLOCKER`, `BLOCKED→BLOCKER`, `SYNC→AFTERCARE`; `UNKNOWN` remains `UNKNOWN` and must not be collapsed into `EDGE`.
- **Authority before aesthetics**: every pane declares `authority:`; every row carries `SRC=<service>`.
- **Bridge / proxy actions are segregated** into their own pane labeled `adapter-only segregated`.
- **Three sizes only**: `120x40` (canonical), `100x32`, `80x24`. Below 80x24 = `[BLOCKER]`.
- **No web UI, mouse interactions, hover states, chat surfaces, animations, gradients, rounded corners, shadows, or emoji.**
- **Type**: monospace only (JetBrains Mono Nerd Font preferred). Single weight per surface; emphasis = bold + color.
- **Forbidden vocabulary** (validated by `cockpit/tokens.py`): `magic, brain, autonomous, smart, seamless, next-gen, all set, everything looks good, supercharged, probably, maybe, I think, as an AI`. Forbidden arrows: `→ ⇒ ➜`. Forbidden ellipsis: `… ...`. Use `->`.
- **ADHD/lifestyle features are advisory/future-only** unless runtime evidence proves implementation.

## Files in this skill

- `README.md` — full design system documentation
- `colors_and_type.css` — CSS tokens
- `preview/` — design-system reference cards
- `ui_kits/cockpit/` — React+Babel UI kit (primitives + composed cockpit)
- `assets/` — glyph + frame-character reference, brand mark
- `fonts/` — font stack notes (no binaries shipped)
