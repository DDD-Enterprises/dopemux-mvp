---
id: frame_chars
title: Frame Chars
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-01'
last_review: '2026-05-01'
next_review: '2026-07-30'
prelude: Frame Chars (reference) for dopemux documentation and developer workflows.
---
# Frame Characters

The static cockpit grid (`src/dopemux/ui/cockpit/frame.py`) is drawn from
this fixed character set. The framebuffer protects these cells — normal
writes refuse to overwrite them; the renderer must call `force=True` to
draw a frame character.

## Borders

| Char | Role |
|------|------|
| `━`  | top + bottom horizontal border |
| `┃`  | left + right vertical border |
| `┏`  | top-left corner |
| `┓`  | top-right corner |
| `┗`  | bottom-left corner |
| `┛`  | bottom-right corner |

## Internal divisions

| Char | Role |
|------|------|
| `│`  | left + right pane divider columns |
| `─`  | horizontal rules (header, body, status) |
| `┠`  | left edge of horizontal rule |
| `┨`  | right edge of horizontal rule |
| `┬`  | rule joining a divider, top half |
| `┴`  | rule joining a divider, bottom half |
| `├`  | left edge of inspector / center split |
| `┤`  | right edge of inspector / center split |

## Brand

| Char | Role |
|------|------|
| `◆`  | brand mark accent |
| `Ø`  | brand mark center glyph (empty set) |

These are the **only** characters allowed in protected cells. Do not
substitute ASCII (`-`, `+`, `|`) or other Unicode box variants.
