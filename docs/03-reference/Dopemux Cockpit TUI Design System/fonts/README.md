# Fonts

**Canonical brand mono:** `Dopemux Term Regular` (`DopemuxTerm-Regular.ttf`).
**Canonical rich-glyph terminal font:** `Dopemux Term Nerd Font Regular`
(`DopemuxTermNerdFont-Regular.ttf`).

User-facing family names are `Dopemux Term` and `Dopemux Term Nerd Font`.
The Iosevka name is build provenance only, and `IosevkaDopemuxTerm` is the
internal build plan name only. Nerd Fonts is patching/tooling provenance
only, not a public fallback dependency.

All cockpit metrics, spacing, and frame-grid dimensions are calibrated to
Dopemux Term Regular. It is the canonical brand font and the only font that
may be referred to as "the brand mono". Single weight; bold is synthesized.
Programming ligatures are disabled or minimized for cockpit terminal use.

## Fallback stack

```
1. Dopemux Term Regular
2. Dopemux Term Nerd Font Regular
3. `ui-monospace`
4. `monospace`
5. ASCII/text fallback for glyph loss
```

These are **terminal fallbacks**, not canonical brand font replacements.
Dopemux Term Regular is the canonical brand mono. Dopemux Term Nerd Font
Regular is the canonical rich-glyph terminal font. Glyphs are optional
rich-mode enhancements.

## Rich glyphs (optional, rich-mode only)

No generated font binary is committed without explicit approval. Rich-mode
glyph coverage is **optional**.
The cockpit can render Powerline / Nerd Font glyphs from the icon set in
`src/dopemux/ui/theme.py::Glyphs` when Dopemux Term Nerd Font is present,
but every glyph has an ASCII fallback in `Glyphs._FALLBACK`. The TUI must
remain legible without rich glyph coverage.

Build Dopemux Term Regular from the project build plan, then patch that
build with Nerd Fonts font-patcher to produce Dopemux Term Nerd Font
Regular. This is a rich-mode enhancement only; it does not replace Dopemux
Term Regular as the canonical brand mono.

If the active font or terminal environment cannot render a glyph, use the
ASCII/text fallback rather than switching brand fonts. ASCII fallback must
preserve meaning, and glyphs must never be the only signal.

See `BUILD.md`, `private-build-plans.toml`, and `patch-nerd-font.sh` for
the local build and patching recipe.
