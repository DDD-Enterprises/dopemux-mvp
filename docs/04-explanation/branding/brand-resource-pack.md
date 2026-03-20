---
id: brand-resource-pack
title: "DØPEMÜX Brand Resource Pack"
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-18'
last_review: '2026-03-18'
next_review: '2026-06-18'
prelude: "Canonical one-stop brand reference for every surface of dopemux. If it's not in this file, it's not canon."
---

# ━━━◆ Ø ◆━━━  DØPEMÜX Brand Resource Pack

> **[LIVE]** Single source of truth for every brand decision across CLI, TUI, Web, TMUX, agents, notifications, and docs. No need to open other files.

---

## 1. Brand Identity

### Pillars

| Pillar | Description | Execution |
|--------|-------------|-----------|
| **Ritualized Desire** | Everything looks like a spell circle rendered in CSS | Circular gradients, halo glows, circuits-as-sigils |
| **Luxury Filth** | Velvet restraints + lab glassware | Velvet blacks, gilt outlines, backlit cyan + mint |
| **Consent Logs** | Kink-coded humor, archived receipts | `[CONSENT CHECK? y/N]`, `[LOGGED]`, `[AFTERCARE]` |
| **Self-Roasting Precision** | Dopemux drags itself before dragging user | Copy admits daemon flaws while flexing control |

### Metaphor System

| Metaphor | Meaning | Where it appears |
|----------|---------|-----------------|
| **Cockpit** | The developer's workspace — TMUX + CLI panes | TMUX layout names, dashboard headers |
| **Flight Deck** | Documentation and operational reference | docs/ folder naming, doc headers |
| **HUD** | Heads-up display — real-time status overlays | TUI dashboard, cognitive load gauge |
| **Ritual Daemon** | The dopemux system persona — filthy librarian, precision gremlin | Agent prompts, CLI banners, voice copy |

### Personality Matrix

| Surface | Focused State | Scattered State | Break/Aftercare State |
|---------|---------------|-----------------|----------------------|
| **CLI** | Terse forensic (ClinicalForensics) | Roast + one action (UXScold) | Gentle close (Aftercare) |
| **TUI Dashboard** | Data-dense HUD | Simplified, fewer widgets | Break reminder, hydration |
| **Web Dashboard** | Full analytics | Highlight critical only | Session summary |
| **Agent Prompts** | Fact/Inference split | Direct imperatives | UNKNOWN+TODO |
| **Notifications** | StatusChip + metric | Single action | 💧 Hydrate reminder |

### Brand Name Variants

| Variant | Usage |
|---------|-------|
| `dopemux` | Default, code references, CLI commands |
| `DOPEMUX` | Headers, emphasis |
| `DPMX` | Abbreviation, file prefixes |
| `💊dopemux` | Playful/branded contexts |
| `DØPEMÜX` | Display headers, brand mark contexts |
| `DOMUX` | Ultra-short reference |

---

## 2. Visual System — Cross-Platform Token Table

**Source of truth**: `src/dopemux/ui/theme.py` (lines 33–57)

