# ACCEPTANCE.md

Acceptance checklist for the Dopemux cockpit design-system package.
Every box must be checkable against the artifacts in this folder.

---

## Tokens
- [x] No invented hex values; every color comes from `colors_and_type.css`.
- [x] No `--severity-*`, `--success-*`, `--warning-*`, `--error-*`,
      `--info-*`, `--debug-*`, `--hazard-*`, `--danger-*` aliases in CSS.
- [x] Token-card labels in `preview/01-brand-palette.html` use chip
      vocabulary (LIVE / LOGGED / BLOCKER / OVERRIDE / AFTERCARE) and
      role language (frame, heading, panel border) — never generic
      severity nouns.
- [x] Forbidden token-card label list is documented on the palette card.

## Status taxonomy
- [x] Closed chip set is the only status vocabulary:
      `LIVE, BLOCKER, OVERRIDE, LOGGED, AFTERCARE, EDGE`.
- [x] Forbidden chips are explicitly named:
      `UNKNOWN, DEGRADED, FAILED, BLOCKED, SYNC, DRAFT, READY, SUCCESS, ERROR`.
- [x] External vocab mapping is documented:
      `DEGRADED → OVERRIDE`, `FAILED → BLOCKER`, `BLOCKED → BLOCKER`,
      `SYNC → AFTERCARE`, `UNKNOWN → EDGE`.
- [x] Status Language explainer (`preview/14-status-language.html`)
      lives in design-system reference, not in the runtime cockpit.

## Chrome vs. data (SRC rule)
- [x] No `SRC=` token appears in the top frame header.
- [x] No `SRC=` in the mode bar.
- [x] No `SRC=` in the command rail.
- [x] No `SRC=` in the status rail.
- [x] No `SRC=` in the bottom flag rail.
- [x] `SRC=` appears on data rows (services, runs).
- [x] `SRC=` appears on inspector pane fields.
- [x] `SRC=` appears on bridge segregator action lines.

## Authority boundaries
- [x] Each pane declares `authority: <service>` in its header.
- [x] Bridge / proxy actions are segregated into a pane that labels
      itself `[EDGE] adapter-only segregated`.
- [x] No bridge / adapter / wrapper / shim is promoted to authority.
- [x] Where authority is unknown, the design uses literal `UNKNOWN`.
- [x] All ten canonical authorities are named in PREIMPLEMENTATION.md
      with their roles.

## Surface separation
- [x] Surface A — Static Terminal Snapshot — is labeled
      "STATIC DEMO · seed-only · read-only · no service adapters · no rte execution".
- [x] Surface A ships at three sizes (`A1` 120×40, `A2` 100×32, `A3` 80×24).
- [x] Surface B — Live Textual cockpit direction — is labeled
      "DESIGN DIRECTION · NOT IMPLEMENTED" and its chrome carries
      `writes:out-of-scope · proof-gen:out-of-scope · rte-exec:out-of-scope`.
- [x] Surface C — Web / operator dashboard direction — is labeled
      "DESIGN DIRECTION · NOT IMPLEMENTED" and preserves authority
      boundaries.
- [x] Surface D — Design-System Reference — lives in `preview/` and is
      not embedded inside any runtime cockpit screen.

## Typography & glyphs
- [x] Brand mono (`Iosevka Hue Term`, `fonts/IosevkaHueTerm-Regular.ttf`)
      is declared via `@font-face` in `colors_and_type.css`.
- [x] Mono fallback chain documented:
      Iosevka → JetBrains Mono Nerd Font → JetBrains Mono → Fira Code → system mono.
- [x] No Nerd Font binary ships; substitution flag is documented in
      `fonts/README.md` and the README.
- [x] ASCII fallback table card exists (`preview/21-ascii-fallback.html`)
      and maps every glyph + frame char to its ASCII substitute.
- [x] Box-drawing characters are single-cell or carry an ASCII fallback.
- [x] No emoji anywhere in operator-facing copy.

## Command glyphs
- [x] TUI surfaces (Surface A, Surface B) use `ctrl+k` / `command: k`,
      never `⌘K`.
- [x] Web surface (Surface C) is allowed to use `⌘K`; it also keeps
      keybinds visible for accessibility.

## Static / live scope discipline
- [x] Surface A footer says "STATIC DEMO · NO WRITES …".
- [x] Surface B footer says "DIRECTION · not implemented" and lists
      `writes / proof-gen / rte-exec` all as `out-of-scope`.
- [x] No surface implies a service adapter, a write, a proof bundle
      generation, or RTE execution.
- [x] No surface fakes a live stream beyond decorative cursor / WS pulse
      tokens that are themselves marked direction-only.

## Adaptation
- [x] Three frame sizes documented (120×40, 100×32, 80×24).
- [x] Adaptation rules documented in
      `preview/07-adaptation.html` — what disappears first, what must
      never disappear.
- [x] Below 80×24 is a `[BLOCKER]` panel — see
      `src/dopemux/ui/cockpit/render.py::TOO_SMALL_MESSAGE`.

## Error / blocker panel anatomy
- [x] Error panels carry `Problem / Why / Fix / NEXT`.
- [x] Forbidden phrasing is enumerated: "Something went wrong", "Oops",
      "Try again later", "Workflow supercharged", "Magic", etc.
- [x] Authority and write scope are part of the panel surface.

## Handoff
- [x] `PREIMPLEMENTATION.md` documents authority list, token map,
      forbidden assumptions, and the review gate.
- [x] `ACCEPTANCE.md` (this file) enumerates pass/fail criteria.
- [x] No file in this package is positioned as production code.
