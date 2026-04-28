---
id: DOPEMUX_COCKPIT_TUI_DESIGN_SYSTEM
title: Dopemux Cockpit TUI Design System
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-27'
last_review: '2026-04-27'
next_review: '2026-06-15'
prelude: Terminal-native operator cockpit reference for the Dopemux design system.
---
# Dopemux Cockpit TUI Design System v0

Terminal-native operator cockpit. **Authority before aesthetics.** Every pane
declares `domain`, `authority`, `role`, `next_action`. Every logical
data/provenance record carries `SRC=<service>` once; wrapped continuation
rows align under the content column and do not repeat SRC unless physical
rows are independently selectable/copyable. Bridge adapter/proxy actions
(`dopecon-bridge`) are segregated and never claim canonical authority.
Status chips are a closed set: `LIVE`, `BLOCKER`, `OVERRIDE`, `LOGGED`,
`AFTERCARE`, `EDGE`. `UNKNOWN` is literal text in affected fields, never a
chip, and is never collapsed into `EDGE`. No web, chat, mouse, hover, new
chips, or unified-PM record. **Authorities never collapse** — the cockpit
is a control surface; it doesn't own data.

## Architecture Safety Overlay (Read First)

This package is governed by the safety overlay set. Read in this order before mocking, designing, or implementing:

- [`ARCHITECTURE_SAFETY_OVERLAY.md`](architecture-safety-overlay.md) — Authority model, visual hierarchy law, pane declaration law, SRC/provenance law, bridge law, viewport degradation, chip/status law, PM/agent law, forbidden phrases. **Wins on all conflicts.**
- [`PM_IMPLEMENTER_COCKPIT_REDIRECTION.md`](pm-implementer-cockpit-redirection.md) — PM and Implementer mode pane semantics; narrower than the overlay and compatible with it.
- [`UX_REFERENCE_RECONCILIATION.md`](ux-reference-reconciliation.md) — How docs/ux supporting references are reconciled; the overlay wins on conflict.
- [`PREIMPLEMENTATION.md`](preimplementation.md) — Safety preconditions and fail-closed rules before promoting any pane from mock to implementation.
- [`ACCEPTANCE.md`](acceptance.md) — Checklist and contradiction gate enforcing the overlay.
- [`SKILL.md`](skill.md) — Operational skill summary for cockpit work.

This system targets **120×40 first**, with explicit adaptation rules for
**100×32** and **80×24**. Anything smaller is a `[BLOCKER]`.

---

## Surfaces

This package separates four surface families. They share tokens, chips,
and authority rules — they do not share chrome, layout, or scope.

| Surface | Folder                       | Role                                             | Implementation status |
|---------|------------------------------|--------------------------------------------------|-----------------------|
| **A**   | `surfaces/A1..A3.html`       | Static terminal snapshot · 120×40 / 100×32 / 80×24 | seed-only · no writes |
| **B**   | `surfaces/B-textual-cockpit-direction.html` | Live Textual cockpit *direction*       | scope marker · not implemented |
| **C**   | `surfaces/C-web-dashboard-direction.html`   | Web / operator dashboard *direction*    | scope marker · not implemented |
| **D**   | `preview/*.html`             | Design-system reference cards                    | reference only        |

`ui_kits/cockpit/` is a CDN-dependent visual reference for the Surface-A
composition (the Services view of the static cockpit). It demos the
primitive set, but it is not self-contained package proof and is not the
Services repo-truth-extractor north star — see the A1 static snapshot file in `surfaces/` for that.

---

## Sources

This design system was derived from runtime evidence in the dopemux-mvp
codebase. Readers without access can still use the tokens and rules here —
nothing in this folder requires the source to render.

