# Dopemux Term Build Recipe

## Purpose

This folder documents the local build recipe for the cockpit terminal font.
It does not ship generated font binaries by default.

Canonical brand mono: `Dopemux Term Regular`.
Canonical rich-glyph terminal font: `Dopemux Term Nerd Font Regular`.
User-facing font families are `Dopemux Term` and `Dopemux Term Nerd Font`.

## Source Tools

- Iosevka Customizer
- Iosevka custom build via `private-build-plans.toml`
- Nerd Fonts font-patcher

Iosevka is build provenance only. Nerd Fonts is patching/tooling provenance
only. Operator-facing docs, CSS, previews, surfaces, and UI kit examples use
the Dopemux family names.

## Local Build Flow

1. Generate/refine `private-build-plans.toml` using the Iosevka Customizer.
2. Build Dopemux Term Regular from Iosevka source.
3. Patch the built font with Nerd Fonts font-patcher.
4. Install/test locally.
5. Do not commit binaries without explicit approval.

## Output Naming

- `DopemuxTerm-Regular.ttf`
- `DopemuxTermNerdFont-Regular.ttf`

## Build Attributes

- spacing: `term`
- serifs: `sans`
- weight: `Regular / 400`
- slope: `upright`
- width: `normal`
- ligatures: disabled or minimized for cockpit terminal use
- character variants prioritize ambiguity reduction
- supports Dopemux cockpit branding and mint-mojo operator surfaces

## Verification Commands

From the repository root:

```sh
SCOPE="docs/03-reference/Dopemux Cockpit TUI Design System"

FORBIDDEN_FONTS='Jet''Brains|Jet''Brains Mono|Fira'' Code|SF''Mono|Men''lo|Con''solas'
rg -n "$FORBIDDEN_FONTS" "$SCOPE" || true

rg -n "Dopemux Term|DopemuxTerm|Dopemux Term Nerd Font|DopemuxTermNerdFont" "$SCOPE" || true

find "$SCOPE" -type f \( -iname "*.ttf" -o -iname "*.otf" -o -iname "*.woff" -o -iname "*.woff2" \) -print
git status --short --untracked-files=all
```

The first command should return no matches. The Dopemux naming command
should show package-wide use of the Dopemux family names. The binary check
must be reviewed before any commit or artifact handoff.

## No-Binary-Commit Rule

Generated `.ttf`, `.otf`, `.woff`, and `.woff2` files are not committed by
default. Commit generated binaries only after explicit approval and after
the binary list has been reviewed.

## Future Variants

- Bold may be added later if cockpit surfaces need a real bold face instead
  of synthesized bold.
- Slab is intentionally excluded from the canonical cockpit terminal font.
  It may be explored later for display-only surfaces, never dense TUI,
  provenance, log, or cockpit rows.