| Token | Hex | theme.py const | dopemux.tcss var | theme.ts key | TMUX | Rich Style |
|-------|-----|----------------|------------------|--------------|------|------------|
| ink.black | `#020617` | `INK_BLACK` | `$base` | `inkBlack` | colour234 | — |
| void.navy | `#041628` | `VOID_NAVY` | `$mantle` | `voidNavy` | colour235 | — |
| velvet.plum | `#1A0520` | `VELVET_PLUM` | — | `velvetPlum` | colour53 | — |
| ritual.cyan | `#7DFBF6` | `RITUAL_CYAN` | `$blue` | `ritualCyan` | colour123 | `mint` |
| serum.mint | `#94FADB` | `SERUM_MINT` | `$green` | `serumMint` | colour122 | `mint.soft` |
| mint.bright | `#B4FFEE` | `MINT_BRIGHT` | — | — | colour159 | `mint.bright` |
| mint.dim | `#4A9E94` | `MINT_DIM` | `$mint-dim` | `mintDim` | colour73 | `mint.dim` |
| gremlin.pink | `#FF8BD1` | `GREMLIN_PINK` | `$red` | `gremlinPink` | colour212 | `magenta` |
| aftercare.violet | `#9B78FF` | `AFTERCARE_VIOLET` | `$mauve` | `aftercareViolet` | colour141 | `violet` |
| violet.dim | `#6B4FBF` | `VIOLET_DIM` | — | — | colour98 | `violet.dim` |
| gilt.edge | `#F5F26D` | `GILT_EDGE` | `$yellow` | `giltEdge` | colour227 | `gold` |
| saint.gold | `#FFCF78` | `SAINT_GOLD` | `$peach` | `saintGold` | colour222 | `amber` |
| text.primary | `#E2E8F0` | `TEXT_PRIMARY` | `$text` | (MUI text.primary) | colour253 | `text` |
| text.secondary | `#94A3B8` | `TEXT_SECONDARY` | `$text-dim` | (MUI text.secondary) | colour248 | `text.dim` |
| text.muted | `#64748B` | `TEXT_MUTED` | `$text-muted` | (MUI text.disabled) | colour243 | `text.muted` |
| text.disabled | `#475569` | `TEXT_DISABLED` | — | — | colour240 | `text.disabled` |

### Gradients & Glows (Web/CSS only)

| Name | CSS | Usage |
|------|-----|-------|
| **Halo** | `radial-gradient(circle at 20% 20%, rgba(125,251,246,0.25), rgba(2,6,23,0.95))` | Global background |
| **Velvet** | `linear-gradient(135deg, rgba(4,22,40,0.9), rgba(26,5,32,0.9))` | Card backgrounds |
| **Cyan Bloom** | `drop-shadow(0 0 30px rgba(125,251,246,0.45))` | Focus/hover glow |
| **Gold Edge** | `1px border rgba(245,242,109,0.65) + inset shadow` | CTA outlines |

### Accessibility

- WCAG AA minimum: 4.5:1 contrast ratio for all text on backgrounds
- ritual.cyan `#7DFBF6` on ink.black `#020617` = **15.2:1** (AAA)
- serum.mint `#94FADB` on ink.black = **14.8:1** (AAA)
- Use gold/peach for warnings instead of pure red (maintains luxe tone)
- Max 5 simultaneous colors per screen (ADHD rule)

### Sync Validation

Run `python scripts/sync_brand_tokens.py` to verify all platforms match theme.py.

---

## 3. Typography

| Role | Font Stack | Where |
|------|-----------|-------|
| **Display** | `"Space Grotesk", "DM Sans", system-ui` | Web headers, hero numbers |
| **Body** | `"Inter", "SF Pro Display", system-ui` | Web paragraphs, lists |
| **Code / CLI** | `"JetBrains Mono Nerd Font", "IBM Plex Mono", monospace` | CLI output, chips, code blocks, TMUX |

**Iconography**: Line art (Lucide, Nerd Font glyphs) with stroke width 1.5–2px, tinted cyan or gold at 60% opacity.

---

## 4. Component System

### CLI Components (`src/dopemux/ui/theme.py`)

#### `styled_table(title, *columns, compact=False, **kw)`

Branded Rich Table. All CLI table output must use this.

```python
from dopemux.ui.theme import styled_table, Glyphs

table = styled_table(
    f"{Glyphs.PACKAGE} Dependencies",
    "Name",
    ("Version", {"justify": "right"}),
    ("Status", {"justify": "center"}),
)
table.add_row("rich", "13.9", "[success]installed[/]")
```

#### `styled_panel(content, title="", border_style="panel.border", **kw)`

Branded Rich Panel. All CLI panel output must use this.

```python
from dopemux.ui.theme import styled_panel
console.print(styled_panel("All checks passed", title="Results"))
```

#### `error_panel(problem, why, fix, title="Error")`

3-part error panel. **All errors must use this structure.**

