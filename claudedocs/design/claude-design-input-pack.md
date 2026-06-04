# DØPEMÜX — Claude Design Input Pack
**Direction B · Electric Refresh · v0.3.0**
*Paste this pack into Claude Design. Sections marked `[GENERATE]` are the active requests.*

---

## 1. Identity

**Product name**: dopemux (wordmark: DØPEMÜX)
**Type**: Operator-first, terminal-native developer platform for ADHD developers
**Mode**: Dark only. No light theme.
**Aesthetic**: Instrument panel. Electric neon on void black. Color signals state — calm surfaces, only danger shouts.
**Audience**: Solo ADHD developers running local AI pipelines and agentic workflows.

---

## 2. Color Tokens (canonical — Direction B)

```
/* Surfaces */
--color-base:          #020617   page background
--color-raised:        #041628   card / panel
--color-overlay:       #081832   modal / elevated
--color-border:        #1E2A3A   subtle border
--color-border-strong: #2E3F54   visible divider

/* Brand */
--color-brand:         #2FFFF0   primary teal — headers, links, focus rings
--color-brand-dim:     #00C9B8   dimmed teal — borders, bar fill

/* Status (ANSI-anchored — never swap families) */
--color-success:       #00FF85   DONE / PASS / healthy       → ANSI green
--color-error:         #FF2255   FAIL / BLOCKED / danger     → ANSI red
--color-warning:       #FFE600   WARN / degraded / caution   → ANSI yellow
--color-info:          #00E5FF   INFO / running              → ANSI cyan
--color-aftercare:     #C07BFF   AFTERCARE / deferred        → ANSI blue

/* Brand accent — decorative only, never a status indicator */
--color-accent:        #FF00CC   gremlin pink (wordmark glow, banners)

/* Text */
--color-text:          #E2E8F0   primary
--color-text-dim:      #94A3B8   secondary / labels
--color-text-muted:    #808DA0   timestamps / hints
--color-text-disabled: #475569   disabled (WCAG-exempt)
--color-text-inverse:  #020617   on filled bright chips
```

---

## 3. Typography (hue stack)

| Role | Font | Usage |
|---|---|---|
| `hue.display` | Space Grotesk | h1–h6, wordmark, panel titles |
| `hue.body` | Inter | body copy, labels, metadata |
| `hue.mono` | JetBrains Mono | code, CLI output, status chips, timestamps |

Scale: 12 · 14 · 16 · 20 · 24 · 32 · 48px

---

## 4. Shape & Spacing

```
Radius:   6px (sm) · 10px (md) · 999px (pill/chips)
Spacing:  4 · 8 · 16 · 24 · 32px
Shadow:   subtle  = 0 1px 3px rgba(0,0,0,0.4)
          overlay = 0 8px 24px rgba(0,0,0,0.55)
```

---

## 5. Component Vocabulary

These are the real components from `src/dopemux/ui/theme.py` — use these names exactly.

### Status Chips
Monospaced, pill-shaped, uppercase bracket notation. Dark text on bright fill.

```
[LIVE]        → --color-info    #00E5FF   currently running
[DONE]        → --color-success #00FF85   completed
[BLOCKER]     → --color-error   #FF2255   blocked / failed
[WARN]        → --color-warning #FFE600   degraded / attention
[AFTERCARE]   → --color-aftercare #C07BFF  deferred / soft
[OVERRIDE]    → --color-warning #FFE600   manually overridden
```

### Status Glyphs (JetBrains Mono Nerd Font)
```
✓  success    ✗  error    ⚠  warning    ●  info
◉  running    ⊘  blocked  ◈  aftercare
```

### Panels
Rounded (10px), border `--color-border-strong`, `Space Grotesk` bold title in `--color-brand`.
Body in Inter. Subtle backdrop `on #041628`.

