---
id: DOPEMUX_COCKPIT_TUI_DESIGN_SYSTEM_FONTS_BUILD
title: Dopemux Term Build Recipe
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-12'
last_review: '2026-06-12'
next_review: '2026-09-12'
prelude: Build and patch recipe for the Dopemux cockpit font stack.
---
# Dopemux Term Build Recipe

## Purpose

Local build + Nerd-Font patch recipe for the cockpit font stack. Generated
binaries are not shipped or committed by default.

Two families:

- `Dopemux Term` — canonical operator mono (spacing `term`).
- `Dopemux Editor` — quasi-proportional prose-set companion (`--font-editor`).

Canonical rich-glyph terminal font: `DopemuxTerm Nerd Font Mono`.

## Source tools

- Iosevka custom build via `private-build-plans.toml` (build provenance only)
- Nerd Fonts `font-patcher` (patching / tooling provenance only)

Operator-facing docs, CSS, previews, and UI kits use the Dopemux family names —
never "Iosevka" or "Nerd Fonts" as user-facing names.

## Faces

Per family: `Regular` + `Medium`, each `Upright` / `Italic` / `Oblique`, normal
width (12 faces total). Bold is the real Medium face — never synthesized. Slab is
excluded.

## Build flow

Prereqs: Node.js + npm; FontForge (`brew install fontforge`); local checkouts of
Iosevka and Nerd Fonts.

```sh
git clone https://github.com/be5invis/Iosevka      # IOSEVKA_REPO
git clone https://github.com/ryanoasis/nerd-fonts  # NERD_FONTS_REPO

export IOSEVKA_REPO=/path/to/Iosevka
export NERD_FONTS_REPO=/path/to/nerd-fonts
export OUT_DIR="$PWD/out"
mkdir -p "$OUT_DIR"

# 1. Build the unpatched Dopemux Term + Dopemux Editor faces.
./build-dopemux-fonts.sh

# 2. Patch each built face with Nerd Font glyphs.
./patch-nerd-font.sh
```

`build-dopemux-fonts.sh` copies `private-build-plans.toml` into the Iosevka
checkout and runs `npm run build -- ttf::IosevkaDopemuxTerm` and
`... ttf::IosevkaDopemuxEditor`, then collects the TTFs into `OUT_DIR`. Set
`IOSEVKA_TARGET=ttf-unhinted` to skip the `ttfautohint` dependency.

`patch-nerd-font.sh` runs `fontforge -script font-patcher --complete --careful`
over the faces from the current build manifest and writes
`$OUT_DIR/nerd-font/DopemuxTermNerdFont-*.ttf` (and `DopemuxEditorNerdFont-*`).
Term faces are patched with `--mono`; Editor faces keep their source spacing.
`--complete` guarantees the codepoints in `src/dopemux/ui/theme.py::Glyphs`.

> Patcher invocation note: `font-patcher` requires FontForge's Python and must be
> run as `fontforge -script font-patcher ...`, never `python3 font-patcher`.

## Output naming

- `DopemuxTerm-{Regular,Italic,Oblique,Medium,MediumItalic,MediumOblique}.ttf`
- `DopemuxEditor-{Regular,Italic,Oblique,Medium,MediumItalic,MediumOblique}.ttf`
- `DopemuxTermNerdFont-{...}.ttf` (internal family `DopemuxTerm Nerd Font Mono`)
- `DopemuxEditorNerdFont-{...}.ttf` (keeps Editor source spacing)

## Verification

From the repository root:

```sh
SCOPE="docs/03-reference/Dopemux Cockpit TUI Design System"

# Off-brand mono families must not appear in operator-facing files.
FORBIDDEN='Jet''Brains|Fira'' Code|SF''Mono|Men''lo|Con''solas'
rg -n "$FORBIDDEN" "$SCOPE" || true

rg -n "Dopemux Term|Dopemux Editor|DopemuxTerm|DopemuxEditor" "$SCOPE" || true

find "$SCOPE" -type f \( -iname '*.ttf' -o -iname '*.otf' -o -iname '*.woff' -o -iname '*.woff2' \) -print
git status --short --untracked-files=all

# After patching, confirm Nerd glyphs landed (example codepoints from Glyphs):
python3 - "$OUT_DIR/nerd-font/DopemuxTermNerdFont-Regular.ttf" <<'PY'
import sys
from fontTools.ttLib import TTFont
cmap = TTFont(sys.argv[1]).getBestCmap()
want = {0xF058: "success", 0xF057: "error", 0xF06A: "warning", 0xE725: "git", 0xF308: "docker"}
for cp, name in want.items():
    print(("OK  " if cp in cmap else "MISS"), f"U+{cp:04X}", name)
PY
```

The forbidden check should return nothing. The verification snippet should print
`OK` for every codepoint once patching has run.

## No-binary-commit rule

Generated `.ttf`, `.otf`, `.woff`, and `.woff2` files are not committed by
default (`.gitignore`). Commit binaries only after explicit approval and review
of the binary list.

## Notes

- `private-build-plans.toml` carries the family / spacing / weight / slope matrix.
  Ambiguity-reduction character variants (`cv__` / `ss__`) should be exported from
  the Iosevka Customizer into the `variants.design` sections, not hand-guessed.
- The legacy `IosevkaHueTerm` / `IosevkaHueEditorQP` exports (single "Extended"
  width, no Nerd glyphs) are superseded by the `Dopemux Term` / `Dopemux Editor`
  naming produced here.

## Future variants

- Additional weights beyond Regular/Medium may be added to
  `private-build-plans.toml` if cockpit surfaces need them.
- Slab is intentionally excluded from the cockpit font; explore only for
  display-only surfaces, never dense TUI / provenance / log / cockpit rows.
