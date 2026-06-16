#!/usr/bin/env bash
set -euo pipefail

# Validate patched Dopemux Nerd Font names and advance-width behavior.
# Exit 77 means NOT_RUN: required local patched fonts or fontTools are absent.

if [[ "${1:-}" != "" ]]; then
  PATCHED_DIR="$1"
elif [[ "${PATCHED_DIR:-}" != "" ]]; then
  :
elif [[ "${OUT_DIR:-}" != "" ]]; then
  PATCHED_DIR="$OUT_DIR/nerd-font"
else
  printf 'NOT_RUN: set PATCHED_DIR or OUT_DIR, or pass the patched font directory.\n' >&2
  exit 77
fi

if ! python3 -c 'import fontTools.ttLib' >/dev/null 2>&1; then
  printf 'NOT_RUN: python fontTools is not installed.\n' >&2
  exit 77
fi

if [[ ! -d "$PATCHED_DIR" ]]; then
  printf 'NOT_RUN: patched font directory not found: %s\n' "$PATCHED_DIR" >&2
  exit 77
fi

has_fonts=0
for f in "$PATCHED_DIR"/DopemuxTermNerdFont-*.ttf "$PATCHED_DIR"/DopemuxEditorNerdFont-*.ttf; do
  [[ -e "$f" ]] || continue
  has_fonts=1
done
if [[ "$has_fonts" -eq 0 ]]; then
  printf 'NOT_RUN: no patched Dopemux Nerd Font TTFs found in %s\n' "$PATCHED_DIR" >&2
  exit 77
fi

python3 - "$PATCHED_DIR" <<'PY'
from pathlib import Path
import sys
from fontTools.ttLib import TTFont

patched_dir = Path(sys.argv[1])
families = {
    "DopemuxTermNerdFont": {
        "expected_name": "Dopemux Term Nerd Font",
        "expect_single_width": True,
    },
    "DopemuxEditorNerdFont": {
        "expected_name": "Dopemux Editor Nerd Font",
        "expect_single_width": False,
    },
}
sample_codepoints = [ord(c) for c in "iWm.M0"]


def preferred_family(font):
    names = font["name"].names
    for name_id in (16, 1):
        for record in names:
            if record.nameID == name_id:
                value = record.toUnicode().strip()
                if value:
                    return value
    raise AssertionError("missing name ID 16 and ID 1 family")


def widths_for(font, cps):
    cmap = font.getBestCmap() or {}
    hmtx = font["hmtx"]
    widths = []
    for cp in cps:
        glyph = cmap.get(cp)
        if glyph is None:
            continue
        widths.append(hmtx[glyph][0])
    if len(widths) < 2:
        raise AssertionError("too few sample glyph widths available")
    return widths


for prefix, contract in families.items():
    paths = sorted(patched_dir.glob(f"{prefix}-*.ttf"))
    if not paths:
        raise AssertionError(f"missing patched faces for {prefix}")

    styles = {p.stem.removeprefix(prefix + "-") for p in paths}
    for required in ("Regular", "Medium"):
        if required not in styles:
            raise AssertionError(f"{prefix} missing required {required} face")

    seen_names = set()
    for path in paths:
        font = TTFont(path)
        family_name = preferred_family(font)
        seen_names.add(family_name)
        widths = widths_for(font, sample_codepoints)
        unique_widths = sorted(set(widths))
        if contract["expect_single_width"]:
            if len(unique_widths) != 1:
                raise AssertionError(f"{path.name}: expected single-width samples, saw {unique_widths}")
        else:
            if len(unique_widths) < 2:
                raise AssertionError(f"{path.name}: expected proportional samples, saw {unique_widths}")

    if seen_names != {contract["expected_name"]}:
        raise AssertionError(f"{prefix}: expected {contract['expected_name']!r}, saw {sorted(seen_names)!r}")

    print(f"PASS {prefix}: family={contract['expected_name']} faces={len(paths)}")
PY