```python
from dopemux.ui.theme import error_panel
console.print(error_panel(
    problem="Connection refused",
    why="Database not running",
    fix="docker compose up db",
))
```

#### Render Modes

| Mode | Env Var | Behavior |
|------|---------|----------|
| `RICH` | `DOPEMUX_RENDER_MODE=rich` | Full themed output (default) |
| `COMPACT` | `DOPEMUX_RENDER_MODE=compact` | No borders, no titles, minimal spacing |
| `PLAIN` | `NO_COLOR=1` | No ANSI — safe for piping |
| `AUDIT` | `DOPEMUX_RENDER_MODE=audit` | Timestamps on every row |

### StatusChip Enum (`theme.py` lines 192–221)

| Chip | Style | When to use |
|------|-------|-------------|
| `StatusChip.LIVE` | `chip.live` (cyan) | Active/running processes |
| `StatusChip.BLOCKER` | `chip.blocker` (pink) | Blocking errors |
| `StatusChip.OVERRIDE` | `chip.override` (yellow) | Manual overrides |
| `StatusChip.LOGGED` | `chip.logged` (mint) | Successfully recorded |
| `StatusChip.AFTERCARE` | `chip.aftercare` (violet) | Post-action follow-up |
| `StatusChip.EDGE` | `chip.edge` (cyan) | Edge cases/experimental |

```python
console.print(StatusChip.LIVE.render("Pipeline running"))
# → [LIVE] Pipeline running
```

### Glyphs Class (`theme.py` lines 128–185)

| Glyph | Constant | Nerd Font | Fallback | Semantic Color |
|-------|----------|-----------|----------|---------------|
| Status check | `Glyphs.SUCCESS` | `\uf058` | `✓` | success |
| Status error | `Glyphs.ERROR` | `\uf057` | `✗` | error |
| Warning | `Glyphs.WARNING` | `\uf06a` | `!` | warning |
| Info | `Glyphs.INFO` | `\uf05a` | `i` | info |
| Running | `Glyphs.RUNNING` | `\uf04b` | `▶` | info |
| Pending | `Glyphs.PENDING` | `\uf017` | `~` | text.dim |
| Blocked | `Glyphs.BLOCKED` | `\uf05e` | `#` | error |
| Skipped | `Glyphs.SKIPPED` | `\uf050` | `-` | text.muted |
| Git branch | `Glyphs.GIT` | `\ue725` | `Y` | info |
| Code | `Glyphs.CODE` | `\uf121` | `<>` | mint |
| Package | `Glyphs.PACKAGE` | `\uf487` | `[]` | violet |
| Bug | `Glyphs.BUG` | `\uf188` | `*` | error |
| Wrench | `Glyphs.WRENCH` | `\uf0ad` | `%` | warning |
| Docker | `Glyphs.DOCKER` | `\uf308` | — | info |
| Server | `Glyphs.SERVER` | `\uf233` | — | info |
| Database | `Glyphs.DATABASE` | `\uf1c0` | — | violet |
| Arrow right | `Glyphs.ARROW_RIGHT` | `\uf054` | `>` | mint |
| Arrow down | `Glyphs.ARROW_DOWN` | `\uf078` | `v` | mint |
| Prompt | `Glyphs.PROMPT` | `❯` | `>` | mint |
| **Brand mark** | `Glyphs.BRAND_MARK` | `━━━◆ Ø ◆━━━` | — | mint |

### TUI Components (`dopemux.tcss`)

Textual widgets use TCSS variables that map to theme.py tokens. All TUI styling flows through `src/dopemux/ui/dopemux.tcss`.

### Web Components (`ui-dashboard/src/theme.ts`)

MUI theme with `brandTokens.colors`, `brandTokens.gradients`, `brandTokens.chips`, `brandTokens.status`. All web components use `theme.ts` tokens.

### ADHD-HUD Elements

