#!/usr/bin/env bash
set -euo pipefail

# Local recipe only. This script does not download dependencies and generated
# font binaries are not committed by default.

: "${IOSEVKA_REPO:?Set IOSEVKA_REPO to a local Iosevka checkout.}"
: "${NERD_FONTS_REPO:?Set NERD_FONTS_REPO to a local Nerd Fonts checkout.}"
: "${OUT_DIR:?Set OUT_DIR to the output directory for generated fonts.}"

if [[ ! -d "$IOSEVKA_REPO" ]]; then
  printf 'Missing IOSEVKA_REPO directory: %s\n' "$IOSEVKA_REPO" >&2
  exit 1
fi

if [[ ! -d "$NERD_FONTS_REPO" ]]; then
  printf 'Missing NERD_FONTS_REPO directory: %s\n' "$NERD_FONTS_REPO" >&2
  exit 1
fi

if [[ ! -d "$OUT_DIR" ]]; then
  printf 'Missing OUT_DIR directory: %s\n' "$OUT_DIR" >&2
  exit 1
fi

FONT_PATCHER="$NERD_FONTS_REPO/font-patcher"
BUILT_FONT="$IOSEVKA_REPO/dist/IosevkaDopemuxTerm/TTF/DopemuxTerm-Regular.ttf"
PATCH_TMP="$OUT_DIR/.dopemux-term-nerd-font-patch"
PATCHED_FONT="$OUT_DIR/DopemuxTermNerdFont-Regular.ttf"

if [[ ! -f "$FONT_PATCHER" ]]; then
  printf 'Missing Nerd Fonts font-patcher: %s\n' "$FONT_PATCHER" >&2
  exit 1
fi

if [[ ! -f "$BUILT_FONT" ]]; then
  printf 'Missing built Dopemux Term font: %s\n' "$BUILT_FONT" >&2
  printf 'Build Dopemux Term Regular from private-build-plans.toml first.\n' >&2
  exit 1
fi

rm -rf "$PATCH_TMP"
mkdir -p "$PATCH_TMP"

# Prefer monospaced/single-width patching for terminal and TUI use.
python3 "$FONT_PATCHER" "$BUILT_FONT" \
  --mono \
  --careful \
  --outputdir "$PATCH_TMP"

mapfile -t PATCHED_OUTPUTS < <(find "$PATCH_TMP" -maxdepth 1 -type f -iname "*.ttf" -print)
if [[ "${#PATCHED_OUTPUTS[@]}" -ne 1 ]]; then
  printf 'Expected exactly one patched TTF in %s; found %s.\n' "$PATCH_TMP" "${#PATCHED_OUTPUTS[@]}" >&2
  exit 1
fi

cp "${PATCHED_OUTPUTS[0]}" "$PATCHED_FONT"
printf 'Wrote %s\n' "$PATCHED_FONT"
printf 'Review generated binaries before committing; binaries are not committed by default.\n'
