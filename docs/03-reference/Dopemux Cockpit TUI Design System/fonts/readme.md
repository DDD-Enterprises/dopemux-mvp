---
id: COCKPIT_FONTS_README
title: Fonts
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-12'
last_review: '2026-06-12'
next_review: '2026-09-12'
prelude: Font stack notes and build/patch pointers for the cockpit design system.
---

# Fonts

The cockpit ships two bespoke Iosevka-derived families, built locally from
`private-build-plans.toml` (see `build.md`). Generated binaries are **not**
committed (`.gitignore`).

| Family | Spacing | Role | CSS token |
|---|---|---|---|
| `Dopemux Term` | term (monospace) | operator / CLI / TUI mono | `--font-mono` |
| `Dopemux Editor` | quasi-proportional | prose-set code companion | `--font-editor` |
| `DopemuxTerm Nerd Font Mono` | term + Nerd glyphs | rich-glyph terminal icon set | terminal font |
| `Dopemux Editor Nerd Font` | quasi-proportional + Nerd glyphs | prose-set companion with icons | editor font |

Each family ships **Regular + Medium**, upright / italic / oblique. Bold is a
real Medium face — never synthesized.

## Font stack

Operator-facing CSS declares (off-brand mono families are excluded per the
forbidden list in `build.md`):

```
"DopemuxTerm Nerd Font Mono", "Dopemux Term", ui-monospace, monospace
```

The web cockpit (`colors_and_type.css`) loads `Dopemux Term` via `@font-face`.

## Nerd Font glyphs

The icon set in `src/dopemux/ui/theme.py::Glyphs` uses Nerd Font / Powerline
codepoints. These are **not** present in the plain `Dopemux Term` build — they
are added by patching it into **`DopemuxTerm Nerd Font Mono`** with the Nerd
Fonts `font-patcher` (`patch-nerd-font.sh`).

The fallback chain degrades gracefully: every glyph has an ASCII fallback in
`Glyphs._FALLBACK`, so the TUI stays legible even without the Nerd Font face.

## Build & patch

```sh
export IOSEVKA_REPO=/path/to/Iosevka          # git clone be5invis/Iosevka
export NERD_FONTS_REPO=/path/to/nerd-fonts    # git clone ryanoasis/nerd-fonts
export OUT_DIR="$PWD/out"  # ignored by fonts/.gitignore; build script creates it

./build-dopemux-fonts.sh    # Iosevka -> Dopemux Term / Dopemux Editor TTFs
./patch-nerd-font.sh        # -> $OUT_DIR/nerd-font/Dopemux{Term,Editor}NerdFont-*.ttf
```

See `build.md` for the full recipe, attributes, and verification.