- **Repo:** `DDD-Enterprises/dopemux-mvp` @ `main`
- **Brand bible:** `BRAND_SYSTEM.md`
- **Theme (Rich/Textual):** `src/dopemux/ui/theme.py`
- **Cockpit renderer:** `src/dopemux/ui/cockpit/{tokens.py, frame.py, render.py, model.py, seed.py}`
- **Reference screenshots:** not package-contained in this remediation
  pass. Browser visual review and screenshot approval remain `UNKNOWN`.

The cockpit renderer in `src/dopemux/ui/cockpit/` is the canonical TUI; the
web cockpit screenshot is a parallel surface that follows the **same IA,
chips, and authority model**. This system documents the TUI form. It does
not document a web variant.

---

## Index

```
README.md                   this file
PREIMPLEMENTATION.md        what implementers must read first
ACCEPTANCE.md               pass/fail checklist for this package
SKILL.md                    agent-skill manifest (cross-compatible)
colors_and_type.css         CSS vars: surfaces, text, chips, grid
preview/                    Surface D — design-system reference cards
surfaces/                   Surface A/B/C — cockpit mockups
  A1-services-repo-truth-workload-120x40.html     static · north star · 120×40
  A2-services-repo-truth-workload-100x32.html     static · compact   · 100×32
  A3-services-repo-truth-workload-80x24.html      static · fallback  · 80×24
  B-textual-cockpit-direction.html   live direction · not implemented
  C-web-dashboard-direction.html     web direction  · not implemented
ui_kits/cockpit/            Surface A — Services composition (React demo)
assets/                     glyphs, brand mark, frame characters reference
fonts/                      Dopemux Term build recipe + substitution notes
```

### What lives where
- **Tokens:** `colors_and_type.css`
- **Component recipes:** `ui_kits/cockpit/*.jsx` (CDN-dependent React+Babel reference renders of
  cockpit primitives — frame, header rule, status chip, run row, mode
  bar, shortcut rail, inspector pane, bridge segregator)
- **Visual reference demo:** `ui_kits/cockpit/index.html` (interactive 120x40
  cockpit with size adaptation; depends on unpkg React/ReactDOM/Babel and
  is not package-contained runtime proof)
- **Cards:** `preview/*.html` (one concept each, registered in the
  Design System tab)

---

## Content fundamentals

The brand voice is set by `BRAND_SYSTEM.md`. The TUI inherits it directly.

**Audience.** Operators, not spectators. Assume they know the system.
Lead with result, then minimum context. Skip explanation.

**Tone.** Calm, specific, unsentimental. No hype, no mascot, no jokes.
No vague reassurance. If something cannot be proven, render `UNKNOWN` as
literal field text — never claim success it didn't observe and never map
UNKNOWN to a chip.

**Person.** Imperative, second-person elided. "Start local services." not
"Starts up everything for you." Never "I", rarely "you".

**Casing.**
- `lowercase mono` for CLI verbs, env vars, paths, ids, SRC values, run ids
  (e.g. `v5-2026-04-22T14:32Z-a91c`, `services/repo-truth-extractor/`)
- `Title Case` for dashboard labels and document headings
  (e.g. `Recent Workload Records`, `Status Language`, `Active Run`)
- `UPPERCASE` for status chips ONLY (`LIVE`, `BLOCKER`) — never decorative

**Emoji.** None. The codebase uses Nerd Font glyphs (`Glyphs.SUCCESS` etc.)
which fall back to ASCII (`✓`, `✗`, `!`) under `NO_COLOR`. Treat emoji as
forbidden in operator-facing copy.

**Forbidden vocabulary** (enforced by `cockpit/tokens.py::validate_rendered_text`):
`probably`, `maybe`, `I think`, `as an AI`, `magic`, `brain`, `autonomous`,
`smart`, `seamless`, `next-gen`, `all set`, `everything looks good`,
`supercharged`. Unicode arrows and Unicode ellipsis are forbidden in copy.
ASCII `->` is allowed when directionality is required. ASCII `...` is allowed
only inside code examples that need literal CLI text.

