---
id: cli-ux-design-spec
title: Cli Ux Design Spec
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Cli Ux Design Spec (explanation) for dopemux documentation and developer
  workflows.
---
# Dopemux CLI UX Design Spec

> Single source of truth for all CLI/TUI output styling across dopemux.
> Implementation lives in `src/dopemux/ui/theme.py`.
> Production operator surfaces must treat this document as the visual and layout authority.

---

## 1. Design Philosophy

- **Dark-first terminal aesthetic** on `#020617` (ink.black).
- **Neon mint as hero color** — cyan/mint family dominates; warm tones reduced to warnings only.
- **Color temperature hierarchy**: cool (mint/cyan) = primary data, warm (magenta/violet) = emphasis/alerts.
- **3-second scan rule**: any CLI output must be scannable in 3 seconds.
- **ADHD rules**: max 5 simultaneous colors per screen, glanceable status, consistent icon-chip-message flow.
- **Progressive disclosure**: summary by default, `--verbose` for details, `--debug` for raw output.

---

## 2. Neon Mint Palette

### Hero Colors (Mint / Cyan Family)

| Token | Hex | Rich Style | Role |
|-------|-----|------------|------|
| `ritual.cyan` | `#7DFBF6` | `mint` | Primary accent, borders, active |
| `serum.mint` | `#94FADB` | `mint.soft` | Data emphasis, secondary |
| mint bright | `#B4FFEE` | `mint.bright` | Highlighted text, glow |
| mint dim | `#4A9E94` | `mint.dim` | De-emphasized, borders |

### Accent Colors (Magenta / Violet)

| Token | Hex | Rich Style | Role |
|-------|-----|------------|------|
| `gremlin.pink` | `#FF8BD1` | `magenta` | Alerts, errors, dopamine |
| `aftercare.violet` | `#9B78FF` | `violet` | Tips, aftercare, debug |
| violet dim | `#6B4FBF` | `violet.dim` | Muted violet background |

### Warm Tones (WARNING-ONLY)

| Token | Hex | Rich Style | Role |
|-------|-----|------------|------|
| `gilt.edge` | `#F5F26D` | `gold` | Warnings only |
| `saint.gold` | `#FFCF78` | `amber` | Override states only |

### Surfaces

| Token | Hex | Rich Style | Role |
|-------|-----|------------|------|
| `ink.black` | `#020617` | `surface` | Primary bg |
| `void.navy` | `#041628` | `surface.raised` | Panel bg, zebra rows |
| `velvet.plum` | `#1A0520` | `surface.deep` | Nested panels |

### Text Hierarchy

| Level | Hex | Rich Style |
|-------|-----|------------|
| Primary | `#E2E8F0` | `text` |
| Secondary | `#94A3B8` | `text.dim` |
| Muted | `#64748B` | `text.muted` |
| Disabled | `#475569` | `text.disabled` |

### Semantic Status Mapping

| Semantic | Maps To | Hex |
|----------|---------|-----|
| Success | serum.mint | `#94FADB` |
| Error | gremlin.pink | `#FF8BD1` |
| Warning | gilt.edge | `#F5F26D` |
| Info | ritual.cyan | `#7DFBF6` |
| Debug | aftercare.violet | `#9B78FF` |

All pairs exceed WCAG AA (4.5:1) against ink.black. Mint/cyan hits AAA (15.2:1).

---

## 3. Rich Theme Object

Defined in `src/dopemux/ui/theme.py` as `DOPEMUX_THEME`.

The theme provides named styles for every UI element. Commands must use style names (e.g. `style="success"`) and never raw hex strings.

See the source file for the full style dictionary. Key style groups:

- **mint.\*** — hero color family
- **text.\*** — text hierarchy
- **chip.\*** — status chip labels
- **table.\*** — table headers, borders, zebra
- **panel.\*** — panel borders, titles
- **bar.\*** — progress bar segments
- **severity.\*** — health/severity indicators
- **rule.line** — horizontal rule separators

---

## 4. Component Standards

> **Developer reference**: See [component-library.md](component-library.md) for the full API reference, code examples, and migration checklist.

### Tables

- Box: `box.ROUNDED` (default); `box.SIMPLE` for compact inline tables.
- Header: `style="table.header"` (bold mint).
- Border: `border_style="table.border"` (dim mint).
- Zebra: odd rows `style="table.row.alt"` (void.navy bg) when > 3 rows.
- Numbers: right-aligned. Text: left-aligned. Status: center-aligned.
- Padding: `(0, 1)` default.
- Title: nerd font glyph + space + title text.
- Helper: `styled_table(title, *columns, **kw) -> Table` in theme.py.

### Panels

