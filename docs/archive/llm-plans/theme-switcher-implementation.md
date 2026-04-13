---
id: theme-switcher-implementation
title: Theme Switcher Implementation
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-13'
last_review: '2026-04-13'
next_review: '2026-07-12'
prelude: Theme Switcher Implementation (explanation) for dopemux documentation and
  developer workflows.
---
# Theme Switcher & Multi-Theme Implementation Plan

## Objective
Implement a theme switching mechanism and define three distinct themes:
1. **Mint Mojo**: The original Dopemux palette.
2. **Pastel Neon Dreams**: The recently updated high-contrast palette.
3. **Pastel Neon Dreamscape on Black**: The new vivid neon palette.

## Proposed Changes

### 1. `src/dopemux/ui/theme.py`
- Define a `THEME_PALETTES` dictionary containing the color constants for each theme.

#### **Theme 1: Mint Mojo (Original)**
- `hero`: #7DFBF6
- `success`: #94FADB
- `accent`: #FF8BD1
- `bg`: #020617

#### **Theme 2: Pastel Neon Dreams (Current Product Theme)**
- `hero`: #00FFFF
- `success`: #7FFFD4
- `accent`: #FF00FF
- `bg`: #000000

#### **Theme 3: Pastel Neon Dreamscape on Black (New Vivid Neon)**
- `RITUAL_CYAN`: #00FFFF (Pure Neon Cyan)
- `GREMLIN_PINK`: #FF00FF (Pure Neon Magenta)
- `YELLOW_NEON`: #FFFF00 (Pure Neon Yellow)
- `GREEN_NEON`: #00FF00 (Pure Neon Green)
- `MINT_BRIGHT`: #66FFFF (Pastel Cyan)
- `VIOLET_PASTEL`: #FF66FF (Pastel Magenta)
- `YELLOW_PASTEL`: #FFFF66 (Pastel Yellow)
- `SERUM_MINT`: #66FF66 (Pastel Green)
- `SURFACE_GREY`: #333333 (Dark Grey)
- `SURFACE_BLACK`: #000000 (Rich Black)

- Refactor `DOPEMUX_THEME` into a function `get_theme(name: str) -> Theme` or a registry.
- Implement `get_active_theme_name() -> str`:
  - Priority: `DOPEMUX_THEME` environment variable -> `dopemux.toml` -> `pastel-neon-dreams` (default).

### 2. `src/dopemux/cli.py`
- Add a new command group or option to switch themes.
- Example: `dopemux theme set mint-mojo`.

### 3. Persistence
- Store the theme choice in `dopemux.toml` under a new `[ui]` section.

## Verification Plan
- **Syntax Check**: Run `python3 -m py_compile` on modified files.
- **Switching Test**: 
  - `DOPEMUX_THEME=mint-mojo dopemux pr-merge flight`
  - `DOPEMUX_THEME=pastel-neon-dreamscape dopemux pr-merge flight`
  - Verify that the UI reflects the chosen palette correctly.
