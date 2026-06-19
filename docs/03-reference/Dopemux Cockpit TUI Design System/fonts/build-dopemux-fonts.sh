#!/usr/bin/env bash
set -euo pipefail

# Build step for the Dopemux cockpit font stack (Dopemux Term + Dopemux Editor).
#
# Local recipe only: this script does NOT download Iosevka and does NOT commit
# binaries. It produces unpatched TTFs in OUT_DIR; run patch-nerd-font.sh next to
# generate the Nerd Font faces. See build.md.
#
# Required env:
#   IOSEVKA_REPO    local checkout of https://github.com/be5invis/Iosevka
#   OUT_DIR         directory to receive the built TTFs
# Optional env:
#   IOSEVKA_TARGET  Iosevka build target prefix (default: ttf; use ttf-unhinted
#                   to skip the ttfautohint dependency)

: "${IOSEVKA_REPO:?Set IOSEVKA_REPO to a local Iosevka checkout (git clone https://github.com/be5invis/Iosevka).}"
: "${OUT_DIR:?Set OUT_DIR to the output directory for built fonts.}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAN_SRC="$SCRIPT_DIR/private-build-plans.toml"
IOSEVKA_TARGET="${IOSEVKA_TARGET:-ttf}"
BUILD_MANIFEST="$OUT_DIR/.dopemux-built-fonts.txt"
BUILD_MANIFEST_TMP="$OUT_DIR/.dopemux-built-fonts.txt.tmp"
BUILD_STAGE="$OUT_DIR/.dopemux-build-stage"
PLAN_DST="$IOSEVKA_REPO/private-build-plans.toml"
PLAN_BACKUP=""
PLAN_HAD_ORIGINAL=0

# Build plans defined in private-build-plans.toml.
PLANS=(DopemuxTerm DopemuxEditor)

cleanup() {
  status=$?
  rm -f "$BUILD_MANIFEST_TMP"
  rm -rf "$BUILD_STAGE"
  if [[ -n "$PLAN_BACKUP" ]]; then
    if [[ "$PLAN_HAD_ORIGINAL" -eq 1 ]]; then
      cp "$PLAN_BACKUP" "$PLAN_DST"
    else
      rm -f "$PLAN_DST"
    fi
    rm -f "$PLAN_BACKUP"
  fi
  exit "$status"
}
trap cleanup EXIT

[[ -d "$IOSEVKA_REPO" ]] || { printf 'Missing IOSEVKA_REPO directory: %s\n' "$IOSEVKA_REPO" >&2; exit 1; }
[[ -f "$PLAN_SRC" ]]     || { printf 'Missing build plan: %s\n' "$PLAN_SRC" >&2; exit 1; }
command -v npm >/dev/null || { printf 'npm not found; install Node.js to build Iosevka.\n' >&2; exit 1; }
mkdir -p "$OUT_DIR"

PLAN_BACKUP="$(mktemp "${TMPDIR:-/tmp}/dopemux-iosevka-plan.XXXXXX")"
if [[ -f "$PLAN_DST" ]]; then
  cp "$PLAN_DST" "$PLAN_BACKUP"
  PLAN_HAD_ORIGINAL=1
fi
cp "$PLAN_SRC" "$PLAN_DST"

if [[ ! -d "$IOSEVKA_REPO/node_modules" ]]; then
  printf 'Installing Iosevka build dependencies (npm ci)...\n'
  ( cd "$IOSEVKA_REPO" && npm ci )
fi

: > "$BUILD_MANIFEST_TMP"
rm -rf "$BUILD_STAGE"
mkdir -p "$BUILD_STAGE"

for plan in "${PLANS[@]}"; do
  printf 'Building %s (%s)...\n' "$plan" "$IOSEVKA_TARGET"
  ( cd "$IOSEVKA_REPO" && npm run build -- "${IOSEVKA_TARGET}::${plan}" )

  case "$IOSEVKA_TARGET" in
    ttf) src="$IOSEVKA_REPO/dist/$plan/TTF" ;;
    ttf-unhinted) src="$IOSEVKA_REPO/dist/$plan/TTF-Unhinted" ;;
    *) printf 'Unsupported IOSEVKA_TARGET for TTF collection: %s\n' "$IOSEVKA_TARGET" >&2; exit 1 ;;
  esac
  [[ -n "$src" ]] || { printf 'No TTF output for %s under %s/dist/%s\n' "$plan" "$IOSEVKA_REPO" "$plan" >&2; exit 1; }
  [[ -d "$src" ]] || { printf 'Expected %s output for %s at %s\n' "$IOSEVKA_TARGET" "$plan" "$src" >&2; exit 1; }

  ttf_outputs=()
  while IFS= read -r f; do ttf_outputs+=("$f"); done < <(find "$src" -maxdepth 1 -type f -iname '*.ttf' -print | sort)
  count="${#ttf_outputs[@]}"
  if [[ "$count" -eq 0 ]]; then
    printf 'No TTF files produced for %s in %s\n' "$plan" "$src" >&2
    exit 1
  fi

  for f in "${ttf_outputs[@]}"; do
    base="$(basename "$f")"
    cp "$f" "$BUILD_STAGE/$base"
    printf '%s\n' "$base" >> "$BUILD_MANIFEST_TMP"
  done
  printf '  copied %s TTF face(s) from %s\n' "$count" "$src"
done

rm -f "$BUILD_MANIFEST"
rm -f "$OUT_DIR"/DopemuxTerm-*.ttf "$OUT_DIR"/DopemuxEditor-*.ttf
while IFS= read -r f; do
  [[ -n "$f" ]] || continue
  cp "$BUILD_STAGE/$f" "$OUT_DIR/$f"
done < "$BUILD_MANIFEST_TMP"
mv "$BUILD_MANIFEST_TMP" "$BUILD_MANIFEST"
rm -rf "$BUILD_STAGE"

printf '\nBuilt faces in %s:\n' "$OUT_DIR"
sed "s#^#$OUT_DIR/#" "$BUILD_MANIFEST"
printf '\nBuild artifacts are not committed (.gitignore). Next: ./patch-nerd-font.sh\n'
