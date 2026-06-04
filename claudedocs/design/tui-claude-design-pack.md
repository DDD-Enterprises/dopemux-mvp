# DØPEMÜX Cockpit TUI — Claude Design Input Pack
**Direction B · Electric Refresh · v0.1.0**
*Paste into Claude Design. Sections marked `[GENERATE]` are the active requests. Companion to `tui-design-spec.md`.*

---

## 1. Identity

**Surface:** terminal-native operator **cockpit** (TUI), not a web app, not a chat.
**Principle:** **authority before aesthetics.** The cockpit transports data; it never owns it.
**Mode:** dark only. Single full-window character grid. No cards, no z-order, no mouse, no hover.
**Aesthetic:** instrument panel. Box-drawing frame, electric signal color on void black, calm by
default, only danger shouts.
**Audience:** operators who know the system. Lead with result, then minimum context.

---

## 2. Color tokens (Direction B — canonical)

```
/* Surfaces */
--base:          #020617   window background (the only background)
--raised:        #041628   inset row / selected row tint ONLY
--border-strong: #2E3F54   frame + divider lines

/* Brand */
--brand:         #2FFFF0   headings, brand mark, active mode, panel titles

/* Status — ANSI-anchored, never swap families, glyph+label ALWAYS */
--info:          #00E5FF   LIVE / running        → ANSI cyan
--success:       #00FF85   LOGGED / healthy / done → ANSI green
--warning:       #FFE600   OVERRIDE / degraded   → ANSI yellow
--error:         #FF2255   BLOCKER / failed      → ANSI red
--aftercare:     #C07BFF   AFTERCARE / deferred  → ANSI blue
--muted:         #808DA0   EDGE / inactive / unknown

/* Brand accent — decorative only, NEVER a status */
--accent:        #FF00CC   brand-mark glow only

/* Text */
--text:          #E2E8F0   primary
--text-dim:      #94A3B8   labels / secondary
--text-muted:    #808DA0   timestamps / hints
```

---

## 3. Typography & grid

- **Mono:** Iosevka Hue Term (fallback: JetBrains Mono Nerd Font → JetBrains Mono → system mono).
  One weight, one size per viewport. Cells 1ch × 1.25em. Emphasis = **bold + color**, never size.
- **Box-drawing grid:** `━ ┃ ┏ ┓ ┗ ┛ ┠ ┨ ┬ ┴ ┤ ├ │ ─`. Hard corners only.
- **Brand mark:** `━━━◆ Ø ◆━━━` (rendered as text — there is no logo image).
- **No emoji. No SVG. No rounded corners, gradient, shadow, blur.**

---

## 4. Closed chip set (the only chips that exist)

Each chip is `<glyph> <LABEL>`, color from the token. The label is literal so `NO_COLOR` keeps signal.

```
◉ LIVE        info     #00E5FF   currently running / active
✓ LOGGED      success  #00FF85   recorded / complete
⚠ OVERRIDE    warning  #FFE600   manual override / degraded
⊘ BLOCKER     error    #FF2255   blocked / failed / refused
◈ AFTERCARE   aftercare #C07BFF  deferred / soft / mirror receipt
· EDGE        muted    #808DA0   placeholder / not-yet-styled slice
```

`UNKNOWN` is **literal text, never a chip**. No `READY/DRAFT/SYNC/SUCCESS/ERROR/FAILED/DEGRADED`
chips — map them: `DEGRADED→OVERRIDE`, `FAILED→BLOCKER`, `BLOCKED→BLOCKER`, `SYNC→AFTERCARE`.

---

## 5. Component vocabulary (cockpit primitives)

`Frame` (hard-cornered box-drawing window) · `ModeBar` (`[ PM ] | Implementer | …`) ·
`PaneHeader` (declares `domain/authority/role/next_action`) · `Rule` (horizontal divider) ·
`Row` (`> ` active marker in col 1) · `Chip` · `RunRow` · `ServiceRow` ·
`CommandRail` (bottom: filter, legality, keybinds) · `StatusRail` (bottom: warnings, `*WS STREAM`) ·
`Inspector` (right column detail) · `BridgeSegregator` (hard-divided adapter/proxy pane).

**Pane header format** (every major pane, top-left):
```
domain: readiness_queue
authority: task-orchestrator workflow transitions
role: canonical
next_action: triage
```

**Data row format:** `[<CHIP>] <subject>  <key=value> …  SRC=<service>` — chip first, SRC last.

---

## 6. Voice & copy

