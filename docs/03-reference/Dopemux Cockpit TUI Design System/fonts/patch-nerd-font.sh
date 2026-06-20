#!/usr/bin/env bash
set -euo pipefail

# Patch every built Dopemux face with Nerd Fonts glyphs.
#
# Local recipe only: does NOT download dependencies and generated binaries are
# NOT committed (.gitignore). Run build-dopemux-fonts.sh first to populate
# OUT_DIR with unpatched Dopemux*-*.ttf. See build.md.
#
# Required env:
#   NERD_FONTS_REPO  local checkout of https://github.com/ryanoasis/nerd-fonts
#   OUT_DIR          directory holding the built Dopemux*-*.ttf
# Optional env:
#   PATCHED_DIR      output dir for patched faces (default: $OUT_DIR/nerd-font)

: "${NERD_FONTS_REPO:?Set NERD_FONTS_REPO to a local Nerd Fonts checkout (git clone https://github.com/ryanoasis/nerd-fonts).}"
: "${OUT_DIR:?Set OUT_DIR to the directory holding built Dopemux*-*.ttf.}"

FONT_PATCHER="$NERD_FONTS_REPO/font-patcher"
PATCHED_DIR="${PATCHED_DIR:-$OUT_DIR/nerd-font}"
PATCH_TMP="$OUT_DIR/.dopemux-nerd-font-patch"
BUILD_MANIFEST="$OUT_DIR/.dopemux-built-fonts.txt"

cleanup_patch_tmp() {
  rm -rf "$PATCH_TMP"
}
trap cleanup_patch_tmp EXIT

[[ -d "$NERD_FONTS_REPO" ]] || { printf 'Missing NERD_FONTS_REPO directory: %s\n' "$NERD_FONTS_REPO" >&2; exit 1; }
[[ -f "$FONT_PATCHER" ]]    || { printf 'Missing Nerd Fonts font-patcher: %s\n' "$FONT_PATCHER" >&2; exit 1; }
[[ -d "$OUT_DIR" ]]        || { printf 'Missing OUT_DIR directory: %s\n' "$OUT_DIR" >&2; exit 1; }
command -v fontforge >/dev/null || { printf 'fontforge not found; install FontForge (brew install fontforge).\n' >&2; exit 1; }

# Inputs: faces produced by the current build-dopemux-fonts.sh run.
# (while-read rather than mapfile so this runs on macOS's stock bash 3.2.)
[[ -f "$BUILD_MANIFEST" ]] || { printf 'Missing build manifest: %s. Run build-dopemux-fonts.sh first.\n' "$BUILD_MANIFEST" >&2; exit 1; }
INPUTS=()
while IFS= read -r f; do
  [[ -n "$f" ]] || continue
  input="$OUT_DIR/$f"
  [[ -f "$input" ]] || { printf 'Manifested built font missing: %s\n' "$input" >&2; exit 1; }
  INPUTS+=("$input")
done < "$BUILD_MANIFEST"
if [[ "${#INPUTS[@]}" -eq 0 ]]; then
  printf 'No built Dopemux faces listed in %s. Run build-dopemux-fonts.sh first.\n' "$BUILD_MANIFEST" >&2
  exit 1
fi

mkdir -p "$PATCHED_DIR"
rm -f "$PATCHED_DIR"/DopemuxTermNerdFont-*.ttf "$PATCHED_DIR"/DopemuxEditorNerdFont-*.ttf

patched=0
for input in "${INPUTS[@]}"; do
  rm -rf "$PATCH_TMP"
  mkdir -p "$PATCH_TMP"
  printf 'Patching %s...\n' "$(basename "$input")"
  base="$(basename "$input" .ttf)"
  family="${base%%-*}"
  face="${base#*-}"

  patch_args=(--complete --careful)
  patch_name=""
  case "$family" in
    DopemuxTerm)
      patch_name="Dopemux Term Nerd Font"
      patch_args+=(--mono)
      ;;
    DopemuxEditor)
      patch_name="Dopemux Editor Nerd Font"
      patch_args+=(--variable-width-glyphs)
      ;;
    *)
      printf 'Unexpected built font family stem: %s (from %s)\n' "$family" "$(basename "$input")" >&2
      exit 1
      ;;
  esac
  patch_args+=(--name "$patch_name")

  # --complete: all Nerd Font glyph sets (guarantees the codepoints documented in
  #             src/dopemux/ui/theme.py::Glyphs).
  # --mono:     single-width cells for terminal / TUI rendering. Term only;
  # --variable-width-glyphs: keeps Editor icon advances proportional.
  # --name:     explicit family name; avoid deriving from full names, which can
  #             fragment Medium faces into a separate family.
  # --careful:  never overwrite glyphs already present in the source face.
  # font-patcher requires FontForge's Python: run via `fontforge -script`,
  # NOT `python3 font-patcher`.
  fontforge -quiet -script "$FONT_PATCHER" "$input" \
    "${patch_args[@]}" \
    --outputdir "$PATCH_TMP" >/dev/null

  produced=()
  while IFS= read -r f; do produced+=("$f"); done < <(find "$PATCH_TMP" -maxdepth 1 -type f -iname '*.ttf' -print)
  if [[ "${#produced[@]}" -ne 1 ]]; then
    printf 'Expected exactly one patched TTF for %s; found %s.\n' "$(basename "$input")" "${#produced[@]}" >&2
    exit 1
  fi

  # DopemuxTerm-MediumOblique.ttf -> DopemuxTermNerdFont-MediumOblique.ttf
  out="$PATCHED_DIR/${family}NerdFont-${face}.ttf"
  cp "${produced[0]}" "$out"
  printf '  -> %s\n' "$out"
  patched=$((patched + 1))
done
cleanup_patch_tmp

printf '\nPatched %s face(s) into %s\n' "$patched" "$PATCHED_DIR"
printf 'DopemuxTerm uses --mono; DopemuxEditor uses --variable-width-glyphs.\n'
printf 'Review generated binaries before committing; binaries are not committed by default (.gitignore).\n'
