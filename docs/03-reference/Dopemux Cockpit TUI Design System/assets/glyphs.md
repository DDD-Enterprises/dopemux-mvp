---
id: glyphs
title: Glyphs
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-01'
last_review: '2026-05-01'
next_review: '2026-07-30'
prelude: Glyphs (reference) for dopemux documentation and developer workflows.
---
# Nerd Font Glyphs

Copied from `src/dopemux/ui/theme.py::Glyphs`. Primary set assumes
**JetBrains Mono Nerd Font**. Every glyph has an ASCII fallback for
non-Nerd-Font terminals.

## Status

| Name      | Glyph    | Codepoint | Fallback |
|-----------|----------|-----------|----------|
| SUCCESS   | `\uf058` | nf-fa-check_circle | `✓` |
| ERROR     | `\uf057` | nf-fa-times_circle | `✗` |
| WARNING   | `\uf06a` | nf-fa-exclamation_circle | `!` |
| INFO      | `\uf05a` | nf-fa-info_circle | `i` |
| RUNNING   | `\uf04b` | nf-fa-play | `▶` |
| PENDING   | `\uf017` | nf-fa-clock_o | `~` |
| BLOCKED   | `\uf05e` | nf-fa-ban | `#` |
| SKIPPED   | `\uf050` | nf-fa-forward | `-` |
| FIRE      | `\uf06d` | nf-fa-fire | `^` |
| GOLD      | `\uf091` | nf-fa-trophy | `*` |

## Dev

| Name    | Glyph    | Codepoint | Fallback |
|---------|----------|-----------|----------|
| GIT     | `\ue725` | nf-dev-git_branch | `Y` |
| CODE    | `\uf121` | nf-fa-code | `<>` |
| PACKAGE | `\uf487` | nf-oct-package | `[]` |
| BUG     | `\uf188` | nf-fa-bug | `*` |
| WRENCH  | `\uf0ad` | nf-fa-wrench | `%` |

## System

| Name     | Glyph    | Codepoint | Fallback |
|----------|----------|-----------|----------|
| DOCKER   | `\uf308` | nf-linux-docker | (none — render as `docker`) |
| SERVER   | `\uf233` | nf-fa-server    | (none — render as `server`) |
| DATABASE | `\uf1c0` | nf-fa-database  | (none — render as `db`)     |

## Navigation

| Name        | Glyph    | Codepoint | Fallback |
|-------------|----------|-----------|----------|
| ARROW_RIGHT | `\uf054` | nf-fa-chevron_right | `>` |
| ARROW_DOWN  | `\uf078` | nf-fa-chevron_down  | `v` |
| PROMPT      | `❯` (`\u276f`) | (no Nerd Font; bare unicode) | `>` |

## Brand

| Name        | Value          |
|-------------|----------------|
| BRAND_MARK  | `━━━◆ Ø ◆━━━`  |
| SECTION_RULE | `───`         |

## Forbidden

`→`, `⇒`, `➜`, `…`, `...` (`tokens.py::FORBIDDEN_ARROWS`).
Use `->` for directionality. Use a literal `NEXT:` line, never an ellipsis.
