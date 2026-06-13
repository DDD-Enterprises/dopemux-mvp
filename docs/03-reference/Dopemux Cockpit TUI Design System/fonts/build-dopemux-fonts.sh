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

# Build plans defined in private-build-plans.toml.
PLANS=(IosevkaDopemuxTerm IosevkaDopemuxEditor)

[[ -d "$IOSEVKA_REPO" ]] || { printf 'Missing IOSEVKA_REPO directory: %s\n' "$IOSEVKA_REPO" >&2; exit 1; }
[[ -d "$OUT_DIR" ]]      || { printf 'Missing OUT_DIR directory: %s\n' "$OUT_DIR" >&2; exit 1; }
[[ -f "$PLAN_SRC" ]]     || { printf 'Missing build plan: %s\n' "$PLAN_SRC" >&2; exit 1; }
command -v npm >/dev/null || { printf 'npm not found; install Node.js to build Iosevka.\n' >&2; exit 1; }

# Iosevka reads private-build-plans.toml from its repo root.
cp "$PLAN_SRC" "$IOSEVKA_REPO/private-build-plans.toml"

if [[ ! -d "$IOSEVKA_REPO/node_modules" ]]; then
  printf 'Installing Iosevka build dependencies (npm ci)...\n'
  ( cd "$IOSEVKA_REPO" && npm ci )
fi

for plan in "${PLANS[@]}"; do
  printf 'Building %s (%s)...\n' "$plan" "$IOSEVKA_TARGET"
  ( cd "$IOSEVKA_REPO" && npm run build -- "${IOSEVKA_TARGET}::${plan}" )

  src=""
  for sub in TTF TTF-Unhinted; do
    if [[ -d "$IOSEVKA_REPO/dist/$plan/$sub" ]]; then
      src="$IOSEVKA_REPO/dist/$plan/$sub"
      break
    fi
  done
  [[ -n "$src" ]] || { printf 'No TTF output for %s under %s/dist/%s\n' "$plan" "$IOSEVKA_REPO" "$plan" >&2; exit 1; }

  ttf_outputs=()
  while IFS= read -r f; do ttf_outputs+=("$f"); done < <(find "$src" -maxdepth 1 -type f -iname '*.ttf' -print | sort)
  count="${#ttf_outputs[@]}"
  if [[ "$count" -eq 0 ]]; then
    printf 'No TTF files produced for %s in %s\n' "$plan" "$src" >&2
    exit 1
  fi

  cp "${ttf_outputs[@]}" "$OUT_DIR"/
  printf '  copied %s TTF face(s) from %s\n' "$count" "$src"
done

printf '\nBuilt faces in %s:\n' "$OUT_DIR"
find "$OUT_DIR" -maxdepth 1 -iname 'Dopemux*-*.ttf' ! -iname '*NerdFont*' -print | sort
printf '\nBuild artifacts are not committed (.gitignore). Next: ./patch-nerd-font.sh\n'