**Forbidden chips** (will fail the validator if rendered):
`UNKNOWN`, `DEGRADED`, `FAILED`, `BLOCKED`, `SYNC`, `DRAFT`, `READY`,
`SUCCESS`, `ERROR`. The closed set is the only set. External vocab maps at
the boundary: `DEGRADED->OVERRIDE`, `FAILED->BLOCKER`, `BLOCKED->BLOCKER`,
`SYNC->AFTERCARE`. **`UNKNOWN` does not map to a chip.** Where authority or
status is unproven, the cockpit renders the literal text `UNKNOWN` in the
affected field. `UNKNOWN` is never a chip and is never collapsed into
`EDGE`.

**Sentence shapes.**
- Success: one line. `Started: MCP services for current workspace.`
- Failure: `Problem:` / `Why:` / `Fix:` / `NEXT:` — every panel.
  Example:
    ```
    [BLOCKER] terminal size unsupported.
    Problem: cockpit snapshot supports 120x40, 100x32, or 80x24.
    Why:     layout invariants are size-bound in slice 1.
    Fix:     choose a supported size.
    NEXT:    rerun with --snapshot 120x40.
    ```
- Status row: `[<CHIP>] <subject> <SRC=...>` — always in that order.

**Authority and SRC.** Every logical data/provenance record carries
`SRC=<service>` once. Wrapped continuation rows align under the content
column and do not repeat `SRC` unless physical rows are independently
selectable/copyable. `SRC` never appears on chrome (top frame, mode bar,
shortcut rail, status rail, bottom flag rail). Each pane declares the
four-field block (`domain`, `authority`, `role`, `next_action`); chrome
panes use `authority: dopemux` and `role: chrome`. Data
authority is declared per child surface / row. A child surface (e.g. the
repo-truth-extractor pane inside Services) declares its own authority — never inherits
silently. Bridge adapter/proxy actions (`dopecon-bridge`) are segregated
to a sub-pane that announces `adapter-only segregated`; the bridge is
never canonical authority for the data it transports.

---

## Visual foundations

**Surface.** The cockpit is a single full-window grid. Background is
`--surface-black` (`#020617`). There is no card stack, no z-order, no
layered glass. Inset panels use `--surface-navy` (`#041628`) for row alt
and selected-row highlight only.

**Type.** **Canonical brand mono: Dopemux Term Regular**. Canonical
rich-glyph terminal font: **Dopemux Term Nerd Font Regular**. User-facing
family names are `Dopemux Term` and `Dopemux Term Nerd Font`. Build
provenance is documented in `fonts/BUILD.md`: Dopemux Term is a
project-branded custom build generated from the Iosevka Customizer and
stored as `fonts/private-build-plans.toml`; `IosevkaDopemuxTerm` is the
internal build plan name only. Nerd Fonts patching produces the rich-glyph
variant. Fallback stack: Dopemux Term Regular; Dopemux Term Nerd Font
Regular; `ui-monospace`; `monospace`; ASCII/text fallback for glyph loss.
Single weight, single size per viewport. No display type, no sans, no serif.
Emphasis is bold + color, never size. Cells are 1ch × 1.25em. The renderer
is character-based; the framebuffer (`cockpit/frame.py`) refuses sub-cell
drawing. Programming ligatures are disabled or minimized for cockpit
terminal use.

**Color.** Restrained mint+navy palette ("mint-mojo"). Cyan and mint do
heading + LIVE/LOGGED. Pink does BLOCKER/error. Gold does
OVERRIDE/warning. Violet does AFTERCARE. Grey does inactive/unknown.
**Color encodes state, not decoration.** Monochrome (`NO_COLOR=1`) must
preserve all signal — that's why every chip carries a literal token.

