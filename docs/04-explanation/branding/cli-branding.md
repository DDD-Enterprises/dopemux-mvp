---
id: cli-branding
title: "D\xD8PEM\xDCX CLI Branding Guide"
type: reference
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: "D\xD8PEM\xDCX CLI Branding Guide (explanation) for dopemux documentation\
  \ and developer workflows."
---
# DØPEMÜX CLI Branding Guide

This document explains how the Ritual Daemon voice surfaces inside `dopemux` CLI commands. Treat it as a quick reference for maintainers who will be adding new `console.print` statements, help text, or tmux hooks.

## 1. Brand primitives

- `RitualConsole` (src/dopemux/cli.py:101): a tiny Rich console subclass that automatically prefixes monospace strings with `[LIVE]` and the prescribed color unless you pass `brand_chip=""`.
- `brand_status(message, chip="[LIVE]", style="cyan")`: convenience helper that routes through `RitualConsole` while keeping `[AFTERCARE]`, `[BLOCKER]`, `[LOGGED]`, etc. chips reusable inside commands.

## 2. Usage patterns

| Scenario | Chip | Style | Example |
|----------|------|-------|---------|
| Routine success | `[LIVE]` \| `cyan` \| `brand_status("Checklist synced")` |
| Logged/aftercare info | `[LOGGED]` / `[AFTERCARE]` \| `dim` / `purple` \| `brand_status("Session saved", chip="[LOGGED]", style="dim")` |
| Blockers | `[BLOCKER]` \| `red` \| `brand_status("Missing database", chip="[BLOCKER]", style="red")` |
| Overrides or migrations | `[OVERRIDE]` \| `yellow` \| `brand_status("Fallback routing active", chip="[OVERRIDE]", style="yellow")` |

The console helper automatically handles color tags, so you can pass `message` as a preformatted string (e.g., `[dim]Hint[/dim]`) and it will still emit the chip in front.

## 3. Printing without chips

If a command needs to print a table, raw Markdown, or other layout-sensitive block, simply call `console.print(..., brand_chip="")`. This bypasses auto-tagging while leaving `RitualConsole` available for other adjacent lines.

## 4. Future contribution tips

1. Start with `brand_status(...)` whenever you want a chip; add new chip constants to the brand system if needed.
1. Avoid sprinkling literal `console.print("[color]...")` lines unless you're printing multiline tables or help text that relies on precise spacing.
1. If you need a new tone (e.g., `[EDGE]`), register it in `docs/branding/DØPEMÜX_BRAND_SYSTEM.md` before using it in code.

Logged. Hydrate. See you in the changelog.