- Terse, procedural, operator-to-operator. Lead with result.
- Success: one line — `Started: MCP services for current workspace.`
- Failure: `Problem:` / `Why:` / `Fix:` / `NEXT:` — every panel.
- Status words in body text: `healthy · degraded · blocked · unknown · queued · running · complete`.
- Time anchor on every data row/pane: `last_check 09:42` / `ticket_age 3d`.
- Empty states explain absence: `No work items ready for triage.` (not "all caught up!").
- **Forbidden vocabulary:** `magic, brain, autonomous, smart, seamless, next-gen, supercharged,
  all set, everything looks good, probably, maybe, I think`. Use `->` not `→`; never `…`.

---

## 7. The fences (hard constraints — do not violate)

1. **Authority before aesthetics** — every pane declares authority; visual weight (top-left
   primacy, full-width, border emphasis) is reserved for the real authority owner. Demote derived /
   mirrored / proxied / advisory panes.
2. **SRC law** — every data row carries `SRC=<service>`; chrome (mode bar, rails, header) never
   does. `SRC=dopemux` is forbidden on canonical data.
3. **Bridge law** — `dopecon-bridge` is adapter/proxy only, in its own hard-divided segregator
   pane labeled `adapter-only segregated`; never a peer to canonical state.
4. **Closed chips only** — the six above. `UNKNOWN` stays literal.
5. **Color-never-alone** — every status carries glyph + label; `NO_COLOR=1` must lose nothing.
6. **Dark only, character grid only** — no mouse, hover, gradient, blur, image, emoji, rounded corner.
7. **ADHD cues are advisory, never gates** — never block operator action.

---

## 8. [GENERATE] — requested mockups

All static terminal snapshots on `--base #020617`, Iosevka Hue Term, box-drawing frame.

### 8.1 PM mode — 120×40 (north star)
Three columns + bottom rails. Left rail: workflow/slice map (Top-3 + `more_count`/`next_token`).
Center upper: readiness queue (rows with `LIVE`/`LOGGED`/`EDGE` chips, `legality=ok`, `blockers=N`,
`SRC=task-orchestrator`). Center lower: adjudication context (linked decision `SRC=conport`,
chronicle `SRC=dope-memory`, metadata `SRC=leantime`). Right inspector upper: selected slice
detail. Right inspector lower: canonical actions, then a **hard-divided bridge segregator**
(`[EDGE] adapter-only segregated`, `SRC=dopecon-bridge`). Command rail: `filter=triage legality=ok
warnings=0 ctrl+k=palette`. Status rail: advisory cue `adhd-engine: focused confidence=0.7
(advisory only)`.

### 8.2 Services mode — 120×40
Left rail: service list. Center: service health grid (`ServiceRow`: name, chip
`LIVE`/`OVERRIDE`/`BLOCKER`, latency, `last_check`, `SRC=<service>`) + MCP status + RTE child
surface (`SRC=repo-truth-extractor`, declares own authority). Right inspector: authority/capability
tiers + risks (TX/TU/T6) + do-not-touch refusal set, all `SRC=orchestrator-policy`.

### 8.3 Implementer mode — 120×40
Left rail: work contract. Center upper: active task + next action + acceptance subset + blockers
(`SRC=task-orchestrator`). Center lower: evidence workspace (Top-3 results, `more_count`,
`next_token`, `SRC=dope-context`). Inspector: selected proof detail (`SRC=proof-fs`), handback
actions (`SRC=conport`), bridge segregator.

### 8.4 Overview mode — 120×40
Three stacked panes: today's plan (`SRC=conport`), productivity/velocity (`SRC=conport`), ADHD
advisory cue (`SRC=adhd-engine role=advisory confidence=0.7`). Show one pane as `· EDGE` with
literal `historical trend data not wired` (no fabricated sparkline).

### 8.5 Events mode — 120×40 (live feed)
Single full-width scrolling feed. Rows: `<ts> [<CHIP>] <event_type> <subject> SRC=<source>` from
`native_hooks` and `workspace-watcher`. Status rail shows `*WS STREAM` live indicator.

### 8.6 PM adaptations — 100×32 and 80×24
Same structure, narrower columns / fewer rows. At 100×32 bridge moves to inspector lower-detail; at
80×24 bridge collapses inline (no peer pane).

### 8.7 BLOCKER — too small
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ⊘ BLOCKER  terminal size unsupported ┃
┃ Problem: supports 120x40/100x32/80x24┃
┃ Why:     layout invariants size-bound ┃
┃ Fix:     choose a supported size      ┃
┃ NEXT:    resize to at least 80x24     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### 8.8 Chip + glyph plate
All six chips rendered in a row (color) and again under `NO_COLOR` (label-only) to prove
color-never-alone. Plus the brand mark `━━━◆ Ø ◆━━━` with a faint `--accent #FF00CC` glow.

---

## 9. Handback

When mockups land, paste them back (or the hexes if any drifted). Verification: every data row has
`SRC=`, every pane a four-field header, only the six chips appear, `NO_COLOR` keeps all signal, and
PM renders at all three viewports. Then the design feeds a Textual implementation packet.