| Element | Color Token | Glyph |
|---------|------------|-------|
| Energy gauge (low) | serum.mint / `$green` | 💧 |
| Energy gauge (optimal) | ritual.cyan / `$blue` | ⚡ |
| Energy gauge (high) | gilt.edge / `$yellow` | 🔥 |
| Energy gauge (critical) | gremlin.pink / `$red` | 🚨 |
| Flow indicator | ritual.cyan | `Glyphs.RUNNING` |
| Break timer | aftercare.violet | `StatusChip.AFTERCARE` |
| Service health | `severity.*` styles | `Glyphs.SUCCESS/ERROR/WARNING` |

---

## 5. Voice System

### Voice Modes

Source: `BRAND_VOICE_BIBLE.md` + `src/dopemux/ui/voice.py`

| Mode | Trigger Context | Tone | Example |
|------|----------------|------|---------|
| **FilthDaemon** | Drift, untagged, too-clean, sanitization | Consequence + imperative | `[LIVE] Operator, I'm the filthy librarian logging your intentions.` |
| **ClinicalForensics** | Privacy, provenance, redaction, determinism | MUST/thresholds + UNKNOWN+TODO | `[BLOCKER] Provenance unverified. MUST tag source before merge.` |
| **UXScold** | Vague input, stuck, leaky attention | Roast + one step + evidence request | `[UXScold] You're still here? Ship something.` |
| **UIStrict** | Microcopy, UI labels, form fields | {label, message, action} — no threats | `Save changes? This action is permanent.` |
| **BannerOneLiner** | Session start, command headers | 1–2 punch lines then utility | `━━━◆ Ø ◆━━━  All memory. No mercy.` |
| **KinkAccent** | Optional spice layer | Consent-coded humor | `[CONSENT CHECK? y/N]` |

### Voice Gates (`VOICE_GATES.yaml`)

| Gate | Type | Phrases |
|------|------|---------|
| **Hard Avoid** | error | "as an ai", "probably", "maybe", "generally speaking" |
| **Soft Avoid** | warning | "no worries", "it's okay", "don't worry", "hope you're doing well" |
| **Required Closers** | structure | "NEXT:", "Next:", "Receipt:", "PROGRESS" |

**Structural gates**:
- Require FACT/INFERENCE split for non-trivial claims
- Require UNKNOWN+TODO instead of guessing

### Scoring Rubric (7 dimensions, pass >= 80/100)

| Dimension | Max Score |
|-----------|-----------|
| Directness | 10 |
| Forensic rigor | 20 |
| Actionable close | 15 |
| Anti-hedge compliance | 10 |
| Mode fidelity | 20 |
| Humor as diagnosis | 10 |
| Optional skin | 5 |

### Emoji Whitelist

| Context | Allowed Emojis |
|---------|---------------|
| **Full set** | 💊 🧪 📼 📎 📈 🧷 🧠 🗜️ |
| **CLI subset** | 💊 🧪 🧠 ⚡ 💧 🔬 |

### Surface → Voice Mapping

| Surface | Primary Mode | Secondary Mode | Closer |
|---------|-------------|----------------|--------|
| CLI commands | ClinicalForensics | UXScold | StatusChip.LOGGED |
| CLI errors | ClinicalForensics | — | error_panel() |
| CLI banner | BannerOneLiner | FilthDaemon | Glyphs.BRAND_MARK |
| TUI dashboard | UIStrict | — | StatusChip.LIVE |
| Web dashboard | UIStrict | — | — |
| Agent prompts | ClinicalForensics | FilthDaemon | UNKNOWN+TODO |
| Notifications | UXScold | ClinicalForensics | 💧 Aftercare |
| Docs | ClinicalForensics | — | — |

### Specimen Ledger

~184 curated specimens in `dopemux_voice_branding_bundle/SPECIMEN_LEDGER_ENRICHED.csv`.

Categories: roast (60), tagline (53), banner (43), error (15), instruction (13).

Loaded by `CopyLibrary` from `src/dopemux/ui/voice.py`.

---

## 6. Surface Catalog

