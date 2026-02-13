#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/Users/hue/code/dopemux-mvp"
PM_DIR="$REPO_ROOT/src/dopemux/pm"
OUT_FILE="$REPO_ROOT/pm_arch_a_bundle.txt"

echo "=== Dopemux PM ARCH-A Export ==="
echo "Repo: $REPO_ROOT"
echo "Branch:"
git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD
echo "Commit:"
git -C "$REPO_ROOT" rev-parse HEAD
echo

if [ ! -d "$PM_DIR" ]; then
  echo "ERROR: $PM_DIR not found"
  exit 1
fi

FILES=(
  "__init__.py"
  "models.py"
  "mapping.py"
  "store.py"
)

echo "Writing bundle to $OUT_FILE"
echo "=== Dopemux PM ARCH-A Bundle ===" > "$OUT_FILE"
echo >> "$OUT_FILE"

for f in "${FILES[@]}"; do
  FULL="$PM_DIR/$f"
  if [ -f "$FULL" ]; then
    echo "----- BEGIN FILE: src/dopemux/pm/$f -----" >> "$OUT_FILE"
    echo >> "$OUT_FILE"
    cat "$FULL" >> "$OUT_FILE"
    echo >> "$OUT_FILE"
    echo "----- END FILE: src/dopemux/pm/$f -----" >> "$OUT_FILE"
    echo >> "$OUT_FILE"
  else
    echo "WARNING: $FULL not found" | tee -a "$OUT_FILE"
  fi
done

echo "Done."
echo "Bundle created at: $OUT_FILE"
