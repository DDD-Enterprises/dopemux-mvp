#!/usr/bin/env bash
# Build verified TP-DMX-MEMORY-TRINITY-001 supervisor input pack zip.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

PACK_DIR="audit_inputs/TP-DMX-MEMORY-TRINITY-001-supervisor-input-pack"
REQUIRED_LIST="$PACK_DIR/PACK_REQUIRED_FILES.txt"
OUT_ZIP="$PACK_DIR/../TP-DMX-MEMORY-TRINITY-001-supervisor-input-pack.zip"
INVENTORY_JSON="$PACK_DIR/PACK_INVENTORY.json"
HEAD_SHA="$(git rev-parse HEAD)"

if [[ ! -f "$REQUIRED_LIST" ]]; then
  echo "ERROR: missing $REQUIRED_LIST" >&2
  exit 1
fi

mapfile -t REQUIRED < <(grep -v '^[[:space:]]*#' "$REQUIRED_LIST" | grep -v '^[[:space:]]*$')

missing=()
for f in "${REQUIRED[@]}"; do
  if [[ ! -f "$f" ]]; then
    missing+=("$f")
  fi
done

if ((${#missing[@]} > 0)); then
  echo "ERROR: missing required pack files:" >&2
  printf '  - %s\n' "${missing[@]}" >&2
  exit 1
fi

# Optional PAL artifacts (not in hard-required gate)
PAL_FILES=(proof/TP-DMX-MEMORY-TRINITY-001/pal/*.md)

rm -f "$OUT_ZIP"
zip -q "$OUT_ZIP" "${REQUIRED[@]}" "${PAL_FILES[@]}"

python3 - <<'PY' "$OUT_ZIP" "$INVENTORY_JSON" "$HEAD_SHA" "${REQUIRED[@]}"
import hashlib, json, sys, zipfile
from pathlib import Path

zip_path, inventory_path, head_sha, *required = sys.argv[1:]
zp = Path(zip_path)
with zipfile.ZipFile(zp, "r") as zf:
    entries = sorted(zf.namelist())
    files = [e for e in entries if not e.endswith("/")]
    total_uncompressed = sum(zf.getinfo(e).file_size for e in files)

inventory = {
    "pack_id": "TP-DMX-MEMORY-TRINITY-001-supervisor-input-pack",
    "built_at": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "repo_head_sha": head_sha,
    "zip_path": str(zp),
    "zip_bytes": zp.stat().st_size,
    "zip_sha256": hashlib.sha256(zp.read_bytes()).hexdigest(),
    "entry_count": len(files),
    "required_count": len(required),
    "required_present": {r: r in files for r in required},
    "entries": files,
    "supersedes": {
        "note": "Any pack < 120000 bytes or missing SUPERVISOR_FINAL_REVIEW / PROOF.json / l0_membership is stale",
        "stale_example_bytes": 108880,
        "stale_example_entries": 33,
    },
}
missing = [r for r, ok in inventory["required_present"].items() if not ok]
if missing:
    raise SystemExit(f"ZIP missing required entries: {missing}")

Path(inventory_path).write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
# Also embed inventory inside zip
import subprocess
subprocess.run(["zip", "-q", str(zp), inventory_path], check=True)
print(json.dumps({
    "zip_bytes": inventory["zip_bytes"],
    "zip_sha256": inventory["zip_sha256"],
    "entry_count": inventory["entry_count"],
    "head_sha": head_sha,
}, indent=2))
PY

echo "Built: $OUT_ZIP"
unzip -l "$OUT_ZIP" | tail -3