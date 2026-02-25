#!/usr/bin/env bash
set -euo pipefail

OUT="/Users/hue/code/dopemux-mvp/out/response_0.patch"

tmp="$(mktemp)"
pbpaste > "$tmp"

if [[ ! -s "$tmp" ]]; then
  echo "ERROR: Clipboard is empty."
  exit 2
fi

# Basic unified diff sanity
if ! grep -qE '^--- a/' "$tmp" || ! grep -qE '^\+\+\+ b/' "$tmp" || ! grep -qE '^@@ ' "$tmp"; then
  echo "ERROR: Clipboard does not look like a unified diff."
  echo "First 20 lines:"
  head -n 20 "$tmp"
  exit 3
fi

mkdir -p "$(dirname "$OUT")"
mv "$tmp" "$OUT"

echo "WROTE: $OUT"
echo "Preview:"
head -n 12 "$OUT"