| Surface | Key Files | Current Status | Target State |
|---------|-----------|---------------|--------------|
| **CLI commands** (17 files) | `src/dopemux/commands/*.py` | Raw Rich constructors | `styled_table` / `styled_panel` |
| **CLI entry** | `src/dopemux/cli.py` | Partial theme imports | Full brand banner + aftercare |
| **TUI dashboard** | `src/dopemux/ui/dashboard.py` | Raw Panel/Text | Themed + voice copy |
| **TUI detail** | `src/dopemux/ui/dashboard_detail.py` | Raw Panel/Text | Themed |
| **Web dashboard** | `ui-dashboard/src/` | theme.ts applied | Expand tokens (mint.bright, mint.dim, violet.dim) |
| **TMUX** | `configs/tmux*` | Generic colors | Brand tokens |
| **Agent prompts** | `services/agents/*.py` | No voice headers | Voice header injection |
| **Notifications** | `services/adhd-notifier/*.py` | Unbranded | StatusChip + branded copy |
| **Docs** | `docs/flight_deck/` | Inconsistent formatting | Brand headers, StatusChip notation |

---

## 7. Verification Protocol

### Automated Checks

| Check | Command | Expected |
|-------|---------|----------|
| Token sync | `python scripts/sync_brand_tokens.py` | Exit 0 |
| Brand lint | `python scripts/brand_lint.py` | 0 errors |
| Voice import | `python -c "from dopemux.ui.voice import VoiceMode, CopyLibrary"` | No error |
| Voice gates | `python -c "from dopemux.ui.voice import validate_output; print(validate_output('test'))"` | `[]` |
| Render modes | `DOPEMUX_RENDER_MODE=plain dopemux --help` | No ANSI escapes |
| Web build | `cd ui-dashboard && npm run build` | Exit 0 |

### WCAG AA Compliance

| Foreground | Background | Ratio | Result |
|-----------|------------|-------|--------|
| ritual.cyan `#7DFBF6` | ink.black `#020617` | 15.2:1 | AAA |
| serum.mint `#94FADB` | ink.black `#020617` | 14.8:1 | AAA |
| gremlin.pink `#FF8BD1` | ink.black `#020617` | 9.1:1 | AAA |
| gilt.edge `#F5F26D` | ink.black `#020617` | 14.5:1 | AAA |
| aftercare.violet `#9B78FF` | ink.black `#020617` | 6.2:1 | AA |
| text.primary `#E2E8F0` | ink.black `#020617` | 15.7:1 | AAA |
| text.muted `#64748B` | ink.black `#020617` | 4.6:1 | AA |

### Brand Lint Rules

1. No `from rich.table import Table` in `commands/` — use `styled_table`
2. No `from rich.panel import Panel` in `commands/` — use `styled_panel`
3. No raw hex color strings in style attributes — use theme style names
4. No `hard_avoid_phrases` in user-facing strings
5. All error outputs use 3-part structure (`error_panel()`)

---

## Appendix: Style Token Quick Reference

### Semantic Mapping (use these, not raw colors)

```
[mint]text[/mint]           → bold #7DFBF6 (primary accent)
[mint.soft]text[/mint.soft] → #94FADB (data emphasis)
[error]text[/error]         → bold #FF8BD1 (errors)
[success]text[/success]     → #94FADB (success)
[warning]text[/warning]     → #F5F26D (warnings)
[info]text[/info]           → #7DFBF6 (informational)
[violet]text[/violet]       → #9B78FF (aftercare/debug)
[gold]text[/gold]           → #F5F26D (override/CTA)
[text.dim]text[/text.dim]   → #94A3B8 (secondary text)
```

### Migration Cheatsheet

```python
# BEFORE → AFTER
"[bold cyan]"    → "[mint]"
"[bold red]"     → "[error]"
"[green]"        → "[success]"
"[yellow]"       → "[warning]"
border_style="cyan" → border_style="panel.border"
border_style="red"  → border_style="error"
Table(...)       → styled_table(...)
Panel(...)       → styled_panel(...)
```
