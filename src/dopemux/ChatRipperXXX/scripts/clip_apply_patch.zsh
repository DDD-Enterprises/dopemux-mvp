#!/usr/bin/env zsh
set -euo pipefail

# Clipboard-to-patch apply (macOS). Reads from pbpaste (no terminal paste).
# Normalizes: BOM, NBSP -> space, CRLF/CR -> LF. Then applies with git.
# If the clipboard is a mailbox patch (git format-patch), uses `git am --3way`.

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not inside a Git repository." >&2
  exit 1
fi

patch_file="$(mktemp -t chat_patch.XXXXXX.diff)"

# Pull from clipboard, normalize UTF-8 + NBSP + CRLF
# - Remove BOM (U+FEFF)
# - NBSP (U+00A0) -> SPACE
# - \r\n and \r -> \n
pbpaste | perl -CS -pe 's/\x{FEFF}//g; s/\x{00A0}/ /g; s/\r\n?/\n/g' > "$patch_file"

if [ ! -s "$patch_file" ]; then
  echo "Error: clipboard is empty or not textual." >&2
  exit 2
fi

# If it's a mailbox patch (git format-patch), prefer git am --3way
if head -n1 "$patch_file" | grep -qE '^From [0-9a-f]{40} '; then
  git am --3way "$patch_file"
  echo "Applied via: git am --3way"
  exit 0
fi

# Detect strip level: a/ b/ prefixes => -p1
strip=0
if grep -qE '^(---|\+\+\+) [ab]/' "$patch_file"; then
  strip=1
fi

# First attempt: 3-way apply with detected -p and whitespace warnings suppressed.
if git apply --index --3way --whitespace=nowarn -p"$strip" "$patch_file"; then
  [ "${1:-}" = "-c" ] && git commit -m "chore: apply clipboard patch"
  echo "Applied via: git apply --index --3way -p$strip"
  exit 0
fi

# Fallback matrix: try other strip levels and --unidiff-zero
for p in 0 1 2; do
  if git apply --index --3way --whitespace=nowarn -p"$p" "$patch_file"; then
    [ "${1:-}" = "-c" ] && git commit -m "chore: apply clipboard patch"
    echo "Applied via: git apply --index --3way -p$p (fallback)"
    exit 0
  fi
  if git apply --index --3way --whitespace=nowarn --unidiff-zero -p"$p" "$patch_file" 2>/dev/null; then
    [ "${1:-}" = "-c" ] && git commit -m "chore: apply clipboard patch"
    echo "Applied via: git apply --index --3way --unidiff-zero -p$p (fallback)"
    exit 0
  fi
done

echo "Failed to apply patch. Patch saved at: $patch_file" >&2
exit 3