### CLI Output Block
```
Background: --color-base (#020617)
Font: JetBrains Mono 13px
Line height: 1.6
Normal text: --color-text
Prompt line: --color-brand (❯ prefix)
Success line: --color-success ✓
Error line:   --color-error   ✗
Warning line: --color-warning ⚠
Muted/dim:    --color-text-muted
```

### Progress Gauge
Fill: `--color-brand` (`█`). Remaining: dim navy (`░`). Pulse: `--color-accent` (gremlin pink).

---

## 6. Voice & Copy Rules

- Lead with result, then next action. Never bury the status.
- Terse. Procedural. No hype, no apology.
- Error format: `✗ [WHAT FAILED] / Why: [root cause] / Fix: [exact command]`
- Status labels: `healthy · degraded · blocked · unknown` — never "all good!" or "uh oh"
- Timestamps always present. Counts over qualitative summaries.
- Empty states explain absence: `No active alerts.` not `You're all caught up!`

---

## 7. ADHD Operator Constraints

- Max 3 choices at any decision point
- Status visible without scrolling (first screenful)
- Color-never-alone: every status has a glyph AND a label (not just color)
- Critical alerts pop; everything else is calm background
- Time anchors on every panel: "started 4m ago", "last updated 09:42"

---

## 8. [GENERATE] — Requested Outputs

### 8.1 Status Chip Row Component
A horizontal row of all 6 chips in their live state:
`[LIVE]` `[DONE]` `[BLOCKER]` `[WARN]` `[AFTERCARE]` `[OVERRIDE]`
Dark base background. Chips pill-shaped, JetBrains Mono, dark inverse text on fill.

### 8.2 Operator Cockpit Panel (dark card)
A single dashboard card with:
- Panel title (Space Grotesk bold, `--color-brand`): "Pipeline State"
- 4 rows: task name + status chip + elapsed time
- A mini progress gauge at the bottom
- Border `--color-border-strong`, surface `--color-raised`

### 8.3 CLI Output Block
6-line terminal simulation:
```
❯ dopemux run --pipeline audit
  ● Connecting to task-orchestrator...    [info cyan]
  ✓ DONE  prescan        0.8s             [success green]
  ✓ DONE  extract        2.1s             [success green]
  ⚠ WARN  model-routing  fallback active  [warning yellow]
  ✗ FAIL  pal/codereview timeout          [error red]
```

### 8.4 Error Panel
3-part error panel in the `error_panel()` format:
- Border: `--color-error` (#FF2255)
- `✗ Connection refused` (bold, error red)
- `Why: Database not running`
- `Fix: docker compose up db` (monospaced, brand teal)

### 8.5 DØPEMÜX Wordmark
The brand wordmark with:
- `DØPEMÜX` in Space Grotesk 600, `--color-brand` (#2FFFF0)
- Subtle gremlin-pink (`#FF00CC`) glow bloom behind it (not on any status element)
- On `--color-base` (#020617)

---

## 9. Fences (hard constraints — do not violate)

1. **ANSI anchors**: success=green, error=red, warning=yellow, info=cyan, aftercare=blue. Never cross families.
2. **WCAG AA**: all status + text tokens ≥4.5:1 on base surface.
3. **Color-never-alone**: every status uses glyph + label, not color alone.
4. **Gremlin-pink is decorative only**: never as a status chip, border, or state indicator.
5. **Dark only**: no light mode, no system-preference switch.

---

## 10. Generated Artifacts (for reference)

All generated from `claudedocs/design/tokens.json` via `python3 claudedocs/design/generate_tokens.py`:

| File | Surface |
|---|---|
| `generated/dopemux_theme.py` | Rich CLI theme (TRUECOLOR + ANSI16 fallback) |
| `generated/dopemux_textual.tcss` | Textual TUI `$var` tokens |
| `generated/colors.css` | Web CSS custom properties |
| `src/dopemux/ui/dopemux.tcss` | Live Textual CSS (written by `--live`) |
| `ui-dashboard/src/theme.ts` | Live MUI web theme |
