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
# Embed inventory inside zip, then refresh sidecar fingerprints (zip size/hash change on embed)
import subprocess
subprocess.run(["zip", "-q", str(zp), inventory_path], check=True)
with zipfile.ZipFile(zp, "r") as zf:
    entries = sorted(zf.namelist())
    files = [e for e in entries if not e.endswith("/")]
inventory["entry_count"] = len(files)
inventory["entries"] = files

def zip_fingerprint(zpath: Path, exclude: str | None = None) -> tuple[int, str]:
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(zpath, "r") as zin, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if exclude and item.filename == exclude:
                continue
            zout.writestr(item, zin.read(item.filename))
    payload = buf.getvalue()
    return len(payload), hashlib.sha256(payload).hexdigest()

def replace_zip_entry(zpath: Path, entry: str, src: Path) -> None:
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(zpath, "r") as zin, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == entry:
                continue
            zout.writestr(item, zin.read(item.filename))
        zout.write(src, entry)
    zpath.write_bytes(buf.getvalue())

# Fingerprint excludes inventory entry to avoid self-referential hash drift
inv_bytes, inv_sha = zip_fingerprint(zp, exclude=inventory_path)
inventory["zip_bytes"] = zp.stat().st_size
inventory["zip_bytes_excluding_inventory"] = inv_bytes
inventory["zip_sha256"] = inv_sha
inventory["zip_sha256_scope"] = "all_entries_except_PACK_INVENTORY.json"
Path(inventory_path).write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
replace_zip_entry(zp, inventory_path, Path(inventory_path))
inventory["zip_bytes"] = zp.stat().st_size
inventory["zip_bytes_excluding_inventory"], inventory["zip_sha256"] = zip_fingerprint(zp, exclude=inventory_path)
Path(inventory_path).write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
replace_zip_entry(zp, inventory_path, Path(inventory_path))
print(json.dumps({
    "zip_bytes": inventory["zip_bytes"],
    "zip_sha256": inventory["zip_sha256"],
    "entry_count": inventory["entry_count"],
    "head_sha": head_sha,
}, indent=2))
PY

echo "Built: $OUT_ZIP"
unzip -l "$OUT_ZIP" | tail -3