**Borders.** Box-drawing characters (`━ ┃ ┏ ┓ ┗ ┛ ┠ ┨ ┬ ┴ ┤ ├ │ ─`)
form a fixed protected grid. The renderer treats border rows/columns as
**immutable**: `FrameBuffer.set_cell` refuses writes into them unless
`force=True`. There are no "rounded corners" anywhere.

**Backgrounds.** No images, no full-bleed photography, no patterns, no
gradients, no texture. Inset rows get a one-token background tint
(`--surface-navy`). That's the entire background system.

**Animation.** Effectively none. The cockpit is a **static snapshot
renderer** by design (`render.py` is pure). The only moving things in
the larger CLI are: spinners during in-flight operations, gauge fills,
and the WS stream indicator (`*WS STREAM`). Motion indicates "refresh,
transition, or changed state only" (`BRAND_SYSTEM.md §6`). No fades, no
bounces, no easing — single-frame state changes.

**Hover / press.** Not applicable. Mouse is forbidden. Selection is
keyboard. The "hover" equivalent is a leading `>` glyph in column 1 of
the active row (see `render.py::_render_services`). The "press"
equivalent is the bracketed `[N]` keybind affordance in the sidebar
(`Workload Records [1]`, `Active Run [LIVE 3]`).

**Inner / outer shadow.** None. Depth comes from rule lines and
divider columns, not z.

**Transparency / blur.** None.

**Corner radii.** Zero. The frame is hard-cornered with `┏ ┓ ┗ ┛`.

**Cards.** No card system. The TUI has **panes**, separated by
divider columns at `layout.left_divider` and `layout.right_divider` and
horizontal rules at protected rows. A pane is a region of the grid, not
a styled container.

**Layout rules — fixed elements.** From `cockpit/frame.py::Layout`:

| Size    | left div | right div | inspector split | center split | body rule | command row | status rule | status row | bottom |
|---------|---------:|----------:|----------------:|-------------:|----------:|------------:|------------:|-----------:|-------:|
| 120x40  | col 25   | col 84    | row 22          | row 25       | row 35    | row 36      | row 37      | row 38     | row 39 |
| 100x32  | col 21   | col 70    | row 17          | row 19       | row 27    | row 28      | row 29      | row 30     | row 31 |
| 80x24   | col 17   | col 56    | row 11          | row 13       | row 19    | row 20      | row 21      | row 22     | row 23 |

The three pane columns are: **Services / mode list (left)**, **active
subject + repo-truth-extractor child surface (center)**, **inspector + bridge segregator
(right)**. Bottom rows are reserved for the shortcut rail and status
rail, in that order.

**Adaptation.** The structure is the same at all three sizes; only the
column widths and the number of rows per pane change. There is no
mobile cascade, no breakpoint reflow. Below 80x24 the renderer refuses
with a `[BLOCKER]` panel (see `render.py::TOO_SMALL_MESSAGE`).

**Imagery vibe.** None. There is no imagery system.

---

## Iconography

**No emoji.** Ever.

**Wordmark.** Canonical stylized wordmark: `DØPΞM∪X`. Plain fallback
wordmark: `DOPEMUX`. The stylized wordmark may appear only in chrome,
title bars, splash / brand previews, and non-semantic headers. It must
never replace required semantic fields: `domain`, `authority`, `role`,
`next_action`, `SRC`, `status`, or `result`.
Compact seal: `◆DØPΞM∪X◆`. Rejected artifact: `ᗪØƤΞM∪╳`.

**Glyph contract.** Glyphs are visual cues only. They do not define
authority, provenance, workflow legality, validation result, source truth,
or state. Every rich glyph has an ASCII fallback. ASCII fallback must
preserve the text contract and remain legible without color or Nerd Font
coverage.

**Nerd Font glyphs** (`src/dopemux/ui/theme.py::Glyphs`) for status,
dev, system, and navigation icons are optional rich-mode enhancements.
Rich-mode glyph examples use Dopemux Term Nerd Font. Every glyph has an
ASCII fallback registered in `Glyphs._FALLBACK` for `NO_COLOR` /
non-Nerd-Font terminals
(`SUCCESS \uf058 -> ✓`, `ERROR \uf057 -> ✗`, `BLOCKED \uf05e -> #`, etc.).

