---
name: dopemux-cockpit-design
description: Use this skill to generate well-branded TUI / cockpit interfaces and assets for dopemux, either for production or throwaway prototypes/mocks/etc. Contains essential design guidelines, colors, type, fonts, assets, and the cockpit UI kit (frame, panes, status chips, mode bar, inspector, command/status rails) for terminal-native operator surfaces. Authority before aesthetics; closed chip set; 120x40 first.
user-invocable: true
---

Read the `README.md` file within this skill, and explore the other available files.

If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out and create static HTML files for the user to view. If working on production code, you can copy assets and read the rules here to become an expert in designing with this brand.

If the user invokes this skill without any other guidance, ask them what they want to build or design, ask some questions, and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.

## Architecture Safety Overlay (read first)

This skill is governed by the safety overlay set in this package. Read in
this order before producing any cockpit artifact:

- `ARCHITECTURE_SAFETY_OVERLAY.md` (wins on any conflict)
- `PM_IMPLEMENTER_COCKPIT_REDIRECTION.md`
- `UX_REFERENCE_RECONCILIATION.md`
- `PREIMPLEMENTATION.md`
- `ACCEPTANCE.md`

## Hard contract (do not violate)

- **Status chips are closed**: `LIVE | BLOCKER | OVERRIDE | LOGGED | AFTERCARE | EDGE`. Never invent new chips. External vocab maps at the boundary: `DEGRADED->OVERRIDE`, `FAILED->BLOCKER`, `BLOCKED->BLOCKER`, `SYNC->AFTERCARE`. **`UNKNOWN` does not map to a chip.** Render `UNKNOWN` as literal text in the affected field; never as a chip; never collapsed into `EDGE`. The mappings `UNKNOWN->EDGE`, `UNKNOWN -> EDGE`, `UNKNOWN=EDGE` are forbidden as positive doctrine.
- **Authority before aesthetics**: every pane declares the four-field block (`domain`, `authority`, `role`, `next_action`). Authority is `dopemux` for chrome (`role: chrome`); data authority is declared per child surface / row.
- **Provenance rule**: Every logical data/provenance record carries `SRC=<service>` once. Wrapped continuation rows align under the content column and do not repeat `SRC` unless physical rows are independently selectable/copyable. `SRC` never appears in chrome.
- **Bridge adapter/proxy: dopecon-bridge.** Bridge actions are adapter / proxy actions only and never represent canonical writes. Bridge surfaces are visually segregated and labeled `adapter-only segregated`. The phrase `Bridge actions authority: dopecon-bridge` is forbidden.
- **Three sizes only**: `120x40` (canonical), `100x32`, `80x24`. Below 80x24 = `[BLOCKER]`. Bridge never sits as a peer pane to canonical state at `80x24`.
- **No web UI, mouse interactions, hover states, chat surfaces, animations, gradients, rounded corners, shadows, or emoji.** Emoji/glyphs may be rich-mode-only or optional, but never the only signal — text and symbols carry meaning without color.
- **Wordmark and glyphs are non-semantic**: canonical stylized wordmark is `DØPΞM∪X`; plain fallback is `DOPEMUX`; compact seal is `◆DØPΞM∪X◆`; rejected artifact is `ᗪØƤΞM∪╳`. The stylized wordmark is allowed only in chrome, title bars, splash / brand previews, and non-semantic headers. Glyphs are visual cues only and must never define authority, provenance, workflow legality, validation result, source truth, state, or replace `domain`, `authority`, `role`, `next_action`, `SRC`, `status`, or `result`.
- **Type**: **Canonical brand mono: Dopemux Term Regular**. Canonical rich-glyph terminal font: Dopemux Term Nerd Font Regular. User-facing family names are `Dopemux Term` and `Dopemux Term Nerd Font`. Build provenance is the Iosevka Customizer plus `fonts/private-build-plans.toml`; `IosevkaDopemuxTerm` is the internal build plan name only. Nerd Fonts patching is tooling provenance only. Fallback stack: Dopemux Term Regular; Dopemux Term Nerd Font Regular; `ui-monospace`; `monospace`; ASCII/text fallback for glyph loss. Single weight per surface; emphasis = bold + color. Programming ligatures are disabled or minimized for cockpit terminal use.
- **Forbidden vocabulary** (validated by `cockpit/tokens.py`): `magic, brain, autonomous, smart, seamless, next-gen, all set, everything looks good, supercharged, probably, maybe, I think, as an AI`. Unicode arrows and Unicode ellipsis are forbidden in package copy. Use ASCII `->` when directionality is needed.
- **PLAIN/AUDIT log-safe rule**: PLAIN and AUDIT modes contain no ANSI escape codes, no animation, and no color-only signal; output is machine-readable and stable across runs.
- **ADHD/lifestyle features are advisory/future-only** unless runtime evidence proves implementation. ADHD cues never gate workflow and never become status chips.

## Files in this skill

- `README.md` — full design system documentation
- `colors_and_type.css` — CSS tokens
- `preview/` — design-system reference cards
- `ui_kits/cockpit/` — React+Babel UI kit (primitives + composed cockpit)
- `assets/` — glyph + frame-character reference, brand mark
- `fonts/` — Dopemux Term build recipe and font stack notes (no binaries committed without explicit approval)
