---
id: DOPEMUX_COCKPIT_TUI_DESIGN_SYSTEM_ASSETS_GLYPHS
title: Cockpit Glyph Contract
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-27'
last_review: '2026-04-27'
next_review: '2026-06-15'
prelude: Wordmark, glyph, and text-fallback contract for cockpit reference cards.
---
# Cockpit Glyph Contract

Canonical stylized wordmark: `DØPΞM∪X`.
Plain fallback wordmark: `DOPEMUX`.
Compact seal: `◆DØPΞM∪X◆`.
Rejected artifact: `ᗪØƤΞM∪╳`.

The stylized wordmark may appear only in chrome, title bars, splash /
brand previews, and non-semantic headers. It must not replace required
semantic fields: `domain`, `authority`, `role`, `next_action`, `SRC`,
`status`, or `result`.

Glyphs are visual cues only. They do not define authority, provenance,
workflow legality, validation result, source truth, or state. Text fields
and declared contracts remain authoritative.

Rich glyphs are optional. Canonical rich-glyph terminal font is Dopemux
Term Nerd Font Regular. Canonical brand mono remains Dopemux Term Regular.
The cockpit must remain legible without rich glyph coverage: every rich
glyph below has an ASCII fallback, ASCII fallback must preserve meaning,
and emoji / glyphs must never be the only signal for state, identity, or
action.

## Wordmark

| Name | Rich | ASCII fallback | Use |
|------|------|----------------|-----|
| wordmark | `DØPΞM∪X` | `DOPEMUX` | chrome, title bars, splash / brand previews, non-semantic headers |
| compact_seal | `◆DØPΞM∪X◆` | `*DOPEMUX*` | decorative brand preview only |
| operator_line | `━━◆ Ø ◆━━ DØPΞM∪X ━━ operator control ━━◆ ◈ ◆━━` | `== * O * == DOPEMUX == operator control == * <> * ==` | decorative brand preview only |
| rejected_artifact | `ᗪØƤΞM∪╳` | (none) | rejected, non-canonical; do not use |

## Rich Cockpit Vocabulary

| Name | Rich glyph | ASCII fallback | Contract |
|------|------------|----------------|----------|
| brand_core | `Ø` | `O` | brand accent only |
| seal | `◆` | `*` | decorative seal |
| double_seal | `◈` | `<>` | decorative double seal |
| void_node | `◉` | `(o)` | visual node cue |
| idle_node | `◎` | `( )` | visual node cue |
| canonical_node | `⬢` | `#` | visual canonical cue only |
| derived_node | `⬡` | `<>` | visual derived cue only |
| mirror_receipt | `◌` | `()` | visual mirror cue only |
| proxy_gate | `⧉` | `[proxy]` | visual proxy cue only |
| adapter_gate | `⊡` | `[adapter]` | visual adapter cue only |
| blocked_gate | `▣` | `[BLOCKED]` | visual blocked cue only |
| hard_stop | `▰` | `[FAIL]` | visual stop cue only |
| warning_spike | `▲` | `!` | visual warning cue only |
| advisory_spike | `△` | `?` | visual advisory cue only |
| drift_signal | `⌁` | `~` | visual drift cue only |
| doctrine_mark | `※` | `*` | visual doctrine cue only |
| operator_cursor | `▸` | `>` | visual cursor cue only |
| section_bar | `━` | `=` | visual section cue only |
| soft_scanline | `┄` | `-` | visual scanline cue only |
| continuation | `│` | `|` | visual continuation cue only |
| more | `+` | `+` | visual more cue only |

These names are a design-system vocabulary for previews and reference
cards. They do not create runtime status chips, provenance labels,
authority labels, or validation results.

## Runtime Glyphs

Copied from `src/dopemux/ui/theme.py::Glyphs` as observed in this package
pass. These remain optional rich-mode enhancements.

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
| BRAND_MARK  | `DØPΞM∪X`      |
| BRAND_FALLBACK | `DOPEMUX`   |
| BRAND_LINE  | `◆DØPΞM∪X◆`    |
| BRAND_RULE  | `━━◆ Ø ◆━━ DØPΞM∪X ━━ operator control ━━◆ ◈ ◆━━` |
| SECTION_RULE | `───`         |

## Forbidden

Unicode arrows and Unicode ellipsis are forbidden in package copy.
The forbidden character classes include U+2192, U+21D2, U+279C, and
U+2026.

Use ASCII `->` for directionality. Use a literal `NEXT:` line, never an
ellipsis.