**Box-drawing Unicode** for the cockpit grid:
`━ ┃ ┏ ┓ ┗ ┛ ┠ ┨ ┬ ┴ ┤ ├ │ ─ ◆ Ø`. Never substitute these for ASCII —
the framebuffer is hard-coded to use them.

**Brand mark.** `DØPΞM∪X` is the stylized text wordmark. `DOPEMUX` is
the plain fallback. Decorative chrome examples may use `◆DØPΞM∪X◆` or
`━━◆ Ø ◆━━ DØPΞM∪X ━━ operator control ━━◆ ◈ ◆━━`. There is no SVG and
no PNG. Brand marks are rendered live as text.

**SVG icons.** None. Adding raster or vector icons would violate the
TUI contract.

**Chevrons.** `\uf054` (right) and `\uf078` (down) are the only nav
glyphs. The prompt glyph is `❯` (`\u276f`). Unicode arrows and Unicode
ellipsis are forbidden in copy. ASCII `->` remains allowed when
directionality is needed.

**Substitution.** The icon system is intentionally tiny — a Nerd Font
+ a handful of box-drawing chars. There is **no CDN icon library**.
If a target terminal cannot render Nerd Font, the ASCII fallback map
in `Glyphs._FALLBACK` is the only acceptable substitute. Do not pull
in Lucide / Heroicons / Phosphor / etc.

> **Dopemux Term Regular** is the canonical brand mono. **Dopemux Term
> Nerd Font Regular** is the canonical rich-glyph terminal font. Font
> binaries are generated locally from the build recipe and are not
> committed without explicit approval.

---

## How to build with this

1. Use `colors_and_type.css` for tokens. Don't invent new ones.
2. Use the closed chip set. If a state isn't listed, it doesn't exist.
3. Compose with the cockpit primitives in `ui_kits/cockpit/`:
   `Frame`, `PaneHeader`, `Rule`, `Chip`, `Row`, `ModeBar`, `CommandRail`,
   `StatusRail`, `Inspector`, `BridgeSegregator`, `RunRow`, `ServiceRow`.
4. Every logical data/provenance record carries `SRC=<service>` once.
   Every pane declares `domain:`, `authority:`, `role:`, and `next_action:`.
   Chrome rows carry no `SRC=`.
5. Bridge and proxy actions live in their own segregator pane and label
   themselves `adapter-only segregated`.
6. Default size is 120x40. Verify the design also lives at 100x32 and
   80x24. Below 80x24 = `[BLOCKER]`.
7. Run output through the `validate_rendered_text` rules from
   `cockpit/tokens.py` — they catch banned vocabulary and chips.

---

## Caveats

- **Surface separation is non-negotiable.** A/B/C/D do not blur. Surface
  D (this `preview/` folder) never embeds inside a runtime cockpit
  screen by default — its job is to teach, not to chrome.
- **No font binaries by default.** Dopemux Term Regular is the canonical
  brand mono. Dopemux Term Nerd Font Regular is the canonical rich-glyph
  terminal font. Generated `.ttf`, `.otf`, `.woff`, and `.woff2` files are
  not committed without explicit approval.
- **ADHD/lifestyle features are advisory/future-only** unless runtime
  evidence proves implementation. Nothing in this system documents them.
- **Slice 1 only.** `Implementer`, `Overview`, `Events`, `PM` modes are
  rendered as `[EDGE]` placeholders in the seed. They are intentionally
  not styled in detail here.
- **Surface B and C are direction, not implementation.** They are scope
  markers for design conversation. They do not imply a live cockpit, a
  web app, service adapters, writes, proof artifact creation, or repo-truth-extractor execution.