- Box: `box.ROUNDED`.
- Border: `"panel.border"` (dim mint `#4A9E94`).
- Title style: `"panel.title"` (bold serum.mint).
- Padding: `(1, 2)` for content, `(0, 1)` for inline status.
- Use for: grouped info, error frames, section headers.
- Helper: `styled_panel(content, title, border_style)` in theme.py.

### Progress Bars

- Spinner: `"dots12"` for all operations.
- Bar: complete=`#7DFBF6`, remaining=`#1A0520`, pulse=`#FF8BD1`.
- Layout: `SpinnerColumn(style="spinner") + TextColumn + BarColumn + TimeRemainingColumn`.
- Indeterminate: `SpinnerColumn(spinner_name="dots12") + TextColumn` only.

### Status Glyphs (Nerd Font)

| State | Nerd Font | Fallback | Style |
|-------|-----------|----------|-------|
| Success | `` | `✓` | mint.soft |
| Error | `` | `✗` | magenta |
| Warning | `` | `!` | gold |
| Info | `` | `i` | mint |
| Running | `` | `▶` | mint |
| Pending | `` | `~` | text.muted |
| Blocked | `` | `#` | magenta |
| Skipped | `` | `-` | text.muted |

Glyph constants live in `Glyphs` class in theme.py.

### Emoji Whitelist (CLI-Approved)

`💊 🧪 🧠 ⚡ 💧 🔬` — all other emoji should migrate to nerd font glyphs.

### Message Formatting

- **Error**: `error_panel(problem, why, fix)` — 3-part structure with `[BLOCKER]` chip.
- **Warning**: `styled_panel(border_style="warning")` with `[OVERRIDE]` chip.
- **Success**: inline `[LOGGED]` chip, no panel unless multi-line.
- **Info**: inline `[LIVE]` chip.

### Tree Views

- Guide style: `#4A9E94` (mint.dim).
- Highlight style: `bold #94FADB` (serum.mint).

### Prompts

- Marker: `❯` in `#7DFBF6`.
- Default values in `text.muted`.

---

## 5. Layout Rules

- Max width: `min(terminal_width, 120)`.
- One blank line before/after panels.
- `console.rule(style="rule.line")` for major section breaks.
- Information hierarchy: Panels > Tables > Inline > Muted.
- Progressive disclosure: Level 1 (default summary), Level 2 (`--verbose`), Level 3 (`--debug`).

---

## 6. Typography & Glyphs

- Primary CLI font: **JetBrains Mono Nerd Font** (assumed available).
- Nerd font categories: Status (8 glyphs), Dev (git/code/package), System (docker/server), Navigation (arrows).
- Box-drawing: brand mark `━━━◆ Ø ◆━━━`, subsection `─── title ───`.
- Section separators via `console.rule()` only — never manual box chars.

---

## 7. Render Modes

Controlled via `DOPEMUX_RENDER_MODE` env var or `NO_COLOR`.

| Mode | Env Value | Behavior |
|------|-----------|----------|
| **RICH** | `rich` (default) | Full themed output |
| **PLAIN** | `plain` or `NO_COLOR=1` | Strip all styles |
| **COMPACT** | `compact` | Reduced spacing, no panels, inline status |
| **AUDIT** | `audit` | Structured text with timestamps for parsing |

Implementation: `RenderMode` enum + `_detect_render_mode()` in theme.py.

---

## 8. Rules & Minimums

### Every command MUST:

1. Import `from dopemux.console import console` (never `Console()`).
2. Show a status chip on completion.
3. Use themed style names, never raw color strings.
4. Show duration for operations > 1 second.

### Error messages MUST:

1. Use `error_panel(problem, why, fix)` or wrap in `styled_panel(border_style="error")`.
2. Use 3-part structure: Problem / Why / Fix.
3. Include an actionable step.
4. Use `[BLOCKER]` chip.

### Tables MUST:

1. Use `styled_table()` or `box.ROUNDED`.
2. Zebra stripe if > 3 rows.
3. Right-align numeric columns.
4. Include a titled header with glyph.

### Progress MUST:

1. Use `dots12` spinner.
2. Show time remaining if > 5 seconds.
3. Use themed colors.

---

## 9. Textual TUI Palette

For the Textual dashboard (`dashboard_detail.py`), replace Catppuccin Mocha CSS vars:

```css
$mint-primary: #7DFBF6;
$mint-secondary: #94FADB;
$accent-magenta: #FF8BD1;
$accent-violet: #9B78FF;
$surface-base: #020617;
$surface-panel: #041628;
$text-primary: #E2E8F0;
$warn-gold: #F5F26D;
```

---

## 10. Accessibility & Degradation

- All color pairs exceed WCAG AA (4.5:1) on ink.black.
- `NO_COLOR` env var strips all styling (auto-detected).
- Status conveyed by text + icon, never color alone.
- 256-color fallbacks: theme degrades gracefully on limited terminals.
