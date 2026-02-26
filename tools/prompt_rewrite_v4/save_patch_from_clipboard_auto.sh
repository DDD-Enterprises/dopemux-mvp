#!/usr/bin/env bash
set -euo pipefail

# Read cursor from state.json to determine correct filename
STATE_FILE="/Users/hue/code/dopemux-mvp/tools/prompt_rewrite_v4/state.json"
if [[ ! -f "$STATE_FILE" ]]; then
  echo "ERROR: State file not found: $STATE_FILE"
  exit 1
fi

CURSOR=$(grep -o '"cursor":[[:space:]]*[0-9]*' "$STATE_FILE" | head -1 | cut -d: -f2 | tr -d ' ,')
if [[ -z "$CURSOR" ]]; then
  echo "ERROR: Could not determine cursor from state file"
  exit 2
fi

OUT="/Users/hue/code/dopemux-mvp/out/response_${CURSOR}.patch"

tmp="$(mktemp)"
pbpaste > "$tmp"

if [[ ! -s "$tmp" ]]; then
  echo "ERROR: Clipboard is empty."
  exit 3
fi

# Basic unified diff sanity
if ! grep -qE '^--- a/' "$tmp" || ! grep -qE '^\+\+\+ b/' "$tmp" || ! grep -qE '^@@ ' "$tmp"; then
  echo "ERROR: Clipboard does not look like a unified diff."
  echo "First 20 lines:"
  head -n 20 "$tmp"
  exit 4
fi

mkdir -p "$(dirname "$OUT")"
mv "$tmp" "$OUT"

echo "WROTE: $OUT (cursor=$CURSOR)"
echo "Preview:"
head -n 12 "$OUT"
echo ""
echo "Next: python tools/prompt_rewrite_v4/run_batch.py --apply"